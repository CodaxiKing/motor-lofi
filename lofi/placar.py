"""Placar dos comentários: abre o episódio mostrando a votação do anterior (a partir do ep. 2).

Plano no roteiro técnico:
{"type": "placar", "start": 7, "end": 14,
 "labels": {"A": "BARULHO", "B": "SILÊNCIO"},
 "votes": {"A": 1, "B": 1},                         # contados no print que o usuário manda
 "platforms": {"TikTok": 2, "Instagram": 0},        # opcional: comentários por rede
 "comments": [{"img": "placar/c1.png", "vote": "A"},                          # recorte do print (preferido)
              {"user": "Adrisia Vieira", "text": "a", "vote": "A"}, ...],   # ou redesenhado; até 5 no total
 "winner": "A",                                     # o voto registrado na bíblia (decide o empate)
 "fundo": {"scene": "carro", ...}}                  # opcional: cena desfocada atrás

Sem empate: as porcentagens sobem, os comentários pulam na tela e o card vencedor cresce com "VOCÊS ESCOLHERAM".
Empate: carimbo "EMPATE!" e uma roleta gira e para na opção `winner` ("DESEMPATE: ...").
Duração recomendada: `dur(shot)` (5,5 s sem empate, 9 s com empate).

Recortar comentários dos prints (um ou vários) — caminhos relativos à pasta do roteiro:
    python3 -m lofi.placar recortar print1.jpg x0 y0 x1 y1 series/dia-zero/placar/c1.png
"""
import sys, os
import math
from PIL import Image, ImageDraw, ImageFilter
from .core import W, H, font, text_center, ease, ease_out, c01, RED, CREAM

COR = {"A": (52, 168, 96), "B": (206, 62, 58)}
AMARELO = (255, 212, 60)
REDE_COR = {"tiktok": (37, 244, 238), "youtube": (255, 40, 40), "instagram": (225, 48, 108), "kwai": (255, 120, 0)}
T_CARDS, T_FALAS, T_RESULT = 0.3, 0.9, 2.4
T_EMPATE, T_ROLETA, T_GIRO, T_PARA = 2.4, 3.0, 3.2, 6.6


def empate(shot):
    v = shot.get("votes", {}); return v.get("A", 0) == v.get("B", 0)


def dur(shot):
    return 9.0 if empate(shot) else 5.5


def pct(shot):
    v = shot.get("votes", {}); a, b = v.get("A", 0), v.get("B", 0); tot = a + b
    if not tot: return 50, 50
    pa = round(100 * a / tot); return pa, 100 - pa


def _giro_final(shot):
    """Rotação final (graus) para o ponteiro (no alto) parar dentro da metade vencedora."""
    return 360 * 5 + (22 if shot.get("winner", "A") == "A" else 180 + 22)


def angulo(shot, rel):
    p = c01((rel - T_GIRO) / (T_PARA - T_GIRO))
    return _giro_final(shot) * (1 - (1 - p) ** 4)


