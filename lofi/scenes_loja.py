"""Cenários da loja de conveniência (série Turno da Noite): a loja por dentro e o estoque com a câmara fria.
Mesmo padrão de lofi/scenes.py (camadas fundo/meio/frente, chão em perspectiva, luz que pisca)."""
import math, random
from PIL import Image, ImageDraw
from .scenes import Scene, canvas, P, PS, down, S, M, W
from .core import add_light, font, lerp


class Loja(Scene):
    """Loja de conveniência 24h por dentro, de madrugada: geladeiras de vidro à esquerda, porta de vidro com sininho
    à direita (lá fora, o pátio do posto), gôndola no fundo e o balcão do caixa na frente, à esquerda, com a
    registradora e o monitor das câmeras. Quem fica na marca `balcao` aparece atrás do balcão (da cintura para cima)."""
    name = "loja"; acoustic = "media"; light = "dark"; grade = "frio"
    ground = (1130, 1900, 0.5, 1.5); amb = "zumbido"
    def build(self):
        back = canvas((22, 26, 30)); d = ImageDraw.Draw(back); r = random.Random(17)
        # paredes, teto e piso (ponto de fuga no centro)
        d.rectangle(PS((-M, 0), (W + M, 1920)), fill=(72, 80, 78))
        d.polygon(PS((-M, 0), (W + M, 0), (760, 640), (320, 640)), fill=(110, 116, 112))
        d.polygon(PS((-M, 1920), (W + M, 1920), (760, 1130), (320, 1130)), fill=(96, 100, 94))
        for i in range(-12, 14):                                                   # piso quadriculado
            d.line(PS((540 + i * 18, 1130), (540 + i * 150, 1920)), fill=(104, 108, 100), width=2 * S)
        for k in range(11):
            y = 1130 + (k / 11) ** 1.7 * 790; d.line(PS((-M, y), (W + M, y)), fill=(104, 108, 100), width=2 * S)
        d.polygon(PS((-M, 0), (320, 640), (320, 1130), (-M, 1920)), fill=(84, 92, 92))                  # parede esq.
        d.polygon(PS((W + M, 0), (760, 640), (760, 1130), (W + M, 1920)), fill=(80, 86, 90))            # parede dir.
        d.rectangle(PS((320, 640), (760, 1130)), fill=(70, 76, 74))                                     # fundo
        # gôndola do fundo com produtos
        d.rectangle(PS((340, 760), (740, 1130)), fill=(50, 54, 60))
        for j in range(5):
            y = 790 + j * 66; d.rectangle(PS((340, y + 50), (740, y + 58)), fill=(110, 114, 120))
            x = 350
            while x < 730:
                w = r.randint(14, 30); h = r.randint(26, 48)
                if r.random() < 0.85:
                    d.rectangle(PS((x, y + 50 - h), (x + w, y + 50)), fill=r.choice(
                        [(200, 60, 50), (230, 190, 60), (60, 140, 200), (90, 170, 90), (230, 230, 230), (230, 120, 40)]))
                x += w + 3
        d.rectangle(PS((380, 666), (700, 736)), fill=(40, 70, 150))                                     # placa
        d.text(P(404, 670), "LUA 24H", font=font("title", 56 * S), fill=(255, 230, 120))
        # geladeiras de vidro (parede esquerda), portas com luz fria
        for k in range(4):
            f0, f1 = k / 4, (k + 1) / 4
            xa, xb = lerp(320, -60, f0 ** 1.25), lerp(320, -60, f1 ** 1.25)
            ta, tb = lerp(700, 260, f0 ** 1.2), lerp(700, 260, f1 ** 1.2)
            ba, bb = lerp(1120, 1560, f0 ** 1.2), lerp(1120, 1560, f1 ** 1.2)
            d.polygon(PS((xa, ta), (xb, tb), (xb, bb), (xa, ba)), fill=(104, 150, 172), outline=(40, 46, 52))
            for j in range(1, 5):
                u = j / 5; d.line(PS((xa, lerp(ta, ba, u)), (xb, lerp(tb, bb, u))), fill=(90, 120, 150), width=3 * S)
                for q in range(3):
                    v = (q + 0.5) / 3; x = lerp(xa, xb, v); y = lerp(lerp(ta, ba, u), lerp(tb, bb, u), v)
                    h = lerp(18, 50, f1); d.rectangle(PS((x - h * 0.2, y - h), (x + h * 0.2, y)), fill=r.choice(
                        [(200, 50, 50), (60, 160, 90), (240, 200, 60), (60, 90, 200)]))
            d.line(PS((xb + 8, lerp(tb, bb, 0.45)), (xb + 8, lerp(tb, bb, 0.6))), fill=(200, 200, 210), width=5 * S)
        back = add_light(back, PS((-120, 240), (330, 1560)), (90, 150, 200), 70 * S, 70)
        # porta de vidro (parede direita): lá fora, o pátio do posto de noite
        d = ImageDraw.Draw(back)
        d.polygon(PS((800, 690), (1010, 470), (1010, 1430), (800, 1180)), fill=(10, 14, 28), outline=(150, 156, 160))
        d.line(PS((905, 580), (905, 1305)), fill=(150, 156, 160), width=5 * S)
        d.polygon(PS((812, 880), (998, 760), (998, 790), (812, 900)), fill=(200, 40, 40))                # cobertura do posto
        for x in (850, 960): d.rectangle(PS((x - 14, 1000), (x + 14, 1140)), fill=(190, 40, 40))         # bombas
        d.text(P(830, 640), "ABERTO", font=font("title", 30 * S), fill=(120, 255, 160))
        d.ellipse(PS((786, 640), (814, 668)), fill=(220, 190, 80))                                       # sininho
        d.line(PS((800, 610), (800, 642)), fill=(120, 120, 120), width=3 * S)
        # luminárias
        for k in range(4):
            y = 120 + k * 150; w = 360 - k * 70
            d.rectangle(PS((540 - w / 2, y), (540 + w / 2, y + 14)), fill=(235, 245, 250))
        back = add_light(back, PS((240, 80), (840, 1250)), (70, 80, 80), 80 * S, 100)
        # balcão do caixa na frente (esquerda): registradora e monitor das câmeras
        front = canvas(alpha=True); f = ImageDraw.Draw(front)
        f.polygon(PS((-M, 1580), (430, 1540), (470, 1600), (470, 1920), (-M, 1920)), fill=(150, 46, 40, 255))
        f.polygon(PS((-M, 1550), (420, 1512), (470, 1540), (470, 1600), (-M, 1600)), fill=(196, 190, 176, 255))
        f.rectangle(PS((-M, 1650), (470, 1680)), fill=(230, 200, 60, 255))                            # faixa amarela
        f.rounded_rectangle(PS((250, 1420), (420, 1530)), 10 * S, fill=(40, 42, 48, 255))              # registradora
        f.rectangle(PS((270, 1436), (400, 1476)), fill=(70, 200, 120, 255))
        f.rounded_rectangle(PS((20, 1360), (210, 1520)), 10 * S, fill=(24, 24, 28, 255))               # monitor CFTV
        f.rectangle(PS((36, 1376), (194, 1494)), fill=(60, 74, 70, 255))
        for gx in (36, 115):
            for gy in (1376, 1435): f.rectangle(PS((gx, gy), (gx + 78, gy + 58)), outline=(20, 24, 22, 255), width=2 * S)
        f.text(P(40, 1378), "CAM", font=font("title", 18 * S), fill=(230, 240, 230, 255))
        return down(back), None, down(front)
    def dynamic(self, img, t, camx, props):
        on = random.Random(int(t * 9) * 23 + 5).random() > props.get("flicker", 0.1)
        if not on: img.paste(Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.55))
        props["_lamp_on"] = on
        # chiado no monitor das câmeras (acompanha a frente)
        off = int(M - camx * self.depths[2]); off = max(0, min(2 * M, off))
        x0, x1 = 36 + M - off + 4, 194 + M - off - 4
        if x1 > 0 and x0 < W:
            rr = random.Random(int(t * 24)); d = ImageDraw.Draw(img)
            for _ in range(40):
                x = rr.uniform(x0, x1); y = rr.uniform(1380, 1490); c = rr.randint(60, 200)
                d.line([(x, y), (x + rr.uniform(4, 18), y)], fill=(c, c + 10, c))


