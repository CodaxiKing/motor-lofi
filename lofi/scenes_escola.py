"""Escola (O Último Sinal): sala de aula com o quadro-negro das regras e a quadra coberta. Mesmo padrão de lofi/scenes.py.

sala_aula  props: "quadro": ["REGRA 1: ...", ...] (giz no quadro; para escrever aos poucos, keyframes de lista:
           [[0, ["REGRA 1"]], [2.5, ["REGRA 1", "REGRA 2"]]]), "hora": "10:40" (relógio da parede), "sinal": 0–1 (a campainha vibra), "sombra": 0–1
           (vulto passando no vidro da porta, da esquerda para a direita).
quadra     props: "luz": 0–1 (refletores; 0 = só a luz das janelas altas), "sinal": 0–1.
"""
import math, random
from PIL import Image, ImageDraw
from .scenes import Scene, canvas, P, PS, down, S, M, W
from .core import add_light, font, lerp

GIZ = (232, 236, 226)


def _desloc(scene, camx, depth_k=0):
    """Deslocamento horizontal da camada do fundo (o que é desenhado no dynamic tem que andar junto com o quadro)."""
    return -max(-110, min(110, camx * scene.depths[depth_k]))


def _campainha(d, x, y, vib):
    d.rectangle([x - 46, y - 14, x + 46, y + 10], fill=(70, 72, 78))
    d.pieslice([x - 40, y - 4, x + 40, y + 76], 180, 360, fill=(200, 40, 34))
    d.ellipse([x - 8, y + 26, x + 8, y + 42], fill=(60, 20, 20))
    if vib > 0.05:
        for k in range(3):
            r = 56 + k * 22 + 10 * math.sin(vib * 40 + k)
            d.arc([x - r, y - r * 0.6 + 30, x + r, y + r * 0.6 + 30], 200, 340, fill=(250, 230, 200), width=4)


def _relogio(d, x, y, hora):
    d.ellipse([x - 70, y - 70, x + 70, y + 70], fill=(30, 30, 34)); d.ellipse([x - 62, y - 62, x + 62, y + 62], fill=(242, 240, 232))
    for k in range(12):
        a = k / 12 * math.tau; d.line([(x + 50 * math.sin(a), y - 50 * math.cos(a)), (x + 58 * math.sin(a), y - 58 * math.cos(a))], fill=(40, 40, 44), width=4)
    try: hh, mm = (int(v) for v in str(hora).split(":"))
    except ValueError: hh, mm = 10, 40
    am = mm / 60 * math.tau; ah = ((hh % 12) + mm / 60) / 12 * math.tau
    d.line([(x, y), (x + 30 * math.sin(ah), y - 30 * math.cos(ah))], fill=(20, 20, 24), width=8)
    d.line([(x, y), (x + 46 * math.sin(am), y - 46 * math.cos(am))], fill=(20, 20, 24), width=5)
    d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(200, 40, 34))


