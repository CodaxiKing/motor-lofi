"""Transcreve arquivos de voz e devolve os trechos com tempo (para montar clips e legendas).

    python3 -m lofi.transcribe roberta.mp3 rafa.mp3 lia.mp3   -> imprime e salva <arquivo>.json
    python3 -m lofi.transcribe --sem-texto roberta.mp3          -> só os tempos (sem Whisper)

Os trechos são separados pelo silêncio (ffmpeg). O texto de cada trecho vem do Whisper (sherpa-onnx), baixado na
primeira vez. Se o sherpa-onnx não estiver instalado ou o modelo não puder ser baixado, o comando continua e entrega
só os tempos, com o texto vazio: nesse caso, case os trechos com as falas do roteiro pela ordem em que aparecem.
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


def load_recognizer(lang="pt"):
    """Devolve o reconhecedor do Whisper, ou None (com o motivo) se não der para usar."""
    try:
        import sherpa_onnx
    except Exception:
        return None, "sherpa-onnx não instalado"
    try:
        ensure_model()
    except Exception as e:
        return None, f"modelo do Whisper indisponível ({e})"
    M = os.path.join(MODEL_DIR, "small-")
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M + "encoder.int8.onnx", decoder=M + "decoder.int8.onnx",
                                                     tokens=M + "tokens.txt", language=lang, task="transcribe", num_threads=4)
    return rec, None


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
        if rec is not None:
            st = rec.create_stream(); st.accept_waveform(sr, a[max(0, int((s - 0.15) * sr)): int((e + 0.15) * sr)])
            rec.decode_stream(st); txt = st.result.text.strip()
        segs.append({"s": round(s, 2), "e": round(e, 2), "t": txt})
    json.dump(segs, open(path + ".json", "w"), ensure_ascii=False, indent=1)
    return segs, dur


if __name__ == "__main__":
    files = [p for p in sys.argv[1:] if not p.startswith("--")]
    rec, motivo = (None, "pedido --sem-texto") if "--sem-texto" in sys.argv else load_recognizer()
    if rec is None:
        print(f"[AVISO] transcrição só com tempos: {motivo}. Case os trechos com as falas do roteiro pela ordem.", flush=True)
    for p in files:
        segs, dur = transcribe(p, rec=rec)
        print(f"=== {os.path.basename(p)} ({dur:.2f}s, {len(segs)} trechos)")
        for s in segs: print(f"{s['s']:6.2f}-{s['e']:6.2f}  {s['t'] or '(sem texto)'}")