class Estoque(Scene):
    """Estoque nos fundos da loja: prateleiras de metal com caixas dos dois lados, uma lâmpada pendurada que balança
    e, no fundo, a porta de aço da câmara fria com gelo nas frestas."""
    name = "estoque"; acoustic = "sala"; light = "dark"; grade = "frio"
    ground = (1200, 1900, 0.55, 1.5); amb = "zumbido"
    def build(self):
        back = canvas((14, 16, 18)); d = ImageDraw.Draw(back); r = random.Random(29)
        d.rectangle(PS((-M, 0), (W + M, 1920)), fill=(58, 60, 62))
        d.polygon(PS((-M, 1920), (W + M, 1920), (720, 1200), (360, 1200)), fill=(66, 66, 64))
        for k in range(10):
            y = 1200 + (k / 10) ** 1.7 * 720; d.line(PS((-M, y), (W + M, y)), fill=(56, 56, 54), width=2 * S)
        d.polygon(PS((-M, 0), (W + M, 0), (720, 560), (360, 560)), fill=(40, 42, 44))
        d.rectangle(PS((360, 560), (720, 1200)), fill=(70, 72, 74))
        # porta da câmara fria
        d.rectangle(PS((400, 640), (680, 1200)), fill=(150, 160, 168), outline=(90, 96, 102), width=6 * S)
        for y in range(700, 1180, 60): d.line(PS((410, y), (670, y)), fill=(130, 140, 148), width=2 * S)
        d.rounded_rectangle(PS((620, 880), (660, 1000)), 8 * S, fill=(60, 64, 70))
        d.rectangle(PS((420, 600), (660, 634)), fill=(40, 90, 160))
        d.text(P(436, 600), "CÂMARA FRIA", font=font("title", 28 * S), fill=(230, 240, 255))
        for x in range(404, 680, 18): d.polygon(PS((x, 1196), (x + 9, 1196), (x + 4, 1180)), fill=(220, 236, 250))
        back = add_light(back, PS((380, 1150), (700, 1260)), (150, 200, 240), 30 * S, 90)
        # prateleiras com caixas dos dois lados
        mid = canvas(alpha=True); md = ImageDraw.Draw(mid)
        for side in (-1, 1):
            for k in range(4):
                f0, f1 = k / 4, (k + 1) / 4
                xa = lerp(540 + side * 190, 540 + side * 760, f0 ** 1.4); xb = lerp(540 + side * 190, 540 + side * 760, f1 ** 1.4)
                ta, tb = lerp(600, 120, f0 ** 1.2), lerp(600, 120, f1 ** 1.2); ba, bb = lerp(1200, 1880, f0 ** 1.4), lerp(1200, 1880, f1 ** 1.4)
                for j in range(5):
                    u = j / 4.6; ya, yb = lerp(ta, ba, u), lerp(tb, bb, u)
                    md.line(PS((xa, ya), (xb, yb)), fill=(120, 126, 132, 255), width=max(2, int(lerp(3, 9, f1))) * S)
                    if j < 4:
                        for q in range(2):
                            v0, v1 = 0.1 + q * 0.45, 0.45 + q * 0.45
                            hh = lerp(30, 120, f1) * r.uniform(0.6, 1.0)
                            pa = (lerp(xa, xb, v0), lerp(ya, yb, v0)); pb = (lerp(xa, xb, v1), lerp(ya, yb, v1))
                            md.polygon(PS((pa[0], pa[1] - 3), (pb[0], pb[1] - 3), (pb[0], pb[1] - hh), (pa[0], pa[1] - hh)),
                                       fill=r.choice([(160, 120, 70, 255), (176, 134, 82, 255), (140, 104, 60, 255)]))
                for x, ta_, ba_ in ((xa, ta, ba), (xb, tb, bb)):
                    md.line(PS((x, ta_), (x, ba_)), fill=(90, 94, 100, 255), width=max(2, int(lerp(3, 10, f1))) * S)
        return down(back), down(mid), None
    def dynamic(self, img, t, camx, props):
        # lâmpada pendurada balançando: o círculo de luz anda de um lado para o outro
        a = math.sin(t * props.get("swing", 1.6)) * 60
        x = 540 + a; d = ImageDraw.Draw(img)
        d.line([(540, 0), (x, 300)], fill=(20, 20, 20), width=3)
        d.ellipse([x - 16, 296, x + 16, 330], fill=(255, 236, 180))
        img.paste(add_light(img, (x - 520, 200, x + 520, 1600), (90, 80, 60), 160, 90))
        if random.Random(int(t * 8) * 31).random() < props.get("flicker", 0.08):
            img.paste(Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.65)); props["_lamp_on"] = False
        else: props["_lamp_on"] = True


CENAS = (Loja, Estoque)
