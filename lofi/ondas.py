"""Ondas de som na tela (padrão em todos os episódios): cada efeito sonoro do roteiro ganha um desenho no lugar de onde vem.

knock → três arcos saindo da porta + "TOC" · bang → estrela de impacto + "BAM!" · door_close → "BLAM" · door_open → "CREC"
glass → cacos + "CRASH" · car_alarm / siren → arcos pulsando (laranja / vermelho e azul) · notif / vibe → tremidinhas + "BZZ"
growl → linhas onduladas + "GRRR" · heartbeat → pulso vermelho nas bordas · beep → arquinhos + "BIP" · lock → "CLAC"
step / echo_step → anel no chão (só com "passos": true)

No roteiro técnico:
  "sfx": [{"t": 12.0, "name": "knock", "x": 690, "y": 1180}]     # x/y = de onde o som vem (coordenadas do cenário)
  sem x/y: usa a porta do cenário (marca "porta"), o carro (marca "carro") ou o centro da tela.
  "onda": false no efeito desliga só ele; "ondas": false no episódio (ou no plano) desliga todas;
  "ondas": {"texto": false} tira as onomatopeias; {"passos": true} liga os anéis de passos.
"""
import math
from PIL import Image, ImageDraw
from .core import W, H, font, c01, ease_out

ESTILO = {   # nome: (duração, cor, onomatopeia)
    "knock": (0.7, (255, 255, 255), "TOC"), "bang": (0.8, (255, 230, 120), "BAM!"),
    "door_close": (0.6, (255, 255, 255), "BLAM"), "door_open": (0.7, (230, 230, 230), "CREC"),
    "glass": (0.8, (200, 235, 255), "CRASH"), "car_alarm": (3.0, (255, 150, 40), None),
    "siren": (4.0, (255, 60, 60), None), "notif": (0.6, (255, 255, 255), "BZZ"), "vibe": (0.8, (255, 255, 255), "BZZ"),
    "growl": (1.2, (190, 60, 60), "GRRR"), "heartbeat": (2.0, (200, 20, 30), None), "beep": (0.5, (120, 255, 160), "BIP"),
    "lock": (0.5, (255, 255, 255), "CLAC"), "step": (0.5, (255, 255, 255), None), "echo_step": (0.8, (255, 255, 255), None),
}
DE_PORTA = {"knock", "bang", "door_close", "door_open", "lock"}


def _ancora(ep, shot, e):
    """Ponto (no cenário) de onde o som vem."""
    if "x" in e and "y" in e: return float(e["x"]), float(e["y"]), True
    from .mapa import marcas
    m = marcas(shot.get("scene", "")) if shot.get("scene") else {}
    if e["name"] in DE_PORTA and "porta" in m: return m["porta"]["x"], m["porta"]["y"] - 480, True
    if e["name"] in DE_PORTA and "porta_camara" in m: return m["porta_camara"]["x"], m["porta_camara"]["y"] - 480, True
    if e["name"] == "car_alarm" and "carro" in m: return m["carro"]["x"], m["carro"]["y"] - 120, True
    return 540, 880, False


def _tela(ep, x, y, no_cenario):
    cam = getattr(ep, "_cam", None)
    if not no_cenario or not cam: return x, y, 1.0
    camx, (z, x0, y0), depth = cam
    return (x - camx * depth - x0) * z, (y - y0) * z, z


def _arcos(d, x, y, k, cor, n=3, r0=40, r1=260, larg=10, abertura=None):
    for i in range(n):
        p = c01(k * 1.3 - i * 0.18)
        if p <= 0 or p >= 1: continue
        r = r0 + (r1 - r0) * ease_out(p); a = int(255 * (1 - p))
        box = [x - r, y - r, x + r, y + r]
        if abertura:
            for a0, a1 in abertura: d.arc(box, a0, a1, fill=cor + (a,), width=max(2, int(larg * (1 - p * 0.6))))
        else: d.ellipse(box, outline=cor + (a,), width=max(2, int(larg * (1 - p * 0.6))))


