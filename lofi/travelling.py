"""Travelling lateral: o cenário passa enquanto o personagem anda ou corre (rua, mata, túnel, corredor, ponte...).

No plano: `"travelling": 320` (px/s no chão; positivo = eles vão para a direita, negativo = para a esquerda)
ou `"travelling": {"speed": 320, "frente": true}` (`frente` = objetos passando borrados na frente da câmera).
Os personagens ficam no lugar (use `walk`/`run` e `facing`) e o mundo rola em camadas com paralaxe: céu parado,
prédios/árvores ao longe devagar, fachadas/paredes no meio, calçada/chão com postes, lixeiras, portas etc. no ritmo dos pés.

Funciona para qualquer cenário: o lugar decide o tema (`TEMA`) e a hora/clima vêm do cenário original (rua_amanhecer
fica clara, rua chove, hospital tem paredes verde-claras...). As tiras são geradas uma vez (procedurais e sem emenda)
e repetem a cada ~3 telas, com elementos espaçados de forma irregular para a repetição não aparecer.
"""
import random
from PIL import Image, ImageDraw, ImageFilter
from .core import W, H, grad, add_light
from . import fx

L = 3 * W          # comprimento da tira que repete
B = 220            # faixa de emenda (fundida para não aparecer o corte)
CHAO = 1540        # onde a parede/fachada encontra o chão

TEMA = {"rua": "cidade", "rua_amanhecer": "cidade", "entrada_metro": "cidade", "posto": "cidade", "telhado": "cidade",
        "janela": "cidade", "portao": "cidade", "beco": "cidade", "viaduto": "ponte", "estacionamento": "tunel", "vagao": "interno", "floresta": "mata", "metro": "tunel", "esgoto": "esgoto", "ponte": "ponte",
        "corredor": "interno", "hospital": "interno", "escola": "interno", "delegacia": "interno", "mercado": "interno",
        "igreja": "interno", "apartamento": "interno", "entrada": "interno", "escada": "interno"}
PAREDE = {"hospital": (150, 176, 160), "escola": (176, 160, 126), "delegacia": (120, 132, 150), "mercado": (170, 170, 160),
          "igreja": (150, 130, 110), "corredor": (120, 110, 96), "apartamento": (110, 100, 120), "entrada": (110, 100, 120),
          "escada": (120, 70, 66)}


def _k(col, k): return tuple(max(0, min(255, int(c * k))) for c in col[:3]) + tuple(col[3:])


def _loop(img):
    """Funde o fim da tira no começo para ela repetir sem corte."""
    n = img.width - B
    out = img.crop((0, 0, n, img.height))
    ramp = Image.linear_gradient("L").rotate(90, expand=True).resize((B, img.height)).transpose(Image.FLIP_LEFT_RIGHT)
    mix = Image.composite(img.crop((n, 0, n + B, img.height)), img.crop((0, 0, B, img.height)), ramp)
    out.paste(mix, (0, 0))
    return out


def _wrapcrop(strip, off):
    n = strip.width; o = int(off) % n
    if o + W <= n: return strip.crop((o, 0, o + W, H))
    out = Image.new(strip.mode, (W, H)); a = strip.crop((o, 0, n, H)); out.paste(a, (0, 0))
    out.paste(strip.crop((0, 0, W - a.width, H)), (a.width, 0))
    return out


def _slots(r, passo, jit, x0=B + 80, x1=L - 80):
    """Posições irregulares ao longo da tira (longe da emenda)."""
    x = x0 + r.uniform(0, passo * 0.5)
    while x < x1:
        yield int(x); x += passo + r.uniform(-jit, jit)


