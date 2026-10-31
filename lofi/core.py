
"""Utilidades básicas do motor lo-fi: tamanho do quadro, easing, gradientes, brilhos e fontes."""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
OUT = (22, 24, 34, 255)          # cor do contorno
RED = (215, 52, 42)
CREAM = (240, 236, 225)

_fcache = {}
def font(name, size):
    key = (name, size)
    if key not in _fcache:
        f = {"title": "Anton-Regular.ttf", "mono": "SpaceMono-Bold.ttf"}[name]
        _fcache[key] = ImageFont.truetype(os.path.join(FONT_DIR, f), size)
    return _fcache[key]

def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def ease_out(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def ease_in(x):
    x = max(0.0, min(1.0, x)); return x ** 3
def lerp(a, b, x): return a + (b - a) * x
def c01(x): return max(0.0, min(1.0, x))

def keyframe(v, t, default=None):
    """v pode ser número fixo, [a, b] (interpola na cena via t∈[0,1]) ou lista de [tempo, valor]."""
    if v is None: return default
    if isinstance(v, (int, float, str)): return v
    if isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(k, (int, float)) for k in v):
        return lerp(v[0], v[1], ease(t))
    if isinstance(v, (list, tuple)) and v and isinstance(v[0], (list, tuple)):
        pts = sorted(v)
        if t <= pts[0][0]: return pts[0][1]
        for (t0, a), (t1, b) in zip(pts, pts[1:]):
            if t0 <= t <= t1:
                if isinstance(a, str): return a if t < t1 else b
                return lerp(a, b, ease((t - t0) / max(1e-6, t1 - t0)))
        return pts[-1][1]
    return v

def grad(w, h, top, bot, horizontal=False):
    n = w if horizontal else h
    a = np.linspace(0, 1, n)
    a = a[None, :, None] if horizontal else a[:, None, None]
    arr = (np.array(top) + (np.array(bot) - np.array(top)) * a) * np.ones((h, w, 1) if horizontal else (1, w, 1))
    return Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))

def add_light(img, box, color, blur, alpha=120, shape="ellipse"):
    """Brilho aditivo (luz) em forma de elipse/polígono desfocado."""
    m = Image.new("L", img.size, 0); md = ImageDraw.Draw(m)
    if shape == "polygon": md.polygon(box, fill=alpha)
    else: getattr(md, shape)(box, fill=alpha)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    layer = Image.composite(Image.new("RGB", img.size, color), Image.new("RGB", img.size, 0), m)
    if img.mode == "RGBA":
        rgb = ImageChops.add(img.convert("RGB"), layer); rgb.putalpha(img.split()[3]); return rgb
    return ImageChops.add(img, layer)

def darken(img, box, alpha=120, blur=40, shape="ellipse"):
    m = Image.new("L", img.size, 0); md = ImageDraw.Draw(m)
    if shape == "polygon": md.polygon(box, fill=alpha)
    else: getattr(md, shape)(box, fill=alpha)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    img.paste((0, 0, 0), (0, 0), m)
    return img

def text_center(d, txt, cx, cy, f, fill, stroke=0, sfill=(0, 0, 0)):
    bb = d.textbbox((0, 0), txt, font=f)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), txt, font=f, fill=fill,
           stroke_width=stroke, stroke_fill=sfill)

def rng(seed): return random.Random(seed)
