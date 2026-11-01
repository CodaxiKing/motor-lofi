"""Cenários de passagem: ligam os lugares para a história não pular (portão do prédio, beco, viaduto,
estacionamento e o vagão por dentro). Mesmo padrão de lofi/scenes.py (camadas fundo/meio/frente, chão em perspectiva)."""
import random
from PIL import ImageDraw, ImageFilter
from .scenes import Scene, canvas, P, PS, down, skyline, S, M, W, CWX
from .core import grad, add_light, font


class Portao(Scene):
    """Frente do prédio vista da calçada: portão de grade, interfone, degraus. Liga o prédio (escada/corredor) à rua."""
    name = "portao"; light = "night"; grade = "noite"; acoustic = "aberto"
    clouds = (60, 360, (60, 50, 70))
    ground = (1380, 1900, 0.8, 1.55)
    rain_full = True; wet = True; amb = "chuva_fora"; lightning_full = True
    ripples = [(200, 1700, 120), (860, 1820, 140)]
    def build(self):
        back = canvas(); back.paste(grad(CWX * S, 700 * S, (12, 16, 32), (40, 26, 40)), (0, 0))
        mid = canvas(alpha=True); d = ImageDraw.Draw(mid)
        d.rectangle(PS((-M, 160), (W + M, 1380)), fill=(70, 58, 56, 255))                    # fachada
        for y in range(240, 1100, 190):
            for x in (60, 300, 780, 1000):
                d.rectangle(PS((x - 70, y), (x + 70, y + 120)), fill=(238, 200, 130, 255) if (x + y) % 3 == 0 else (28, 32, 46, 255))
                d.rectangle(PS((x - 78, y + 120), (x + 78, y + 132)), fill=(50, 42, 40, 255))
        d.rectangle(PS((330, 860), (750, 1380)), fill=(36, 30, 30, 255))                       # vão da entrada
        d.rectangle(PS((360, 900), (720, 1380)), fill=(150, 130, 90, 255))                     # hall iluminado
        d.rectangle(PS((360, 1290), (720, 1380)), fill=(110, 96, 70, 255))
        for k in range(3): d.rectangle(PS((300 - k * 30, 1380 + k * 26), (780 + k * 30, 1406 + k * 26)), fill=(84 + k * 8, 80 + k * 8, 84 + k * 8, 255))
        d.rectangle(PS((-M, 1458), (W + M, 1920)), fill=(44, 44, 52, 255))                    # calçada
        for k in range(6): d.line(PS((-M, 1500 + k * 80), (W + M, 1500 + k * 80)), fill=(56, 56, 64, 255), width=3 * S)
        d.rectangle(PS((780, 1060), (830, 1150)), fill=(60, 60, 66, 255)); d.ellipse(PS((795, 1080), (815, 1100)), fill=(120, 220, 140, 255))
        d.rounded_rectangle(PS((420, 800), (660, 850)), 8 * S, fill=(40, 40, 46, 255))
        d.text(P(446, 806), "Nº 214", font=font("title", 34 * S), fill=(220, 210, 180, 255))
        mid = add_light(mid, PS((360, 860), (720, 1460)), (230, 200, 130), 60 * S, 90)
        front = canvas(alpha=True); f = ImageDraw.Draw(front)                                 # grade do portão
        for x in range(360, 721, 30): f.rectangle(PS((x, 900), (x + 8, 1380)), fill=(22, 22, 26, 255))
        for y in (920, 1140, 1360): f.rectangle(PS((360, y), (728, y + 12)), fill=(22, 22, 26, 255))
        return down(back), down(mid), down(front)


