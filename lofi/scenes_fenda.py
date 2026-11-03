"""Cenários de fantasia urbana com portais (série Rank Zero).

    fenda       rua à noite isolada por cones e fita, com uma rachadura de luz em pé no meio do ar.
                props: aberta (0–1, quanto a Fenda abriu), cor ([r, g, b], padrão azul), pulso (0–1, força do brilho)
    masmorra    caverna de pedra por dentro da Fenda: pilares, cristais e o portal de volta no fundo.
                props: portal (True/False, o portal de volta aceso ou fechado), cor ([r, g, b]), luz (0–1, força dos cristais)
    associacao  saguão da Associação de Caçadores: balcão à esquerda, painel de ranks E a S e bandeiras.
                props: rank ("E"…"S" ou "0": a letra acesa no painel), erro (True = painel piscando em vermelho)
    trono       salão dos deuses no vazio: palco de pedra, trono vazio e fileiras de olhos no escuro.
                props: olhos (0–1, quantos olhos abertos), ocupado (True = vulto no trono), cor ([r, g, b])
"""
import math, random
from PIL import Image, ImageDraw, ImageFilter
from .core import W_D as W, H_D as H, grad, add_light, lerp, font
from .scenes import Scene, M, S, P, PS, canvas, down

AZUL = (90, 170, 255)


def _cor(props, padrao=AZUL):
    c = props.get("cor")
    return tuple(int(v) for v in c[:3]) if c else padrao


def _clarao(img, box, cor, alfa, blur):
    return img.paste(add_light(img, box, cor, blur, alfa))


def _rachadura(cx, topo, base, largura, semente=7):
    """Contorno serrilhado de uma fenda em pé (lista de pontos em tela)."""
    r = random.Random(semente); n = 13; esq, dir_ = [], []
    for k in range(n + 1):
        f = k / n; y = lerp(topo, base, f)
        meia = largura * math.sin(math.pi * f) ** 0.8
        desvio = r.uniform(-1, 1) * largura * 0.22 * math.sin(math.pi * f)
        esq.append((cx + desvio - meia * r.uniform(0.75, 1.1), y))
        dir_.append((cx + desvio + meia * r.uniform(0.75, 1.1), y))
    return esq + dir_[::-1]


# ======================= FENDA (rua com o portal) =======================
class Fenda(Scene):
    name = "fenda"; acoustic = "aberto"; light = "night"; grade = "frio"; amb = "cidade"
    ground = (1230, 1900, 0.55, 1.42)
    def build(self):
        r = random.Random(41)
        back = canvas((14, 18, 36)); d = ImageDraw.Draw(back)
        back.paste(grad(W + 2 * M, 1240, (10, 14, 34), (38, 44, 78)).resize(((W + 2 * M) * S, 1240 * S)), (0, 0))
        d = ImageDraw.Draw(back)
        x = -M
        while x < W + M:                                                                             # prédios de São Paulo
            w = r.randint(130, 240); h = r.randint(620, 1060); topo = 1240 - h
            d.rectangle(PS((x, topo), (x + w, 1240)), fill=r.choice([(26, 30, 48), (34, 36, 54), (22, 26, 42)]))
            for yy in range(topo + 34, 1190, 58):
                for xx in range(x + 20, x + w - 24, 44):
                    if r.random() < 0.2: d.rectangle(PS((xx, yy), (xx + 22, yy + 30)), fill=(226, 196, 120))
                    else: d.rectangle(PS((xx, yy), (xx + 22, yy + 30)), fill=(18, 20, 32))
            x += w + r.randint(0, 12)
        d.rectangle(PS((-M, 1240), (W + M, 1920)), fill=(38, 40, 52))                                # asfalto
        d.rectangle(PS((-M, 1240), (W + M, 1270)), fill=(70, 72, 84))                                # meio-fio
        for k in range(5):                                                                           # faixa central
            y0 = 1300 + k * 130; y1 = y0 + 62
            d.polygon(PS((530 - k * 4, y0), (550 + k * 4, y0), (556 + k * 5, y1), (524 - k * 5, y1)), fill=(170, 170, 150))
        for cx, cy, k in ((180, 1400, 1.0), (900, 1400, 1.0), (70, 1590, 1.45), (1010, 1590, 1.45)):  # cones
            d.polygon(PS((cx, cy - 92 * k), (cx + 34 * k, cy), (cx - 34 * k, cy)), fill=(232, 112, 36))
            d.rectangle(PS((cx - 18 * k, cy - 46 * k), (cx + 18 * k, cy - 28 * k)), fill=(240, 236, 226))
            d.rectangle(PS((cx - 48 * k, cy), (cx + 48 * k, cy + 12 * k)), fill=(50, 40, 34))
        d.line(PS((180, 1340), (900, 1340)), fill=(232, 200, 60), width=9 * S)                       # fita de isolamento
        return down(back), None, None
    def dynamic(self, img, t, camx, props):
        dx = camx * self.depths[0]; cor = _cor(props); ab = max(0.0, min(1.0, float(props.get("aberta", 1.0))))
        forca = float(props.get("pulso", 0.7)) * (0.82 + 0.18 * math.sin(t * 2.6))
        cx = 540 + dx
        if ab > 0.02:
            lay = Image.new("L", img.size, 0); dl = ImageDraw.Draw(lay)
            dl.polygon(_rachadura(cx, 500, 1330, 150 * ab), fill=255)
            halo = lay.filter(ImageFilter.GaussianBlur(70)).point(lambda v: int(v * min(1.0, forca * 1.2)))
            img.paste(cor, (0, 0), halo)
            img.paste(tuple(int(c * 0.28) for c in cor), (0, 0), lay)                                # o escuro lá dentro
            ImageDraw.Draw(img).line(_rachadura(cx, 500, 1330, 150 * ab) + [_rachadura(cx, 500, 1330, 150 * ab)[0]],
                                     fill=tuple(min(255, c + 110) for c in cor), width=7)
            r = random.Random(11); d = ImageDraw.Draw(img)
            for k in range(26):                                                                      # fagulhas subindo
                sp = r.uniform(30, 90); fase = r.uniform(0, 900)
                y = 1330 - (t * sp + fase) % 850; x = cx + r.uniform(-230, 230) * ab + math.sin(t + k) * 12
                d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=tuple(min(255, c + 90) for c in cor))
            _clarao(img, (cx - 460, 1180, cx + 460, 1880), cor, int(70 * forca), 110)