def make(base):
    """Cria (uma vez) a versão em travelling do cenário `base` (instância de scenes.Scene)."""
    from .scenes import Scene
    class Travelling(Scene):
        def __init__(self):
            for k in ("name", "light", "grade", "acoustic", "amb", "rain_full", "rain_strength", "wet", "fog_cfg",
                      "lightning_full", "clouds"):
                setattr(self, k, getattr(base, k, None))
            self.rain_boxes = []; self.lightning_boxes = []; self.ripples = None
            self.depths = (0.15, 0.55, 1.0)
            self.ground = (1560, 1880, 1.02, 1.22)
            self.tema = TEMA.get(base.name, "cidade" if base.acoustic == "aberto" else "interno")
            self.kluz = {"night": 0.55, "dark": 0.45, "dawn": 0.85, "day": 1.0, "red": 0.6}.get(base.light, 0.7)
            if base.name == "rua_amanhecer": self.kluz = 0.85
            self.ceu, self.longe, self.meio, self.perto = getattr(self, "_" + self.tema)()
            self.front = None
        # ---------------- temas ----------------
        def _ceu(self):
            cols = getattr(base, "sky_cols", None) or (((10, 14, 30), (60, 26, 34)) if self.kluz < 0.7 else ((150, 150, 180), (230, 170, 150)))
            img = grad(W, H, *cols)
            if getattr(base, "moon", self.kluz < 0.7):
                d = ImageDraw.Draw(img); d.ellipse((760, 300, 880, 420), fill=(215, 210, 195)); d.ellipse((738, 288, 858, 408), fill=cols[0])
            else:
                img = add_light(img, (560, 560, 900, 900), (240, 170, 130), 110, 80)
            return img

        def _predios_longe(self, r, base_y=1300, cor=(36, 46, 70)):
            img = Image.new("RGBA", (L + B, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img); x = -20
            far = _k(cor, self.kluz * 1.2) + (255,)
            while x < L + B:
                bw = r.randint(60, 150); top = r.randint(380, 900)
                d.rectangle((x, top, x + bw, base_y), fill=far)
                for wy in range(top + 14, base_y - 10, 22):
                    for wx in range(x + 8, x + bw - 10, 16):
                        if r.random() < 0.18 * (1.4 - self.kluz): d.rectangle((wx, wy, wx + 6, wy + 9), fill=(240, 200, 130, 255))
                x += bw + r.randint(2, 14)
            return _loop(img.filter(ImageFilter.GaussianBlur(2)))

        def _cidade(self):
            r = random.Random(41)
            ceu = self._ceu(); longe = self._predios_longe(r)
            # fachadas
            meio = Image.new("RGBA", (L + B, H), (0, 0, 0, 0)); d = ImageDraw.Draw(meio); x = -10
            tons = [(92, 70, 64), (80, 84, 96), (104, 92, 76), (70, 76, 70), (96, 80, 90)]
            while x < L + B:
                bw = r.randint(280, 520); top = r.randint(380, 820)
                if r.random() < 0.14:   # beco
                    d.rectangle((x, 700, x + 90, CHAO), fill=_k((14, 14, 20), 1) + (255,)); x += 90; continue
                c = _k(r.choice(tons), self.kluz)
                d.rectangle((x, top, x + bw, CHAO), fill=c + (255,))
                d.rectangle((x - 6, top - 18, x + bw + 6, top), fill=_k(c, 0.75) + (255,))
                for wy in range(top + 50, CHAO - 300, 120):
                    for wx in range(x + 40, x + bw - 70, 110):
                        acesa = r.random() < 0.3 * (1.3 - self.kluz)
                        d.rectangle((wx, wy, wx + 56, wy + 74), fill=(250, 210, 140, 255) if acesa else _k((30, 36, 52), self.kluz + 0.3) + (255,))
                        d.rectangle((wx - 4, wy + 74, wx + 60, wy + 80), fill=_k(c, 0.6) + (255,))
                # térreo: loja com porta de enrolar, ou porta de prédio
                gy = CHAO - 250
                d.rectangle((x, gy - 12, x + bw, gy), fill=_k(c, 0.6) + (255,))
                if r.random() < 0.55:
                    sx0, sx1 = x + 30, x + bw - 30
                    d.rectangle((sx0, gy + 20, sx1, CHAO), fill=_k((88, 90, 96), self.kluz) + (255,))
                    for yy in range(gy + 30, CHAO, 16): d.line((sx0, yy, sx1, yy), fill=_k((60, 62, 70), self.kluz) + (255,), width=3)
                    if r.random() < 0.6:
                        aw = _k(r.choice([(150, 50, 46), (40, 90, 80), (170, 130, 50)]), self.kluz)
                        d.polygon([(sx0 - 10, gy - 6), (sx1 + 10, gy - 6), (sx1 + 30, gy + 60), (sx0 - 30, gy + 60)], fill=aw + (255,))
                else:
                    dx0 = x + bw // 2 - 60
                    d.rectangle((dx0, gy + 30, dx0 + 120, CHAO), fill=_k((40, 30, 26), self.kluz) + (255,))
                    d.rectangle((dx0 + 14, gy + 50, dx0 + 106, gy + 130), fill=(240, 200, 130, 200) if r.random() < 0.4 else _k((20, 24, 34), 1) + (255,))
                x += bw + r.randint(0, 6)
            meio = _loop(meio.filter(ImageFilter.GaussianBlur(1)))
            perto = self._chao_calcada(r)
            return ceu, longe, meio, perto

        def _chao_calcada(self, r):
            img = Image.new("RGBA", (L + B, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
            cal = _k((96, 96, 104), self.kluz)
            img.paste(grad(L + B, 1840 - CHAO, _k(cal, 0.8), cal).convert("RGBA"), (0, CHAO))
            d.rectangle((0, CHAO, L + B, CHAO + 8), fill=_k((20, 20, 26), 1) + (255,))
            for xx in range(0, L + B, 150):
                d.line((xx, CHAO + 8, xx - 40, 1840), fill=_k(cal, 0.7) + (255,), width=3)
            d.line((0, 1690, L + B, 1690), fill=_k(cal, 0.75) + (255,), width=2)
            d.rectangle((0, 1840, L + B, 1862), fill=_k((140, 140, 146), self.kluz) + (255,))
            d.rectangle((0, 1862, L + B, H), fill=_k((30, 30, 38), self.kluz + 0.2) + (255,))
            for xx in range(60, L + B, 260): d.rectangle((xx, 1895, xx + 120, 1905), fill=_k((170, 160, 90), self.kluz) + (255,))
            luzes = []
            for xp in _slots(r, 640, 180):            # postes
                d.rectangle((xp - 9, 560, xp + 9, 1600), fill=(24, 24, 30, 255))
                d.rectangle((xp - 16, 1580, xp + 16, 1610), fill=(24, 24, 30, 255))
                d.rectangle((xp, 560, xp + 110, 572), fill=(24, 24, 30, 255))
                d.ellipse((xp + 90, 560, xp + 136, 590), fill=(255, 230, 170, 255))
                luzes.append(xp + 113)
            for xp in _slots(r, 900, 300):            # lixeira / hidrante / caixa
                tipo = r.choice(("lixeira", "hidrante", "caixa"))
                if tipo == "lixeira":
                    d.rounded_rectangle((xp, 1470, xp + 70, 1600), 8, fill=_k((50, 90, 60), self.kluz) + (255,))
                    d.rectangle((xp - 6, 1460, xp + 76, 1476), fill=_k((40, 70, 50), self.kluz) + (255,))
                elif tipo == "hidrante":
                    d.rounded_rectangle((xp, 1520, xp + 44, 1600), 10, fill=_k((170, 40, 36), self.kluz) + (255,))
                    d.ellipse((xp - 4, 1506, xp + 48, 1534), fill=_k((190, 50, 44), self.kluz) + (255,))
                else:
                    d.rectangle((xp, 1440, xp + 90, 1600), fill=_k((60, 66, 80), self.kluz) + (255,))
            if self.wet or self.kluz < 0.7:
                for xl in luzes:
                    img = add_light(img, (xl - 160, 560, xl + 160, 1700), (220, 190, 120), 70, 90 if self.kluz < 0.7 else 40)
            return _loop(img)

        def _mata(self):
            r = random.Random(7); ceu = self._ceu()
            longe = Image.new("RGBA", (L + B, H), (0, 0, 0, 0)); d = ImageDraw.Draw(longe)
            for xp in range(-40, L + B, 70):
                h = r.randint(500, 900); c = _k((30, 52, 44), self.kluz * 1.2) + (255,)
                d.polygon([(xp, 1400), (xp + 60, 1400 - h), (xp + 120, 1400)], fill=c)
            longe = _loop(longe.filter(ImageFilter.GaussianBlur(3)))
            meio = Image.new("RGBA", (L + B, H), (0, 0, 0, 0)); d = ImageDraw.Draw(meio)
            d.rectangle((0, 1300, L + B, CHAO), fill=_k((26, 40, 30), self.kluz) + (255,))
            for xp in _slots(r, 260, 120, 0, L + B):
                tw = r.randint(40, 80); c = _k((52, 40, 32), self.kluz) + (255,)
                d.rectangle((xp, 200, xp + tw, CHAO), fill=c)
                for _ in range(4):
                    cx, cy, rr = xp + tw // 2 + r.randint(-120, 120), r.randint(100, 600), r.randint(90, 170)
                    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=_k((34, 64, 44), self.kluz) + (255,))
            meio = _loop(meio.filter(ImageFilter.GaussianBlur(1.5)))
            perto = Image.new("RGBA", (L + B, H), (0, 0, 0, 0)); d = ImageDraw.Draw(perto)
            perto.paste(grad(L + B, H - CHAO, _k((70, 56, 40), self.kluz), _k((44, 34, 24), self.kluz)).convert("RGBA"), (0, CHAO))
            for xp in range(0, L + B, 34):
                h = r.randint(16, 46); d.polygon([(xp, CHAO + 6), (xp + 8, CHAO - h), (xp + 16, CHAO + 6)], fill=_k((50, 90, 50), self.kluz) + (255,))
            for xp in _slots(r, 380, 160):
                d.ellipse((xp, 1760, xp + r.randint(30, 70), 1790), fill=_k((110, 104, 96), self.kluz) + (255,))
            for xp in _slots(r, 1100, 300):
                d.rectangle((xp, 1500, xp + 110, 1610), fill=_k((70, 52, 36), self.kluz) + (255,))
                d.ellipse((xp, 1480, xp + 110, 1520), fill=_k((120, 96, 70), self.kluz) + (255,))
            return ceu, longe, meio, _loop(perto)

        def _tunel(self, parede=(70, 74, 80), agua=False):
            r = random.Random(13)
            ceu = Image.new("RGB", (W, H), _k((12, 12, 16), 1))
            longe = None
            meio = Image.new("RGBA", (L + B, H), (0, 0, 0, 0)); d = ImageDraw.Draw(meio)
            kp = max(self.kluz, 0.5)
            d.rectangle((0, 0, L + B, 280), fill=_k((30, 30, 36), kp) + (255,))
            d.rectangle((0, 280, L + B, CHAO), fill=_k(parede, kp) + (255,))
            for yy in range(300, CHAO, 46): d.line((0, yy, L + B, yy), fill=_k(parede, kp * 0.8) + (255,), width=2)
            for xx in range(0, L + B, 64): d.line((xx, 280, xx, CHAO), fill=_k(parede, kp * 0.85) + (255,), width=2)
            luzes = []
            for xp in _slots(r, 520, 120, 0, L + B):
                d.rectangle((xp, 280, xp + 100, CHAO), fill=_k(parede, kp * 0.7) + (255,))
                d.rectangle((xp - 10, 270, xp + 110, 300), fill=_k(parede, kp * 0.55) + (255,))
            for xp in _slots(r, 640, 100, 0, L + B):
                d.rectangle((xp, 250, xp + 160, 270), fill=(230, 240, 220, 255)); luzes.append(xp + 80)
            if not agua:
                for xp in _slots(r, 1300, 300):
                    d.rectangle((xp, 760, xp + 300, 1100), fill=_k((40, 44, 56), kp) + (255,), outline=(20, 20, 24, 255), width=8)
                    d.rectangle((xp + 20, 780, xp + 280, 1080), fill=_k((90, 70, 60), kp) + (255,))
            for xl in luzes: meio = add_light(meio, (xl - 220, 240, xl + 220, 900), (210, 220, 200), 80, 70)
            meio = _loop(meio)
            perto = Image.new("RGBA", (L + B, H), (0, 0, 0, 0)); d = ImageDraw.Draw(perto)
            if agua:
                d.rectangle((0, CHAO, L + B, 1840), fill=_k((50, 52, 48), kp) + (255,))
                perto.paste(grad(L + B, H - 1840, _k((40, 60, 44), kp), _k((20, 30, 22), kp)).convert("RGBA"), (0, 1840))
                for xx in range(0, L + B, 90): d.line((xx, 1880, xx + 50, 1880), fill=_k((90, 120, 90), kp) + (255,), width=2)
            else:
                perto.paste(grad(L + B, H - CHAO, _k((84, 84, 90), kp), _k((50, 50, 56), kp)).convert("RGBA"), (0, CHAO))
                for xx in range(0, L + B, 120): d.line((xx, CHAO, xx - 50, H), fill=_k((60, 60, 66), kp) + (255,), width=2)
                d.rectangle((0, 1850, L + B, 1872), fill=_k((210, 180, 40), kp) + (255,))
            return ceu, longe, meio, _loop(perto)

        def _esgoto(self): return self._tunel(parede=(66, 74, 62), agua=True)

        def _interno(self):
            r = random.Random(23); kp = max(self.kluz, 0.6)
            cor = PAREDE.get(base.name, (120, 110, 96))
            ceu = Image.new("RGB", (W, H), _k(cor, kp * 0.5))
            longe = None
            meio = Image.new("RGBA", (L + B, H), (0, 0, 0, 0)); d = ImageDraw.Draw(meio)
            d.rectangle((0, 0, L + B, 260), fill=_k(cor, kp * 0.6) + (255,))
            d.rectangle((0, 260, L + B, CHAO), fill=_k(cor, kp) + (255,))
            d.rectangle((0, 1240, L + B, CHAO), fill=_k(cor, kp * 0.8) + (255,))
            d.rectangle((0, 1232, L + B, 1244), fill=_k(cor, kp * 0.6) + (255,))
            luzes = []
            for xp in _slots(r, 560, 160, 0, L + B):
                if r.random() < 0.7:   # porta
                    d.rectangle((xp - 12, 720, xp + 182, CHAO), fill=_k(cor, kp * 0.55) + (255,))
                    d.rectangle((xp, 734, xp + 170, CHAO), fill=_k((110, 82, 60), kp) + (255,))
                    d.rectangle((xp + 50, 790, xp + 120, 900), fill=_k((160, 190, 200), kp) + (255,))
                    d.ellipse((xp + 140, 1140, xp + 156, 1156), fill=(200, 190, 150, 255))
                    d.rectangle((xp + 60, 680, xp + 110, 706), fill=(230, 230, 220, 255))
                else:                   # quadro / janela interna
                    d.rectangle((xp, 600, xp + 260, 980), fill=_k((40, 50, 60), kp) + (255,), outline=_k(cor, kp * 0.5) + (255,), width=10)
            for xp in _slots(r, 480, 80, 0, L + B):
                d.rectangle((xp, 236, xp + 200, 256), fill=(240, 245, 235, 255)); luzes.append(xp + 100)
            for xl in luzes: meio = add_light(meio, (xl - 200, 220, xl + 200, 760), (240, 240, 220), 80, 32)
            meio = _loop(meio)
            perto = Image.new("RGBA", (L + B, H), (0, 0, 0, 0)); d = ImageDraw.Draw(perto)
            chao = _k((150, 146, 136), kp)
            perto.paste(grad(L + B, H - CHAO, _k(chao, 0.8), chao).convert("RGBA"), (0, CHAO))
            d.rectangle((0, CHAO, L + B, CHAO + 14), fill=_k(cor, kp * 0.45) + (255,))
            for xx in range(0, L + B, 130): d.line((xx, CHAO + 14, xx - 60, H), fill=_k(chao, 0.8) + (255,), width=2)
            for yy in (1660, 1790): d.line((0, yy, L + B, yy), fill=_k(chao, 0.82) + (255,), width=2)
            return ceu, longe, meio, _loop(perto)

        def _ponte(self):
            r = random.Random(31); ceu = self._ceu()
            longe = self._predios_longe(r, base_y=1180, cor=(40, 50, 76))
            ld = ImageDraw.Draw(longe); ld.rectangle((0, 1180, longe.width, CHAO), fill=_k((30, 40, 60), self.kluz * 1.2) + (255,))
            meio = Image.new("RGBA", (L + B, H), (0, 0, 0, 0)); d = ImageDraw.Draw(meio)
            c = _k((60, 64, 74), self.kluz + 0.2) + (255,)
            for xt in range(0, L + B, 1620):
                d.rectangle((xt + 600, 120, xt + 660, CHAO), fill=c)
            for xx in range(0, L + B, 60):
                fase = ((xx - 630) % 1620) / 1620.0
                ytop = 1140 - 1000 * (2 * abs(fase - 0.5)) ** 1.6
                d.line((xx, ytop, xx, CHAO - 120), fill=c, width=4)
            d.rectangle((0, CHAO - 130, L + B, CHAO - 110), fill=c)
            for xx in range(0, L + B, 80): d.rectangle((xx, CHAO - 120, xx + 10, CHAO), fill=c)
            meio = _loop(meio)
            perto = Image.new("RGBA", (L + B, H), (0, 0, 0, 0)); d = ImageDraw.Draw(perto)
            perto.paste(grad(L + B, H - CHAO, _k((80, 80, 88), self.kluz), _k((40, 40, 46), self.kluz)).convert("RGBA"), (0, CHAO))
            for xx in range(40, L + B, 280): d.rectangle((xx, 1800, xx + 150, 1812), fill=_k((200, 190, 120), self.kluz) + (255,))
            return ceu, longe, meio, _loop(perto)

        # ---------------- desenho por quadro ----------------
        def build(self): return None, None, None
        def render_back(self, t, camx, props):
            s = props.get("_scroll", 0.0)
            img = self.ceu.copy()
            self.sky(img, t, camx + s * 0.4)
            for strip, dep in ((self.longe, self.depths[0]), (self.meio, self.depths[1]), (self.perto, self.depths[2])):
                if strip is None or strip.width <= W: continue
                lay = _wrapcrop(strip, (s + camx) * dep + 2000); img.paste(lay, (0, 0), lay)
            if self.wet and self.rain_full and self.rain_strength: fx.splashes(img, t, CHAO + 40, 1880, n=24)
            return img
        def render_front(self, img, t, camx, props, flashes):
            if self.fog_cfg: fx.fog(img, t, **self.fog_cfg)
            if props.get("_frente"):
                s = props.get("_scroll", 0.0); d = ImageDraw.Draw(img); r = random.Random(3)
                per = 1700
                for k in range(-1, 3):
                    xw = k * per + r.uniform(0, 400) - ((s * 1.7) % per)
                    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
                    ld.rectangle((xw, 0, xw + 90, H), fill=(10, 10, 14, 255))
                    lay = lay.filter(ImageFilter.GaussianBlur(14)); img.paste(lay, (0, 0), lay)
            if self.rain_full and self.rain_strength: fx.rain(img, t, strength=self.rain_strength)
            if flashes and (self.lightning_full or self.tema in ("cidade", "mata", "ponte")):
                img = fx.lightning(img, t, flashes)
            return img
    return Travelling()
