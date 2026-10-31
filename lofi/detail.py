
"""Planos de detalhe (inserts): maçaneta, olho, celular, chave, relógio. Mostram sem precisar narrar.

Uso no roteiro: {"type": "detail", "subject": "macaneta", "params": {"turn": [0, 60], "light": true}}
"""
import math, random
from PIL import Image, ImageDraw, ImageFilter
from .core import W, H, font, text_center, add_light, lerp, ease, c01

OUT = (22, 24, 34)

def _wood(col=(92, 58, 40)):
    img = Image.new("RGB", (W, H), col); d = ImageDraw.Draw(img); r = random.Random(3)
    for y in range(0, H, 6):
        k = 0.9 + 0.1 * math.sin(y * 0.02 + r.random())
        d.line([(0, y), (W, y + r.randint(-4, 4))], fill=tuple(int(c * k) for c in col), width=3)
    return img

def macaneta(t, p):
    img = _wood(); d = ImageDraw.Draw(img)
    if p.get("light", True):
        d.rectangle([W - 60, 0, W, H], fill=(200, 160, 90))
        img = add_light(img, (W - 400, -200, W + 200, H + 200), (120, 80, 30), 120, 150); d = ImageDraw.Draw(img)
    d.rounded_rectangle([300, 640, 520, 1300], 40, fill=(170, 150, 100), outline=OUT, width=8)
    d.ellipse([370, 1150, 450, 1230], fill=(20, 18, 16))
    ang = math.radians(p.get("turn_now", 0))
    cx, cy = 410, 900
    d.ellipse([cx - 110, cy - 110, cx + 110, cy + 110], fill=(190, 170, 110), outline=OUT, width=8)
    ex, ey = cx + math.cos(ang) * 330, cy + math.sin(ang) * 330
    d.line([(cx, cy), (ex, ey)], fill=OUT, width=96); d.line([(cx, cy), (ex, ey)], fill=(205, 185, 125), width=82)
    d.ellipse([ex - 48, ey - 48, ex + 48, ey + 48], fill=(205, 185, 125), outline=OUT, width=8)
    d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], fill=(230, 215, 160))
    return img

def olho(t, p):
    img = Image.new("RGB", (W, H), (226, 222, 214)); d = ImageDraw.Draw(img)
    skin = tuple(p.get("skin", (236, 236, 230)))
    d.rectangle([0, 0, W, H], fill=skin)
    cx, cy = 540, 960
    open_k = 1.0
    bl = p.get("blink_at")
    if bl is not None and 0 <= t - bl < 0.18: open_k = abs((t - bl) / 0.09 - 1)
    hh = 260 * open_k
    d.ellipse([cx - 420, cy - hh, cx + 420, cy + hh], fill=(250, 250, 248), outline=OUT, width=14)
    pup = p.get("pupil_now", 0.4)
    ir = 210
    mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).ellipse([cx - 410, cy - hh + 8, cx + 410, cy + hh - 8], fill=255)
    lay = Image.new("RGB", (W, H), (250, 250, 248)); ld = ImageDraw.Draw(lay)
    lx = cx + p.get("look_now", 0)
    ld.ellipse([lx - ir, cy - ir, lx + ir, cy + ir], fill=tuple(p.get("iris", (70, 50, 36))))
    for k in range(24):
        a = k / 24 * 2 * math.pi
        ld.line([(lx + math.cos(a) * 60, cy + math.sin(a) * 60), (lx + math.cos(a) * ir * 0.95, cy + math.sin(a) * ir * 0.95)], fill=(50, 36, 26), width=4)
    pr = 50 + 120 * pup
    ld.ellipse([lx - pr, cy - pr, lx + pr, cy + pr], fill=(10, 10, 12))
    if p.get("reflect"):
        ld.ellipse([lx - 40, cy - 70, lx + 20, cy - 10], fill=(150, 156, 152))
        ld.ellipse([lx - 28, cy - 50, lx - 18, cy - 40], fill=(255, 255, 240)); ld.ellipse([lx - 4, cy - 50, lx + 6, cy - 40], fill=(255, 255, 240))
    ld.ellipse([lx + 60, cy - 120, lx + 120, cy - 60], fill=(255, 255, 255))
    img.paste(lay, (0, 0), mask); d = ImageDraw.Draw(img)
    d.ellipse([cx - 420, cy - hh, cx + 420, cy + hh], outline=OUT, width=14)
    br = p.get("brow", 0)
    d.line([(cx - 380, cy - 360 - br), (cx + 360, cy - 330 + br)], fill=OUT, width=40)
    if p.get("tear"):
        dy = (t * 160) % 500
        d.ellipse([cx + 330, cy + 180 + dy, cx + 370, cy + 240 + dy], fill=(140, 190, 245))
    return img

