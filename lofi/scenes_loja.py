"""Cenários da loja de conveniência 24h (série Turno da Noite).

    loja         salão visto do corredor: caixa com o balcão à esquerda (frente: esconde quem está atrás dele),
                 porta de vidro no fundo, geladeiras à direita, relógio digital e monitor das câmeras na parede.
                 props: relogio ("03:00"), vulto (0–1, silhueta alta na porta de vidro), flicker (0–1),
                        reflexo (0–1, silhueta parada no vidro da geladeira), apagado (True = só a luz das geladeiras)
    deposito     fundos da loja: caixas, gerador e a porta de aço da câmara fria.
                 props: batida (0–1, porta tremendo), rosto (0–1, rosto no vidro da porta), cadeado (True),
                        gerador (True = ligado), luz (0–1, lâmpada; 0 = breu)
    camara_fria  câmara fria por dentro: prateleiras de aço, gelo, lâmpada azul, cortina de tiras na frente.
                 props: flicker (0–1), tiras (True = cortina na frente)
    cftv         close no monitor das câmeras (4 quadrantes) em cima do balcão.
                 props: hora ("03:00:00"), vulto (nº da câmera 1–4 ou lista), duplo (True = alguém no caixa na CAM 1),
                        ruido (0–1), cam (1–4: uma câmera em tela cheia)
"""
import math, random
from PIL import Image, ImageDraw, ImageFilter
from . import partes
from .core import W, H, grad, add_light, lerp, font
from .scenes import Scene, M, S, CWX, P, PS, canvas, down


def _sombra_alta(img, x, y_pe, alt, a=1.0, col=(8, 8, 12)):
    """Silhueta alta e magra (o Cliente): chapéu, ombros estreitos, braços longos."""
    lay = Image.new("L", img.size, 0); d = ImageDraw.Draw(lay); k = alt / 600.0; v = int(255 * a)
    d.ellipse([x - 34 * k, y_pe - alt, x + 34 * k, y_pe - alt + 80 * k], fill=v)                      # cabeça
    d.rectangle([x - 60 * k, y_pe - alt - 8 * k, x + 60 * k, y_pe - alt + 6 * k], fill=v)            # aba do chapéu
    d.rectangle([x - 32 * k, y_pe - alt - 50 * k, x + 32 * k, y_pe - alt], fill=v)
    d.polygon([(x - 56 * k, y_pe - alt + 110 * k), (x + 56 * k, y_pe - alt + 110 * k),
               (x + 40 * k, y_pe - 230 * k), (x - 40 * k, y_pe - 230 * k)], fill=v)                   # tronco
    d.rectangle([x - 18 * k, y_pe - alt + 76 * k, x + 18 * k, y_pe - alt + 116 * k], fill=v)         # pescoço
    for s in (-1, 1):
        d.line([(x + s * 54 * k, y_pe - alt + 118 * k), (x + s * 70 * k, y_pe - 160 * k)], fill=v, width=int(22 * k) + 1)
        d.line([(x + s * 18 * k, y_pe - 240 * k), (x + s * 26 * k, y_pe)], fill=v, width=int(30 * k) + 1)
    img.paste(col, (0, 0), lay.filter(ImageFilter.GaussianBlur(3)))