class Beco(Scene):
    """Beco estreito entre prédios: paredes convergindo, lixeiras, escada de incêndio e luz no fim. Atalho entre ruas."""
    name = "beco"; light = "night"; grade = "noite"; acoustic = "media"
    ground = (1260, 1900, 0.4, 1.6)
    rain_full = True; wet = True; amb = "chuva_fora"; lightning_full = True
    ripples = [(520, 1600, 110), (420, 1800, 150)]
    fog_cfg = dict(y=1100, height=500, alpha=0.4, col=(80, 70, 90), speed=10)
    def build(self):
        back = canvas(); back.paste(grad(CWX * S, 1300 * S, (10, 12, 24), (40, 30, 50)), (0, 0))
        back = add_light(back, PS((440, 900), (640, 1300)), (220, 180, 120), 60 * S, 120)       # luz da rua lá no fim
        mid = canvas(alpha=True); d = ImageDraw.Draw(mid)
        d.polygon(PS((-M, 0), (470, 700), (470, 1260), (-M, 1920)), fill=(54, 42, 40, 255))   # parede esquerda
        d.polygon(PS((W + M, 0), (610, 700), (610, 1260), (W + M, 1920)), fill=(44, 40, 48, 255))
        for k in range(12):                                                                     # tijolos (linhas em perspectiva)
            y = 760 + k * 60
            d.line(PS((470, 700 + k * 48), (-M, 0 + k * 160)), fill=(44, 34, 32, 255), width=2 * S)
            d.line(PS((610, 700 + k * 48), (W + M, k * 160)), fill=(36, 32, 40, 255), width=2 * S)
        d.polygon(PS((-M, 1920), (470, 1260), (610, 1260), (W + M, 1920)), fill=(30, 30, 36, 255))  # chão
        for x0, x1, y0 in ((690, 900, 720), (700, 960, 1000)):                                  # escada de incêndio
            d.rectangle(PS((x0, y0), (x1, y0 + 14)), fill=(20, 20, 24, 255))
            for x in range(x0, x1, 24): d.line(PS((x, y0 - 60), (x, y0)), fill=(20, 20, 24, 255), width=3 * S)
        d.line(PS((700, 734), (940, 1000)), fill=(20, 20, 24, 255), width=6 * S)
        for x, y, w, h, c in ((120, 1520, 200, 220, (40, 70, 50)), (300, 1400, 120, 140, (70, 70, 80)), (820, 1560, 230, 240, (60, 50, 40))):
            d.rectangle(PS((x, y), (x + w, y + h)), fill=c + (255,)); d.rectangle(PS((x - 8, y - 16), (x + w + 8, y)), fill=tuple(int(v * 0.8) for v in c) + (255,))
        d.ellipse(PS((560, 760), (600, 790)), fill=(255, 220, 150, 255))
        mid = add_light(mid, PS((480, 740), (680, 1000)), (240, 200, 130), 40 * S, 100)
        return down(back), down(mid), None