def _texto(d, txt, x, y, k, cor, tam=86, ang=0):
    if not txt or k <= 0 or k >= 1: return None
    s = 0.7 + 0.5 * ease_out(c01(k / 0.25)); a = int(255 * (1 - c01((k - 0.6) / 0.4)))
    f = font("title", int(tam * s))
    tb = d.textbbox((0, 0), txt, font=f); w, h = tb[2] - tb[0], tb[3] - tb[1]
    lay = Image.new("RGBA", (w + 40, h + 50), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    dl.text((20, 10 - tb[1] + 10), txt, font=f, fill=cor + (a,), stroke_width=7, stroke_fill=(15, 12, 18, a))
    return lay.rotate(ang, Image.BICUBIC, expand=True), (int(x - (w + 40) / 2), int(y - (h + 50) / 2))


def desenhar(ep, img, shot, t):
    cfg = shot.get("ondas", ep.spec.get("ondas", True))
    if cfg is False: return img
    cfg = cfg if isinstance(cfg, dict) else {}
    lay = None; textos = []
    for e in ep.spec.get("sfx", []):
        nome = e.get("name")
        if nome not in ESTILO or e.get("onda") is False: continue
        if nome in ("step", "echo_step") and not cfg.get("passos"): continue
        dur, cor, txt = ESTILO[nome]; dur = e.get("dur", dur)
        rel = t - e["t"]
        if not (0 <= rel < dur) or not (shot["start"] <= e["t"] < shot["end"] + 0.5): continue
        k = rel / dur
        if lay is None: lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        ax, ay, cen = _ancora(ep, shot, e); x, y, z = _tela(ep, ax, ay, cen); zz = min(2.2, max(0.6, z))
        seed = int(e["t"] * 100) % 7
        if nome in ("knock", "lock", "door_open", "door_close"):
            _arcos(d, x, y, k, cor, 3, 30 * zz, 210 * zz, 9, [(-60, 60), (120, 240)])
        elif nome == "bang":
            for i in range(12):
                a = i / 12 * 2 * math.pi + seed; r0, r1 = 60 * zz, (150 + 120 * ease_out(k)) * zz
                al = int(255 * (1 - k))
                d.line([(x + math.cos(a) * r0, y + math.sin(a) * r0), (x + math.cos(a) * r1, y + math.sin(a) * r1)], fill=cor + (al,), width=10)
            _arcos(d, x, y, k, (255, 255, 255), 2, 40 * zz, 320 * zz, 12)
        elif nome == "glass":
            for i in range(9):
                a = i / 9 * 2 * math.pi + seed * 0.7; r = (60 + 260 * ease_out(k)) * zz; al = int(255 * (1 - k))
                cx, cy = x + math.cos(a) * r, y + math.sin(a) * r + 200 * k * k
                d.polygon([(cx, cy - 22), (cx + 14, cy + 10), (cx - 12, cy + 16)], fill=cor + (al,), outline=(255, 255, 255, al))
        elif nome in ("car_alarm", "siren"):
            per = 0.5 if nome == "car_alarm" else 0.7
            fase = (rel % per) / per; c2 = cor if nome == "car_alarm" or int(rel / per) % 2 == 0 else (60, 120, 255)
            fade = min(1.0, (dur - rel) / 0.5, rel / 0.2)
            for i in range(3):
                p = (fase + i / 3) % 1; r = (60 + 300 * p) * zz; al = int(200 * (1 - p) * fade)
                d.arc([x - r, y - r * 0.7, x + r, y + r * 0.7], 200, 340, fill=c2 + (al,), width=8)
                d.arc([x - r, y - r * 0.7, x + r, y + r * 0.7], 20, 160, fill=c2 + (al,), width=8)
        elif nome in ("notif", "vibe"):
            al = int(255 * (1 - k)); j = math.sin(rel * 90) * 6
            for s in (-1, 1):
                for i in range(3):
                    xx = x + s * (70 + i * 26) * zz + j
                    d.arc([xx - 30, y - 50 - i * 12, xx + 30, y + 50 + i * 12], -50 if s > 0 else 130, 50 if s > 0 else 230, fill=cor + (al,), width=6)
        elif nome == "growl":
            al = int(220 * (1 - k))
            for i in range(4):
                yy = y - 90 + i * 60; pts = [(x - 260 + j * 20, yy + math.sin(j * 0.9 + rel * 18 + i) * 14) for j in range(27)]
                d.line(pts, fill=cor + (al,), width=6)
        elif nome == "heartbeat":
            bt = rel % 0.8; p = max(c01(1 - bt / 0.25), c01(1 - abs(bt - 0.3) / 0.15) * 0.7) * (1 - k * 0.5)
            if p > 0:
                for i in range(6):
                    w = 40 + i * 30; al = int(70 * p * (1 - i / 6))
                    d.rectangle([0, 0, W, H], outline=cor + (al,), width=w)
            txt = None
        elif nome == "beep":
            _arcos(d, x, y, k, cor, 2, 20 * zz, 120 * zz, 6, [(-50, 50), (130, 230)])
        elif nome in ("step", "echo_step"):
            p = ease_out(k); al = int(160 * (1 - k)); r = (30 + 120 * p) * zz
            d.ellipse([x - r, y - r * 0.25, x + r, y + r * 0.25], outline=cor + (al,), width=4)
        if cfg.get("texto", True) and txt:
            ang = (-8, 6, -4, 9, -10, 3, 7)[seed]
            tx, ty = x + (150 if x < W / 2 else -150) * min(zz, 1.4), y - 120 * min(zz, 1.4)
            r = _texto(d, txt, max(150, min(W - 150, tx)), max(520, min(1250, ty)), k, cor if nome != "knock" else (255, 255, 255), 90, ang)
            if r: textos.append(r)
    if lay is None: return img
    for im, pos in textos: lay.alpha_composite(im, (max(0, pos[0]), max(0, pos[1])))
    base = img.convert("RGBA"); base.alpha_composite(lay)
    return base.convert("RGB")