# ======================= LOJA (salão com caixa) =======================
class Loja(Scene):
    name = "loja"; acoustic = "media"; light = "night"; grade = "frio"; amb = "zumbido"
    ground = (1180, 1900, 0.5, 1.45)
    def build(self):
        r = random.Random(24)
        back = canvas((40, 44, 44)); d = ImageDraw.Draw(back)
        d.rectangle(PS((-M, 0), (W + M, 300)), fill=(30, 32, 34))                                    # forro
        d.rectangle(PS((-M, 300), (W + M, 1180)), fill=(112, 122, 112))                              # parede
        d.rectangle(PS((-M, 1080), (W + M, 1180)), fill=(84, 92, 84))                             # rodapé
        # piso xadrez em perspectiva
        d.rectangle(PS((-M, 1180), (W + M, 1920)), fill=(140, 144, 136))
        lin = [1180 + (k / 14) ** 1.8 * 740 for k in range(15)]
        for i in range(14):
            for j in range(-14, 15):
                if (i + j) % 2: continue
                def X(jj, yy): return 540 + jj * lerp(46, 150, (yy - 1180) / 740)
                y0, y1 = lin[i], lin[i + 1]
                d.polygon(PS((X(j, y0), y0), (X(j + 1, y0), y0), (X(j + 1, y1), y1), (X(j, y1), y1)), fill=(100, 104, 98))
        # prateleira de cigarros atrás do caixa
        d.rectangle(PS((20, 640), (440, 1080)), fill=(70, 50, 40))
        for row in range(6):
            for col in range(9):
                c = r.choice([(210, 60, 50), (230, 230, 225), (60, 90, 170), (220, 180, 60), (40, 40, 44)])
                x = 36 + col * 45; y = 660 + row * 68
                d.rectangle(PS((x, y), (x + 34, y + 50)), fill=c)
        # porta de vidro no fundo (fora: escuro, bombas e o letreiro)
        d.rectangle(PS((480, 600), (780, 1170)), fill=(60, 64, 66))
        out = grad(280 * S, 550 * S, (8, 10, 22), (26, 18, 30))
        back.paste(out, P(490, 610))
        d.rectangle(PS((490, 1000), (770, 1160)), fill=(28, 28, 32))
        for x in (560, 700):
            d.rounded_rectangle(PS((x - 26, 900), (x + 26, 1010)), 6 * S, fill=(150, 34, 34))
        d.rectangle(PS((490, 840), (770, 858)), fill=(200, 40, 40)); d.rectangle(PS((490, 858), (770, 866)), fill=(220, 220, 220))
        d.line(PS((630, 610), (630, 1160)), fill=(60, 64, 66), width=10 * S)
        d.text(P(500, 630), "ABERTO 24H", font=font("mono", 30 * S), fill=(255, 90, 70))
        # geladeiras na parede da direita (perspectiva)
        for k in range(4):
            f0, f1 = k / 4, (k + 1) / 4
            xa, xb = lerp(800, 1190, f0 ** 1.3), lerp(800, 1190, f1 ** 1.3)
            ta, tb = lerp(560, 120, f0 ** 1.2), lerp(560, 120, f1 ** 1.2)
            ba, bb = lerp(1190, 1720, f0 ** 1.3), lerp(1190, 1720, f1 ** 1.3)
            d.polygon(PS((xa, ta), (xb, tb), (xb, bb), (xa, ba)), fill=(30, 40, 44))
            g = 10
            d.polygon(PS((xa + g, ta + g), (xb - g, tb + g), (xb - g, bb - g), (xa + g, ba - g)), fill=(120, 170, 180))
            for j in range(4):
                ya, yb = lerp(ta, ba, (j + 1) / 5), lerp(tb, bb, (j + 1) / 5)
                d.line(PS((xa + g, ya), (xb - g, yb)), fill=(60, 80, 86), width=4 * S)
                for q in range(5):
                    u = (q + 0.3) / 5; x = lerp(xa, xb, u); y = lerp(ya, yb, u); h = lerp(30, 90, f0)
                    c = r.choice([(220, 60, 50), (240, 200, 60), (70, 160, 90), (240, 240, 240), (60, 100, 200)])
                    d.rectangle(PS((x - h * 0.15, y - h), (x + h * 0.15, y)), fill=c)
        # relógio digital e monitor das câmeras na parede
        d.rounded_rectangle(PS((520, 470), (740, 560)), 8 * S, fill=(18, 18, 20))
        d.rounded_rectangle(PS((300, 400), (460, 520)), 6 * S, fill=(200, 196, 180))
        d.rectangle(PS((314, 412), (446, 506)), fill=(20, 30, 30))
        back = add_light(back, PS((-200, 300), (1300, 1500)), (170, 200, 190), 120 * S, 45)
        back = down(back)
        # balcão do caixa (frente: tapa as pernas de quem está atrás)
        front = canvas(alpha=True); d = ImageDraw.Draw(front)
        d.polygon(PS((-M, 1330), (470, 1330), (470, 1358), (-M, 1358)), fill=(214, 210, 200, 255))      # tampo
        d.rectangle(PS((-M, 1358), (460, 1560)), fill=(160, 36, 36, 255))                               # frente vermelha
        d.rectangle(PS((-M, 1540), (460, 1560)), fill=(80, 18, 18, 255))
        d.rectangle(PS((300, 1262), (420, 1332)), fill=(40, 40, 44, 255))                               # caixa registradora
        d.rectangle(PS((314, 1272), (406, 1300)), fill=(80, 200, 120, 255))
        d.rectangle(PS((60, 1306), (136, 1332)), fill=(60, 60, 64, 255))                               # maquininha
        d.rectangle(PS((60, 1384), (196, 1528)), fill=(236, 232, 214, 255))                             # folha das regras
        d.text(P(72, 1392), "REGRAS", font=font("mono", 26 * S), fill=(30, 30, 30, 255))
        for k in range(8): d.line(PS((72, 1436 + k * 11), (182 - (k % 3) * 18, 1436 + k * 11)), fill=(70, 70, 70, 255), width=2 * S)
        d.line(PS((80, 1380), (110, 1390)), fill=(200, 200, 160, 255), width=8 * S)                    # durex
        return back, None, down(front)
    def dynamic(self, img, t, camx, props):
        d = ImageDraw.Draw(img); dx = camx * self.depths[0]
        apagado = props.get("apagado", False)
        on = (not apagado) and random.Random(int(t * 9) * 31 + 5).random() > props.get("flicker", 0.04)
        props["_lamp_on"] = on
        for k in range(3):                                                                           # lâmpadas tubulares
            y = 120 + k * 70; w = 520 - k * 120
            d.rectangle([540 - w / 2 + dx, y, 540 + w / 2 + dx, y + 16], fill=(235, 250, 240) if on else (70, 74, 72))
        hora = str(props.get("relogio", "03:00"))
        d.text((540 + dx, 482), hora, font=font("mono", 64), fill=(255, 50, 40))
        if props.get("vulto", 0):                                                                    # silhueta na porta
            _sombra_alta(img, 630 + dx, 1160, 520, a=min(1.0, float(props["vulto"])))
        if props.get("reflexo", 0):                                                                  # alguém no vidro da geladeira
            lay = Image.new("RGB", img.size, (0, 0, 0)); _sombra_alta(lay, 900 + dx * 1.2, 1300, 560, col=(200, 230, 235))
            m = lay.convert("L").point(lambda v: int(v * 0.45 * float(props["reflexo"])))
            img.paste((10, 14, 16), (0, 0), m)
        cam = (314 + dx, 412, 446 + dx, 506)                                                         # monitor da parede
        n = random.Random(int(t * 12))
        for q in range(4):
            qx = cam[0] + (q % 2) * 66; qy = cam[1] + (q // 2) * 47
            d.rectangle([qx + 2, qy + 2, qx + 64, qy + 45], fill=(40 + n.randint(0, 20), 60 + n.randint(0, 20), 56))
        if not on:
            img.paste(Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.78 if apagado else 0.6))
            if apagado:                                                                              # só as geladeiras acesas
                img.paste(add_light(img, (760 + dx, 200, 1080, 1700), (90, 170, 190), 70, 110))