def celular(t, p):
    img = Image.new("RGB", (W, H), (14, 16, 22)); d = ImageDraw.Draw(img)
    img = add_light(img, (40, 200, 1040, 1700), (60, 80, 140), 120, 140); d = ImageDraw.Draw(img)
    d.rounded_rectangle([170, 260, 910, 1660], 70, fill=(20, 20, 24), outline=(70, 70, 80), width=10)
    d.rounded_rectangle([200, 300, 880, 1620], 50, fill=(40, 46, 62))
    d.text((240, 320), "21:12", font=font("mono", 40), fill=(220, 220, 230))
    sig = p.get("signal", 0)
    for k in range(4):
        d.rectangle([760 + k * 26, 360 - k * 12, 778 + k * 26, 372], fill=(220, 220, 230) if k < sig else None, outline=(150, 150, 160), width=2)
    lines = p.get("text", ["SEM SERVIÇO"])
    n_show = int(c01(t / max(0.01, p.get("type_dur", 0.0001))) * sum(len(l) for l in lines)) if p.get("type_dur") else 10 ** 6
    y = 760
    for line in lines:
        show = line[:max(0, n_show)]; n_show -= len(line)
        text_center(d, show, 540, y, font("title", 92 if len(line) < 14 else 64), tuple(p.get("color", (255, 120, 110))))
        y += 130
    if p.get("notifs"):
        for k, nt in enumerate(p["notifs"]):
            yy = 1100 + k * 120
            d.rounded_rectangle([240, yy, 840, yy + 100], 20, fill=(60, 64, 80))
            d.rectangle([260, yy + 20, 272, yy + 80], fill=(215, 52, 42))
            d.text((300, yy + 28), nt, font=font("mono", 34), fill=(230, 230, 230))
    return img

def chave(t, p):
    img = Image.new("RGB", (W, H), (60, 52, 46)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([270, 520, 810, 1400], 60, fill=(150, 140, 120), outline=OUT, width=10)
    cx, cy = 540, 900
    d.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], fill=(20, 18, 16)); d.polygon([(cx - 40, cy + 40), (cx + 40, cy + 40), (cx + 26, cy + 230), (cx - 26, cy + 230)], fill=(20, 18, 16))
    ang = p.get("turn_now", 0)
    k = Image.new("RGBA", (700, 700), (0, 0, 0, 0)); kd = ImageDraw.Draw(k)
    kd.rectangle([330, 100, 370, 350], fill=(230, 190, 70, 255), outline=OUT + (255,), width=6)
    kd.ellipse([240, 330, 460, 550], fill=(230, 190, 70, 255), outline=OUT + (255,), width=8)
    kd.ellipse([310, 400, 390, 480], fill=(0, 0, 0, 0), outline=OUT + (255,), width=6)
    k = k.rotate(-ang, center=(350, 120), resample=Image.BICUBIC)
    img.paste(k, (cx - 350, cy - 120), k)
    hand = p.get("hand", True)
    if hand:
        d.ellipse([cx - 90, cy + 300, cx + 120, cy + 520], fill=(236, 236, 230), outline=OUT, width=8)
        d.line([(cx + 60, cy + 470), (W + 100, H + 100)], fill=OUT, width=150); d.line([(cx + 60, cy + 470), (W + 100, H + 100)], fill=(210, 212, 220), width=136)
    return img

def relogio(t, p):
    img = Image.new("RGB", (W, H), (30, 34, 46)); d = ImageDraw.Draw(img)
    cx, cy, r = 540, 920, 380
    d.ellipse([cx - r - 30, cy - r - 30, cx + r + 30, cy + r + 30], fill=(80, 60, 44), outline=OUT, width=10)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(236, 230, 214))
    for k in range(12):
        a = k / 12 * 2 * math.pi
        d.line([(cx + math.sin(a) * r * 0.82, cy - math.cos(a) * r * 0.82), (cx + math.sin(a) * r * 0.95, cy - math.cos(a) * r * 0.95)], fill=OUT, width=12)
    mins = p.get("minutes_now", 0)
    for frac, ln, w in ((mins / 720, 0.5, 22), ((mins % 60) / 60, 0.78, 12)):
        a = frac * 2 * math.pi
        d.line([(cx, cy), (cx + math.sin(a) * r * ln, cy - math.cos(a) * r * ln)], fill=OUT, width=w)
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(200, 50, 40))
    return img

SUBJECTS = {"macaneta": macaneta, "maçaneta": macaneta, "olho": olho, "celular": celular, "chave": chave, "relogio": relogio, "relógio": relogio}

def render_detail(subject, t, params):
    return SUBJECTS[subject](t, params)