# ======================= MASMORRA (dentro da Fenda) =======================
class Masmorra(Scene):
    name = "masmorra"; acoustic = "grande"; light = "night"; grade = "frio"; amb = "zumbido"
    ground = (1180, 1900, 0.42, 1.42)
    def build(self):
        r = random.Random(77)
        back = canvas((14, 14, 26)); d = ImageDraw.Draw(back)
        d.rectangle(PS((-M, 0), (W + M, 1920)), fill=(24, 24, 40))
        d.polygon(PS((-M, 1920), (W + M, 1920), (660, 1160), (420, 1160)), fill=(50, 50, 70))        # chão em perspectiva
        for k in range(10):                                                                          # lajes
            f = (k + 1) / 10; y = 1160 + f ** 1.8 * 760; xa = lerp(420, -M, f ** 1.2); xb = lerp(660, W + M, f ** 1.2)
            d.line(PS((xa, y), (xb, y)), fill=(36, 36, 54), width=max(1, int(2 + f * 6)) * S)
        for j in range(-5, 6):
            d.line(PS((540 + j * 22, 1160), (540 + j * 240, 1920)), fill=(38, 38, 56), width=3 * S)
        for lado in (-1, 1):                                                                         # paredes com blocos
            for k in range(26):
                f = r.random(); y = r.uniform(120, 1560); x = 540 + lado * lerp(190, 800, f)
                w = lerp(40, 160, f); h = lerp(20, 70, f)
                d.rectangle(PS((x - w / 2, y), (x + w / 2, y + h)), fill=r.choice([(32, 32, 50), (20, 20, 34), (40, 40, 58)]))
        for f in (0.15, 0.45, 0.85):                                                                 # pilares
            for lado in (-1, 1):
                x = 540 + lado * lerp(170, 620, f); w = lerp(38, 130, f); base = lerp(1200, 1800, f)
                d.rectangle(PS((x - w / 2, 0), (x + w / 2, base)), fill=(46, 46, 66))
                d.rectangle(PS((x - w / 2, 0), (x - w / 4, base)), fill=(60, 60, 82))
                d.rectangle(PS((x - w * 0.62, base - w * 0.25), (x + w * 0.62, base + w * 0.12)), fill=(30, 30, 46))
        d.polygon(PS((470, 1170), (480, 860), (540, 760), (600, 860), (610, 1170)), fill=(10, 10, 20))  # arco do fundo
        return down(back), None, None
    def dynamic(self, img, t, camx, props):
        dx = camx * self.depths[0]; cor = _cor(props); luz = float(props.get("luz", 0.8))
        d = ImageDraw.Draw(img); r = random.Random(5)
        for x, y, k in ((80, 1580, 1.6), (1000, 1560, 1.6), (250, 1320, 0.9), (830, 1310, 0.9), (360, 1215, 0.5), (720, 1215, 0.5)):  # cristais
            bri = 0.75 + 0.25 * math.sin(t * 1.7 + x)
            c = tuple(min(255, int(v * bri + 50)) for v in cor); cx = x + camx * lerp(0.3, 1.1, k / 1.6)
            for u in (-46, 0, 42):
                alt = (120 if u == 0 else 76) * k; lg = 26 * k
                d.polygon([(cx + u * k, y - alt), (cx + u * k + lg, y), (cx + u * k - lg, y)], fill=c, outline=(235, 245, 255))
            _clarao(img, (cx - 190 * k, y - 220 * k, cx + 190 * k, y + 110 * k), cor, int(58 * luz * bri), 70)
            d = ImageDraw.Draw(img)
        if props.get("portal", True):                                                                # portal de volta no fundo
            cxp = 540 + dx; pts = _rachadura(cxp, 790, 1168, 56, semente=9)
            lay = Image.new("L", img.size, 0); ImageDraw.Draw(lay).polygon(pts, fill=255)
            img.paste(cor, (0, 0), lay.filter(ImageFilter.GaussianBlur(34)))
            ImageDraw.Draw(img).polygon(pts, fill=tuple(min(255, c + 90) for c in cor))
        d = ImageDraw.Draw(img)
        for k in range(30):                                                                          # poeira de luz
            sp = r.uniform(10, 34); x = r.uniform(0, W) + math.sin(t * 0.6 + k) * 18; y = 1700 - (t * sp + r.uniform(0, 1300)) % 1300
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=tuple(min(255, c + 70) for c in cor))


