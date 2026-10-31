"""Transcreve arquivos de voz e devolve os trechos com tempo (para montar clips e legendas).

    python3 -m lofi.transcribe roberta.mp3 rafa.mp3 lia.mp3   -> imprime e salva <arquivo>.json
Baixa o Whisper (sherpa-onnx, GitHub) na primeira vez.
"""
import sys, os, re, json, subprocess, tarfile, urllib.request
MODEL_DIR = os.path.expanduser("~/.lofi_models/sherpa-onnx-whisper-small")
URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2"

def ensure_model():
    if os.path.exists(os.path.join(MODEL_DIR, "small-tokens.txt")): return
    os.makedirs(os.path.dirname(MODEL_DIR), exist_ok=True)
    tgz = MODEL_DIR + ".tar.bz2"
    print("baixando modelo de transcrição (~600 MB)...", flush=True)
    subprocess.run(["curl", "-sL", "-o", tgz, URL], check=True)
    with tarfile.open(tgz) as t: t.extractall(os.path.dirname(MODEL_DIR))
    os.remove(tgz)

def transcribe(path, lang="pt"):
    import sherpa_onnx, soundfile as sf
    ensure_model()
    M = os.path.join(MODEL_DIR, "small-")
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M + "encoder.int8.onnx", decoder=M + "decoder.int8.onnx",
                                                     tokens=M + "tokens.txt", language=lang, task="transcribe", num_threads=4)
    wav = path + ".16k.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-ar", "16000", "-ac", "1", wav], check=True)
    a, sr = sf.read(wav, dtype="float32")
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "silencedetect=noise=-35dB:d=0.3", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    ss = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    dur = len(a) / sr; segs = []
    for s, e in zip([0.0] + se, ss + [dur]):
        if e - s < 0.15: continue
        st = rec.create_stream(); st.accept_waveform(sr, a[max(0, int((s - 0.15) * sr)): int((e + 0.15) * sr)]); rec.decode_stream(st)
        segs.append({"s": round(s, 2), "e": round(e, 2), "t": st.result.text.strip()})
    json.dump(segs, open(path + ".json", "w"), ensure_ascii=False, indent=1)
    return segs, dur

if __name__ == "__main__":
    for p in sys.argv[1:]:
        segs, dur = transcribe(p)
        print(f"=== {os.path.basename(p)} ({dur:.2f}s)")
        for s in segs: print(f"{s['s']:6.2f}-{s['e']:6.2f}  {s['t']}")
