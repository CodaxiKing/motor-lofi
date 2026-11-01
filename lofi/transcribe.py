"""Transcreve arquivos de voz e devolve os trechos com tempo (para montar clips e legendas).

    python3 -m lofi.transcribe roberta.mp3 rafa.mp3 lia.mp3   -> imprime e salva <arquivo>.json
    python3 -m lofi.transcribe --sem-texto roberta.mp3          -> só os tempos (sem Whisper)
    python3 -m lofi.transcribe --conferir series/x/ep03.json     -> o que é falado em cada cena da mixagem

Os trechos são separados pelo silêncio (ffmpeg). O texto de cada trecho vem do Whisper small (modelo ONNX do sherpa-onnx,
~640 MB, baixado do GitHub na primeira vez). Roda com o pacote sherpa-onnx ou, se ele não instalar, só com numpy +
onnxruntime (lofi/whisper_ort.py). Só se nada disso funcionar o comando entrega os tempos sem texto.

ATENÇÃO: um trecho pode conter várias falas (a voz não pausa entre todas). Case as falas pelo TEXTO, nunca pela ordem ou
pela duração, e quando um trecho juntar falas que vão para cenas diferentes, divida-o nas micropausas e confira cada
pedaço transcrevendo de novo. Depois de montar, confira a mixagem cena a cena (transcreva o _mix.wav por cena).
"""
import sys, os, re, json, subprocess, tarfile
from . import wavio

MODEL_DIR = os.path.expanduser("~/.lofi_models/sherpa-onnx-whisper-small")
URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2"


def ensure_model():
    if os.path.exists(os.path.join(MODEL_DIR, "small-tokens.txt")): return
    os.makedirs(os.path.dirname(MODEL_DIR), exist_ok=True)
    tgz = MODEL_DIR + ".tar.bz2"
    print("baixando modelo de transcrição (~600 MB)...", flush=True)
    subprocess.run(["curl", "-sfL", "-o", tgz, URL], check=True)
    with tarfile.open(tgz) as t: t.extractall(os.path.dirname(MODEL_DIR))
    os.remove(tgz)


class _OrtRecognizer:
    """Mesma interface usada abaixo, mas com o Whisper rodando só em numpy + onnxruntime (lofi/whisper_ort.py)."""
    def __init__(self, lang):
        from .whisper_ort import Whisper
        M = os.path.join(MODEL_DIR, "small-")
        self.w = Whisper(M + "encoder.int8.onnx", M + "decoder.int8.onnx", M + "tokens.txt"); self.lang = lang
    def text(self, audio16k):
        return self.w.transcribe(audio16k, self.lang)


def load_recognizer(lang="pt"):
    """Devolve o reconhecedor do Whisper, ou None (com o motivo) se não der para usar.
    Ordem: sherpa-onnx (se instalado) → onnxruntime puro (lofi/whisper_ort.py) → só tempos."""
    try:
        ensure_model()
    except Exception as e:
        return None, f"modelo do Whisper indisponível ({e})"
    try:
        import sherpa_onnx
        M = os.path.join(MODEL_DIR, "small-")
        rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M + "encoder.int8.onnx", decoder=M + "decoder.int8.onnx",
                                                         tokens=M + "tokens.txt", language=lang, task="transcribe", num_threads=4)
        return rec, None
    except ImportError:
        pass
    try:
        return _OrtRecognizer(lang), None
    except Exception as e:
        return None, f"sherpa-onnx não instalado e onnxruntime indisponível ({e})"


def segments(wav, dur):
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "silencedetect=noise=-35dB:d=0.3", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    ss = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    return [(s, e) for s, e in zip([0.0] + se, ss + [dur]) if e - s >= 0.15]


def transcribe(path, lang="pt", rec=None):
    wav = path + ".16k.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-ar", "16000", "-ac", "1", wav], check=True)
    a, sr = wavio.read(wav, dtype="float32")
    dur = len(a) / sr; segs = []
    for s, e in segments(wav, dur):
        txt = ""
        piece = a[max(0, int((s - 0.15) * sr)): int((e + 0.15) * sr)]
        if isinstance(rec, _OrtRecognizer):
            txt = rec.text(piece)
        elif rec is not None:
            st = rec.create_stream(); st.accept_waveform(sr, piece)
            rec.decode_stream(st); txt = st.result.text.strip()
        segs.append({"s": round(s, 2), "e": round(e, 2), "t": txt})
    json.dump(segs, open(path + ".json", "w"), ensure_ascii=False, indent=1)
    return segs, dur


def conferir(spec_path):
    """Ouve a mixagem do episódio cena a cena e imprime o que é falado em cada plano, para comparar com o roteiro."""
    from .render import Episode
    rec, motivo = load_recognizer()
    if not isinstance(rec, _OrtRecognizer) and rec is not None:
        rec = _OrtRecognizer("pt")  # interface simples de texto
    if rec is None: print(f"[ERRO] sem transcrição: {motivo}"); return 1
    ep = Episode(spec_path); ep.build_audio()
    wav = os.path.join(ep.base, "_conferir16k.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", ep.mix_path, "-ar", "16000", "-ac", "1", wav], check=True)
    a, sr = wavio.read(wav, dtype="float32"); os.remove(wav)
    for s in ep.shots:
        if s.get("type") in ("title", "choice"): continue
        txt = rec.text(a[int(s["start"] * sr): int(s["end"] * sr)])
        rot = s.get("scene") or s.get("subject") or s.get("type")
        print(f"{s['start']:6.1f}-{s['end']:6.1f}  {rot:14s} | {txt or '(sem fala)'}")
    return 0


if __name__ == "__main__":
    if "--conferir" in sys.argv:
        sys.exit(conferir(sys.argv[sys.argv.index("--conferir") + 1]))
    files = [p for p in sys.argv[1:] if not p.startswith("--")]
    rec, motivo = (None, "pedido --sem-texto") if "--sem-texto" in sys.argv else load_recognizer()
    if rec is None:
        print(f"[AVISO] transcrição só com tempos: {motivo}. Case os trechos com as falas do roteiro pela ordem.", flush=True)
    for p in files:
        segs, dur = transcribe(p, rec=rec)
        print(f"=== {os.path.basename(p)} ({dur:.2f}s, {len(segs)} trechos)")
        for s in segs: print(f"{s['s']:6.2f}-{s['e']:6.2f}  {s['t'] or '(sem texto)'}")