def sons(shot):
    """Efeitos sonoros do plano (tempo absoluto)."""
    s0 = shot["start"]; out = [{"t": s0, "name": "whoosh"}]
    for i, _ in enumerate(shot.get("comments", [])[:5]): out.append({"t": s0 + T_FALAS + i * 0.32, "name": "notif", "gain": 0.6})
    if empate(shot):
        out.append({"t": s0 + T_EMPATE, "name": "stamp"})
        last = 0; t = T_GIRO
        while t < T_PARA:                                   # tique a cada 45° que passa pelo ponteiro
            a = angulo(shot, t)
            if int(a // 45) != last: out.append({"t": s0 + t, "name": "click", "gain": 0.5}); last = int(a // 45)
            t += 1 / 60
        out.append({"t": s0 + T_PARA + 0.05, "name": "stamp"})
    else:
        out.append({"t": s0 + T_RESULT, "name": "stamp"})
    return out


def _card(d, box, letra, label, p, cor, brilho, apagado):
    x0, y0, x1, y1 = box
    base = tuple(int(c * (0.35 if apagado else 1)) for c in cor)
    if brilho > 0:
        for k in range(4, 0, -1):
            d.rounded_rectangle([x0 - k * 7, y0 - k * 7, x1 + k * 7, y1 + k * 7], 40 + k * 6,
                                outline=tuple(min(255, int(c * 0.5 + 120)) for c in cor) + (int(60 * brilho / k),), width=7)
    d.rounded_rectangle(box, 36, fill=(16, 16, 20, 235), outline=base + (255,), width=9)
    fundo = [x0 + 9, y0 + (y1 - y0) * 0.48, x1 - 9, y1 - 9]
    d.rounded_rectangle(fundo, 28, fill=tuple(int(c * (0.3 if apagado else 0.85)) for c in cor) + (255,))
    cx = (x0 + x1) / 2
    d.ellipse([cx - 46, y0 + 36, cx + 46, y0 + 128], fill=base + (255,))
    text_center(d, letra, cx, y0 + 80, font("title", 70), (255, 255, 255))
    text_center(d, label, cx, y0 + 180, font("title", 70 if len(label) < 9 else 54), (245, 242, 235) if not apagado else (130, 128, 125), 5)
    text_center(d, f"{p}%", cx, y1 - 92, font("title", 128), (255, 255, 255) if not apagado else (150, 150, 150), 7)


_RECORTES = {}


def recorte(path, largura=620):
    """Imagem do comentário recortado do print: cantos redondos, borda e sombra, na largura certa."""
    key = (path, largura)
    if key not in _RECORTES:
        im = Image.open(path).convert("RGB")
        h = int(im.height * largura / im.width); im = im.resize((largura, h), Image.LANCZOS)
        pad = 18; out = Image.new("RGBA", (largura + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
        sh = Image.new("L", out.size, 0); ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 8, pad + largura, pad + h + 8], 26, fill=150)
        out.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(9)))
        m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, largura - 1, h - 1], 26, fill=255)
        out.paste(im, (pad, pad), m)
        ImageDraw.Draw(out).rounded_rectangle([pad, pad, pad + largura - 1, pad + h - 1], 26, outline=(255, 255, 255, 120), width=3)
        _RECORTES[key] = out
    return _RECORTES[key]


def _colar(img, b, x, y, ang, k, tag=None):
    s = 0.6 + 0.4 * ease_out(k) + 0.08 * math.sin(k * math.pi)
    b = b.resize((int(b.width * s), int(b.height * s)), Image.BICUBIC)
    if tag:
        d = ImageDraw.Draw(b); txt, cor = tag
        tb = d.textbbox((0, 0), txt, font=font("title", int(30 * s))); tl = tb[2] - tb[0] + 34 * s
        d.rounded_rectangle([b.width - tl - 30 * s, b.height - 54 * s, b.width - 18 * s, b.height - 14 * s], 16, fill=cor + (255,))
        text_center(d, txt, b.width - tl / 2 - 24 * s, b.height - 34 * s, font("title", int(30 * s)), (255, 255, 255))
    b = b.rotate(ang, Image.BICUBIC, expand=True)
    if k < 1: b.putalpha(b.getchannel("A").point(lambda a: int(a * min(1, k * 2))))
    img.alpha_composite(b, (int(x - b.width / 2), int(y - b.height / 2)))


def _bolha(img, c, x, y, ang, k, labels, base="."):
    if k <= 0: return
    if c.get("img"):
        v = c.get("vote")
        _colar(img, recorte(os.path.join(base, c["img"]), c.get("w", 560)), x, y, ang, k,
               (labels.get(v, v), COR.get(v, (120, 120, 120))) if v else None)
        return
    f_u, f_t = font("sansb", 30), font("sansb", 40)
    user, txt = "@" + c.get("user", "").replace("@", "")[:22], c.get("text", "")[:34]
    tw = max(ImageDraw.Draw(img).textbbox((0, 0), user, font=f_u)[2], ImageDraw.Draw(img).textbbox((0, 0), txt, font=f_t)[2])
    w, h = int(tw + 150), 150
    b = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    d.rounded_rectangle([10, 10, w + 10, h + 10], 30, fill=(24, 24, 28, 245), outline=(255, 255, 255, 60), width=2)
    ini = (c.get("user", "?").strip("@") or "?")[0].upper()
    v = c.get("vote", "A")
    d.ellipse([28, 30, 92, 94], fill=COR.get(v, (120, 120, 120)) + (255,))
    text_center(d, ini, 60, 62, font("title", 38), (255, 255, 255))
    d.text((108, 28), user, font=f_u, fill=(200, 200, 205))
    d.text((108, 66), txt, font=f_t, fill=(255, 255, 255))
    tag = labels.get(v, v)
    tb = d.textbbox((0, 0), tag, font=font("title", 28)); tl = tb[2] - tb[0] + 34
    d.rounded_rectangle([w - tl - 8, h - 36, w + 2, h + 2], 16, fill=COR.get(v, (120, 120, 120)) + (255,))
    text_center(d, tag, w - tl / 2 - 3, h - 17, font("title", 28), (255, 255, 255))
    s = 0.6 + 0.4 * ease_out(k) + 0.08 * math.sin(k * math.pi)
    b = b.resize((int(b.width * s), int(b.height * s)), Image.BICUBIC).rotate(ang, Image.BICUBIC, expand=True)
    if k < 1: b.putalpha(b.getchannel("A").point(lambda a: int(a * min(1, k * 2))))
    img.alpha_composite(b, (int(x - b.width / 2), int(y - b.height / 2)))


