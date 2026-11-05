"""Acabamento e vida dos cenários (automático em todos os cenários).

1. Acabamento (uma vez, ao montar o cenário): textura de papel no fundo, sombra de contato onde a parede encontra o chão
   e teto mais escuro nos internos. Tira o aspecto "chapado" das cores lisas.
2. Objetos extras nos cenários mais vazios (entrada, corredor, telhado, rua).
3. Vida (a cada quadro): mariposas nas lâmpadas, lâmpadas piscando, gotas pingando, vapor subindo, vaga-lumes, papel
   voando, moscas, luz vermelha de antena e pássaros no amanhecer.

Plano: "vida": false desliga; "vida": {"mariposas": false, ...} desliga um efeito.
"""
import math, random
from PIL import Image, ImageDraw, ImageFilter
from .core import W_D as W, H_D as H

# ---------------- configuração por cenário (coordenadas do cenário, 1080×1920) ----------------
VIDA = {
    "apartamento": {"mariposas": [(300, 1010)]},
    "corredor":    {"pisca": [(540, 308), (540, 648)], "poeira": (380, 300, 700, 1500)},
    "hospital":    {"pisca": [(540, 262), (540, 566)]},
    "escola":      {"pisca": [(540, 254)]},
    "vagao":       {"pisca": [(540, 270), (540, 520)]},
    "delegacia":   {"pisca": [(540, 230)]},
    "mercado":     {"pisca": [(540, 300)]},
    "loja":        {"pisca": [(540, 230)]},
    "deposito":    {"mariposas": [(540, 400)], "poeira": (380, 380, 700, 1400)},
    "beco":        {"mariposas": [(585, 775)], "gotas": [(300, 900, 1650), (760, 820, 1700)], "vapor": [(440, 1700)],
                    "moscas": [(220, 1580)], "papel": (1500, 1880)},
    "esgoto":      {"gotas": [(420, 520, 1500), (650, 600, 1550), (540, 420, 1450)], "vapor": [(540, 1500)]},
    "associacao":  {"pisca": [(540, 226)]},
    "camara_fria": {"vapor": [(380, 1650), (700, 1700)], "pisca": [(540, 330)]},
    "estacionamento": {"pisca": [(400, 520), (680, 520)], "gotas": [(820, 700, 1700)]},
    "metro":       {"gotas": [(560, 900, 1600)], "poeira": (300, 700, 800, 1500)},
    "rua":         {"mariposas": [(130, 770), (950, 770)], "vapor": [(700, 1600)], "papel": (1300, 1840)},
    "rua_amanhecer": {"passaros": (100, 300, 1000, 700), "papel": (1300, 1840), "vapor": [(700, 1600)]},
    "entrada_metro": {"vapor": [(780, 1700)], "papel": (1300, 1860)},
    "floresta":    {"vagalumes": (40, 1050, 1040, 1750)},
    "telhado":     {"farol": [(420, 640)], "vapor": [(340, 960)]},
    "ponte":       {"farol": [(470, 1180), (610, 1180)], "passaros": (100, 300, 1000, 800)},
    "posto":       {"mariposas": [(300, 1060), (780, 1060)], "pisca": [(540, 930)]},
    "igreja":      {"poeira": (300, 300, 800, 1300)},
    "portao":      {"mariposas": [(540, 1240)], "papel": (1450, 1880)},
    "viaduto":     {"farol": [(540, 1240)], "papel": (1500, 1880)},
}
VIDA_TIPOS = ("pisca", "mariposas", "gotas", "vapor", "vagalumes", "poeira", "moscas", "papel", "farol", "passaros")
PAREDE_RETA = {"entrada", "apartamento", "deposito", "delegacia", "loja"}
INTERNOS = {"sala_aula", "quadra", "associacao", "masmorra", "trono", "apartamento", "entrada", "corredor", "hospital", "escola", "vagao", "delegacia", "mercado", "loja", "deposito",
            "camara_fria", "estacionamento", "igreja", "escada", "metro", "esgoto"}