# ======================= DEPÓSITO (fundos + porta da câmara fria) =======================
class Deposito(Scene):
    name = "deposito"; acoustic = "sala"; light = "warm"; grade = "quente"; amb = "zumbido"
    ground = (1260, 1900, 0.55, 1.4)
    def build(self):
        r = random.Random(7)
        back = canvas((30, 28, 26)); d = ImageDraw.Draw(back)
        d.rectangle(PS((-M, 0), (W + M, 1260)), fill=(96, 92, 84))                                  # parede de concreto
        for _ in range(140):
            x, y = r.uniform(-M, W + M), r.uniform(0, 1250)
            d.ellipse(PS((x, y), (x + 6, y + 6)), fill=(86, 82, 76))
        d.rectangle(PS((-M, 1260), (W + M, 1920)), fill=(70, 68, 64))                               # chão
        for k in range(10):
            y = 1260 + (k / 10) ** 1.7 * 660; d.line(PS((-M, y), (W + M, y)), fill=(62, 60, 56), width=2 * S)
        # pilhas de caixas à esquerda
        for (x, y, w, h) in ((-60, 1000, 200, 270), (140, 1060, 170, 210), (-40, 760, 180, 240), (160, 880, 140, 180)):
            d.rectangle(PS((x, y), (x + w, y + h)), fill=(170, 130, 84)); d.rectangle(PS((x, y), (x + w, y + h)), outline=(120, 90, 56), width=4 * S)
            d.line(PS((x + w / 2, y), (x + w / 2, y + h)), fill=(200, 180, 130), width=10 * S)
        # gerador
        d.rounded_rectangle(PS((330, 1060), (500, 1270)), 10 * S, fill=(200, 160, 40))
        d.rectangle(PS((350, 1090), (480, 1140)), fill=(40, 40, 40)); d.text(P(356, 1094), "GERADOR", font=font("mono", 22 * S), fill=(240, 220, 120))
        d.line(PS((470, 1180), (470, 1230)), fill=(30, 30, 30), width=10 * S)
        # placa da câmara fria
        d.rectangle(PS((560, 640), (880, 720)), fill=(230, 220, 60))
        d.text(P(574, 650), "CÂMARA FRIA", font=font("title", 40 * S), fill=(30, 30, 30))
        d.text(P(612, 698), "NÃO ABRIR", font=font("mono", 18 * S), fill=(160, 20, 20))
        # cano e fios
        d.line(PS((-M, 260), (W + M, 260)), fill=(60, 58, 54), width=24 * S)
        d.line(PS((420, 260), (420, 1060)), fill=(30, 30, 30), width=6 * S)
        return down(back), None, None
    def dynamic(self, img, t, camx, props):
        dx = camx * self.depths[0]; d = ImageDraw.Draw(img)
        bat = float(props.get("batida", 0) or 0)
        tr = (math.sin(t * 70) * 6 * bat) if bat and (t * 2.2) % 1 < 0.35 else 0
        x0, x1 = 570 + dx + tr, 870 + dx + tr
        d.rectangle([x0 - 16, 744, x1 + 16, 1280], fill=(60, 64, 70))                              # batente
        d.rectangle([x0, 760, x1, 1270], fill=(176, 184, 190))                                      # porta de aço
        for k in range(5): d.line([(x0 + 10, 800 + k * 100), (x1 - 10, 800 + k * 100)], fill=(150, 158, 164), width=3)
        jan = [x0 + 100, 820, x0 + 200, 930]
        d.rectangle(jan, fill=(150, 196, 210), outline=(80, 86, 92), width=5)                       # vidro embaçado
        if props.get("rosto", 0):
            a = float(props["rosto"]); lay = Image.new("L", img.size, 0); dl = ImageDraw.Draw(lay)
            dl.ellipse([jan[0] + 22, jan[1] + 14, jan[2] - 22, jan[3] - 4], fill=int(200 * a))
            img.paste((214, 226, 230), (0, 0), lay.filter(ImageFilter.GaussianBlur(6))); d = ImageDraw.Draw(img)
            for ex in (jan[0] + 38, jan[2] - 46):
                d.ellipse([ex, jan[1] + 44, ex + 8, jan[1] + 52], fill=(30, 40, 50))
            for hx in (jan[0] + 8, jan[2] - 22):                                                     # mãos no vidro
                d.ellipse([hx, jan[3] - 30, hx + 16, jan[3] - 6], fill=(200, 214, 220))
        d.rectangle([x1 - 60, 1010, x1 - 20, 1040], fill=(60, 60, 64))                              # maçaneta
        if props.get("cadeado", True):
            d.arc([x1 - 66, 1032, x1 - 30, 1070], 180, 360, fill=(140, 140, 140), width=6)
            d.rounded_rectangle([x1 - 72, 1050, x1 - 24, 1100], 6, fill=(200, 170, 60))
        # lâmpada pendurada
        luz = float(props.get("luz", 1.0)); ger = props.get("gerador", True)
        on = luz > 0 and random.Random(int(t * 7) * 13).random() > props.get("flicker", 0.05)
        props["_lamp_on"] = on
        d.line([(540 + dx, 270), (540 + dx, 380)], fill=(20, 20, 20), width=4)
        d.ellipse([520 + dx, 378, 560 + dx, 420], fill=(255, 230, 160) if on else (60, 56, 50))
        if on: img.paste(add_light(img, (140 + dx, 300, 940 + dx, 1500), (255, 210, 140), 90, int(70 * luz)))
        d = ImageDraw.Draw(img)
        d.ellipse([440 + dx, 1100, 456 + dx, 1116], fill=(80, 230, 90) if ger else (230, 50, 40))   # LED do gerador
        if not on: img.paste(Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.72))