class SalaAula(Scene):
    """Sala vista do fundo: quadro-negro no centro (com as regras a giz), relógio em cima, campainha à direita, porta
    com vidro à esquerda e as carteiras em fileiras."""
    name = "sala_aula"; acoustic = "sala"; light = "night"; grade = "frio"
    ground = (1260, 1900, 0.62, 1.45); amb = "zumbido"
    QX0, QY0, QX1, QY1 = 170, 470, 910, 930          # o quadro (coordenadas do cenário)
    def build(self):
        back = canvas((0, 0, 0)); d = ImageDraw.Draw(back)
        d.rectangle(PS((-M, 0), (W + M, 1260)), fill=(176, 186, 170))                      # parede
        d.rectangle(PS((-M, 1000), (W + M, 1260)), fill=(96, 128, 112))                    # barra pintada
        d.rectangle(PS((-M, 990), (W + M, 1004)), fill=(70, 92, 80))
        d.rectangle(PS((-M, 1260), (W + M, 1920)), fill=(150, 116, 82))                    # piso de taco
        for k in range(14):
            y = 1260 + (k / 14) ** 1.6 * 660; d.line(PS((-M, y), (W + M, y)), fill=(132, 100, 70), width=2 * S)
        for x in range(-200, 1300, 90): d.line(PS((540 + (x - 540) * 0.45, 1260), (x, 1920)), fill=(138, 106, 74), width=2 * S)
        # quadro-negro com moldura e calha do giz
        x0, y0, x1, y1 = self.QX0, self.QY0, self.QX1, self.QY1
        d.rectangle(PS((x0 - 22, y0 - 22), (x1 + 22, y1 + 22)), fill=(120, 84, 52))
        d.rectangle(PS((x0, y0), (x1, y1)), fill=(42, 74, 58))
        r = random.Random(8)
        for _ in range(26):                                                                 # marcas de apagador
            xx, yy = r.uniform(x0 + 30, x1 - 120), r.uniform(y0 + 20, y1 - 60)
            d.ellipse(PS((xx, yy), (xx + r.uniform(80, 200), yy + r.uniform(20, 50))), fill=(48, 82, 64))
        d.rectangle(PS((x0 - 30, y1 + 22), (x1 + 30, y1 + 44)), fill=(104, 72, 44))
        d.rectangle(PS((x0 + 60, y1 + 12), (x0 + 130, y1 + 24)), fill=(232, 232, 220)); d.rectangle(PS((x1 - 200, y1 + 10), (x1 - 110, y1 + 26)), fill=(70, 60, 50))
        # mesa do professor
        d.rectangle(PS((620, 1090), (960, 1120)), fill=(110, 76, 46)); d.rectangle(PS((640, 1120), (940, 1250)), fill=(92, 64, 40))
        # porta com vidro (esquerda) e janela (direita)
        d.rectangle(PS((-60, 560), (130, 1262)), fill=(110, 80, 56)); d.rectangle(PS((-20, 640), (90, 820)), fill=(140, 160, 170))
        d.ellipse(PS((96, 900), (116, 920)), fill=(200, 190, 140))
        d.rectangle(PS((960, 380), (W + M, 980)), fill=(70, 90, 120)); d.rectangle(PS((960, 670), (W + M, 684)), fill=(176, 186, 170))
        # cartazes
        for xx, col in ((-40, (220, 190, 80)), (960, (200, 110, 90))):
            d.rectangle(PS((xx, 240 if xx < 0 else 1010), (xx + 150, 400 if xx < 0 else 1110)), fill=col)
        back = add_light(back, PS((140, 140), (940, 1100)), (230, 240, 255), 120 * S, 70)
        # carteiras (meio): três fileiras, as da frente maiores
        mid = canvas(alpha=True); d = ImageDraw.Draw(mid)
        for fila, (y, s) in enumerate(((1330, 0.62), (1480, 0.8), (1680, 1.05))):
            for cx in (150, 420, 660, 930):
                cx = 540 + (cx - 540) * (0.7 + 0.3 * s); w, h = 150 * s, 26 * s
                if fila == 2 and 300 < cx < 780: continue                                  # corredor livre no meio
                d.rectangle(PS((cx - w, y - h), (cx + w, y)), fill=(170, 130, 80, 255))
                d.rectangle(PS((cx - w, y), (cx + w, y + 10 * s)), fill=(120, 88, 54, 255))
                for lx in (cx - w + 14 * s, cx + w - 22 * s): d.rectangle(PS((lx, y), (lx + 8 * s, y + 120 * s)), fill=(60, 62, 70, 255))
                d.rectangle(PS((cx - 70 * s, y - h - 110 * s), (cx + 70 * s, y - h - 30 * s)), fill=(70, 96, 140, 255))   # encosto
        return down(back), down(mid), None
    def dynamic(self, img, t, camx, props):
        d = ImageDraw.Draw(img); dx = _desloc(self, camx)
        linhas = props.get("quadro") or []
        if isinstance(linhas, str): linhas = [linhas]
        n = max(1, len(linhas)); fs = int(min(64, 380 / n)); larg = self.QX1 - self.QX0 - 70
        while fs > 18 and max((font("sansb", fs).getlength(str(ln)) for ln in linhas), default=0) > larg: fs -= 2
        f = font("sansb", fs)
        for k, ln in enumerate(linhas):
            yy = self.QY0 + 40 + k * (self.QY1 - self.QY0 - 60) / n
            rr = random.Random(k * 31)
            d.text((self.QX0 + 40 + dx + rr.uniform(-6, 6), yy + rr.uniform(-4, 4)), str(ln), font=f, fill=GIZ)
        _relogio(d, 540 + dx, 330, props.get("hora", "10:40"))
        _campainha(d, 960 + dx, 240, float(props.get("sinal", 0) or 0) * (0.6 + 0.4 * math.sin(t * 60)))
        sb = props.get("sombra")
        if sb:
            sx = lerp(-30, 110, float(sb)) + dx
            d.ellipse([sx - 30, 660, sx + 30, 720], fill=(30, 34, 40)); d.rectangle([sx - 40, 712, sx + 40, 830], fill=(30, 34, 40))