def _roleta(shot, rel, labels, alpha):
    R = 330; S = 2 * R + 40
    r = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(r); c = S / 2
    # metade A centrada no alto (-90°) quando a rotação é zero
    d.pieslice([20, 20, S - 20, S - 20], 180, 360, fill=COR["A"] + (255,), outline=(255, 255, 255, 255), width=8)
    d.pieslice([20, 20, S - 20, S - 20], 0, 180, fill=COR["B"] + (255,), outline=(255, 255, 255, 255), width=8)
    for k in range(16):
        a = math.radians(k * 22.5)
        d.line([(c + math.cos(a) * (R - 40), c + math.sin(a) * (R - 40)), (c + math.cos(a) * (R - 6), c + math.sin(a) * (R - 6))], fill=(255, 255, 255, 140), width=4)
    text_center(d, labels.get("A", "A"), c, c - R * 0.48, font("title", 62 if len(labels.get("A", "")) < 9 else 48), (255, 255, 255), 5)
    text_center(d, labels.get("B", "B"), c, c + R * 0.48, font("title", 62 if len(labels.get("B", "")) < 9 else 48), (255, 255, 255), 5)
    d.ellipse([c - 46, c - 46, c + 46, c + 46], fill=(20, 20, 24, 255), outline=(255, 255, 255, 255), width=6)
    r = r.rotate(-angulo(shot, rel), Image.BICUBIC)
    if alpha < 1: r.putalpha(r.getchannel("A").point(lambda a: int(a * alpha)))
    return r