# ======================= ASSOCIAÇÃO DE CAÇADORES =======================
class Associacao(Scene):
    name = "associacao"; acoustic = "media"; light = "night"; grade = "neutro"; amb = "zumbido"
    ground = (1210, 1900, 0.52, 1.42)
    def build(self):
        back = canvas((36, 40, 52)); d = ImageDraw.Draw(back)
        d.rectangle(PS((-M, 0), (W + M, 260)), fill=(24, 26, 36))                                    # forro
        for x in (150, 540, 930): d.rectangle(PS((x - 130, 214), (x + 130, 238)), fill=(226, 232, 240))
        d.rectangle(PS((-M, 260), (W + M, 1210)), fill=(74, 82, 104))                                # parede
        d.rectangle(PS((-M, 1120), (W + M, 1210)), fill=(46, 52, 70))
        d.rectangle(PS((-M, 1210), (W + M, 1920)), fill=(116, 120, 134))                             # piso polido
        for k in range(9):
            y = 1210 + (k / 9) ** 1.7 * 710; d.line(PS((-M, y), (W + M, y)), fill=(96, 100, 114), width=4 * S)
        for j in range(-12, 13):
            d.line(PS((540 + j * 62, 1210), (540 + j * 210, 1920)), fill=(96, 100, 114), width=3 * S)
        d.rectangle(PS((360, 330), (1040, 820)), fill=(16, 20, 32))                                  # painel
        d.rectangle(PS((360, 330), (1040, 820)), outline=(140, 150, 170), width=10 * S)
        d.text(P(390, 354), "ASSOCIAÇÃO DE CAÇADORES", font=font("mono", 32 * S), fill=(190, 205, 230))
        d.rounded_rectangle(PS((30, 960), (420, 1400)), 12 * S, fill=(48, 62, 104))                  # balcão
        d.rectangle(PS((10, 930), (440, 972)), fill=(198, 200, 208))
        d.ellipse(PS((172, 1090), (278, 1196)), outline=(226, 196, 110), width=8 * S)                # selo
        d.rectangle(PS((70, 870), (170, 930)), fill=(20, 24, 34))                                    # monitor
        for x, cor in ((520, (168, 38, 44)), (960, (38, 74, 150))):                                  # bandeiras
            d.rectangle(PS((x - 58, 860), (x + 58, 1100)), fill=cor)
        return down(back), None, None
    def dynamic(self, img, t, camx, props):
        dx = camx * self.depths[0]; d = ImageDraw.Draw(img)
        atual = str(props.get("rank", "E")).upper(); erro = props.get("erro", False)
        for i, letra in enumerate(("E", "D", "C", "B", "A", "S")):
            x = 400 + i * 104 + dx; aceso = letra == atual
            d.rounded_rectangle([x, 440, x + 88, 590], 10, fill=(226, 186, 72) if aceso else (40, 46, 66))
            d.text((x + 44, 515), letra, font=font("title", 88), fill=(18, 18, 24) if aceso else (120, 130, 150), anchor="mm")
        if atual == "0" or erro:                                                                     # o rank que não está no painel
            pisca = int(t * 5) % 2 == 0
            d.rectangle([380 + dx, 620, 1020 + dx, 790], fill=(160, 22, 28) if pisca else (70, 12, 16))
            d.text((700 + dx, 705), "RANK 0" if atual == "0" else "ERRO", font=font("title", 104), fill=(255, 236, 226), anchor="mm")
            _clarao(img, (340 + dx, 300, 1060 + dx, 980), (220, 40, 40), 46 if pisca else 12, 70)
        else:
            d.text((700 + dx, 705), "PRÓXIMAS FENDAS", font=font("mono", 44), fill=(120, 200, 150), anchor="mm")