class Quadra(Scene):
    """Quadra coberta vista da linha de fundo: piso de madeira com as linhas, gol de futsal no fundo, arquibancada à
    esquerda, janelas altas e refletores."""
    name = "quadra"; acoustic = "grande"; light = "night"; grade = "frio"
    ground = (1180, 1900, 0.5, 1.45); amb = "eco"
    def build(self):
        back = canvas((0, 0, 0)); d = ImageDraw.Draw(back)
        d.rectangle(PS((-M, 0), (W + M, 1180)), fill=(86, 92, 110))                         # parede do fundo
        for x in range(-M, W + M, 180):                                                     # janelas altas
            d.rectangle(PS((x + 20, 120), (x + 150, 420)), fill=(120, 150, 190)); d.line(PS((x + 85, 120), (x + 85, 420)), fill=(70, 76, 90), width=6 * S)
        for x in range(-M, W + M, 60): d.line(PS((x, 0), (x + 30, 90)), fill=(64, 68, 82), width=4 * S)   # treliça do teto
        d.rectangle(PS((-M, 980), (W + M, 1180)), fill=(196, 92, 54))                      # faixa pintada
        d.text(P(330, 1010), "E.E. PROF.ª MARIA DAS DORES", font=font("title", 44 * S), fill=(240, 220, 200))
        d.polygon(PS((-M, 1920), (W + M, 1920), (W + M, 1180), (-M, 1180)), fill=(196, 150, 96))   # piso
        for k in range(18):
            y = 1180 + (k / 18) ** 1.5 * 740; d.line(PS((-M, y), (W + M, y)), fill=(184, 138, 88), width=2 * S)
        lc = (240, 240, 236)
        d.line(PS((-M, 1230), (W + M, 1230)), fill=lc, width=5 * S)                          # linha de fundo
        d.line(PS((230, 1230), (-200, 1920)), fill=lc, width=6 * S); d.line(PS((850, 1230), (1280, 1920)), fill=lc, width=6 * S)
        d.arc(PS((300, 1140), (780, 1420)), 0, 180, fill=lc, width=6 * S)                    # área
        d.ellipse(PS((530, 1440), (550, 1452)), fill=lc)
        # gol de futsal
        d.rectangle(PS((410, 1060), (670, 1232)), outline=(240, 240, 240), width=10 * S)
        for x in range(420, 670, 22): d.line(PS((x, 1066), (x + 10, 1226)), fill=(200, 200, 206), width=2 * S)
        for y in range(1074, 1230, 22): d.line(PS((414, y), (666, y)), fill=(200, 200, 206), width=2 * S)
        # arquibancada (esquerda)
        for k in range(6):
            y = 1080 + k * 90; xr = 170 + k * 46
            d.polygon(PS((-M, y), (xr, y + 40), (xr, y + 90), (-M, y + 60)), fill=(150 - k * 8, 156 - k * 8, 170 - k * 8))
        mid = canvas(alpha=True); d = ImageDraw.Draw(mid)
        for x in (180, 540, 900):                                                           # refletores
            d.rectangle(PS((x - 90, 40), (x + 90, 70)), fill=(220, 226, 236, 255))
        mid = add_light(mid, PS((-200, 0), (1280, 700)), (240, 244, 255), 120 * S, 50)
        return down(back), down(mid), None
    def dynamic(self, img, t, camx, props):
        luz = props.get("luz", 1.0)
        if luz is not None and float(luz) < 1:
            img.paste(Image.blend(img, Image.new("RGB", img.size, (8, 10, 20)), 0.55 * (1 - float(luz))))
        vib = float(props.get("sinal", 0) or 0)
        if vib: _campainha(ImageDraw.Draw(img), 960 + _desloc(self, camx), 560, vib * (0.6 + 0.4 * math.sin(t * 60)))


CENAS = (SalaAula, Quadra)