class Viaduto(Scene):
    """Viaduto elevado: pista com mureta e a cidade lá embaixo. Caminho da rua até a ponte."""
    name = "viaduto"; light = "night"; grade = "noite"; acoustic = "aberto"
    clouds = (60, 500, (60, 50, 70))
    ground = (1240, 1900, 0.35, 1.6)
    rain_full = True; wet = True; amb = "chuva_fora"; lightning_full = True
    ripples = [(380, 1600, 120), (760, 1760, 150)]
    fog_cfg = dict(y=1000, height=500, alpha=0.45, col=(90, 80, 100), speed=16)
    def build(self):
        back = canvas()
        city = skyline(CWX * S, 1240 * S, 55, sky=((10, 14, 30), (70, 34, 44)), hmin=0.15, hmax=0.5, lit=0.4)
        back.paste(city.filter(ImageFilter.GaussianBlur(2 * S)), (0, 0))
        mid = canvas(alpha=True); d = ImageDraw.Draw(mid)
        d.polygon(PS((-M, 1920), (500, 1240), (580, 1240), (W + M, 1920)), fill=(46, 46, 54, 255))   # pista
        for k in range(7):
            y = 1280 + k * 90; w = 5 + k * 4
            d.polygon(PS((540 - w, y), (540 + w, y), (540 + w + 4, y + 40 + k * 6), (540 - w - 4, y + 40 + k * 6)), fill=(220, 210, 160, 255))
        for side in (-1, 1):                                                                         # muretas
            x0 = 500 if side < 0 else 580; x1 = -M if side < 0 else W + M
            d.polygon(PS((x0, 1240), (x0, 1200), (x1, 1660), (x1, 1920)), fill=(110, 110, 118, 255))
            for k in range(10):
                fx = x0 + (x1 - x0) * k / 9; fy = 1200 + (1660 - 1200) * k / 9
                d.line(PS((fx, fy), (fx, fy - 20 - k * 22)), fill=(60, 60, 66, 255), width=(2 + k) * S)
        for k in range(4):                                                                            # postes de luz
            fx = 500 - k * 180; fy = 1200 + k * 150
            d.line(PS((fx, fy), (fx, fy - 140 - k * 120)), fill=(30, 30, 36, 255), width=(3 + k * 2) * S)
            mid = add_light(mid, PS((fx - 60 - k * 40, fy - 220 - k * 140), (fx + 60 + k * 40, fy)), (230, 200, 130), 30 * S, 80)
            d = ImageDraw.Draw(mid)
        d.rounded_rectangle(PS((620, 980), (900, 1080)), 8 * S, fill=(30, 110, 60, 255))
        d.text(P(642, 996), "PONTE  →", font=font("title", 52 * S), fill=(240, 240, 240, 255))
        d.line(PS((760, 1080), (760, 1230)), fill=(40, 40, 46, 255), width=6 * S)
        return down(back), down(mid), None


class Estacionamento(Scene):
    """Garagem subterrânea: teto baixo de concreto, pilares, vagas pintadas e carros parados. Esconderijo/atalho."""
    name = "estacionamento"; light = "night"; grade = "noite"; acoustic = "grande"; amb = "chuva_dentro"
    ground = (1280, 1900, 0.45, 1.55)
    def build(self):
        back = canvas((22, 24, 28)); b = ImageDraw.Draw(back)
        b.polygon(PS((-M, 0), (W + M, 0), (760, 980), (320, 980)), fill=(52, 52, 56))                 # teto
        for k in range(6): b.line(PS((-M + k * 260, 0), (320 + k * 88, 980)), fill=(40, 40, 44), width=3 * S)
        b.rectangle(PS((320, 980), (760, 1280)), fill=(16, 16, 20))                                     # fundo escuro
        b.polygon(PS((-M, 1920), (320, 1280), (760, 1280), (W + M, 1920)), fill=(70, 70, 74))           # piso
        for k in range(8):                                                                               # vagas
            x0 = 320 + k * 63; b.line(PS((x0, 1280), (-M + k * 190, 1920)), fill=(200, 190, 120), width=4 * S)
        mid = canvas(alpha=True); d = ImageDraw.Draw(mid)
        for x, y, w, h in ((120, 700, 90, 1100), (860, 700, 90, 1100), (330, 980, 40, 330), (700, 980, 40, 330)):
            d.rectangle(PS((x, y), (x + w, y + h)), fill=(96, 96, 100, 255)); d.rectangle(PS((x, y + h - 120), (x + w, y + h)), fill=(200, 170, 40, 255))
        r = random.Random(5)
        for x, y, s in ((380, 1240, 0.5), (600, 1250, 0.5), (-60, 1420, 1.0)):
            c = r.choice([(90, 40, 40), (40, 60, 90), (120, 120, 120)])
            d.rounded_rectangle(PS((x, y), (x + 360 * s, y + 130 * s)), int(30 * s) * S, fill=c + (255,))
            d.rounded_rectangle(PS((x + 70 * s, y - 60 * s), (x + 280 * s, y + 20 * s)), int(24 * s) * S, fill=tuple(int(v * 0.8) for v in c) + (255,))
        for x in (300, 540, 780): d.rectangle(PS((x - 80, 600), (x + 80, 620)), fill=(230, 240, 230, 255))
        for x in (300, 540, 780): mid = add_light(mid, PS((x - 260, 560), (x + 260, 1500)), (220, 230, 220), 80 * S, 50)
        return down(back), down(mid), None


