"""Boca pela voz com o Rhubarb Lip Sync (github.com/DanielSWolf/rhubarb-lip-sync), modo fonético (funciona em português).

O Rhubarb é baixado do GitHub na primeira vez (≈ 90 MB, guardado em ~/.cache/motor-lofi) e roda no processador.
Ele devolve um formato de boca por trecho (9 formatos de animação de desenho), que viram os códigos do rig:

    Rhubarb  som                         código do rig
    X        repouso                     0
    A        M, B, P (lábios fechados)   1
    B        K, S, T, I (dentes)          3
    C        E, É (aberta)                2
    D        A (bem aberta)               8
    E        Ó, Ô (redonda)               4
    F        U, W (biquinho)              5
    G        F, V (dente no lábio)        6
    H        L (língua)                   7

Uso no motor: automático (audio.mix chama `visemas`). Desligue com `"boca": "espectro"` no episódio.
Linha de comando:  python3 -m lofi.rhubarb voz.mp3   → imprime os formatos com os tempos.
"""
import os, sys, json, hashlib, shutil, subprocess, tempfile
import numpy as np

VERSAO = "1.13.0"
URL = f"https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v{VERSAO}/Rhubarb-Lip-Sync-{VERSAO}-Linux.zip"
PASTA = os.path.join(os.path.expanduser("~"), ".cache", "motor-lofi")
BIN = os.path.join(PASTA, f"Rhubarb-Lip-Sync-{VERSAO}-Linux", "rhubarb")
CODIGO = {"X": 0, "A": 1, "B": 3, "C": 2, "D": 8, "E": 4, "F": 5, "G": 6, "H": 7}
_AVISO = {"feito": False}


def binario():
    """Caminho do rhubarb (baixa e descompacta se preciso) ou None se não der."""
    if os.path.exists(BIN): return BIN
    if os.environ.get("LOFI_SEM_RHUBARB"): return None
    os.makedirs(PASTA, exist_ok=True)
    z = os.path.join(PASTA, "rhubarb.zip")
    try:
        for _ in range(4):        # o download às vezes cai no meio: continua de onde parou
            r = subprocess.run(["curl", "-sSL", "--retry", "3", "-C", "-", "-o", z, URL], capture_output=True, timeout=600)
            if r.returncode == 0: break
        subprocess.run(["unzip", "-q", "-o", z, "-d", PASTA], check=True, capture_output=True, timeout=300)
        os.chmod(BIN, 0o755); os.remove(z)
        return BIN if os.path.exists(BIN) else None
    except Exception as e:
        if not _AVISO["feito"]:
            print(f"rhubarb indisponível ({e}); a boca usa o cálculo pelo espectro", file=sys.stderr); _AVISO["feito"] = True
        return None


def cues(wav_path):
    """Lista [(início, fim, letra)] do Rhubarb para um WAV."""
    b = binario()
    if not b: return None
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "o.json")
        r = subprocess.run([b, "-q", "-r", "phonetic", "-f", "json", "-o", out, wav_path], capture_output=True, timeout=1800)
        if r.returncode != 0 or not os.path.exists(out): return None
        d = json.load(open(out))
    return [(c["start"], c["end"], c["value"]) for c in d.get("mouthCues", [])]


def visemas(buf, sr, step, cache_dir=None):
    """Código de boca por quadro (array int8) para a voz `buf` (float, já no tempo do episódio), ou None se falhar.
    Trechos de silêncio longos são pulados (o Rhubarb roda só onde há fala) e o resultado fica em cache."""
    n = len(buf) // step
    if n == 0: return np.zeros(0, dtype=np.int8)
    h = hashlib.sha1(np.round(buf[::7] * 2000).astype(np.int16).tobytes()).hexdigest()[:16]
    cpath = os.path.join(cache_dir, f"rhubarb_{h}.json") if cache_dir else None
    lista = None
    if cpath and os.path.exists(cpath):
        try: lista = json.load(open(cpath))
        except Exception: lista = None
    if lista is None:
        lista = []
        for a, b in _trechos(buf, sr):
            seg = buf[a:b]
            with tempfile.TemporaryDirectory() as tmp:
                w = os.path.join(tmp, "v.wav"); _grava_wav(w, seg, sr)
                cs = cues(w)
            if cs is None: return None
            lista += [[a / sr + c0, a / sr + c1, v] for c0, c1, v in cs]
        if cpath:
            os.makedirs(cache_dir, exist_ok=True); json.dump(lista, open(cpath, "w"))
    out = np.zeros(n, dtype=np.int8)
    fps = sr / step
    for c0, c1, v in lista:
        i0, i1 = int(round(c0 * fps)), int(round(c1 * fps))
        out[max(0, i0):min(n, max(i1, i0 + 1))] = CODIGO.get(v, 0)
    return out


def _trechos(buf, sr, gap=1.0, pad=0.25):
    """Intervalos (amostras) com fala, unindo pausas menores que `gap` s."""
    blk = int(sr * 0.05); nb = len(buf) // blk
    if nb == 0: return []
    lv = np.sqrt(np.mean(buf[:nb * blk].reshape(nb, blk) ** 2, axis=1))
    on = lv > max(1e-4, np.percentile(lv[lv > 1e-5], 60) * 0.12) if np.any(lv > 1e-5) else np.zeros(nb, bool)
    res, ini, ult = [], None, None
    for i, v in enumerate(on):
        if v:
            if ini is None: ini = i
            elif (i - ult) * 0.05 > gap: res.append((ini, ult)); ini = i
            ult = i
    if ini is not None: res.append((ini, ult))
    p = int(pad / 0.05)
    return [(max(0, (a - p) * blk), min(len(buf), (b + 1 + p) * blk)) for a, b in res]


def _grava_wav(path, sig, sr):
    from scipy.io import wavfile
    from scipy.signal import resample_poly
    x = resample_poly(sig, 16000, sr) if sr != 16000 else sig
    wavfile.write(path, 16000, (np.clip(x, -1, 1) * 32000).astype(np.int16))


if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    src = sys.argv[1]
    with tempfile.TemporaryDirectory() as tmp:
        w = os.path.join(tmp, "v.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", "16000", w], check=True)
        cs = cues(w)
    if cs is None: print("rhubarb indisponível"); sys.exit(1)
    for a, b, v in cs: print(f"{a:7.2f} {b:7.2f}  {v}")