def frame(ep, shot, t):
    rel = t - shot["start"]; labels = shot.get("labels", {"A": "A", "B": "B"}); win = shot.get("winner", "A")
    tie = empate(shot); pa, pb = pct(shot)
    # fundo: cena do episódio desfocada e escura, ou degradê
    fundo = shot.get("fundo") or (shot.get("scene") if isinstance(shot.get("scene"), dict) else None)
    if fundo:
        sc = dict(fundo, start=shot["start"], end=shot["end"])
        bg = ep.scene_frame(sc, t).filter(ImageFilter.GaussianBlur(14))
        img = Image.blend(bg, Image.new("RGB", (W, H), (6, 6, 10)), 0.62).convert("RGBA")
    else:
        img = Image.new("RGBA", (W, H), (10, 10, 16, 255))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # cabeçalho
    k = ease_out(c01(rel / 0.35)); yh = 560 - (1 - k) * 80
    tot = sum(shot.get("votes", {}).values())
    hb = d.textbbox((0, 0), "PLACAR DOS COMENTÁRIOS", font=font("title", 58))
    hw = hb[2] - hb[0] + 80
    d.rounded_rectangle([W / 2 - hw / 2, yh - 48, W / 2 + hw / 2, yh + 48], 48, fill=AMARELO + (int(255 * k),))
    text_center(d, "PLACAR DOS COMENTÁRIOS", W / 2, yh, font("title", 58), (24, 20, 10))
    text_center(d, f"{tot} {'COMENTÁRIO' if tot == 1 else 'COMENTÁRIOS'}", W / 2, yh + 92, font("title", 44), (240, 238, 230), 4)
    # cards
    kc = ease_out(c01((rel - T_CARDS) / 0.45)); conta = ease(c01((rel - T_CARDS) / 1.4))
    rel_res = T_PARA + 0.1 if tie else T_RESULT
    res = c01((rel - rel_res) / 0.35)
    roleta_on = tie and T_ROLETA + 0.3 <= rel < T_PARA + 1.3
    for key, x0, p in (("A", 80, pa), ("B", 580, pb)):
        if roleta_on: break
        y0 = 740 + (1 - kc) * 160
        ganhou = res > 0 and key == win; perdeu = res > 0 and key != win
        s = 1 + (0.06 * ease_out(res) + 0.02 * math.sin(rel * 6) * res if ganhou else 0)
        cx, cy = x0 + 210, y0 + 210
        box = [cx - 210 * s, cy - 210 * s, cx + 210 * s, cy + 210 * s]
        _card(d, box, key, labels.get(key, key), int(round(p * conta)), COR[key], res if ganhou else 0, perdeu)
    # redes
    redes = [(n, c) for n, c in shot.get("platforms", {}).items() if c]
    if redes and kc > 0:
        wch = 300 if len(redes) <= 2 else 280 if len(redes) == 3 else 220; x = W / 2 - (len(redes) * wch + (len(redes) - 1) * 20) / 2
        for n, c in redes:
            d.rounded_rectangle([x, 1200, x + wch, 1280], 40, fill=(22, 22, 26, int(235 * kc)), outline=(255, 255, 255, int(50 * kc)), width=2)
            d.ellipse([x + 22, 1220, x + 62, 1260], fill=REDE_COR.get(n.lower(), (200, 200, 200)) + (int(255 * kc),))
            d.text((x + 74, 1220), f"{n} {c}", font=font("sansb", 30 if len(redes) >= 3 else 34), fill=(255, 255, 255, int(255 * kc)))
            x += wch + 20
    img.alpha_composite(lay)
    # comentários do print pulando na tela, por cima dos cards
    spots = [(330, 1340, -4), (720, 1530, 4), (540, 1560, -2), (300, 1520, 3), (790, 1330, -3)]
    for i, c in enumerate(shot.get("comments", [])[:5]):
        kb = c01((rel - T_FALAS - i * 0.32) / 0.3)
        if tie and rel > T_ROLETA: kb *= 1 - c01((rel - T_ROLETA) / 0.3)
        if not tie and rel > T_RESULT: kb *= 1 - c01((rel - T_RESULT) / 0.25)
        x, y, a = spots[i]; _bolha(img, c, c.get("x", x), c.get("y", y), c.get("ang", a), kb, labels, ep.base)
    d = ImageDraw.Draw(img)
    # empate: carimbo + roleta
    if tie and rel >= T_EMPATE:
        ke = ease_out(c01((rel - T_EMPATE) / 0.2)); sz = int(170 - 50 * ke)
        if rel < T_ROLETA + 0.4:
            fade = 1 - c01((rel - T_ROLETA) / 0.4)
            text_center(d, "EMPATE!", W / 2, 960, font("title", sz), tuple(int(v * fade) for v in AMARELO), 10)
        if rel >= T_ROLETA:
            ka = ease_out(c01((rel - T_ROLETA) / 0.35)) * (1 - c01((rel - (T_PARA + 1.2)) / 0.4))
            if ka > 0:
                veu = Image.new("RGBA", (W, H), (0, 0, 0, int(205 * ka))); img.alpha_composite(veu)
                r = _roleta(shot, rel, labels, ka); cy = 1060
                img.alpha_composite(r, (int(W / 2 - r.width / 2), int(cy - r.height / 2)))
                d = ImageDraw.Draw(img)
                py = cy - r.height / 2 + 6        # ponteiro no alto
                d.polygon([(W / 2 - 38, py - 46), (W / 2 + 38, py - 46), (W / 2, py + 34)], fill=AMARELO + (int(255 * ka),), outline=(20, 20, 20))
                if rel < T_PARA + 0.1:
                    text_center(d, "A ROLETA DECIDE", W / 2, cy + r.height / 2 + 80, font("title", 72), tuple(int(v * ka) for v in (255, 255, 255)), 6)
    # resultado
    if res > 0:
        topo = "DESEMPATE:" if tie else "VOCÊS ESCOLHERAM"
        palavra = labels.get(win, win)
        k1 = ease_out(res); y = 1470 if tie else 1440
        text_center(d, topo, W / 2, y, font("title", 84), tuple(int(v * k1) for v in (250, 250, 248)), 8)
        sz = int(150 * (1.25 - 0.25 * k1))
        text_center(d, palavra, W / 2, y + 140, font("title", sz), tuple(int(v * k1) for v in AMARELO), 10)
    if 0 <= rel - rel_res < 0.1: img = Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.45)
    return img.convert("RGB")


if __name__ == "__main__":
    if len(sys.argv) == 8 and sys.argv[1] == "recortar":
        _, _, src, x0, y0, x1, y1, dst = sys.argv
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        Image.open(src).convert("RGB").crop(tuple(int(float(v)) for v in (x0, y0, x1, y1))).save(dst)
        print(dst)
    else:
        print(__doc__)
