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
from .core import W, H, grad, add_light, font
from . import fx

L = 3 * W          # comprimento da tira que repete
B = 220            # faixa de emenda (fundida para não aparecer o corte)
CHAO = 1540        # onde a parede/fachada encontra o chão

TEMA = {"rua": "cidade", "rua_amanhecer": "cidade", "entrada_metro": "cidade", "posto": "cidade", "telhado": "cidade",
        "janela": "cidade", "portao": "cidade", "beco": "cidade", "viaduto": "ponte", "estacionamento": "tunel", "vagao": "interno", "floresta": "mata", "metro": "tunel", "esgoto": "esgoto", "ponte": "ponte",
        "corredor": "interno", "hospital": "interno", "escola": "interno", "delegacia": "interno", "mercado": "interno",
        "igreja": "interno", "loja": "interno", "deposito": "interno", "camara_fria": "interno", "apartamento": "interno", "entrada": "interno", "escada": "interno"}
PAREDE = {"hospital": (150, 176, 160), "escola": (176, 160, 126), "delegacia": (120, 132, 150), "mercado": (170, 170, 160),
          "igreja": (150, 130, 110), "corredor": (120, 110, 96), "apartamento": (110, 100, 120), "entrada": (110, 100, 120),
          "escada": (120, 70, 66), "loja": (112, 122, 112), "deposito": (96, 92, 84), "camara_fria": (110, 140, 158)}


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
            ch = props.get("_chegada")
            if ch:
                tipo, x = ch
                if tipo not in self._spr: self._spr[tipo] = sprite_chegada(tipo, self.kluz)
                spr = self._spr[tipo]
                if -spr.width < x + spr.width / 2 and x - spr.width / 2 < W:
                    img.paste(spr, (int(x - spr.width / 2), CHAO + 150 - spr.height), spr)
            return img
        _spr = {}
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


CHEGADAS = ("carro", "porta", "escada", "portao")