# ======================= CÂMARA FRIA (por dentro) =======================
class CamaraFria(Scene):
    name = "camara_fria"; acoustic = "abafado"; light = "dark"; grade = "frio"; amb = "zumbido"
    ground = (1220, 1900, 0.55, 1.4)
    fog_cfg = dict(y=1500, height=420, alpha=0.5, col=(190, 220, 235), speed=8)
    def build(self):
        r = random.Random(11)
        back = canvas((40, 56, 70)); d = ImageDraw.Draw(back)
        d.polygon(PS((-M, 0), (W + M, 0), (680, 520), (400, 520)), fill=(60, 80, 96))                # teto
        d.rectangle(PS((400, 520), (680, 1220)), fill=(110, 140, 158))                               # parede do fundo
        d.polygon(PS((-M, 1920), (W + M, 1920), (680, 1220), (400, 1220)), fill=(96, 110, 120))       # chão de chapa
        for k in range(12):
            y = 1220 + (k / 12) ** 1.7 * 700; xa = lerp(400, -M, (y - 1220) / 700); xb = lerp(680, W + M, (y - 1220) / 700)
            d.line(PS((xa, y), (xb, y)), fill=(84, 98, 108), width=2 * S)
        for side in (-1, 1):                                                                         # prateleiras de aço
            for k in range(5):
                f0, f1 = k / 5, (k + 1) / 5
                xa = lerp(540 + side * 140, 540 + side * 760, f0 ** 1.4); xb = lerp(540 + side * 140, 540 + side * 760, f1 ** 1.4)
                ta, tb = lerp(560, 0, f0 ** 1.2), lerp(560, 0, f1 ** 1.2); ba, bb = lerp(1210, 1900, f0 ** 1.4), lerp(1210, 1900, f1 ** 1.4)
                d.polygon(PS((xa, ta), (xb, tb), (xb, bb), (xa, ba)), fill=(54, 70, 82))
                for j in range(4):
                    ya, yb = lerp(ta, ba, (j + 1) / 5), lerp(tb, bb, (j + 1) / 5)
                    d.line(PS((xa, ya), (xb, yb)), fill=(170, 186, 196), width=max(2, int(lerp(2, 9, f1))) * S)
                    for q in range(3):
                        u = (q + r.random() * 0.4) / 3; x = lerp(xa, xb, u); y = lerp(ya, yb, u); h = lerp(16, 80, f0)
                        c = r.choice([(170, 130, 84), (200, 200, 196), (150, 120, 80), (110, 150, 170)])
                        d.rectangle(PS((min(x, x + side * h), y - h * 0.8), (max(x, x + side * h), y)), fill=c)
        for _ in range(260):                                                                         # gelo
            x, y = r.uniform(-M, W + M), r.uniform(0, 1900)
            d.ellipse(PS((x, y), (x + 4, y + 4)), fill=(220, 236, 244))
        d.rectangle(PS((470, 680), (610, 1220)), fill=(150, 176, 190))                               # porta lá no fundo
        d.rectangle(PS((510, 740), (570, 820)), fill=(255, 236, 180))
        return down(back), None, None
    def dynamic(self, img, t, camx, props):
        dx = camx * self.depths[0]; d = ImageDraw.Draw(img)
        on = random.Random(int(t * 8) * 7 + 1).random() > props.get("flicker", 0.08)
        props["_lamp_on"] = on
        d.rectangle([515 + dx, 560, 565 + dx, 600], outline=(30, 30, 30), width=4)
        d.ellipse([522 + dx, 566, 558 + dx, 596], fill=(170, 220, 255) if on else (40, 50, 60))
        if on: img.paste(add_light(img, (140 + dx, 400, 940 + dx, 1600), (140, 200, 255), 110, 80))
        else: img.paste(Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.65))
    def render_front(self, img, t, camx, props, flashes):
        img = super().render_front(img, t, camx, props, flashes)
        if props.get("tiras", False):                                                                # cortina de tiras plásticas
            lay = Image.new("L", img.size, 0); d = ImageDraw.Draw(lay)
            for k in range(9):
                x = 20 + k * 124 + math.sin(t * 1.4 + k) * 6 - camx * 1.3
                d.rectangle([x, 0, x + 100, H], fill=60)
                d.line([(x + 8, 0), (x + 8, H)], fill=140, width=3)
            img.paste((210, 230, 240), (0, 0), lay)
        return img