# ---------------- acabamento ----------------
_GRAO = {}
def _grao(size, seed=5, forca=7):
    key = (size, seed, forca)
    if key not in _GRAO:
        r = random.Random(seed); w, h = size
        small = Image.effect_noise((max(2, w // 3), max(2, h // 3)), 40).resize(size, Image.BILINEAR)
        _GRAO[key] = small.point(lambda v: int(128 + (v - 128) * forca / 40))
    return _GRAO[key]


def acabamento(sc):
    """Textura e sombras de contato aplicadas uma vez na camada de fundo."""
    if getattr(sc, "_acabado", False) or sc.back is None: return
    back = sc.back.convert("RGB"); w, h = back.size
    # textura de papel (bem leve): ±7 níveis
    g = _grao((w, h), 5, 4).convert("RGB")
    from PIL import ImageChops
    back = ImageChops.add(ImageChops.subtract(back, Image.new("RGB", (w, h), (4, 4, 4))), g.point(lambda v: max(0, v - 124)))
    lay = Image.new("L", (w, h), 0); d = ImageDraw.Draw(lay)
    if sc.name in INTERNOS:
        for y in range(0, 360):                                       # teto mais escuro
            d.line([(0, y), (w, y)], fill=int(70 * (1 - y / 360) ** 1.6))
        y0 = int(sc.ground[0])                                        # sombra de contato parede/chão (só parede reta)
        for k in (range(-26, 40) if sc.name in PAREDE_RETA else ()):
            a = int(60 * math.exp(-(k / 18) ** 2)) if k < 0 else int(60 * math.exp(-(k / 26) ** 2))
            yy = y0 + k
            if 0 <= yy < h: d.line([(0, yy), (w, yy)], fill=max(0, a))
    back = Image.composite(Image.new("RGB", (w, h), (4, 4, 8)), back, lay)
    sc.back = back; sc._acabado = True


# ---------------- objetos extras ----------------
S = 2
def _camada(size):
    return Image.new("RGBA", (size[0] * S, size[1] * S), (0, 0, 0, 0))

def _p(M, *pts): return [((x + M) * S, y * S) for x, y in pts]


def objetos(sc):
    from .scenes import M
    nome = sc.name
    alvo = "mid" if sc.mid is not None else "back"
    base = getattr(sc, alvo); lay = _camada(base.size); d = ImageDraw.Draw(lay); OUT = (16, 14, 18, 255)
    P = lambda *pts: _p(M, *pts)
    if nome == "entrada":
        d.polygon(P((540, 1512), (860, 1512), (900, 1570), (500, 1570)), fill=(110, 40, 40, 255), outline=OUT)      # capacho
        for k in range(5): d.line(P((520 + k * 2, 1530 + k * 8), (880 - k * 2, 1530 + k * 8)), fill=(130, 56, 50, 255), width=2 * S)
        d.rectangle(P((975, 820), (1075, 960)), fill=(60, 44, 34, 255), outline=OUT, width=5 * S)                     # quadro
        d.rectangle(P((990, 835), (1060, 945)), fill=(70, 96, 120, 255))
        d.polygon(P((990, 945), (1020, 880), (1040, 910), (1060, 870), (1060, 945)), fill=(46, 70, 60, 255))
        d.rounded_rectangle(P((955, 1040), (985, 1085)), 4 * S, fill=(200, 198, 190, 255), outline=OUT, width=3 * S)  # interruptor
        d.rectangle(P((965, 1052), (975, 1068)), fill=(160, 158, 150, 255))
        for x in (250, 300):                                                                                           # tênis
            d.rounded_rectangle(P((x, 1520), (x + 42, 1546)), 10 * S, fill=(230, 230, 236, 255), outline=OUT, width=3 * S)
            d.line(P((x + 4, 1540), (x + 40, 1540)), fill=(200, 60, 60, 255), width=3 * S)
    elif nome == "corredor":
        d.rounded_rectangle(P((408, 960), (424, 1030)), 6 * S, fill=(196, 40, 36, 255), outline=OUT, width=2 * S)  # extintor (no fundo: nunca atrás da cabeça em close)
        d.rectangle(P((358, 1158), (374, 1172)), fill=(40, 40, 44, 255)); d.line(P((372, 1166), (392, 1190)), fill=OUT, width=3 * S)
        d.rectangle(P((690, 1110), (740, 1170)), fill=(120, 70, 46, 255), outline=OUT, width=3 * S)                   # vaso
        for k in range(7):
            a = -1.2 + k * 0.4
            d.line(P((715, 1112), (715 + math.sin(a) * 50, 1112 - math.cos(a) * 70)), fill=(54, 96, 60, 255), width=6 * S)
    elif nome == "telhado":
        d.rectangle(P((280, 950), (420, 1042)), fill=(150, 154, 160, 255), outline=OUT, width=4 * S)                   # ar-condicionado
        d.ellipse(P((300, 962), (374, 1032)), fill=(70, 74, 82, 255), outline=OUT, width=3 * S)
        for k in range(4): d.line(P((337, 997), (337 + 30 * math.cos(k * 1.57), 997 + 30 * math.sin(k * 1.57))), fill=(40, 42, 48, 255), width=3 * S)
        d.rectangle(P((468, 990), (488, 1045)), fill=(70, 72, 80, 255), outline=OUT, width=3 * S)                       # respiro
        d.rectangle(P((462, 980), (494, 994)), fill=(80, 82, 90, 255), outline=OUT, width=3 * S)
        d.line(P((60, 840), (240, 900), (420, 870)), fill=(30, 30, 38, 255), width=2 * S)                               # varal
        for x, c in ((120, (170, 60, 60)), (200, (60, 90, 150)), (330, (200, 190, 150))):
            yy = 840 + (x - 60) * 0.33 if x < 240 else 900 - (x - 240) * 0.17
            d.rectangle(P((x - 18, yy), (x + 18, yy + 46)), fill=c + (255,), outline=OUT, width=2 * S)
    elif nome in ("rua", "rua_amanhecer"):
        for (x, y, r_) in ((930, 1250, 34), (975, 1244, 30), (1010, 1254, 28)):                                         # sacos de lixo
            d.ellipse(P((x - r_, y - r_ * 1.1), (x + r_, y + r_ * 0.4)), fill=(26, 26, 30, 255), outline=OUT, width=3 * S)
            d.line(P((x - 6, y - r_ * 1.05), (x + 6, y - r_ * 1.2)), fill=(40, 40, 46, 255), width=3 * S)
        d.rounded_rectangle(P((150, 1206), (178, 1262)), 8 * S, fill=(170, 40, 36, 255), outline=OUT, width=3 * S)     # hidrante
        d.ellipse(P((146, 1196), (182, 1214)), fill=(150, 34, 30, 255), outline=OUT, width=3 * S)
        d.rectangle(P((140, 1224), (188, 1234)), fill=(150, 34, 30, 255), outline=OUT, width=2 * S)
        d.rectangle(P((60, 980), (120, 1060)), fill=(200, 196, 170, 255), outline=OUT, width=2 * S)                    # cartaz no poste
        d.line(P((68, 1000), (112, 1000)), fill=(170, 40, 40, 255), width=4 * S); d.line(P((68, 1020), (104, 1020)), fill=(90, 90, 90, 255), width=3 * S)
        d.line(P((68, 1036), (110, 1036)), fill=(90, 90, 90, 255), width=3 * S)
    else:
        return
    lay = lay.resize(base.size, Image.LANCZOS)
    b = base.convert("RGBA"); b.alpha_composite(lay)
    setattr(sc, alvo, b if alvo == "mid" else b.convert("RGB"))


# ---------------- vida (por quadro) ----------------
def _r(seed): return random.Random(seed)


def vida(sc, img, t, camx, props, cfg=True):
    if cfg is False: return
    conf = VIDA.get(sc.name)
    if not conf: return
    from . import fx
    part = fx.NIVEL.get("part", 1.0)
    # efeitos "leve": some o que vira névoa/sujeira na tela (vapor, poeira, vaga-lumes); "nenhum": só a lâmpada piscando
    corta = set() if part >= 0.99 else ({"vapor", "poeira", "vagalumes", "moscas"} if part > 0 else set(VIDA_TIPOS) - {"pisca"})
    liga = (lambda k: cfg.get(k, k not in corta)) if isinstance(cfg, dict) else (lambda k: k not in corta)
    dx = -camx * sc.depths[1]
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); usou = False
    if liga("pisca") and "pisca" in conf and props.get("_lamp_on", True):
        for i, (x, y) in enumerate(conf["pisca"]):
            k = int(t * 14); r = _r(k * 13 + i * 7 + len(sc.name))
            falha = r.random() < 0.05 or (int(t * 0.5 + i) % 7 == 3 and r.random() < 0.6)
            if falha:
                usou = True
                d.rectangle([x + dx - 90, y - 30, x + dx + 90, y + 40], fill=(0, 0, 0, 170))
                # a sala escurece um pouco quando a lâmpada falha: mancha bem suave (sem borda visível)
                sm = Image.new("L", (img.size[0] // 8, img.size[1] // 8), 0)
                ImageDraw.Draw(sm).ellipse([(x + dx - 300) / 8, (y - 40) / 8, (x + dx + 300) / 8, (y + 700) / 8], fill=38)
                sm = sm.filter(ImageFilter.GaussianBlur(9)).resize(img.size, Image.BILINEAR)
                sombra = Image.new("RGBA", img.size, (0, 0, 0, 0)); sombra.putalpha(sm)
                lay.alpha_composite(sombra)
    if liga("mariposas") and "mariposas" in conf:
        for j, (x, y) in enumerate(conf["mariposas"]):
            for m in range(3):
                a = t * (2.6 + m * 0.7) + m * 2.1 + j; rx, ry = 34 + m * 12, 20 + m * 8
                mx, my = x + dx + math.cos(a) * rx + math.sin(t * 9 + m) * 4, y + math.sin(a * 1.3) * ry
                asa = 3 + abs(math.sin(t * 40 + m)) * 4
                d.ellipse([mx - asa, my - 2, mx + asa, my + 2], fill=(230, 220, 190, 200)); usou = True
    if liga("gotas") and "gotas" in conf:
        for j, (x, ytop, ychao) in enumerate(conf["gotas"]):
            per = 1.6 + j * 0.45; ph = ((t + j * 0.7) % per) / per; queda = 0.55
            if ph < queda:
                p = ph / queda; y = ytop + (ychao - ytop) * p * p
                d.ellipse([x + dx - 4, y - 8, x + dx + 4, y + 6], fill=(170, 200, 230, 210)); usou = True
            else:
                p = (ph - queda) / (1 - queda)
                if p < 0.5:
                    rr = 8 + 50 * p; a = int(200 * (1 - p * 2))
                    d.ellipse([x + dx - rr, ychao - rr * 0.22, x + dx + rr, ychao + rr * 0.22], outline=(170, 200, 230, a), width=2); usou = True
    if liga("vapor") and "vapor" in conf:
        for j, (x, y) in enumerate(conf["vapor"]):
            for k in range(6):
                p = ((t * 0.22 + k / 6 + j * 0.31) % 1.0); rr = 20 + 80 * p
                xx = x + dx + math.sin(t * 0.8 + k * 1.7) * 30 * p; yy = y - 340 * p
                a = int(26 * math.sin(math.pi * p))
                d.ellipse([xx - rr, yy - rr * 0.7, xx + rr, yy + rr * 0.7], fill=(200, 205, 215, a)); usou = True
    if liga("vagalumes") and "vagalumes" in conf:
        x0, y0, x1, y1 = conf["vagalumes"]; r = _r(11)
        for k in range(14):
            bx, by = r.uniform(x0, x1), r.uniform(y0, y1); f = r.uniform(0.3, 0.8)
            x = bx + dx + math.sin(t * f + k) * 40; y = by + math.cos(t * f * 1.3 + k * 2) * 28
            a = max(0.0, math.sin(t * r.uniform(1.2, 2.4) + k * 1.9)) ** 2
            if a > 0.05:
                d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=(220, 255, 120, int(50 * a))); d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(240, 255, 170, int(240 * a))); usou = True
    if liga("poeira") and "poeira" in conf:
        x0, y0, x1, y1 = conf["poeira"]; r = _r(23)
        for k in range(26):
            bx, by = r.uniform(x0, x1), r.uniform(y0, y1)
            x = bx + dx + math.sin(t * 0.3 + k) * 26; y = by + ((t * r.uniform(4, 12) + k * 37) % (y1 - y0)) * 0.3
            a = int(90 * (0.5 + 0.5 * math.sin(t * 0.9 + k)))
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 240, 210, a)); usou = True
    if liga("moscas") and "moscas" in conf:
        for j, (x, y) in enumerate(conf["moscas"]):
            for m in range(5):
                a = t * (5 + m) + m * 1.3
                mx = x + dx + math.cos(a) * (20 + m * 8) + math.sin(t * 17 + m) * 6; my = y + math.sin(a * 1.7) * (12 + m * 4)
                d.ellipse([mx - 3, my - 3, mx + 3, my + 3], fill=(20, 20, 20, 220)); usou = True
    if liga("papel") and "papel" in conf:
        y0, y1 = conf["papel"]
        for k in range(2):
            per = 7.0 + k * 3; p = ((t + k * 4.1) % per) / per
            x = -80 + 1240 * p + dx; y = y0 + (y1 - y0) * (0.3 + 0.5 * k) - abs(math.sin(p * 18 + k)) * 60
            ang = p * 900 + k * 40; w_, h_ = 26, 18
            pts = [(x + math.cos(math.radians(ang + a_)) * r_, y + math.sin(math.radians(ang + a_)) * r_ * 0.6)
                   for a_, r_ in ((30, w_), (150, w_), (210, h_), (330, h_))]
            d.polygon(pts, fill=(220, 214, 196, 220)); usou = True
    if liga("farol") and "farol" in conf:
        for j, (x, y) in enumerate(conf["farol"]):
            on = (t * 0.8 + j * 0.37) % 1.0 < 0.35
            if on:
                d.ellipse([x + dx - 26, y - 26, x + dx + 26, y + 26], fill=(255, 40, 30, 70))
                d.ellipse([x + dx - 7, y - 7, x + dx + 7, y + 7], fill=(255, 90, 80, 255)); usou = True
    if liga("passaros") and "passaros" in conf:
        x0, y0, x1, y1 = conf["passaros"]; r = _r(3)
        for k in range(5):
            per = r.uniform(14, 22); p = ((t + r.uniform(0, per)) % per) / per
            x = x0 - 100 + (x1 - x0 + 200) * p + dx * 0.4; y = r.uniform(y0, y1) + math.sin(p * 30 + k) * 10
            bat = math.sin(t * 9 + k * 2) * 9
            d.line([(x - 16, y - bat), (x, y), (x + 16, y - bat)], fill=(30, 26, 36, 230), width=3); usou = True
    if usou:
        base = img.convert("RGBA"); base.alpha_composite(lay)
        img.paste(base.convert("RGB"))
