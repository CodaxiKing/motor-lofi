
"""Efeitos: chuva em 2 camadas, respingos, relâmpago, névoa, granulado, vinheta, tratamento de cor, tremor, transições, carimbo, olho mágico."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
from .core import W, H, RED, CREAM, font, text_center, ease, ease_out, c01, lerp

# ---------- chuva ----------
def _rain_tex(n, lmin, lmax, amin, amax, width, seed):
    m = Image.new("L", (W, H * 2), 0); d = ImageDraw.Draw(m); r = random.Random(seed)
    for _ in range(n):
        x = r.randint(-40, W + 40); y = r.randint(0, H * 2); ln = r.randint(lmin, lmax)
        d.line([(x, y), (x - ln * 0.16, y + ln)], fill=r.randint(amin, amax), width=width)
    return m
RAIN_FAR = _rain_tex(2200, 14, 30, 40, 100, 1, 1)
RAIN_NEAR = _rain_tex(380, 50, 110, 70, 150, 3, 2).filter(ImageFilter.GaussianBlur(1.2))

def rain(img, t, box=None, strength=1.0, col=(175, 195, 235), near=True):
    x0, y0, x1, y1 = box or (0, 0, W, H)
    for tex, sp, k in ((RAIN_FAR, 1500, 1.0), (RAIN_NEAR, 2600, 0.9 if near else 0)):
        if k == 0: continue
        off = int(t * sp) % H
        m = tex.crop((x0, off + y0, x1, off + y1))
        if strength * k != 1: m = m.point(lambda v: int(v * strength * k))
        img.paste(col, (x0, y0), m)

def splashes(img, t, y0, y1, n=40, seed=5, col=(190, 205, 235)):
    d = ImageDraw.Draw(img); r = random.Random(seed + int(t * 10))
    for _ in range(n):
        x = r.randint(0, W); y = r.randint(y0, y1); k = r.random()
        w = 6 + 14 * k
        d.arc([x - w, y - w * 0.3, x + w, y + w * 0.3], 180, 360, fill=col, width=2)

# ---------- relâmpago ----------
def _bolt(seed, x0=760, length=900):
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m); r = random.Random(seed)
    pts = [(x0, -10)]; y = 0
    while y < length:
        y += r.randint(40, 80); pts.append((pts[-1][0] + r.randint(-60, 45), y))
    d.line(pts, fill=255, width=5)
    for k in (3, 6):
        if k < len(pts): d.line([pts[k], (pts[k][0] + r.randint(60, 140), pts[k][1] + r.randint(90, 170))], fill=200, width=3)
    return m, m.filter(ImageFilter.GaussianBlur(16))
BOLTS = [_bolt(s, x) for s, x in ((3, 760), (8, 300), (13, 560))]

def flash_amount(t, times):
    v = 0.0
    for th in times:
        dt = t - th
        if 0 <= dt < 0.7: v = max(v, (1 - dt / 0.7) * (1.0 if dt < 0.07 or 0.15 < dt < 0.22 else 0.45))
    return v

def lightning(img, t, times, box=None, bolt=True, room=0.3):
    f = flash_amount(t, times)
    if f <= 0: return img
    which = BOLTS[int(sum(times)) % len(BOLTS)] if times else BOLTS[0]
    if box:
        x0, y0, x1, y1 = box
        win = img.crop(box); win = Image.blend(win, Image.new("RGB", win.size, (210, 220, 255)), 0.55 * f)
        if bolt:
            b, bg = which[0].crop((0, 0, x1 - x0, y1 - y0)), which[1].crop((0, 0, x1 - x0, y1 - y0))
            win.paste((150, 170, 255), (0, 0), bg.point(lambda v: int(v * f)))
            win.paste((240, 244, 255), (0, 0), b.point(lambda v: int(v * f)))
        img.paste(win, (x0, y0))
        return Image.blend(img, Image.new("RGB", img.size, (160, 175, 230)), room * f * 0.5)
    img = Image.blend(img, Image.new("RGB", img.size, (200, 210, 250)), 0.45 * f)
    if bolt:
        img.paste((150, 170, 255), (0, 0), which[1].point(lambda v: int(v * f)))
        img.paste((240, 244, 255), (0, 0), which[0].point(lambda v: int(v * f)))
    return img

# ---------- névoa ----------
def _fog_tex(seed=4):
    r = np.random.default_rng(seed)
    small = r.random((24, 60))
    img = Image.fromarray((small * 255).astype("uint8")).resize((W * 2, 700), Image.BICUBIC).filter(ImageFilter.GaussianBlur(40))
    return img
FOG = _fog_tex()
def fog(img, t, y=1100, height=700, alpha=0.5, col=(80, 90, 120), speed=18):
    off = int(t * speed) % W
    m = FOG.crop((off, 0, off + W, 700)).resize((W, height))
    m = m.point(lambda v: int(v * alpha))
    img.paste(col, (0, int(y - height / 2)), m)

# ---------- granulado e vinheta ----------
_G = np.random.default_rng(1).normal(0, 4.5, (H, W)).astype(np.float32)
GRAIN_P = Image.fromarray(np.clip(_G, 0, 255).astype("uint8")).convert("RGB")
GRAIN_N = Image.fromarray(np.clip(-_G, 0, 255).astype("uint8")).convert("RGB")
def grain(img): return ImageChops.subtract(ImageChops.add(img, GRAIN_P), GRAIN_N)
def _vig(strength):
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((xx - 540) / 700) ** 2 + ((yy - 1050) / 1150) ** 2)
    return Image.fromarray((np.clip(1.18 - dist * 0.72 * strength, 0.25, 1) * 255).astype("uint8"))
VIG = {k: _vig(k) for k in (0.6, 1.0, 1.4)}
BLACK = Image.new("RGB", (W, H), 0)
def vignette(img, k=1.0):
    return Image.composite(img, BLACK, VIG[min(VIG, key=lambda v: abs(v - k))])

# ---------- tratamento de cor ----------
GRADES = {
    "noite":  dict(lift=(6, 10, 24), gain=(0.94, 0.97, 1.06), gamma=1.05, sat=0.95),
    "quente": dict(lift=(14, 8, 4), gain=(1.06, 0.98, 0.88), gamma=1.0, sat=1.05),
    "amanhecer": dict(lift=(18, 18, 24), gain=(0.98, 0.98, 1.02), gamma=0.95, sat=0.75),
    "emergencia": dict(lift=(16, 2, 4), gain=(1.08, 0.82, 0.82), gamma=1.05, sat=1.1),
    "frio":   dict(lift=(4, 10, 20), gain=(0.9, 0.98, 1.08), gamma=1.0, sat=0.85),
    "neutro": dict(lift=(0, 0, 0), gain=(1, 1, 1), gamma=1.0, sat=1.0),
}
_LUT = {}
def grade(img, name="noite"):
    g = GRADES.get(name, GRADES["neutro"])
    if name not in _LUT:
        lut = []
        for ch in range(3):
            lift, gain = g["lift"][ch], g["gain"][ch]
            for v in range(256):
                x = (v / 255) ** g["gamma"]
                lut.append(int(max(0, min(255, lift + x * 255 * gain))))
        _LUT[name] = lut
    img = img.point(_LUT[name])
    if g["sat"] != 1.0: img = ImageEnhance.Color(img).enhance(g["sat"])
    return img

# ---------- câmera ----------
def shake_offset(t, times, amp=16, dur=0.35):
    dx = dy = 0.0
    for s in times:
        dt = t - s
        if 0 <= dt < dur:
            k = (1 - dt / dur) ** 2
            dx += math.sin(dt * 95) * amp * k; dy += math.cos(dt * 77) * amp * 0.6 * k
    return dx, dy
def apply_camera(img, zoom=1.0, cx=0.5, cy=0.5, dx=0, dy=0, rot=0.0):
    if zoom == 1.0 and dx == 0 and dy == 0 and rot == 0: return img
    if rot: img = img.rotate(rot, resample=Image.BILINEAR)
    cw, ch = W / zoom, H / zoom
    x0 = (W - cw) * cx - dx; y0 = (H - ch) * cy - dy
    x0 = max(-40, min(W - cw + 40, x0)); y0 = max(-40, min(H - ch + 40, y0))
    return img.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)

# ---------- transições ----------
def motion_blur_h(img, amount):
    if amount < 2: return img
    acc = None; n = 6
    for k in range(n):
        sh = ImageChops.offset(img, int((k - n / 2) * amount / n), 0)
        acc = sh if acc is None else Image.blend(acc, sh, 1 / (k + 1))
    return acc
def transition(img, prev_img, kind, p):
    """p: 0→1 no início do plano (duração curta)."""
    if kind == "fade": return Image.blend(BLACK, img, ease(p))
    if kind == "flash": return Image.blend(Image.new("RGB", img.size, (255, 255, 255)), img, ease(p))
    if kind == "whip":
        off = int((1 - ease_out(p)) * W * 0.6)
        return motion_blur_h(ImageChops.offset(img, off, 0), (1 - p) * 160)
    if kind == "zoom":
        z = lerp(1.25, 1.0, ease_out(p)); return Image.blend(BLACK, apply_camera(img, z), min(1, p * 3))
    if kind == "glitch":
        if p < 0.6:
            arr = np.asarray(img).copy(); r = random.Random(int(p * 100))
            for _ in range(8):
                y = r.randint(0, H - 60); h = r.randint(10, 60); s = r.randint(-80, 80)
                arr[y:y + h] = np.roll(arr[y:y + h], s, axis=1)
            arr[..., 0] = np.roll(arr[..., 0], 8, axis=1)
            return Image.fromarray(arr)
        return img
    if kind == "dip":
        return Image.blend(BLACK, img, ease(p))
    return img

# ---------- olho mágico ----------
PEEP = Image.new("L", (W, H), 0); ImageDraw.Draw(PEEP).ellipse([50, 380, W - 50, 380 + W - 100], fill=255)
PEEP = PEEP.filter(ImageFilter.GaussianBlur(40))
def peephole(img):
    # leve distorção de lente: zoom no centro
    z = img.transform((W, H), Image.EXTENT, (60, 180, W - 60, H - 180), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.8))
    return Image.composite(z, BLACK, PEEP)

# ---------- carimbo ----------
def stamp(img, t, start, top="A MAIORIA ESCOLHEU", word="ESPIAR", y=1200, color=RED):
    if t < start: return img
    p = c01((t - start) / 0.18); sc = lerp(2.4, 1.0, ease(p))
    jitter = math.sin((t - start) * 60) * 10 * max(0, 1 - (t - start) * 4)
    st = Image.new("RGBA", (920, 440), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    sd.rectangle([20, 20, 900, 420], outline=color + (255,), width=14)
    sd.rectangle([40, 40, 880, 400], outline=color + (150,), width=4)
    text_center(sd, top, 460, 108, font("title", 62), (235, 230, 220, 255))
    fs = 210 if len(word) <= 8 else max(110, int(1500 / len(word)))
    text_center(sd, word, 460, 275, font("title", fs), color + (255,))
    # textura "tinta falhada"
    r = random.Random(4)
    for _ in range(90):
        x, yy = r.randint(20, 900), r.randint(20, 420)
        sd.ellipse([x, yy, x + r.randint(3, 9), yy + r.randint(3, 9)], fill=(0, 0, 0, 0))
    st = st.rotate(-8, expand=True, resample=Image.BICUBIC)
    st = st.resize((int(st.width * sc), int(st.height * sc)), Image.BILINEAR)
    img.paste(st, (int(W / 2 - st.width / 2 + jitter), int(y - st.height / 2)), st)
    return img

# ======================= v3: luz, lente, estilo, clima =======================
def handheld(t, amp=10.0):
    """Balanço suave de câmera na mão (dx, dy, rot)."""
    dx = (math.sin(t * 1.3) + 0.6 * math.sin(t * 2.9 + 1.1) + 0.3 * math.sin(t * 5.3)) * amp * 0.5
    dy = (math.sin(t * 1.7 + 0.4) + 0.5 * math.sin(t * 3.7 + 2.0)) * amp * 0.4
    return dx, dy, math.sin(t * 1.1) * amp * 0.03

def bloom(img, threshold=170, strength=0.6, radius=18):
    br = img.point(lambda v: int(max(0, v - threshold) * 255 / max(1, 255 - threshold) * strength))
    return ImageChops.add(img, br.filter(ImageFilter.GaussianBlur(radius)))

def chromatic(img, amount=8):
    r, g, b = img.split()
    return Image.merge("RGB", (ImageChops.offset(r, int(amount), 0), g, ImageChops.offset(b, -int(amount), 0)))

def scare_amount(t, times, dur=0.35):
    v = 0.0
    for s in times:
        dt = t - s
        if 0 <= dt < dur: v = max(v, 1 - dt / dur)
    return v

_DROPS = [(random.Random(k).uniform(40, W - 40), random.Random(k + 50).uniform(0, H), random.Random(k + 90).uniform(10, 34),
           random.Random(k + 130).uniform(4, 22)) for k in range(26)]
def lens_drops(img, t, strength=1.0):
    """Gotas de chuva escorrendo na lente."""
    for (x, y0, r, sp) in _DROPS:
        y = (y0 + t * sp) % (H + 80) - 40
        box = (int(x - r), int(y - r), int(x + r), int(y + r))
        if box[0] < 0 or box[1] < 0 or box[2] > W or box[3] > H: continue
        reg = img.crop(box).transpose(Image.FLIP_TOP_BOTTOM).filter(ImageFilter.GaussianBlur(1.5))
        m = Image.new("L", reg.size, 0); ImageDraw.Draw(m).ellipse([0, 0, reg.width - 1, reg.height - 1], fill=int(200 * strength))
        img.paste(reg, box[:2], m)
        d = ImageDraw.Draw(img)
        d.arc([box[0] + 3, box[1] + 3, box[2] - 3, box[3] - 3], 200, 290, fill=(235, 240, 255), width=2)
        d.arc([box[0], box[1], box[2], box[3]], 20, 160, fill=(20, 24, 32), width=2)
    return img

def _paper():
    r = np.random.default_rng(7)
    big = Image.fromarray((r.random((60, 34)) * 255).astype("uint8")).resize((W, H), Image.BICUBIC)
    fine = Image.fromarray((r.normal(128, 30, (H // 2, W // 2))).clip(0, 255).astype("uint8")).resize((W, H))
    m = ImageChops.add(big.point(lambda v: v // 2), fine.point(lambda v: v // 2))
    return m.filter(ImageFilter.GaussianBlur(0.6))
PAPER = None
def hand_drawn(img, strength=1.0):
    """Textura de papel + traço de nanquim leve nas bordas (cara de desenhado à mão)."""
    global PAPER
    if PAPER is None: PAPER = _paper()
    g = img.convert("L").filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 38 else 0).filter(ImageFilter.GaussianBlur(0.7))
    img.paste((12, 10, 16), (0, 0), g.point(lambda v: int(v * 0.32 * strength)))
    shade = PAPER.point(lambda v: int(abs(v - 128) * 0.45 * strength))
    img.paste((230, 220, 200), (0, 0), shade.point(lambda v: v // 3))
    img.paste((0, 0, 0), (0, 0), shade.point(lambda v: v // 4))
    return img

def tint(img, color, amount):
    if amount <= 0: return img
    return Image.blend(img, ImageChops.multiply(img, Image.new("RGB", img.size, tuple(color))).point(lambda v: min(255, int(v * 1.5))), amount)

TIMES = {"noite": None, "dia": ((255, 250, 235), 0.22, 1.18), "entardecer": ((255, 150, 90), 0.28, 1.05),
         "amanhecer": ((255, 200, 180), 0.22, 1.08), "madrugada": ((90, 110, 200), 0.3, 0.8)}
def time_of_day(img, name):
    p = TIMES.get(name)
    if not p: return img
    col, amt, bright = p
    img = tint(img, col, amt)
    if bright != 1.0: img = img.point(lambda v: min(255, int(v * bright)))
    return img

_SNOW = [(random.Random(k).uniform(0, W), random.Random(k + 7).uniform(0, H), random.Random(k + 9).uniform(2, 6),
          random.Random(k + 11).uniform(40, 120), random.Random(k + 13).uniform(0, 6.28)) for k in range(260)]
def snow(img, t, density=1.0):
    d = ImageDraw.Draw(img)
    for i, (x0, y0, r, sp, ph) in enumerate(_SNOW):
        if i > len(_SNOW) * density: break
        y = (y0 + t * sp) % H; x = x0 + math.sin(t * 0.8 + ph) * 26
        d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 240, 250))

def darkness(img, amount, beams=(), circles=(), soft=40, soft_circles=()):
    """Breu com áreas iluminadas: beams = [(origem, ângulo, comprimento, abertura)], circles = [(x, y, raio)]."""
    if amount <= 0: return img
    m = Image.new("L", img.size, 0); d = ImageDraw.Draw(m)
    for (o, ang, ln, spread) in beams:
        a1, a2 = math.radians(ang - spread * 1.15), math.radians(ang + spread * 1.15)
        d.polygon([o, (o[0] + math.cos(a1) * ln, o[1] + math.sin(a1) * ln), (o[0] + math.cos(a2) * ln, o[1] + math.sin(a2) * ln)], fill=255)
        d.ellipse([o[0] - 70, o[1] - 70, o[0] + 70, o[1] + 70], fill=200)
    for (x, y, r) in circles:
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    for (x, y, r) in soft_circles:
        d.ellipse([x - r, y - r, x + r, y + r], fill=110)
    m = m.filter(ImageFilter.GaussianBlur(soft))
    dark = Image.blend(img, Image.new("RGB", img.size, (2, 3, 8)), amount)
    return Image.composite(img, dark, m)
