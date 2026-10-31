
"""Partículas e luzes práticas: poeira no ar, respingos nos personagens, bafo de frio, feixe de lanterna."""
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from .core import W, H

def dust(img, t, box=(0, 0, W, H), n=60, col=(255, 236, 200), seed=3, alpha=150):
    """Poeira flutuando (fica bonita dentro de feixes de luz)."""
    x0, y0, x1, y1 = box; r = random.Random(seed)
    lay = Image.new("L", img.size, 0); d = ImageDraw.Draw(lay)
    for i in range(n):
        bx, by = r.uniform(x0, x1), r.uniform(y0, y1); ph = r.uniform(0, 6.28); sp = r.uniform(4, 14)
        x = bx + math.sin(t * 0.4 + ph) * 30; y = (by - t * sp - y0) % max(1, (y1 - y0)) + y0
        s = r.choice((1.5, 2, 2.5, 3.5))
        d.ellipse([x - s, y - s, x + s, y + s], fill=int(alpha * (0.5 + 0.5 * math.sin(t * 1.3 + ph))))
    img.paste(col, (0, 0), lay.filter(ImageFilter.GaussianBlur(0.8)))

def splash_on(img, t, box, n=5, seed=0, col=(200, 215, 240)):
    """Respingos de chuva batendo no topo da cabeça/ombros (box = x0,y0,x1,y1 da cabeça)."""
    x0, y0, x1, y1 = box; d = ImageDraw.Draw(img); r = random.Random(seed + int(t * 12))
    for _ in range(n):
        x = r.uniform(x0, x1); y = y0 + r.uniform(-4, 10); w = r.uniform(4, 9)
        d.arc([x - w, y - w * 0.6, x + w, y + w * 0.6], 200, 340, fill=col, width=2)
        if r.random() < 0.4:
            px, py = x + r.uniform(-12, 12), y - r.uniform(6, 16)
            d.ellipse([px - 1.5, py - 1.5, px + 1.5, py + 1.5], fill=col)

def breath_fog(img, t, mouth_xy, facing=1, period=2.6, seed=0, strength=1.0):
    """Bafo de frio saindo da boca a cada expiração."""
    ph = ((t + seed * 0.37) % period) / period
    if ph > 0.55: return
    k = ph / 0.55
    x, y = mouth_xy
    lay = Image.new("L", img.size, 0); d = ImageDraw.Draw(lay)
    for j in range(5):
        kk = max(0.0, k - j * 0.06)
        cx = x + facing * (10 + 70 * kk) + math.sin(t * 3 + j) * 6; cy = y - 10 - 50 * kk
        r = 8 + 34 * kk
        d.ellipse([cx - r, cy - r * 0.7, cx + r, cy + r * 0.7], fill=int(170 * (1 - kk) * strength))
    img.paste((225, 232, 245), (0, 0), lay.filter(ImageFilter.GaussianBlur(10)))

def flashlight(img, t, origin, angle_deg, length=900, spread=22, color=(255, 240, 200), alpha=150, flicker=True):
    """Feixe de lanterna (cone de luz aditivo) com poeira dentro. angle 0 = para a direita, 90 = para baixo."""
    ox, oy = origin
    a = math.radians(angle_deg); s1, s2 = math.radians(angle_deg - spread), math.radians(angle_deg + spread)
    p1 = (ox + math.cos(s1) * length, oy + math.sin(s1) * length); p2 = (ox + math.cos(s2) * length, oy + math.sin(s2) * length)
    f = 1.0 if not flicker else (0.85 + 0.15 * math.sin(t * 23) * math.sin(t * 7.1))
    m = Image.new("L", img.size, 0); md = ImageDraw.Draw(m)
    md.polygon([origin, p1, p2], fill=int(alpha * f))
    md.ellipse([ox - 18, oy - 18, ox + 18, oy + 18], fill=230)
    m = m.filter(ImageFilter.GaussianBlur(24))
    out = ImageChops.add(img, Image.composite(Image.new("RGB", img.size, color), Image.new("RGB", img.size, 0), m))
    img.paste(out)
    # poeira no feixe
    lay = Image.new("L", img.size, 0); d = ImageDraw.Draw(lay); r = random.Random(11)
    for i in range(40):
        u = r.uniform(0.1, 1.0); v = r.uniform(-1, 1)
        ang = a + v * math.radians(spread) * 0.9
        dist = (u * length + t * r.uniform(10, 40)) % length
        x = ox + math.cos(ang) * dist + math.sin(t + i) * 6; y = oy + math.sin(ang) * dist
        sz = r.choice((1.5, 2, 3))
        d.ellipse([x - sz, y - sz, x + sz, y + sz], fill=int(180 * f * (1 - dist / length)))
    img.paste(color, (0, 0), lay)

def crowd_actors(spec, t_rel):
    """Gera atores de horda com andares variados. spec: {count, area:[x0,y0,x1,y1], dir:1|-1, speed, seed, char, eyes}."""
    r = random.Random(spec.get("seed", 1)); out = []
    x0, y0, x1, y1 = spec.get("area", [0, 1300, W, 1700])
    for i in range(spec.get("count", 10)):
        y = r.uniform(y0, y1); bx = r.uniform(x0 - 200, x1 + 200)
        sp = spec.get("speed", 40) * r.uniform(0.5, 1.4)
        dirn = spec.get("dir", 0)
        if dirn == 0: dirn = r.choice((-1, 1)); sp *= 0.4
        span = (x1 - x0) + 400
        x = (bx - x0 + 200 + dirn * sp * t_rel) % span + x0 - 200
        tint = r.choice([(90, 96, 92), (110, 86, 66), (70, 80, 100), (100, 70, 70), (84, 90, 60)])
        out.append({"char": spec.get("char", "zombie"), "x": x, "y": y, "view": spec.get("view", "side"), "facing": dirn,
                    "walk": True, "seed": i * 7 + 3, "pose": "forward", "custom": {"top": tint},
                    "scale_k": r.uniform(0.85, 1.1), "_crowd": True, "_limp": r.uniform(0.6, 1.3)})
    return out
