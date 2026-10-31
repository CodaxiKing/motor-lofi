
"""Biblioteca de cenários reutilizáveis em camadas (fundo / meio / frente) com paralaxe, luz e clima.

Cenários: apartamento, entrada, corredor, rua, janela, escada, telhado, ponte, radio
Cada cenário define: camadas, chão (perspectiva), luz dos personagens, tratamento de cor, chuva, relâmpago, névoa.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from .core import W, H, grad, add_light, darken, lerp, ease, font
from . import fx

M = 110                     # margem lateral para paralaxe
S = 2                       # supersampling
CWX = W + 2 * M
def P(x, y): return (int((x + M) * S), int(y * S))
def PS(*pts): return [P(*p) for p in pts]
def canvas(col=(0, 0, 0), alpha=False):
    return Image.new("RGBA" if alpha else "RGB", (CWX * S, H * S), col + ((0,) if alpha else ()))
def down(img):
    return img.resize((CWX, H), Image.LANCZOS)

def skyline(w, h, seed, sky=((28, 44, 78), (20, 30, 52)), far=(30, 42, 66), near=(18, 26, 44), lit=0.36, hmin=0.45, hmax=0.95,
            warm=((255, 214, 140), (255, 196, 110), (240, 230, 190))):
    img = grad(w, h, *sky); d = ImageDraw.Draw(img); r = random.Random(seed)
    x = -20
    while x < w:
        bw = r.randint(40, 90) * S; bh = int(r.uniform(hmin, hmax) * h)
        d.rectangle([x, h - bh, x + bw, h], fill=far)
        if r.random() < 0.25: d.rectangle([x + bw // 2 - 2 * S, h - bh - 40 * S, x + bw // 2 + 2 * S, h - bh], fill=far)
        x += bw + r.randint(4, 14) * S
    x = -10
    while x < w:
        bw = r.randint(55, 110) * S; bh = int(r.uniform(hmin * 0.7, hmax * 0.85) * h); top = h - bh
        d.rectangle([x, top, x + bw, h], fill=near)
        for wy in range(top + 10 * S, h - 6 * S, 16 * S):
            for wx in range(x + 7 * S, x + bw - 9 * S, 13 * S):
                if r.random() < lit: d.rectangle([wx, wy, wx + 6 * S, wy + 8 * S], fill=r.choice(warm))
        x += bw + r.randint(6, 18) * S
    return ImageChops.add(img, img.filter(ImageFilter.GaussianBlur(10 * S)).point(lambda v: int(v * 0.5)))

class Scene:
    name = "base"
    light = "night"; grade = "noite"
    ground = (1300, 1900, 0.6, 1.4)          # y_longe, y_perto, escala_longe, escala_perto
    rain_boxes = []; rain_full = False; rain_strength = 1.0
    lightning_boxes = []; lightning_full = False
    wet = False; fog_cfg = None; amb = "chuva_dentro"
    depths = (0.25, 0.6, 1.25)               # fundo, meio, frente
    def __init__(self):
        self.back, self.mid, self.front = self.build()
    def build(self): raise NotImplementedError
    def scale_at(self, y):
        y0, y1, s0, s1 = self.ground
        return lerp(s0, s1, max(0, min(1, (y - y0) / (y1 - y0))))
    def crop(self, layer, camx, depth):
        off = int(M - camx * depth); off = max(0, min(2 * M, off))
        return layer.crop((off, 0, off + W, H))
    def render_back(self, t, camx, props):
        img = self.crop(self.back, camx, self.depths[0]).convert("RGB")
        for (x0, y0, x1, y1) in self.rain_boxes:
            dx = int(-camx * self.depths[0])
            fx.rain(img, t, (max(0, x0 + dx), y0, min(W, x1 + dx), y1), self.rain_strength, near=False)
        if self.mid is not None:
            m = self.crop(self.mid, camx, self.depths[1]); img.paste(m, (0, 0), m)
        self.dynamic(img, t, camx, props)
        return img
    def render_front(self, img, t, camx, props, flashes):
        if self.fog_cfg: fx.fog(img, t, **self.fog_cfg)
        if self.front is not None:
            f = self.crop(self.front, camx, self.depths[2]); img.paste(f, (0, 0), f)
        if self.rain_full: fx.rain(img, t, strength=self.rain_strength)
        if flashes:
            if self.lightning_full: img = fx.lightning(img, t, flashes)
            for b in self.lightning_boxes:
                dx = int(-camx * self.depths[0]); bb = (max(0, b[0] + dx), b[1], min(W, b[2] + dx), b[3])
                img = fx.lightning(img, t, flashes, box=bb)
        return img
    def dynamic(self, img, t, camx, props): pass

# ======================= APARTAMENTO (sala) =======================
class Apartamento(Scene):
    name = "apartamento"; light = "night"; grade = "noite"
    ground = (1420, 1800, 1.05, 1.5)
    rain_boxes = [(240, 730, 860, 1240)]; lightning_boxes = [(240, 730, 860, 1240)]
    def build(self):
        back = canvas((14, 20, 34))
        win = skyline(620 * S, 510 * S, 4); back.paste(win.filter(ImageFilter.GaussianBlur(1.5 * S)), P(240, 730))
        mid = canvas(alpha=True); d = ImageDraw.Draw(mid)
        # paredes, teto, janela
        wall = (24, 30, 48)
        d.polygon(PS((-M, 0), (W + M, 0), (880, 480), (200, 480)), fill=(26, 32, 50, 255))
        d.polygon(PS((-M, 0), (200, 480), (200, 1300), (-M, 1620)), fill=(18, 24, 38, 255))
        d.polygon(PS((W + M, 0), (880, 480), (880, 1300), (W + M, 1620)), fill=(24, 30, 46, 255))
        for box in [((200, 480), (880, 730)), ((200, 730), (240, 1300)), ((860, 730), (880, 1300)), ((200, 1240), (880, 1300))]:
            d.rectangle(PS(*box), fill=(22, 28, 44, 255))
        # quadro na parede
        d.rectangle(PS((930, 760), (1040, 900)), fill=(40, 44, 60, 255), outline=(14, 16, 24, 255), width=4 * S)
        # chão
        fl = grad(CWX * S, 620 * S, (32, 32, 44), (12, 14, 22)); fd = ImageDraw.Draw(fl)
        for i in range(-14, 16): fd.line([P(540 + i * 40, 0)[0], 0, P(540 + i * 150, 0)[0], 620 * S], fill=(22, 22, 32), width=2 * S)
        fm = Image.new("L", fl.size, 0); ImageDraw.Draw(fm).polygon([P(200, 0), P(880, 0), P(W + M, 300), P(W + M, 620), P(-M, 620), P(-M, 300)], fill=255)
        mid.paste(fl, P(-M, 1300), fm); d = ImageDraw.Draw(mid)
        # moldura da janela + persiana
        for x in (240, 400, 560, 720, 860): d.rectangle(PS((x - 7, 730), (x + 7, 1240)), fill=(12, 16, 26, 255))
        d.rectangle(PS((232, 722), (868, 736)), fill=(12, 16, 26, 255)); d.rectangle(PS((232, 1234), (868, 1250)), fill=(12, 16, 26, 255))
        d.rectangle(PS((240, 1120), (860, 1130)), fill=(14, 18, 30, 255))
        for x in range(250, 860, 26): d.line(PS((x, 1130), (x, 1236)), fill=(14, 18, 30, 255), width=3 * S)
        for k in range(15):
            y = 500 + k * 15; d.rectangle(PS((225, y), (875, y + 10)), fill=(40, 46, 62, 255)); d.line(PS((225, y + 10), (875, y + 10)), fill=(18, 22, 34, 255), width=2 * S)
        # ventilador
        d.line(PS((540, 140), (540, 230)), fill=(10, 12, 18, 255), width=6 * S); d.ellipse(PS((505, 220), (575, 260)), fill=(10, 12, 18, 255))
        # estante
        r = random.Random(2)
        d.rectangle(PS((40, 640), (200, 1380)), fill=(16, 18, 28, 255))
        for y in range(690, 1360, 120):
            d.rectangle(PS((46, y), (194, y + 8)), fill=(26, 26, 36, 255)); bx = 54
            while bx < 186:
                bw = r.randint(10, 20); bh = r.randint(60, 100)
                d.rectangle(PS((bx, y - bh), (bx + bw, y)), fill=r.choice([(44, 40, 56, 255), (54, 44, 44, 255), (36, 46, 58, 255), (60, 56, 44, 255)])); bx += bw + 3
        # TV, abajur, tapete, mesa, sofá
        d.rectangle(PS((-M, 1330), (200, 1440)), fill=(16, 16, 24, 255))
        d.polygon(PS((10, 1040), (170, 1060), (170, 1300), (10, 1320)), fill=(8, 10, 14, 255))
        d.polygon(PS((22, 1056), (160, 1072), (160, 1288), (22, 1306)), fill=(26, 34, 52, 255))
        d.line(PS((300, 1080), (300, 1460)), fill=(30, 28, 26, 255), width=5 * S); d.ellipse(PS((260, 1450), (340, 1474)), fill=(30, 28, 26, 255))
        d.polygon(PS((255, 1080), (345, 1080), (325, 990), (275, 990)), fill=(255, 205, 130, 255))
        d.polygon(PS((230, 1520), (900, 1520), (1040, 1760), (130, 1760)), fill=(74, 30, 34, 255))
        d.polygon(PS((250, 1534), (884, 1534), (1010, 1746), (160, 1746)), outline=(96, 44, 46, 255), width=4 * S)
        d.rectangle(PS((380, 1410), (680, 1470)), fill=(34, 28, 26, 255))
        d.rectangle(PS((395, 1470), (410, 1590)), fill=(24, 20, 20, 255)); d.rectangle(PS((650, 1470), (665, 1590)), fill=(24, 20, 20, 255))
        d.rounded_rectangle(PS((440, 1372), (470, 1412)), 4 * S, fill=(200, 196, 186, 255))
        d.rounded_rectangle(PS((760, 1240), (W + M, 1420)), 30 * S, fill=(30, 38, 56, 255))
        d.rounded_rectangle(PS((730, 1380), (W + M, 1560)), 26 * S, fill=(36, 46, 66, 255))
        d.rounded_rectangle(PS((720, 1330), (800, 1560)), 24 * S, fill=(40, 50, 72, 255))
        mid = add_light(mid, PS((140, 860), (460, 1260)), (190, 130, 50), 80 * S, 220)
        mid = add_light(mid, PS((200, 1500), (900, 1800)), (40, 60, 110), 40 * S, 60)
        # frente: planta desfocada no canto
        front = canvas(alpha=True); fd = ImageDraw.Draw(front)
        for k in range(7):
            a = -0.9 + k * 0.3; x0, y0 = P(W + 95, 1980)
            fd.ellipse([x0 + int(math.sin(a) * 260 * S) - 70 * S, y0 - int(math.cos(a) * 360 * S) - 30 * S,
                        x0 + int(math.sin(a) * 260 * S) + 70 * S, y0 - int(math.cos(a) * 360 * S) + 30 * S], fill=(12, 20, 18, 255))
        fd.rectangle(PS((W - 40, 1760), (W + 90, 1920)), fill=(40, 26, 22, 255))
        front = front.filter(ImageFilter.GaussianBlur(9 * S))
        return down(back), down(mid), down(front)
    def dynamic(self, img, t, camx, props):
        if props.get("tv"):
            dx = int(-camx * self.depths[1])
            flick = 0.75 + 0.25 * math.sin(t * 17) * math.sin(t * 5.3)
            d = ImageDraw.Draw(img)
            d.polygon([(22 + dx, 1056), (160 + dx, 1072), (160 + dx, 1288), (22 + dx, 1306)], fill=(int(110 * flick), int(170 * flick), 255))
            img.paste(add_light(img, (-200 + dx, 900, 520 + dx, 1750), (40, 90, 200), 110, int(150 * flick)))

# ======================= ENTRADA (porta do apê) =======================
class Entrada(Scene):
    name = "entrada"; light = "night"; grade = "noite"
    ground = (1500, 1900, 1.0, 1.5)
    def build(self):
        back = canvas((20, 26, 40)); d = ImageDraw.Draw(back)
        d.rectangle(PS((-M, 0), (W + M, 1500)), fill=(30, 38, 56))
        d.rectangle(PS((-M, 1500), (W + M, 1920)), fill=(26, 26, 36))
        for i in range(-12, 14): d.line(PS((540 + i * 40, 1500), (540 + i * 140, 1920)), fill=(20, 20, 28), width=2 * S)
        d.rectangle(PS((-M, 1490), (W + M, 1504)), fill=(40, 40, 54))
        d.rectangle(PS((470, 560), (930, 1510)), fill=(16, 18, 26))     # moldura
        d.line(PS((180, 700), (180, 1500)), fill=(40, 30, 26), width=8 * S); d.ellipse(PS((130, 1480), (230, 1510)), fill=(40, 30, 26))
        d.polygon(PS((130, 760), (230, 760), (210, 1000), (150, 1000)), fill=(120, 40, 40))
        d.ellipse(PS((150, 690), (210, 750)), fill=(70, 50, 40))
        d.rectangle(PS((20, 1360), (330, 1500)), fill=(50, 40, 36))
        for k in range(4): d.rounded_rectangle(PS((40 + k * 70, 1330), (95 + k * 70, 1362)), 8 * S, fill=(30 + k * 12, 30, 34))
        back = add_light(back, PS((-500, 400), (400, 1900)), (30, 50, 110), 100 * S, 150)
        return down(back), None, None
    def dynamic(self, img, t, camx, props):
        op = max(0.0, min(1.0, props.get("door", 0.0)))
        dx = int(-camx * self.depths[0])
        d = ImageDraw.Draw(img)
        if op > 0:
            d.rectangle([490 + dx, 580, 910 + dx, 1500], fill=(160, 118, 66))
            img.paste(add_light(img, (360 + dx, 700, 1040 + dx, 1920), (130, 86, 34), 60, int(160 * op)))
            d = ImageDraw.Draw(img)
            d.polygon([(490 + dx, 1500), (910 + dx, 1500), (1040 + dx, 1920), (360 + dx, 1920)], fill=(110, 80, 46))
        dw = int(420 * (1 - op * 0.84))
        dark = props.get("dark", False); k = 0.55 if dark else 1.0
        c = lambda v: tuple(int(x * k) for x in v)
        d.rectangle([490 + dx, 580, 490 + dx + dw, 1500], fill=c((92, 58, 40)), outline=c((40, 26, 18)), width=6)
        if dw > 200:
            d.rectangle([530 + dx, 640, 490 + dx + dw - 40, 960], outline=c((70, 44, 30)), width=5)
            d.rectangle([530 + dx, 1020, 490 + dx + dw - 40, 1440], outline=c((70, 44, 30)), width=5)
            d.ellipse([690 + dx, 760, 712 + dx, 782], fill=(8, 8, 10))
            d.ellipse([840 + dx, 1060, 880 + dx, 1100], fill=c((200, 176, 110)))
            locks = props.get("locks", 0)
            for i, ly in enumerate([900, 1000]):
                on = locks > i
                d.rectangle([860 + dx, ly, 900 + dx, ly + 20], fill=(160, 160, 165))
                d.rectangle([(900 if on else 880) + dx, ly + 4, (950 if on else 920) + dx, ly + 16], fill=(210, 210, 215))
        if props.get("under_door_light"):
            d.rectangle([500 + dx, 1494, 900 + dx, 1506], fill=(230, 200, 140))
            if props.get("feet"):
                d.rectangle([600 + dx, 1494, 660 + dx, 1506], fill=(16, 12, 10)); d.rectangle([720 + dx, 1494, 780 + dx, 1506], fill=(16, 12, 10))
        if dark: img.paste(Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.35))

# ======================= CORREDOR =======================
class Corredor(Scene):
    name = "corredor"; light = "warm"; grade = "quente"
    ground = (1080, 1900, 0.3, 1.5)
    amb = "zumbido"
    def build(self):
        back = canvas((0, 0, 0)); d = ImageDraw.Draw(back)
        vpx = 540
        d.rectangle(PS((-M, 0), (W + M, 1920)), fill=(70, 58, 46))
        d.polygon(PS((-M, 1920), (W + M, 1920), (640, 1080), (440, 1080)), fill=(46, 36, 32))
        d.polygon(PS((200, 1920), (880, 1920), (590, 1080), (490, 1080)), fill=(110, 38, 40))
        d.polygon(PS((-M, 0), (W + M, 0), (640, 700), (440, 700)), fill=(80, 72, 62))
        d.polygon(PS((-M, 0), (440, 700), (440, 1080), (-M, 1920 + 100)), fill=(92, 76, 58))
        d.polygon(PS((W + M, 0), (640, 700), (640, 1080), (W + M, 1920 + 100)), fill=(84, 68, 54))
        d.rectangle(PS((440, 700), (640, 1080)), fill=(52, 44, 38)); d.rectangle(PS((500, 860), (580, 1080)), fill=(36, 28, 24))
        for (xa, xb, ya, yb, yc, yd) in [(-40, 220, 430, 590, 1500, 1800), (300, 400, 640, 700, 1180, 1280)]:
            d.polygon(PS((xa, ya), (xb, yb), (xb, yc), (xa, yd)), fill=(96, 60, 40))
            d.polygon(PS((1080 - xa, ya), (1080 - xb, yb), (1080 - xb, yc), (1080 - xa, yd)), fill=(90, 56, 38))
        d.text(P(80, 700), "903", font=font("mono", 40 * S), fill=(200, 180, 130))
        for (x, y) in [(540, 300), (540, 640)]: d.rectangle(PS((x - 60, y), (x + 60, y + 16)), fill=(250, 236, 200))
        back = add_light(back, PS((240, 260), (840, 1500)), (110, 80, 40), 60 * S, 120)
        return down(back), None, None
    def dynamic(self, img, t, camx, props):
        k = int(t * 12); on = random.Random(k * 31 + 7).random() > props.get("flicker", 0.13)
        if not on: img.paste(Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.62))
        props["_lamp_on"] = on

# ======================= RUA =======================
class Rua(Scene):
    name = "rua"; light = "night"; grade = "noite"
    ground = (1250, 1900, 0.35, 1.6)
    rain_full = True; wet = True; amb = "chuva_fora"
    lightning_full = True
    fog_cfg = dict(y=1240, height=520, alpha=0.55, col=(90, 60, 80), speed=14)
    def build(self):
        back = canvas()
        city = skyline(CWX * S, 1250 * S, 77, sky=((10, 14, 30), (60, 26, 34)), hmin=0.35, hmax=0.9, lit=0.3)
        back.paste(city.filter(ImageFilter.GaussianBlur(2 * S)), (0, 0))
        back = add_light(back, PS((-300, 900), (1380, 1500)), (130, 30, 26), 140 * S, 170)
        d = ImageDraw.Draw(back)
        d.ellipse(PS((760, 420), (880, 540)), fill=(215, 210, 195)); d.ellipse(PS((738, 408), (858, 528)), fill=(18, 18, 32))
        mid = canvas(alpha=True); d = ImageDraw.Draw(mid)
        road = grad(CWX * S, 670 * S, (34, 34, 44), (14, 14, 20)); mid.paste(road, P(-M, 1250))
        d.rectangle(PS((-M, 1250), (W + M, 1275)), fill=(60, 60, 70, 255))
        for i in range(7):
            y = 1330 + i * 95; w = 10 + i * 6
            d.polygon(PS((540 - w, y), (540 + w, y), (540 + w + 6, y + 48 + i * 8), (540 - w - 6, y + 48 + i * 8)), fill=(150, 138, 80, 255))
        refl = city.crop((0, city.height - 480 * S, city.width, city.height)).transpose(Image.FLIP_TOP_BOTTOM).resize((city.width, 520 * S))
        refl = refl.filter(ImageFilter.GaussianBlur(6 * S)); rm = Image.new("L", refl.size, 70)
        mid.paste(refl, P(-M, 1275), rm)
        # postes
        for x in (90, 990):
            d.rectangle(PS((x - 6, 760), (x + 6, 1262)), fill=(18, 18, 24, 255)); d.rectangle(PS((min(x - 4, x + 70 * (1 if x < 500 else -1)), 760), (max(x - 4, x + 70 * (1 if x < 500 else -1)), 770)), fill=(18, 18, 24, 255))
        mid = add_light(mid, PS((60, 740), (260, 1300)), (200, 170, 100), 50 * S, 120)
        mid = add_light(mid, PS((820, 740), (1020, 1300)), (200, 170, 100), 50 * S, 120)
        # carro
        car = Image.new("RGBA", (360 * S, 200 * S), (0, 0, 0, 0)); cd = ImageDraw.Draw(car)
        cd.rounded_rectangle([10 * S, 70 * S, 350 * S, 170 * S], 30 * S, fill=(110, 40, 36, 255), outline=(20, 18, 22, 255), width=5 * S)
        cd.rounded_rectangle([80 * S, 20 * S, 270 * S, 90 * S], 26 * S, fill=(96, 34, 30, 255), outline=(20, 18, 22, 255), width=5 * S)
        cd.rectangle([100 * S, 34 * S, 170 * S, 80 * S], fill=(26, 30, 42, 255)); cd.rectangle([186 * S, 34 * S, 252 * S, 80 * S], fill=(26, 30, 42, 255))
        cd.ellipse([50 * S, 140 * S, 120 * S, 200 * S], fill=(14, 14, 16, 255)); cd.ellipse([240 * S, 140 * S, 310 * S, 200 * S], fill=(14, 14, 16, 255))
        cd.ellipse([320 * S, 100 * S, 348 * S, 124 * S], fill=(255, 236, 180, 255))
        car = car.rotate(7, expand=True, resample=Image.BICUBIC); mid.paste(car, P(-90, 1215), car)
        mid = add_light(mid, PS((220, 1240), (760, 1420)), (190, 160, 90), 40 * S, 110)
        front = canvas(alpha=True); fd = ImageDraw.Draw(front)
        fd.rectangle(PS((-M, 1820), (W + M, 1920)), fill=(10, 10, 14, 255))
        fd.polygon(PS((W - 120, 1920), (W + M, 1600), (W + M, 1920)), fill=(12, 12, 16, 255))
        front = front.filter(ImageFilter.GaussianBlur(6 * S))
        return down(back), down(mid), down(front)
    def dynamic(self, img, t, camx, props):
        fx.splashes(img, t, 1300, 1880, n=30)

# ======================= JANELA (vista de cima da rua) =======================
class Janela(Scene):
    name = "janela"; light = "dawn"; grade = "amanhecer"
    ground = (760, 1700, 0.18, 0.32)
    rain_full = True; rain_strength = 0.55; amb = "chuva_fora"
    def build(self):
        back = canvas()
        bld = skyline(CWX * S, 700 * S, 9, sky=((120, 132, 150), (140, 146, 158)), far=(70, 78, 92), near=(56, 62, 76), lit=0.06, hmin=0.5, hmax=1.0)
        back.paste(bld, (0, 0)); d = ImageDraw.Draw(back)
        d.rectangle(PS((-M, 700), (W + M, 1920)), fill=(66, 68, 76))
        d.rectangle(PS((-M, 700), (W + M, 760)), fill=(90, 92, 100)); d.rectangle(PS((-M, 1700), (W + M, 1760)), fill=(90, 92, 100))
        for i in range(8): d.rectangle(PS((20 + i * 150, 1220), (100 + i * 150, 1236)), fill=(170, 164, 120))
        for (cx, cy, ang, col) in [(240, 980, 12, (140, 60, 50)), (760, 1080, -20, (80, 100, 130)), (500, 1450, 5, (170, 160, 140)), (880, 1560, 30, (60, 70, 60))]:
            car = Image.new("RGBA", (260 * S, 140 * S), (0, 0, 0, 0)); cd = ImageDraw.Draw(car)
            cd.rounded_rectangle([10 * S, 20 * S, 250 * S, 120 * S], 30 * S, fill=col + (255,), outline=(30, 30, 36, 255), width=4 * S)
            cd.rounded_rectangle([70 * S, 40 * S, 190 * S, 100 * S], 16 * S, fill=(40, 46, 58, 255))
            car = car.rotate(ang, expand=True, resample=Image.BICUBIC); p = P(cx, cy); back.paste(car, (p[0] - car.width // 2, p[1] - car.height // 2), car)
        front = canvas(alpha=True); fd = ImageDraw.Draw(front)
        fr = (24, 28, 38, 255)
        fd.rectangle(PS((-M, 0), (W + M, 170)), fill=fr); fd.rectangle(PS((-M, 1640), (W + M, 1920)), fill=fr)
        fd.rectangle(PS((-M, 0), (60, 1920)), fill=fr); fd.rectangle(PS((W - 60, 0), (W + M, 1920)), fill=fr)
        fd.rectangle(PS((531, 170), (549, 1640)), fill=fr)
        return down(back), None, down(front)

# ======================= ESCADA =======================
class Escada(Scene):
    name = "escada"; light = "red"; grade = "emergencia"
    ground = (700, 1800, 0.55, 1.3)
    amb = "eco"
    def build(self):
        back = canvas((36, 30, 34)); d = ImageDraw.Draw(back)
        for k in range(4):
            y0 = 500 + k * 360; left = k % 2 == 0
            xs = (120, 960) if left else (960, 120)
            for s_ in range(9):
                t_ = s_ / 9; x = lerp(xs[0], xs[1], t_); y = y0 + t_ * 300; w = 90 if left else -90
                d.rectangle(PS((min(x, x + w), y), (max(x, x + w), y + 34)), fill=(64, 56, 58))
                d.line(PS((x, y), (x + w, y)), fill=(90, 80, 82), width=3 * S)
            d.line(PS((xs[0], y0 - 120), (xs[1], y0 + 180)), fill=(20, 18, 20), width=8 * S)
            for s_ in range(0, 10, 2):
                x = lerp(xs[0], xs[1], s_ / 9); y = y0 - 120 + s_ / 9 * 300
                d.line(PS((x, y), (x, y + 120)), fill=(20, 18, 20), width=4 * S)
        d.rectangle(PS((800, 380), (1000, 550)), fill=(44, 38, 42)); d.text(P(845, 360), "9", font=font("title", 160 * S), fill=(150, 140, 120))
        return down(back), None, None
    def dynamic(self, img, t, camx, props):
        on = int(t * 2.2) % 2 == 0
        dx = int(-camx * self.depths[0])
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([780 + dx, 250, 960 + dx, 320], 10, fill=(255, 60, 50) if on else (60, 20, 18))
        if on: img.paste(add_light(img, (600 + dx, 100, 1140 + dx, 950), (170, 20, 16), 120, 170))
        else: img.paste(Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.45))
        props["_light_on"] = on

# ======================= TELHADO =======================
class Telhado(Scene):
    name = "telhado"; light = "night"; grade = "frio"
    ground = (1060, 1900, 0.65, 1.6)
    rain_full = True; lightning_full = True; wet = True; amb = "chuva_fora"
    fog_cfg = dict(y=1000, height=500, alpha=0.35, col=(60, 70, 100), speed=22)
    def build(self):
        back = canvas()
        city = skyline(CWX * S, 1100 * S, 31, sky=((14, 20, 38), (30, 40, 70)), hmin=0.25, hmax=0.75)
        back.paste(city.filter(ImageFilter.GaussianBlur(2.5 * S)), (0, 0))
        mid = canvas(alpha=True); d = ImageDraw.Draw(mid)
        d.polygon(PS((660, 1180), (W + M, 1150), (W + M, 1920), (660, 1920)), fill=(30, 34, 48, 255))
        d.rectangle(PS((660, 1170), (W + M, 1200)), fill=(46, 50, 64, 255))
        d.polygon(PS((-M, 1050), (540, 1080), (540, 1920), (-M, 1920)), fill=(42, 46, 60, 255))
        d.rectangle(PS((-M, 1040), (550, 1080)), fill=(60, 64, 80, 255))
        d.rectangle(PS((40, 800), (240, 1050)), fill=(54, 58, 72, 255)); d.ellipse(PS((40, 760), (240, 840)), fill=(64, 68, 84, 255))
        d.line(PS((420, 1040), (420, 640)), fill=(20, 22, 30, 255), width=5 * S); d.line(PS((380, 700), (460, 700)), fill=(20, 22, 30, 255), width=4 * S)
        d.rectangle(PS((540, 1080), (660, 1920)), fill=(6, 8, 14, 255))
        # poças
        for (x, y, w) in [(160, 1500, 140), (380, 1700, 110), (860, 1600, 120)]:
            d.ellipse(PS((x - w, y - 18), (x + w, y + 18)), fill=(70, 84, 120, 255))
        front = canvas(alpha=True); fd = ImageDraw.Draw(front)
        fd.rectangle(PS((-M, 1840), (W + M, 1920)), fill=(16, 18, 26, 255))
        fd.line(PS((-M, 1780), (W + M, 1760)), fill=(30, 32, 44, 255), width=14 * S)
        front = front.filter(ImageFilter.GaussianBlur(5 * S))
        return down(back), down(mid), down(front)

# ======================= PONTE =======================
class Ponte(Scene):
    name = "ponte"; light = "dawn"; grade = "amanhecer"
    ground = (1200, 1900, 0.4, 1.5)
    rain_full = True; rain_strength = 0.5; wet = True; amb = "vento"
    fog_cfg = dict(y=1180, height=600, alpha=0.6, col=(150, 140, 150), speed=12)
    def build(self):
        back = canvas()
        sky = grad(CWX * S, 1100 * S, (70, 70, 100), (220, 150, 120)); back.paste(sky, (0, 0))
        d = ImageDraw.Draw(back)
        d.ellipse(PS((480, 900), (640, 1060)), fill=(255, 200, 150))
        back = add_light(back, PS((200, 700), (900, 1300)), (180, 100, 60), 120 * S, 120)
        river = grad(CWX * S, 820 * S, (150, 110, 110), (40, 40, 60)); back.paste(river, P(-M, 1100))
        mid = canvas(alpha=True); d = ImageDraw.Draw(mid)
        # tabuleiro da ponte em perspectiva
        d.polygon(PS((440, 1150), (640, 1150), (W + M, 1920), (-M, 1920)), fill=(60, 60, 70, 255))
        for i in range(12):
            y = 1160 + i ** 1.6 * 9
            d.line(PS((540 - 6, y), (540 + 6, y)), fill=(200, 190, 140, 255), width=3 * S)
        # treliças
        for side in (-1, 1):
            base_x = 540 + side * 120
            for k in range(8):
                f = k / 7; x = lerp(base_x, 540 + side * 760, f ** 1.4); top = lerp(1060, 300, f ** 1.2); bot = lerp(1150, 1920, f ** 1.4)
                d.line(PS((x, top), (x, bot)), fill=(40, 36, 46, 255), width=int(lerp(3, 26, f) * S))
                if k:
                    d.line(PS((px, ptop), (x, bot)), fill=(40, 36, 46, 255), width=int(lerp(2, 14, f) * S))
                px, ptop = x, top
            d.line(PS((base_x, 1060), (540 + side * 760, 300)), fill=(40, 36, 46, 255), width=10 * S)
        # barreira militar no fundo
        d.rectangle(PS((450, 1120), (630, 1150)), fill=(200, 60, 40, 255))
        for k in range(6): d.rectangle(PS((450 + k * 32, 1120), (466 + k * 32, 1150)), fill=(240, 240, 230, 255))
        mid = add_light(mid, PS((420, 1040), (660, 1200)), (255, 240, 200), 30 * S, 140)
        return down(back), down(mid), None

# ======================= RÁDIO (close) =======================
class Radio(Scene):
    name = "radio"; light = "warm"; grade = "quente"
    ground = (1500, 1900, 1.0, 1.0)
    rain_boxes = [(140, 300, 940, 1000)]; lightning_boxes = [(140, 300, 940, 1000)]
    def build(self):
        back = canvas((20, 24, 36))
        win = skyline(800 * S, 700 * S, 21); back.paste(win.filter(ImageFilter.GaussianBlur(3 * S)), P(140, 300))
        mid = canvas(alpha=True); d = ImageDraw.Draw(mid)
        d.rectangle(PS((-M, 0), (W + M, 300)), fill=(20, 24, 36, 255)); d.rectangle(PS((-M, 0), (140, 1250)), fill=(20, 24, 36, 255))
        d.rectangle(PS((940, 0), (W + M, 1250)), fill=(20, 24, 36, 255)); d.rectangle(PS((-M, 1000), (W + M, 1250)), fill=(20, 24, 36, 255))
        d.rectangle(PS((130, 290), (950, 1010)), outline=(12, 14, 22, 255), width=14 * S); d.line(PS((540, 300), (540, 1000)), fill=(12, 14, 22, 255), width=12 * S)
        d.rectangle(PS((-M, 1250), (W + M, 1920)), fill=(60, 44, 36, 255)); d.rectangle(PS((-M, 1250), (W + M, 1280)), fill=(80, 60, 48, 255))
        mid = add_light(mid, PS((-100, 900), (500, 1500)), (170, 110, 40), 80 * S, 160)
        return down(back), down(mid), None
    def dynamic(self, img, t, camx, props):
        on = props.get("on", True); lvl = props.get("level", 0.0)
        d = ImageDraw.Draw(img)
        if on: img.paste(add_light(img, (200, 900, 900, 1500), (255, 190, 110), 70, int(60 + 120 * lvl))); d = ImageDraw.Draw(img)
        d.line([(760, 1010), (900, 700)], fill=(170, 170, 175), width=7)
        d.rounded_rectangle([200, 1000, 880, 1380], 36, fill=(120, 80, 54), outline=(40, 26, 18), width=8)
        d.rounded_rectangle([248, 1050, 560, 1330], 18, fill=(70, 50, 36))
        for gy in range(1068, 1320, 24): d.line([(266, gy), (542, gy)], fill=(50, 36, 26), width=8)
        d.rounded_rectangle([600, 1060, 840, 1130], 10, fill=(240, 220, 170) if on else (110, 100, 80))
        for k in range(9): d.line([(615 + k * 26, 1068), (615 + k * 26, 1090 if k % 2 else 1104)], fill=(80, 70, 50), width=3)
        ang = 30 + 25 * math.sin(t * 2)
        kx, ky = 720, 1250
        d.ellipse([kx - 56, ky - 56, kx + 56, ky + 56], fill=(60, 40, 30), outline=(30, 20, 14), width=5)
        d.line([(kx, ky), (kx + 46 * math.cos(math.radians(ang)), ky + 46 * math.sin(math.radians(ang)))], fill=(230, 220, 190), width=7)
        d.ellipse([815, 1335, 845, 1365], fill=(255, 70, 50) if on else (70, 30, 26))
        sleeve = props.get("sleeve", (210, 212, 220))
        if props.get("hand", True):
            d.line([(1120, 1640), (kx + 60, ky + 50)], fill=(22, 24, 34), width=104)
            d.line([(1120, 1640), (kx + 60, ky + 50)], fill=sleeve, width=92)
            d.ellipse([kx + 26, ky + 16, kx + 94, ky + 84], fill=(220, 220, 214), outline=(22, 24, 34), width=5)
        if on and lvl > 0.02:
            for k in range(12):
                h = 30 + lvl * 700 * (0.5 + 0.5 * math.sin(t * 25 + k * 1.3)); x = 230 + k * 52
                d.rounded_rectangle([x, 880 - h / 2, x + 28, 880 + h / 2], 12, fill=(255, 226, 120))


# ======================= HOSPITAL (corredor) =======================
class Hospital(Scene):
    name = "hospital"; light = "dawn"; grade = "frio"
    ground = (1100, 1900, 0.4, 1.5)
    amb = "zumbido"
    def build(self):
        back = canvas((0, 0, 0)); d = ImageDraw.Draw(back)
        d.rectangle(PS((-M, 0), (W + M, 1920)), fill=(150, 170, 165))
        d.polygon(PS((-M, 1920), (W + M, 1920), (640, 1100), (440, 1100)), fill=(120, 132, 130))
        for i in range(-10, 12):   # piso de ladrilho
            d.line(PS((540 + i * 12, 1100), (540 + i * 150, 1920)), fill=(104, 116, 114), width=2 * S)
        for k in range(10):
            y = 1100 + (k / 10) ** 1.7 * 820; d.line(PS((-M, y), (W + M, y)), fill=(104, 116, 114), width=2 * S)
        d.polygon(PS((-M, 0), (W + M, 0), (640, 720), (440, 720)), fill=(200, 210, 206))
        d.polygon(PS((-M, 0), (440, 720), (440, 1100), (-M, 2000)), fill=(170, 190, 184))
        d.polygon(PS((W + M, 0), (640, 720), (640, 1100), (W + M, 2000)), fill=(160, 180, 176))
        d.rectangle(PS((440, 720), (640, 1100)), fill=(120, 140, 136))
        d.rectangle(PS((490, 880), (590, 1100)), fill=(80, 100, 100)); d.line(PS((540, 880), (540, 1100)), fill=(60, 80, 80), width=3 * S)
        # faixa verde nas paredes
        d.polygon(PS((-M, 1500), (440, 960), (440, 1000), (-M, 1600)), fill=(70, 140, 120))
        d.polygon(PS((W + M, 1500), (640, 960), (640, 1000), (W + M, 1600)), fill=(70, 140, 120))
        # portas e placas
        for (xa, xb, ya, yb, yc, yd) in [(-60, 200, 420, 580, 1560, 1840), (300, 400, 640, 700, 1180, 1280)]:
            d.polygon(PS((xa, ya), (xb, yb), (xb, yc), (xa, yd)), fill=(110, 150, 160))
            d.polygon(PS((1080 - xa, ya), (1080 - xb, yb), (1080 - xb, yc), (1080 - xa, yd)), fill=(104, 144, 154))
        d.rectangle(PS((470, 760), (610, 810)), fill=(40, 140, 80)); d.text(P(488, 762), "SAÍDA", font=font("title", 36 * S), fill=(230, 255, 230))
        # maca
        d.rectangle(PS((700, 1300), (960, 1340)), fill=(220, 225, 228)); d.rectangle(PS((700, 1340), (960, 1356)), fill=(150, 160, 165))
        for x in (720, 940): d.line(PS((x, 1356), (x, 1440)), fill=(120, 126, 130), width=4 * S)
        d.polygon(PS((700, 1300), (760, 1270), (960, 1270), (960, 1300)), fill=(235, 238, 240))
        for (x, y) in [(540, 260), (540, 560)]: d.rectangle(PS((x - 90, y), (x + 90, y + 14)), fill=(240, 250, 255))
        back = add_light(back, PS((240, 200), (840, 1400)), (40, 60, 60), 80 * S, 90)
        return down(back), None, None
    def dynamic(self, img, t, camx, props):
        k = int(t * 10); on = random.Random(k * 13 + 1).random() > props.get("flicker", 0.08)
        if not on: img.paste(Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.55))
        props["_lamp_on"] = on

# ======================= MERCADO =======================
class Mercado(Scene):
    name = "mercado"; light = "dark"; grade = "frio"
    ground = (1150, 1900, 0.45, 1.5)
    amb = "zumbido"
    def build(self):
        back = canvas((30, 34, 40)); d = ImageDraw.Draw(back); r = random.Random(6)
        d.rectangle(PS((-M, 0), (W + M, 1150)), fill=(36, 40, 46))
        d.polygon(PS((-M, 1920), (W + M, 1920), (620, 1150), (460, 1150)), fill=(70, 74, 78))
        for k in range(12):
            y = 1150 + (k / 12) ** 1.7 * 770; d.line(PS((-M, y), (W + M, y)), fill=(60, 62, 66), width=2 * S)
        # prateleiras em perspectiva dos dois lados
        for side in (-1, 1):
            for k in range(6):
                f0, f1 = k / 6, (k + 1) / 6
                xa = lerp(540 + side * 90, 540 + side * 760, f0 ** 1.5); xb = lerp(540 + side * 90, 540 + side * 760, f1 ** 1.5)
                ta, tb = lerp(900, 200, f0 ** 1.3), lerp(900, 200, f1 ** 1.3); ba, bb = lerp(1150, 1920, f0 ** 1.5), lerp(1150, 1920, f1 ** 1.5)
                d.polygon(PS((xa, ta), (xb, tb), (xb, bb), (xa, ba)), fill=(56, 60, 70))
                for j in range(5):
                    yy_a = lerp(ta, ba, (j + 0.5) / 5); yy_b = lerp(tb, bb, (j + 0.5) / 5)
                    d.line(PS((xa, yy_a), (xb, yy_b)), fill=(90, 94, 104), width=max(2, int(lerp(2, 8, f1))) * S)
                    for q in range(4):
                        u = (q + r.random() * 0.5) / 4; x = lerp(xa, xb, u); y = lerp(yy_a, yy_b, u)
                        h = lerp(10, 60, f0); c = r.choice([(200, 60, 50), (230, 190, 60), (60, 140, 200), (90, 170, 90), (230, 230, 230)])
                        if r.random() < 0.75: d.rectangle(PS((min(x, x + side * h * 0.7), y - h), (max(x, x + side * h * 0.7), y)), fill=c)
        # luminárias
        for k in range(4):
            y = 160 + k * 170; w = 300 - k * 60
            d.rectangle(PS((540 - w / 2, y), (540 + w / 2, y + 14)), fill=(230, 240, 250))
        # placa
        d.rectangle(PS((430, 820), (650, 880)), fill=(200, 40, 40)); d.text(P(452, 820), "OFERTAS", font=font("title", 44 * S), fill=(255, 240, 220))
        # produtos caídos
        for _ in range(14):
            x, y = r.uniform(200, 900), r.uniform(1300, 1850); c = r.choice([(200, 60, 50), (230, 190, 60), (60, 140, 200)])
            d.ellipse(PS((x - 14, y - 8), (x + 14, y + 8)), fill=c)
        back = add_light(back, PS((300, 100), (780, 1200)), (60, 70, 80), 80 * S, 100)
        return down(back), None, None
    def dynamic(self, img, t, camx, props):
        k = int(t * 9); on = random.Random(k * 17 + 2).random() > props.get("flicker", 0.18)
        if not on: img.paste(Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.6))
        props["_lamp_on"] = on

# ======================= METRÔ =======================
class Metro(Scene):
    name = "metro"; light = "dark"; grade = "frio"
    ground = (1250, 1900, 0.5, 1.5)
    amb = "eco"
    def build(self):
        back = canvas((14, 16, 22)); d = ImageDraw.Draw(back)
        # túnel ao fundo
        d.rectangle(PS((-M, 0), (W + M, 1250)), fill=(36, 40, 50))
        d.ellipse(PS((-200, 300), (1280, 1700)), fill=(10, 12, 16))
        d.ellipse(PS((60, 560), (1020, 1460)), fill=(4, 4, 8))
        for k in range(8):   # anéis do túnel
            f = k / 8; w = lerp(620, 120, f)
            d.ellipse(PS((540 - w, 1010 - w * 0.95), (540 + w, 1010 + w * 0.95)), outline=(26, 28, 36), width=int(lerp(10, 2, f) * S))
        # trilhos
        d.polygon(PS((380, 1920), (700, 1920), (560, 1100), (520, 1100)), fill=(30, 26, 24))
        d.line(PS((430, 1920), (530, 1100)), fill=(120, 120, 130), width=6 * S); d.line(PS((650, 1920), (550, 1100)), fill=(120, 120, 130), width=6 * S)
        for k in range(14):
            y = 1100 + (k / 14) ** 1.8 * 820; w = lerp(30, 180, (y - 1100) / 820)
            d.line(PS((540 - w, y), (540 + w, y)), fill=(50, 40, 34), width=max(2, int(lerp(2, 10, (y - 1100) / 820))) * S)
        # plataforma (direita) com faixa amarela
        d.polygon(PS((700, 1920), (W + M, 1920), (W + M, 1250), (580, 1150)), fill=(70, 70, 76))
        d.polygon(PS((700, 1920), (760, 1920), (600, 1150), (580, 1150)), fill=(220, 190, 40))
        # placa
        d.rectangle(PS((760, 520), (1060, 600)), fill=(30, 70, 140)); d.text(P(782, 524), "ESTAÇÃO SÉ", font=font("title", 50 * S), fill=(240, 240, 250))
        for (x, y) in [(860, 300), (1000, 420)]: d.rectangle(PS((x - 80, y), (x + 80, y + 12)), fill=(220, 230, 240))
        back = add_light(back, PS((700, 200), (1300, 1200)), (40, 50, 70), 80 * S, 110)
        return down(back), None, None
    def dynamic(self, img, t, camx, props):
        tr = props.get("train", 0.0)       # 0..1: farol do trem chegando no túnel
        if tr > 0:
            r_ = 30 + 300 * tr
            img.paste(add_light(img, (540 - r_, 1010 - r_, 540 + r_, 1010 + r_), (255, 240, 200), 40 + 60 * tr, int(80 + 170 * tr)))

REGISTRY = {c.name: c for c in (Apartamento, Entrada, Corredor, Rua, Janela, Escada, Telhado, Ponte, Radio, Hospital, Mercado, Metro)}
_inst = {}
def get(name):
    if name not in _inst: _inst[name] = REGISTRY[name]()
    return _inst[name]
