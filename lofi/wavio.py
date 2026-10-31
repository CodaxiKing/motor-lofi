"""Leitura e escrita de WAV sem depender do `soundfile`.

Usa o `soundfile` quando estiver instalado; senão cai para `scipy.io.wavfile` (que já é dependência do motor).
Arquivos que não são WAV (mp3, m4a...) são convertidos antes com o ffmpeg por quem chama.
"""
import numpy as np

try:
    import soundfile as _sf
except Exception:  # pacote ausente ou libsndfile indisponível
    _sf = None


def read(path, dtype="float64"):
    """Devolve (amostras, taxa). Amostras em ponto flutuante entre -1 e 1; mono vira vetor 1-D."""
    if _sf is not None:
        return _sf.read(path, dtype=dtype)
    from scipy.io import wavfile
    sr, x = wavfile.read(path)
    if np.issubdtype(x.dtype, np.integer):
        x = x.astype(np.float64) / float(np.iinfo(x.dtype).max + 1)
    return x.astype(dtype), sr


def write(path, data, sr):
    """Grava WAV 16 bits (mesmo padrão do soundfile para .wav)."""
    data = np.asarray(data, dtype=np.float64)
    if _sf is not None:
        _sf.write(path, data, sr); return
    from scipy.io import wavfile
    wavfile.write(path, sr, (np.clip(data, -1, 1) * 32767).astype(np.int16))