# ======================= TRONO (o salão dos deuses) =======================
class Trono(Scene):
    name = "trono"; acoustic = "grande"; light = "dark"; grade = "frio"; amb = "zumbido"
    ground = (1260, 1900, 0.5, 1.42)
    def build(self):
        back = canvas((5, 5, 12)); d = ImageDraw.Draw(back)
        back.paste(grad(W + 2 * M, H, (4, 4, 12), (22, 16, 44)).resize(((W + 2 * M) * S, H * S)), (0, 0))
        d = ImageDraw.Draw(back)
        d.polygon(PS((-M, 1920), (W + M, 1920), (820, 1240), (260, 1240)), fill=(46, 42, 68))         # palco
        d.polygon(PS((260, 1240), (820, 1240), (800, 1200), (280, 1200)), fill=(70, 64, 96))
        for k in range(7):
            f = (k + 1) / 7; y = 1240 + f ** 1.7 * 680; xa = lerp(260, -M, f); xb = lerp(820, W + M, f)
            d.line(PS((xa, y), (xb, y)), fill=(32, 30, 50), width=4 * S)
        d.polygon(PS((400, 1210), (680, 1210), (660, 840), (420, 840)), fill=(30, 26, 44))            # trono
        d.polygon(PS((440, 860), (540, 500), (640, 860)), fill=(38, 32, 54))
        d.rectangle(PS((400, 1010), (680, 1070)), fill=(62, 54, 82))
        d.rectangle(PS((370, 960), (420, 1210)), fill=(46, 40, 64)); d.rectangle(PS((660, 960), (710, 1210)), fill=(46, 40, 64))
        for x, y in ((540, 610), (480, 760), (600, 760)): d.ellipse(PS((x - 12, y - 12), (x + 12, y + 12)), fill=(226, 186, 72))
        return down(back), None, None
    def dynamic(self, img, t, camx, props):
        dx = camx * self.depths[0]; quant = max(0.0, min(1.0, float(props.get("olhos", 1.0))))
        cor = _cor(props, (232, 196, 96)); r = random.Random(33); d = ImageDraw.Draw(img)
        for fileira in range(8):                                                                     # a plateia
            y = 110 + fileira * 118; passo = 112 - fileira * 3; alt = 11 + fileira * 1.4
            x = -30 + (fileira % 2) * passo / 2
            while x < W + 40:
                abre = r.random(); fase = r.uniform(0, 7)
                if abre <= quant and not (360 < x < 720 and y > 480):
                    fecha = abs(math.sin(t * 0.5 + fase)) > 0.985                                    # piscada rara
                    ax = x + dx * (0.4 + fileira * 0.06)
                    if fecha: d.line([(ax - alt * 1.7, y), (ax + alt * 1.7, y)], fill=cor, width=2)
                    else:
                        d.ellipse([ax - alt * 1.7, y - alt * 0.8, ax + alt * 1.7, y + alt * 0.8], fill=cor)
                        olhar = math.sin(t * 0.3 + fase) * alt * 0.4
                        d.ellipse([ax - alt * 0.5 + olhar, y - alt * 0.5, ax + alt * 0.5 + olhar, y + alt * 0.5], fill=(8, 6, 14))
                x += passo
        if props.get("ocupado"):                                                                     # vulto no trono
            cx = 540 + dx; d.ellipse([cx - 58, 790, cx + 58, 906], fill=(4, 4, 10))
            d.polygon([(cx - 110, 1200), (cx + 110, 1200), (cx + 84, 910), (cx - 84, 910)], fill=(4, 4, 10))
            d.ellipse([cx - 28, 838, cx - 8, 852], fill=cor); d.ellipse([cx + 8, 838, cx + 28, 852], fill=cor)
        _clarao(img, (120 + dx, 700, 960 + dx, 1500), (140, 110, 220), 38, 120)


CENAS = (Fenda, Masmorra, Associacao, Trono)