def sprite_chegada(tipo, k=0.6):
    """Destino que entra no quadro no fim de um travelling com chegada (base = chão da calçada)."""
    if tipo == "carro":
        img = Image.new("RGBA", (520, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
        d.rounded_rectangle((10, 100, 510, 220), 40, fill=_k((120, 40, 36), k + 0.2) + (255,), outline=(16, 14, 18, 255), width=6)
        d.rounded_rectangle((110, 30, 400, 120), 34, fill=_k((104, 34, 30), k + 0.2) + (255,), outline=(16, 14, 18, 255), width=6)
        d.rectangle((140, 46, 245, 110), fill=(24, 28, 40, 255)); d.rectangle((265, 46, 370, 110), fill=(24, 28, 40, 255))
        for cx in (110, 410): d.ellipse((cx - 50, 170, cx + 50, 260), fill=(14, 14, 16, 255)); d.ellipse((cx - 22, 192, cx + 22, 238), fill=(90, 90, 96, 255))
        d.ellipse((470, 130, 504, 156), fill=(255, 236, 180, 255)); d.rectangle((250, 140, 280, 148), fill=(30, 26, 30, 255))
        return img
    if tipo == "porta":
        img = Image.new("RGBA", (260, 560), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
        d.rectangle((0, 0, 260, 560), fill=(40, 34, 30, 255)); d.rectangle((24, 24, 236, 560), fill=_k((120, 86, 60), k + 0.3) + (255,))
        d.rectangle((80, 70, 180, 200), fill=(240, 210, 140, 255)); d.ellipse((200, 300, 220, 320), fill=(220, 200, 150, 255))
        return img
    if tipo == "portao":
        img = Image.new("RGBA", (420, 620), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
        d.rectangle((0, 0, 420, 620), fill=(36, 30, 30, 255)); d.rectangle((30, 40, 390, 620), fill=(150, 130, 90, 255))
        for x in range(30, 391, 30): d.rectangle((x, 40, x + 8, 620), fill=(22, 22, 26, 255))
        for y in (60, 320, 600): d.rectangle((30, y, 398, y + 12), fill=(22, 22, 26, 255))
        return img
    if tipo == "escada":     # boca da estação na calçada, com a placa
        img = Image.new("RGBA", (520, 760), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
        d.rectangle((60, 600, 460, 760), fill=(12, 12, 16, 255))
        for kk in range(5): d.line((70 + kk * 6, 620 + kk * 28, 450 - kk * 6, 620 + kk * 28), fill=(40 + kk * 10, 40 + kk * 10, 48 + kk * 10, 255), width=6)
        for x in (60, 460): d.line((x, 520, x, 760), fill=(150, 150, 160, 255), width=8)
        d.line((60, 520, 460, 520), fill=(150, 150, 160, 255), width=8)
        d.rectangle((24, 120, 36, 600), fill=(30, 30, 36, 255)); d.ellipse((-30, 40, 90, 160), fill=(200, 40, 40, 255), outline=(240, 240, 240, 255), width=5)
        d.text((10, 62), "M", font=font("title", 70), fill=(255, 255, 255, 255))
        return img
    raise ValueError(f"chegada desconhecida: {tipo} (use {', '.join(CHEGADAS)})")


def posicao(tv, rel, dur):
    """Quanto o chão andou (px) em `rel` segundos e, se houver chegada, onde o destino está na tela.
    Com "chegada", o travelling desacelera nos últimos `para` segundos e para com o destino em `chegada_x`."""
    v = float(tv.get("speed", 300)); ch = tv.get("chegada")
    if not ch: return v * rel, None
    p = min(float(tv.get("para", 1.5)), dur * 0.8); t0 = dur - p
    def pos(r):
        if r <= t0: return v * r
        u = min(r - t0, p); return v * t0 + v * (u - u * u / (2 * p))
    fim = pos(dur); x_alvo = float(tv.get("chegada_x", 760 if v > 0 else 320))
    return pos(rel), (ch, x_alvo + (fim - pos(rel)) * (1 if v > 0 else -1))


# ======================= travelling de frente / de costas =======================
# Câmera no meio do caminho olhando para o ponto de fuga. "dir": "frente" = os personagens vêm na direção da câmera
# (a câmera recua e o caminho vai ficando para trás deles); "dir": "fundo" = a câmera segue por trás e o caminho vem.
YH = 1150; GH = 770                    # horizonte e altura da câmera (px na profundidade 1)


def _proj(X, Y, z): return 540 + X / z, YH + (GH - Y) / z


def make_frente(base):
    lat = make(base)                                    # reaproveita tema, cores e clima do travelling lateral
    from .scenes import Scene

    class Frente(Scene):
        def __init__(self):
            for k in ("name", "light", "grade", "acoustic", "amb", "rain_full", "rain_strength", "wet", "fog_cfg",
                      "lightning_full", "clouds", "tema", "kluz", "ceu"):
                setattr(self, k, getattr(lat, k, None))
            self.rain_boxes = []; self.lightning_boxes = []; self.ripples = None
            self.depths = (0.15, 0.55, 1.0); self.ground = lat.ground; self.front = None
            fora = self.tema in ("cidade", "ponte", "mata")
            k = self.kluz
            self.cfg = dict(
                fora=fora,
                chao=_k({"mata": (70, 56, 40), "tunel": (84, 84, 90), "esgoto": (50, 60, 50)}.get(self.tema, (46, 46, 54)), k + 0.15),
                lado=_k({"mata": (60, 50, 36), "interno": (150, 146, 136)}.get(self.tema, (96, 96, 104)), k),
                parede=_k(PAREDE.get(base.name, {"cidade": (90, 76, 70), "tunel": (70, 74, 80), "esgoto": (66, 74, 62),
                                                  "ponte": (60, 64, 74), "mata": (34, 60, 42)}.get(self.tema, (120, 110, 96))), k),
                largura=380 if fora else 300, muro=900 if fora else 520, teto=None if fora else 1300)
        def build(self): return None, None, None

        def _quad(self, d, pts, cor):
            d.polygon([_proj(*p) for p in pts], fill=cor)

        def render_back(self, t, camx, props):
            s = props.get("_scroll", 0.0) * 0.004                          # profundidade andada
            c = self.cfg; img = self.ceu.copy() if c["fora"] else Image.new("RGB", (W, H), _k(c["parede"], 0.45))
            if c["fora"]: self.sky(img, t, camx)
            d = ImageDraw.Draw(img); zf, zn = 40.0, 0.55
            L_, M_ = c["largura"], c["muro"]
            if c["fora"] and self.tema != "mata":                          # silhueta da cidade no horizonte
                r = random.Random(5); x = -20
                while x < W:
                    bw = r.randint(30, 70); bh = r.randint(40, 260)
                    d.rectangle((x, YH - bh, x + bw, YH), fill=_k((36, 46, 70), self.kluz * 1.2)); x += bw + 2
            self._quad(d, [(-M_ * 3, 0, zf), (M_ * 3, 0, zf), (M_ * 3, 0, zn), (-M_ * 3, 0, zn)], c["lado"])     # calçadas/piso
            self._quad(d, [(-L_, 0, zf), (L_, 0, zf), (L_, 0, zn), (-L_, 0, zn)], c["chao"])                      # pista/corredor
            # faixas e juntas que andam
            per = 2.0
            for kk in range(60):
                z0 = per * kk - (s % per) + 0.4
                if z0 < zn or z0 > zf: continue
                if c["fora"] and self.tema == "cidade":
                    self._quad(d, [(-14, 0, z0), (14, 0, z0), (14, 0, z0 + 0.8), (-14, 0, z0 + 0.8)], _k((200, 190, 120), self.kluz))
                else:
                    x0, y0 = _proj(-L_, 0, z0); x1, _ = _proj(L_, 0, z0); d.line((x0, y0, x1, y0), fill=_k(c["chao"], 0.8), width=2)
            # paredes / fachadas dos dois lados (em blocos que andam) e elementos
            blocos = []
            perb = 3.0
            for kk in range(16):
                zb = perb * kk - (s % perb) + 0.3
                blocos.append(zb)
            for zb in sorted(blocos, reverse=True):
                if zb + perb < zn or zb > zf: continue
                idx = int((zb + s) // perb + 1000)
                r = random.Random(idx)
                for lado in (-1, 1):
                    X = lado * M_; altura = r.randint(1500, 3200) if c["fora"] else c["teto"]
                    if self.tema == "mata":
                        cx, cy = _proj(lado * (M_ + r.randint(-200, 200)), 0, max(zb, zn))
                        tw = 60 / max(zb, zn); th = 1400 / max(zb, zn)
                        d.rectangle((cx - tw, cy - th, cx + tw, cy), fill=_k((52, 40, 32), self.kluz))
                        d.ellipse((cx - tw * 6, cy - th * 1.3, cx + tw * 6, cy - th * 0.6), fill=_k((34, 64, 44), self.kluz))
                        continue
                    cor = _k(r.choice([(92, 70, 64), (80, 84, 96), (104, 92, 76), (70, 76, 70)]), self.kluz) if c["fora"] else c["parede"]
                    za, zb2 = max(zb, zn), min(zb + perb * 0.96, zf)
                    self._quad(d, [(X, 0, za), (X, altura, za), (X, altura, zb2), (X, 0, zb2)], cor)
                    # janelas / portas
                    for j in range(3):
                        zj = za + (zb2 - za) * (0.15 + 0.3 * j)
                        if c["fora"]:
                            for yy in range(500, altura - 200, 360):
                                acesa = r.random() < 0.3 * (1.3 - self.kluz)
                                self._quad(d, [(X, yy, zj), (X, yy + 180, zj), (X, yy + 180, zj + 0.25), (X, yy, zj + 0.25)],
                                           (250, 210, 140) if acesa else _k((30, 36, 52), self.kluz + 0.3))
                        elif r.random() < 0.5:
                            self._quad(d, [(X, 0, zj), (X, 700, zj), (X, 700, zj + 0.35), (X, 0, zj + 0.35)], _k((110, 82, 60), self.kluz + 0.2))
                    if c["fora"] and r.random() < 0.8:                    # poste
                        px, py = _proj(lado * (L_ + 120), 0, za); top = _proj(lado * (L_ + 120), 1500, za)[1]
                        d.line((px, py, px, top), fill=(24, 24, 30), width=max(2, int(16 / za)))
                        d.ellipse((px - 24 / za, top - 10 / za, px + 24 / za, top + 14 / za), fill=(255, 230, 170))
                if c["teto"]:
                    self._quad(d, [(-M_, c["teto"], max(zb, zn)), (M_, c["teto"], max(zb, zn)), (M_, c["teto"], min(zb + perb, zf)),
                                   (-M_, c["teto"], min(zb + perb, zf))], _k(c["parede"], 0.6))
                    self._quad(d, [(-120, c["teto"] - 2, max(zb, zn) + 0.4), (120, c["teto"] - 2, max(zb, zn) + 0.4),
                                   (120, c["teto"] - 2, max(zb, zn) + 1.0), (-120, c["teto"] - 2, max(zb, zn) + 1.0)], (240, 245, 235))
            if self.wet and self.rain_full and self.rain_strength: fx.splashes(img, t, YH + 100, 1880, n=24)
            return img

        def render_front(self, img, t, camx, props, flashes):
            if self.fog_cfg: fx.fog(img, t, **self.fog_cfg)
            if self.rain_full and self.rain_strength: fx.rain(img, t, strength=self.rain_strength)
            if flashes and self.cfg["fora"]: img = fx.lightning(img, t, flashes)
            return img
    return Frente()