class Vagao(Scene):
    """Vagão do metrô por dentro: bancos dos dois lados, barras, janelas com o túnel escuro passando."""
    name = "vagao"; light = "night"; grade = "noite"; acoustic = "media"; amb = "chuva_dentro"
    ground = (1320, 1900, 0.55, 1.6)
    def build(self):
        back = canvas((10, 10, 14))
        mid = canvas(alpha=True); d = ImageDraw.Draw(mid)
        d.polygon(PS((-M, 0), (W + M, 0), (680, 760), (400, 760)), fill=(170, 172, 168, 255))         # teto
        d.polygon(PS((-M, 0), (400, 760), (400, 1320), (-M, 1920)), fill=(150, 156, 158, 255))         # lateral esquerda
        d.polygon(PS((W + M, 0), (680, 760), (680, 1320), (W + M, 1920)), fill=(140, 146, 150, 255))
        d.polygon(PS((-M, 1920), (400, 1320), (680, 1320), (W + M, 1920)), fill=(80, 84, 92, 255))      # piso
        d.rectangle(PS((400, 760), (680, 1320)), fill=(60, 64, 70, 255))                                  # porta do fundo
        d.rectangle(PS((470, 820), (610, 1000)), fill=(16, 16, 22, 255))
        for side in (-1, 1):
            for k in range(3):                                                                            # janelas e bancos
                t0, t1 = 0.12 + k * 0.28, 0.32 + k * 0.28
                xa = lambda t: (400 + (-M - 400) * (1 - t)) if side < 0 else (680 + (W + M - 680) * (1 - t))
                ya = lambda t, y0, y1: y0 + (y1 - y0) * (1 - t)
                d.polygon(PS((xa(t0), ya(t0, 860, 300)), (xa(t1), ya(t1, 860, 300)), (xa(t1), ya(t1, 1060, 1000)), (xa(t0), ya(t0, 1060, 1000))), fill=(14, 16, 22, 255))
                d.polygon(PS((xa(t0), ya(t0, 1180, 1500)), (xa(t1), ya(t1, 1180, 1500)), (xa(t1), ya(t1, 1240, 1640)), (xa(t0), ya(t0, 1240, 1640))), fill=(40, 90, 120, 255))
        for x, y0, y1 in ((250, 300, 1700), (830, 300, 1700), (470, 760, 1330), (610, 760, 1330)):
            d.line(PS((x, y0), (x, y1)), fill=(210, 210, 214, 255), width=(10 if x in (250, 830) else 5) * S)
        for k in range(3): d.rectangle(PS((430 - k * 160, 760 - k * 250), (650 + k * 160, 780 - k * 250)), fill=(245, 250, 240, 255))
        mid = add_light(mid, PS((200, 300), (880, 1400)), (230, 240, 230), 120 * S, 40)
        return down(back), down(mid), None

    def dynamic(self, img, t, camx, props):   # luzes do túnel passando nas janelas
        d = ImageDraw.Draw(img); v = props.get("velocidade", 1.0)
        if not v: return
        for side, (x0, x1) in ((-1, (0, 330)), (1, (750, 1080))):
            ph = (t * 900 * v) % 700
            for k in range(-1, 3):
                x = x0 + ((ph + k * 700) % 700) * (x1 - x0) / 700 if side > 0 else x1 - ((ph + k * 700) % 700) * (x1 - x0) / 700
                d.rectangle((x - 6, 560, x + 6, 600), fill=(250, 220, 150))


CENAS = (Portao, Beco, Viaduto, Estacionamento, Vagao)