# ======================= CFTV (close no monitor) =======================
class Cftv(Scene):
    name = "cftv"; acoustic = "sala"; light = "tv"; grade = "frio"; amb = "zumbido"
    ground = (1500, 1900, 1.0, 1.0)
    def build(self):
        back = canvas((14, 16, 18)); d = ImageDraw.Draw(back)
        d.rectangle(PS((-M, 1500), (W + M, 1920)), fill=(150, 36, 36))                               # balcão
        d.rectangle(PS((-M, 1480), (W + M, 1510)), fill=(214, 210, 200))
        d.rounded_rectangle(PS((70, 360), (1010, 1420)), 50 * S, fill=(196, 190, 170))                 # gabinete
        d.rounded_rectangle(PS((70, 360), (1010, 1420)), 50 * S, outline=(120, 116, 104), width=8 * S)
        d.rectangle(PS((380, 1420), (700, 1490)), fill=(150, 146, 130))
        d.ellipse(PS((900, 1330), (940, 1370)), fill=(60, 60, 60))
        return down(back), None, None
    def _quadro(self, d, box, cam, t):
        x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0; c = (150, 170, 160)
        def L(a, b, cc=c, wd=3): d.line([(x0 + a[0] * w, y0 + a[1] * h), (x0 + b[0] * w, y0 + b[1] * h)], fill=cc, width=wd)
        if cam == 1:   # caixa
            d.rectangle([x0 + 0.05 * w, y0 + 0.62 * h, x0 + 0.7 * w, y0 + 0.78 * h], outline=c, width=3)
            L((0.6, 0.15), (0.95, 0.15)); L((0.6, 0.15), (0.6, 0.6))
        elif cam == 2:  # corredor
            L((0.0, 1.0), (0.4, 0.35)); L((1.0, 1.0), (0.6, 0.35)); L((0.4, 0.35), (0.6, 0.35))
            for k in range(4): L((0.1 + k * 0.06, 0.85 - k * 0.12), (0.9 - k * 0.06, 0.85 - k * 0.12), (110, 126, 120), 2)
        elif cam == 3:  # bombas
            for xx in (0.3, 0.7): d.rectangle([x0 + (xx - 0.06) * w, y0 + 0.45 * h, x0 + (xx + 0.06) * w, y0 + 0.8 * h], outline=c, width=3)
            L((0.0, 0.3), (1.0, 0.3)); L((0.0, 0.85), (1.0, 0.85))
        else:           # câmara fria
            L((0.1, 1.0), (0.38, 0.2)); L((0.9, 1.0), (0.62, 0.2))
            d.rectangle([x0 + 0.42 * w, y0 + 0.2 * h, x0 + 0.58 * w, y0 + 0.6 * h], outline=c, width=3)
        nomes = {1: "CAM1 CAIXA", 2: "CAM2 CORREDOR", 3: "CAM3 BOMBAS", 4: "CAM4 CAMARA FRIA"}
        d.text((x0 + 10, y0 + 8), nomes[cam], font=font("mono", 22 if w < 500 else 34), fill=(230, 240, 230))
    def dynamic(self, img, t, camx, props):
        d = ImageDraw.Draw(img); tela = (130, 420, 950, 1250)
        d.rectangle(tela, fill=(18, 26, 24))
        so = props.get("cam"); vul = props.get("vulto", [])
        vul = [vul] if isinstance(vul, int) and vul else (vul or [])
        boxes = {so: tela} if so else {1: (130, 420, 538, 833), 2: (542, 420, 950, 833), 3: (130, 837, 538, 1250), 4: (542, 837, 950, 1250)}
        for cam, b in boxes.items():
            self._quadro(d, b, cam, t)
            bw, bh = b[2] - b[0], b[3] - b[1]
            if cam in vul: _sombra_alta(img, b[0] + bw * 0.5, b[1] + bh * 0.92, bh * 0.8, col=(6, 8, 8))
            if cam == 1 and props.get("duplo"):                                                      # alguém atrás do caixa
                lay = Image.new("L", img.size, 0); dl = ImageDraw.Draw(lay); cx, cy = b[0] + bw * 0.38, b[1] + bh * 0.62
                dl.ellipse([cx - bh * 0.06, cy - bh * 0.34, cx + bh * 0.06, cy - bh * 0.2], fill=255)
                dl.rectangle([cx - bh * 0.09, cy - bh * 0.37, cx + bh * 0.09, cy - bh * 0.33], fill=255)      # boné
                dl.rectangle([cx - bh * 0.1, cy - bh * 0.2, cx + bh * 0.1, cy], fill=255)
                img.paste((10, 12, 12), (0, 0), lay.filter(ImageFilter.GaussianBlur(2)))
        d = ImageDraw.Draw(img)
        r = random.Random(int(t * 15)); rz = float(props.get("ruido", 0.15))
        for y in range(tela[1], tela[3], 4): d.line([(tela[0], y), (tela[2], y)], fill=(10, 16, 14), width=1)   # linhas da tela
        for _ in range(int(600 * rz)):
            x, y = r.uniform(tela[0], tela[2]), r.uniform(tela[1], tela[3]); v = r.randint(80, 220)
            d.rectangle([x, y, x + 3, y + 2], fill=(v, v, v))
        if rz > 0.5 and r.random() < rz - 0.4:                                                       # faixa de interferência
            y = r.uniform(tela[1], tela[3] - 60); d.rectangle([tela[0], y, tela[2], y + 40], fill=(200, 210, 205))
        d.line([(130, 837 - 2), (950, 837 - 2)], fill=(0, 0, 0), width=4) if not so else None
        d.line([(540, 420), (540, 1250)], fill=(0, 0, 0), width=4) if not so else None
        if int(t * 2) % 2: d.ellipse([880, 440, 904, 464], fill=(255, 40, 30))                       # REC
        d.text((790, 436), "REC", font=font("mono", 26), fill=(255, 80, 60))
        d.text((150, 1196), str(props.get("hora", "03:00:00")), font=font("mono", 36), fill=(240, 240, 230))
        img.paste(add_light(img, tela, (110, 160, 150), 60, 50))
        v, pos = props.get("_hand", (None, None))
        if v and pos: props.setdefault("_avoid", []).append(partes.braco(img, pos["ombro"], pos["mao"], v))


CENAS = (Loja, Deposito, CamaraFria, Cftv)
