"""Cartela de regra do mundo (formato narrado: 3 a 5 regras por série).

REGRA  {"type": "regra", "n": 2, "texto": "NÃO CORRA NO CORREDOR", "scene": "escola", "props": {...}, "quebrada": 1.6}
    Um cartão no centro da tela ("REGRA 2" em cima, a regra em caixa alta) entra carimbado, com o som "stamp".
    Com "scene" (e "props"/"actors" como num plano normal), o cenário fica atrás, desfocado e escurecido; sem ele, fundo
    marrom-escuro. "quebrada": segundos desde o início do plano em que a regra é quebrada: o cartão treme, fica vermelho
    e ganha o carimbo "QUEBRADA" (som "impact"). Dure 2,5 a 4 s; a narração pode ler a regra por cima.
"""
import math
from PIL import Image, ImageDraw, ImageFilter
from .core import W, H, RED, CREAM, font, text_center, ease_out, c01, fast_blur

PAPEL = (236, 226, 204)
TINTA = (40, 30, 24)


def _linhas(texto, f, larg):
    out, cur = [], ""
    for w in str(texto).upper().split():
        tst = (cur + " " + w).strip()
        if f.getlength(tst) <= larg or not cur: cur = tst
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out


def frame(ep, shot, t):
    rel = t - shot["start"]
    if shot.get("scene"):
        bg = ep.scene_frame({k: v for k, v in shot.items() if k not in ("type",)}, t)
        bg = fast_blur(bg, 14)
        img = Image.blend(bg, Image.new("RGB", (W, H), (34, 22, 14)), 0.62)
    else:
        img = Image.new("RGB", (W, H), (30, 20, 14))
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse([-200, 300, W + 200, 1600], fill=90)
        img.paste((90, 60, 36), (0, 0), fast_blur(m, 120))
    qb = shot.get("quebrada")
    q = c01((rel - qb) / 0.25) if qb is not None else 0.0
    p = ease_out(c01(rel / 0.28))
    k = 1.0 + 0.5 * (1 - p)                                          # entra grande e assenta (carimbo)
    jx = math.sin(rel * 70) * 14 * (1 - c01((rel - qb - 0.25) / 0.5)) if qb is not None and rel >= qb else 0
    bw, cy = 880, 900
    f = font("title", 92); linhas = _linhas(shot.get("texto", ""), f, bw - 120)
    bh = 200 + 110 * len(linhas)
    card = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
    fundo = tuple(int(a + (b - a) * q) for a, b in zip(PAPEL, (232, 196, 186)))
    d.rounded_rectangle([0, 0, bw - 1, bh - 1], 18, fill=fundo + (255,), outline=(RED if q else TINTA) + (255,), width=8)
    d.line([(60, 150), (bw - 60, 150)], fill=TINTA + (255,), width=4)
    text_center(d, f"REGRA {shot.get('n', 1)}", bw / 2, 82, font("mono", 54), RED if q else TINTA)
    for i, ln in enumerate(linhas): text_center(d, ln, bw / 2, 230 + i * 110, f, TINTA)
    if q:
        st = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); ds = ImageDraw.Draw(st)
        ds.rounded_rectangle([bw / 2 - 330, bh / 2 - 78, bw / 2 + 330, bh / 2 + 78], 14, fill=(250, 236, 230, 215), outline=RED + (255,), width=12)
        text_center(ds, "QUEBRADA", bw / 2, bh / 2, font("title", 120), RED)
        st = st.rotate(-12, resample=Image.BICUBIC)
        st.putalpha(st.split()[3].point(lambda v: int(v * q)))
        card.alpha_composite(st)
    card = card.rotate(-2 + 2 * q, resample=Image.BICUBIC, expand=True)
    if k != 1.0: card = card.resize((int(card.width * k), int(card.height * k)), Image.BICUBIC)
    card.putalpha(card.split()[3].point(lambda v: int(v * p)))
    sh = Image.new("L", (W, H), 0)
    sh.paste(card.split()[3], (int(W / 2 - card.width / 2 + 16 + jx), int(cy - card.height / 2 + 24)))
    img.paste((0, 0, 0), (0, 0), fast_blur(sh, 18).point(lambda v: int(v * 0.6)))
    img.paste(card, (int(W / 2 - card.width / 2 + jx), int(cy - card.height / 2)), card)
    return img


def sons(shot):
    s = shot["start"]; out = [{"t": s + 0.18, "name": "stamp", "gain": 0.9}]
    if shot.get("quebrada") is not None: out += [{"t": s + shot["quebrada"], "name": "impact", "gain": 1.0}]
    return out
