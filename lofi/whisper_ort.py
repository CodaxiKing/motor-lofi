"""Whisper (modelos ONNX do sherpa-onnx) rodando só com numpy + onnxruntime.

Usado por `lofi.transcribe` quando o pacote `sherpa-onnx` não está instalado. Baseado em
scripts/whisper/test.py do sherpa-onnx (Apache-2.0), sem torch e sem kaldi-native-fbank.
"""
import base64
import numpy as np

SR = 16000; N_FFT = 400; HOP = 160


def _mel_filters(n_mels=80, sr=SR, n_fft=N_FFT):
    """Banco de filtros mel no padrão do Whisper (librosa: escala Slaney, normalização Slaney)."""
    def hz_to_mel(f):
        f = np.asarray(f, float); m = f / (200.0 / 3)
        log_t = f >= 1000.0
        return np.where(log_t, 15.0 + np.log(np.maximum(f, 1e-10) / 1000.0) / (np.log(6.4) / 27.0), m)
    def mel_to_hz(m):
        m = np.asarray(m, float); f = m * (200.0 / 3)
        log_t = m >= 15.0
        return np.where(log_t, 1000.0 * np.exp((np.log(6.4) / 27.0) * (m - 15.0)), f)
    fft_f = np.linspace(0, sr / 2, 1 + n_fft // 2)
    mel_f = mel_to_hz(np.linspace(hz_to_mel(0.0), hz_to_mel(sr / 2), n_mels + 2))
    fdiff = np.diff(mel_f); ramps = mel_f[:, None] - fft_f[None, :]
    w = np.zeros((n_mels, len(fft_f)))
    for i in range(n_mels):
        lower = -ramps[i] / fdiff[i]; upper = ramps[i + 2] / fdiff[i + 1]
        w[i] = np.maximum(0, np.minimum(lower, upper))
    w *= (2.0 / (mel_f[2:n_mels + 2] - mel_f[:n_mels]))[:, None]
    return w.astype(np.float32)


def log_mel(audio, n_mels=80):
    audio = np.asarray(audio, np.float32)
    pad = N_FFT // 2
    x = np.pad(audio, (pad, pad), mode="reflect")
    win = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(N_FFT) / N_FFT)).astype(np.float32)  # hann periódica
    n = 1 + (len(x) - N_FFT) // HOP
    frames = np.lib.stride_tricks.as_strided(x, (n, N_FFT), (x.strides[0] * HOP, x.strides[0]))
    mag = np.abs(np.fft.rfft(frames * win, axis=1)) ** 2
    mag = mag[:-1]                                                    # o Whisper descarta o último quadro
    mel = mag @ _mel_filters(n_mels).T                                # (T, n_mels)
    log_spec = np.log10(np.maximum(mel, 1e-10))
    log_spec = np.maximum(log_spec, log_spec.max() - 8.0)
    return ((log_spec + 4.0) / 4.0).astype(np.float32)


class Whisper:
    def __init__(self, encoder, decoder, tokens, threads=4):
        import onnxruntime as ort
        so = ort.SessionOptions(); so.inter_op_num_threads = 1; so.intra_op_num_threads = threads
        self.enc = ort.InferenceSession(encoder, sess_options=so, providers=["CPUExecutionProvider"])
        self.dec = ort.InferenceSession(decoder, sess_options=so, providers=["CPUExecutionProvider"])
        m = self.enc.get_modelmeta().custom_metadata_map
        self.n_text_layer = int(m["n_text_layer"]); self.n_text_ctx = int(m["n_text_ctx"])
        self.n_text_state = int(m["n_text_state"]); self.n_mels = int(m["n_mels"])
        self.sot = int(m["sot"]); self.eot = int(m["eot"]); self.translate = int(m["translate"])
        self.no_timestamps = int(m["no_timestamps"]); self.no_speech = int(m["no_speech"]); self.blank = int(m["blank_id"])
        self.sot_sequence = list(map(int, m["sot_sequence"].split(","))) + [self.no_timestamps]
        self.lang2id = dict(zip(m["all_language_codes"].split(","), map(int, m["all_language_tokens"].split(","))))
        self.table = {}
        for line in open(tokens, encoding="utf-8"):
            t, i = line.split(); self.table[int(i)] = t

    def _decode_step(self, tokens, sk, sv, ck, cv, offset):
        o = self.dec.get_outputs(); i = self.dec.get_inputs()
        logits, sk, sv = self.dec.run([o[0].name, o[1].name, o[2].name],
                                      {i[0].name: tokens, i[1].name: sk, i[2].name: sv, i[3].name: ck, i[4].name: cv, i[5].name: offset})[:3]
        return logits, sk, sv

    def _suppress(self, lg, initial):
        if initial: lg[self.eot] = -np.inf; lg[self.blank] = -np.inf
        for t in (self.no_timestamps, self.sot, self.no_speech, self.translate): lg[t] = -np.inf

    def transcribe(self, audio16k, lang="pt"):
        mel = log_mel(audio16k, self.n_mels)
        mel = np.pad(mel, ((0, 1500), (0, 0)))                          # cauda de silêncio para achar o fim
        if mel.shape[0] > 3000: mel = np.pad(mel[:2950], ((0, 50), (0, 0)))
        mel = mel.T[None]
        o = self.enc.get_outputs()
        ck, cv = self.enc.run([o[0].name, o[1].name], {self.enc.get_inputs()[0].name: mel})
        sk = np.zeros((self.n_text_layer, 1, self.n_text_ctx, self.n_text_state), np.float32); sv = sk.copy()
        seq = list(self.sot_sequence); seq[1] = self.lang2id.get(lang, seq[1])
        offset = np.zeros(1, np.int64)
        logits, sk, sv = self._decode_step(np.array([seq], np.int64), sk, sv, ck, cv, offset)
        offset += len(seq); lg = logits[0, -1].copy(); self._suppress(lg, True); tok = int(lg.argmax())
        out = []
        for _ in range(self.n_text_ctx - len(seq)):
            if tok == self.eot: break
            out.append(tok)
            logits, sk, sv = self._decode_step(np.array([[tok]], np.int64), sk, sv, ck, cv, offset)
            offset += 1; lg = logits[0, -1].copy(); self._suppress(lg, False); tok = int(lg.argmax())
        b = b"".join(base64.b64decode(self.table[t]) for t in out if t in self.table)
        return b.decode("utf-8", errors="ignore").strip()
