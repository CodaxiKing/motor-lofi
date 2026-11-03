"""Clipe de vídeo como fundo de um plano ("video_clip": "ep01/clips/cena003.mp4").

O clipe (ex.: gerado por IA a partir do quadro da cena) substitui o desenho do cenário e dos
personagens daquele plano; tudo o que o motor desenha por cima (legendas, selo, contador,
barras, efeitos de susto, tinta, vinheta) continua igual. O clipe começa no início do plano;
se for mais curto que o plano, o último quadro fica parado.
"""
import os
import subprocess

import numpy as np
from PIL import Image

_CACHE = {}


def _decode(path):
    """Todos os quadros do clipe na resolução original (um processo do FFmpeg por clipe)."""
    st = os.stat(path)
    key = (path, st.st_mtime, st.st_size)
    if key in _CACHE:
        return _CACHE[key]
    info = subprocess.run(["ffmpeg", "-hide_banner", "-i", path], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stderr
    import re
    m = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", info)
    fps = re.search(r"(\d+(?:\.\d+)?) fps", info)
    if not m:
        raise RuntimeError(f"clipe ilegível: {path}")
    w, h = int(m.group(1)), int(m.group(2))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    frames = np.frombuffer(raw, np.uint8)[: (len(raw) // (w * h * 3)) * w * h * 3].reshape(-1, h, w, 3)
    if not len(frames):
        raise RuntimeError(f"clipe sem quadros: {path}")
    if len(_CACHE) > 8:
        _CACHE.clear()
    _CACHE[key] = (frames, float(fps.group(1)) if fps else 24.0)
    return _CACHE[key]


def quadro(shot, t, base, size):
    """Quadro do clipe no tempo t do episódio, ajustado (cobrindo, sem distorcer) ao tamanho do vídeo."""
    path = shot["video_clip"]
    path = path if os.path.isabs(path) else os.path.join(base, path)
    frames, fps = _decode(path)
    i = min(len(frames) - 1, max(0, int((t - shot["start"]) * fps)))
    im = Image.fromarray(frames[i])
    W, H = size
    s = max(W / im.width, H / im.height)
    im = im.resize((max(W, round(im.width * s)), max(H, round(im.height * s))), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))
