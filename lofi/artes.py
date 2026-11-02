"""Artes para as redes (1080×1920, PNG), no estilo da série: agenda/maratona, aviso, meta da comunidade, resultado da meta
e ranking dos comentários. Comandos: /serie-agenda, /serie-aviso e /serie-comunidade.

    python3 -m lofi.artes series/dia-zero/artes/agenda_0211.json series/dia-zero/artes/agenda_0211.png

O JSON tem "tipo" e os campos de cada tipo (exemplos em SPEC.md, "Artes para as redes"). Campos comuns:
  "serie": "dia-zero" (pasta: usa título, personagens travados e um cenário da série no fundo), "perfil": "@seuperfil",
  "cor": [255, 196, 60] (cor de destaque; padrão amarelo).
"""
import sys, os, json, math, random
from PIL import Image, ImageDraw, ImageFilter
from .core import W, H, font, text_center

AMARELO = (255, 198, 52); VERDE = (52, 190, 110); VERMELHO = (226, 64, 58); AZUL = (16, 30, 70)
BRANCO = (246, 244, 238); CINZA = (150, 160, 185)


# ---------------- base ----------------
def _serie(dados):
    s = dados.get("serie")
    if not s: return None, {}
    pasta = s if os.path.isdir(s) else os.path.join("series", s)
    locked = {}
    p = os.path.join(pasta, "personagens.json")
    if os.path.exists(p): locked = {k: v for k, v in json.load(open(p, encoding="utf-8")).items() if not k.startswith("_")}
    return pasta, locked


def _titulo_serie(dados, pasta):
    if dados.get("titulo_serie"): return dados["titulo_serie"]
    if pasta and os.path.exists(os.path.join(pasta, "biblia.md")):
        l = open(os.path.join(pasta, "biblia.md"), encoding="utf-8").readline().strip("# \n")
        return l.split("—")[0].strip()
    return ""


def _fundo_cena(dados, escurece=0.6, blur=10):
    """Um quadro de cenário do motor, desfocado e escuro (ou degradê se não houver)."""
    cena = dados.get("cenario")
    if cena:
        try:
            from . import scenes
            sc = scenes.get(cena)
            img = sc.render_back(0.0, 0.0, {}) if hasattr(sc, "render_back") else None
            if img is not None:
                img = img.convert("RGB").resize((W, H)).filter(ImageFilter.GaussianBlur(blur))
                return Image.blend(img, Image.new("RGB", (W, H), (6, 8, 16)), escurece)
        except Exception:
            pass
    img = Image.new("RGB", (W, H), (10, 12, 24)); d = ImageDraw.Draw(img)
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=(int(14 + 10 * k), int(16 + 8 * k), int(34 + 12 * (1 - k))))
    return img


def _blueprint(cor=(18, 44, 96)):
    img = Image.new("RGB", (W, H), cor); d = ImageDraw.Draw(img)
    for y in range(H):
        k = abs(y - H / 2) / (H / 2); d.line([(0, y), (W, y)], fill=tuple(int(c * (1.15 - 0.45 * k)) for c in cor))
    for x in range(0, W, 36): d.line([(x, 0), (x, H)], fill=(255, 255, 255, 0) if False else tuple(min(255, c + 14) for c in cor), width=1)
    for y in range(0, H, 36): d.line([(0, y), (W, y)], fill=tuple(min(255, c + 14) for c in cor), width=1)
    for x in range(0, W, 180): d.line([(x, 0), (x, H)], fill=tuple(min(255, c + 26) for c in cor), width=2)
    for y in range(0, H, 180): d.line([(0, y), (W, y)], fill=tuple(min(255, c + 26) for c in cor), width=2)
    d.rectangle([40, 190, W - 40, 1780], outline=tuple(min(255, c + 40) for c in cor), width=2)
    return img


def _pilula(d, cx, cy, txt, f, fundo, cor_txt=(20, 18, 12), pad=44, esp=0):
    tb = d.textbbox((0, 0), txt, font=f); w = tb[2] - tb[0] + esp * len(txt)
    h = tb[3] - tb[1] + 36
    d.rounded_rectangle([cx - w / 2 - pad, cy - h / 2, cx + w / 2 + pad, cy + h / 2], h / 2, fill=fundo)
    _espacado(d, txt, cx, cy, f, cor_txt, esp)


def _espacado(d, txt, cx, cy, f, cor, esp=0, stroke=0):
    if not esp: text_center(d, txt, cx, cy, f, cor, stroke); return
    larg = [d.textbbox((0, 0), c, font=f)[2] for c in txt]; tot = sum(larg) + esp * (len(txt) - 1)
    x = cx - tot / 2
    for c, w in zip(txt, larg):
        tb = d.textbbox((0, 0), c, font=f)
        d.text((x, cy - (tb[1] + tb[3]) / 2), c, font=f, fill=cor, stroke_width=stroke, stroke_fill=(0, 0, 0)); x += w + esp


def _titulo(d, txt, cy, tam, cor=BRANCO, max_w=980, sombra=True):
    f = font("title", tam)
    while d.textbbox((0, 0), txt, font=f)[2] > max_w and tam > 40: tam -= 6; f = font("title", tam)
    if sombra: text_center(d, txt, W / 2 + 6, cy + 8, f, (0, 0, 0))
    text_center(d, txt, W / 2, cy, f, cor, 6)
    return tam


def _cabecalho(d, esq, dir_, cor=CINZA):
    f = font("mono", 24)
    d.text((70, 230), esq.upper(), font=f, fill=cor)
    tb = d.textbbox((0, 0), dir_.upper(), font=f); d.text((W - 70 - tb[2], 230), dir_.upper(), font=f, fill=cor)


def _quebra(d, txt, f, largura):
    linhas, atual = [], ""
    for p in txt.split():
        t = (atual + " " + p).strip()
        if d.textbbox((0, 0), t, font=f)[2] > largura and atual: linhas.append(atual); atual = p
        else: atual = t
    return linhas + ([atual] if atual else [])


def _paragrafo(d, txt, cy, f, cor=BRANCO, destaque=None, cor_dest=AMARELO, largura=860, entre=50):
    """Texto centralizado; trechos entre *asteriscos* saem na cor de destaque."""
    for i, linha in enumerate(_quebra(d, txt, f, largura)):
        pedacos = linha.split("*"); larg = sum(d.textbbox((0, 0), p, font=f)[2] for p in pedacos)
        x = W / 2 - larg / 2; y = cy + i * entre
        for k, p in enumerate(pedacos):
            d.text((x, y), p, font=f, fill=cor_dest if k % 2 else cor); x += d.textbbox((0, 0), p, font=f)[2]


# ---------------- objetos desenhados ----------------
def caixa(aberta=False, largura=720, brilho=None):
    """Baú militar lo-fi (verde, faixas de perigo, cadeado e crachá). Devolve RGBA."""
    Wc, Hc = largura, int(largura * 0.62); im = Image.new("RGBA", (Wc + 80, Hc + 220), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, y0 = 40, 170; x1, y1 = x0 + Wc, y0 + Hc; tampa = int(Hc * 0.3)
    out = (24, 28, 26); verde = (78, 96, 62); verde2 = (62, 78, 50); faixa = (214, 170, 52)
    d.ellipse([x0 - 10, y1 - 20, x1 + 10, y1 + 40], fill=(0, 0, 0, 90))
    d.rounded_rectangle([x0, y0 + tampa, x1, y1], 18, fill=verde, outline=out, width=8)
    for xs in (x0 + 40, x1 - 140):
        for k in range(4):
            d.polygon([(xs + k * 26, y0 + tampa + 20), (xs + k * 26 + 14, y0 + tampa + 20), (xs + k * 26 + 64, y1 - 20), (xs + k * 26 + 50, y1 - 20)], fill=faixa)
    for xs in (x0 + Wc * 0.3, x0 + Wc * 0.7):
        d.rectangle([xs - 24, y0 + tampa, xs + 24, y1], fill=verde2, outline=out, width=6)
    if aberta:
        cor = brilho or (255, 214, 90)
        gl = Image.new("RGBA", im.size, (0, 0, 0, 0)); dg = ImageDraw.Draw(gl)
        dg.polygon([(x0 + 40, y0 + tampa), (x1 - 40, y0 + tampa), (x1 + 60, 0), (x0 - 60, 0)], fill=cor + (120,))
        im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(30)))
        d.polygon([(x0 + 10, y0 + tampa), (x1 - 10, y0 + tampa), (x1 - 60, y0 - 90), (x0 + 60, y0 - 90)], fill=verde2, outline=out)
        d.rectangle([x0 + 20, y0 + tampa - 14, x1 - 20, y0 + tampa + 14], fill=(30, 22, 10))
    else:
        d.rounded_rectangle([x0 - 8, y0, x1 + 8, y0 + tampa], 16, fill=verde2, outline=out, width=8)
        for xs in (x0 + Wc * 0.3, x0 + Wc * 0.7):
            d.rectangle([xs - 24, y0, xs + 24, y0 + tampa], fill=verde, outline=out, width=6)
    for cx_, cy_ in ((x0, y0 + tampa), (x1, y0 + tampa), (x0, y1), (x1, y1)):
        d.rounded_rectangle([cx_ - 34, cy_ - 34, cx_ + 34, cy_ + 34], 8, fill=(70, 74, 82), outline=out, width=5)
    cx = (x0 + x1) / 2
    d.rectangle([cx - 40, y0 + tampa - 30, cx + 40, y0 + tampa + 30], fill=(70, 74, 82), outline=out, width=5)
    if not aberta:
        d.arc([cx - 34, y0 + tampa - 10, cx + 34, y0 + tampa + 70], 180, 360, fill=(120, 110, 70), width=12)
        d.rounded_rectangle([cx - 46, y0 + tampa + 30, cx + 46, y0 + tampa + 120], 12, fill=(176, 150, 70), outline=out, width=5)
        d.ellipse([cx - 10, y0 + tampa + 60, cx + 10, y0 + tampa + 80], fill=out); d.rectangle([cx - 4, y0 + tampa + 75, cx + 4, y0 + tampa + 100], fill=out)
    bx, by = x1 - 190, y1 - 120
    d.line([(x1 - 170, y0 + tampa + 20), (bx + 40, by)], fill=out, width=5); d.line([(x1 - 120, y0 + tampa + 20), (bx + 80, by)], fill=out, width=5)
    d.rounded_rectangle([bx, by, bx + 130, by + 90], 10, fill=(214, 222, 232), outline=out, width=5)
    d.line([(bx + 20, by + 70), (bx + 60, by + 20)], fill=(255, 255, 255), width=6)
    return im


# ---------------- tipos ----------------
def agenda(dados):
    pasta, _ = _serie(dados); cor = tuple(dados.get("cor", AMARELO))
    img = _fundo_cena(dados, 0.72, 14); d = ImageDraw.Draw(img)
    d.ellipse([60, 228, 84, 252], fill=VERMELHO)
    d.text((100, 222), dados.get("canto_esq", _titulo_serie(dados, pasta) or "AO VIVO").upper(), font=font("sansb", 30), fill=BRANCO)
    if dados.get("canto_dir"):
        tb = d.textbbox((0, 0), dados["canto_dir"].upper(), font=font("mono", 26))
        d.text((W - 70 - tb[2], 226), dados["canto_dir"].upper(), font=font("mono", 26), fill=(240, 90, 80))
    text_center(d, dados.get("data", "HOJE").upper(), W / 2, 350, font("sansb", 60), BRANCO, 4)
    _titulo(d, dados.get("titulo", "MARATONA").upper(), 530, 200, cor)
    if dados.get("selo"):
        f = font("sansb", 76); tb = d.textbbox((0, 0), dados["selo"].upper(), font=f); w = tb[2] - tb[0] + 140
        d.rounded_rectangle([W / 2 - w / 2 + 8, 668, W / 2 + w / 2 + 8, 792], 18, fill=(120, 70, 10))
        d.rounded_rectangle([W / 2 - w / 2, 660, W / 2 + w / 2, 784], 18, fill=cor)
        text_center(d, dados["selo"].upper(), W / 2, 722, f, (24, 18, 8))
    if dados.get("sub"): _espacado(d, dados["sub"].upper(), W / 2, 860, font("sansb", 40), (220, 222, 235), 6)
    y = 940; itens = dados.get("itens", [])
    alt = min(240, int(760 / max(1, len(itens))))
    for it in itens:
        st = it.get("status", "proximo" if it.get("proximo") else "depois")
        box = [80, y, W - 80, y + alt - 30]
        if st == "no_ar":
            d.rounded_rectangle(box, 30, fill=(22, 64, 40), outline=VERDE, width=6)
            corl, cort = VERDE, BRANCO
        elif st == "proximo":
            d.rounded_rectangle([box[0] + 6, box[1] + 10, box[2] + 6, box[3] + 10], 30, fill=(110, 60, 6))
            d.rounded_rectangle(box, 30, fill=cor); corl, cort = (40, 28, 6), (24, 18, 8)
        else:
            d.rounded_rectangle(box, 30, fill=(22, 24, 44), outline=(70, 76, 110), width=4); corl, cort = cor, BRANCO
        cy = (box[1] + box[3]) / 2
        rot = it.get("rotulo") or (f"EPISÓDIO {it.get('ep', '')}" + {"no_ar": " · JÁ SAIU", "proximo": " · O PRÓXIMO"}.get(st, ""))
        _espacado_esq(d, rot.upper(), box[0] + 50, cy - 40, font("sansb", 34), corl, 4)
        f = font("sansb", 64); t = it.get("titulo", "").upper()
        while d.textbbox((0, 0), t, font=f)[2] > (box[2] - box[0]) * 0.62 and f.size > 34: f = font("sansb", f.size - 4)
        d.text((box[0] + 50, cy + 2), t, font=f, fill=cort)
        if st == "no_ar":
            d.rounded_rectangle([box[2] - 290, cy - 76, box[2] - 50, cy - 6], 35, fill=VERDE)
            text_center(d, "✓ NO AR" if False else "NO AR", box[2] - 170, cy - 41, font("sansb", 40), (10, 30, 16))
        elif it.get("hora"):
            fh = font("title", 120 if st == "proximo" else 104); tb = d.textbbox((0, 0), it["hora"].upper(), font=fh)
            d.text((box[2] - 50 - tb[2], cy - (tb[1] + tb[3]) / 2), it["hora"].upper(), font=fh, fill=(24, 18, 8) if st == "proximo" else cor)
        y += alt
    _rodape(d, dados, cor)
    return img


def _espacado_esq(d, txt, x, cy, f, cor, esp):
    for c in txt:
        tb = d.textbbox((0, 0), c, font=f); d.text((x, cy - (tb[1] + tb[3]) / 2), c, font=f, fill=cor); x += tb[2] + esp


def _rodape(d, dados, cor):
    if dados.get("chamada", "ATIVA AS NOTIFICAÇÕES E SEGUE"):
        _espacado(d, dados.get("chamada", "ATIVA AS NOTIFICAÇÕES E SEGUE").upper(), W / 2, 1690, font("sansb", 40), BRANCO, 3)
    if dados.get("perfil"): _espacado(d, dados["perfil"].upper(), W / 2, 1750, font("sansb", 42), cor, 6)


def aviso(dados):
    pasta, locked = _serie(dados); cor = tuple(dados.get("cor", AMARELO))
    img = _fundo_cena(dados, 0.55, 3)
    from .rig import render_char
    ch = dados.get("personagem", "roberta")
    spr, anc = render_char(ch, view=dados.get("vista", "front"), emotion=dados.get("emocao", "sad"), pose=dados.get("pose", "chest"),
                           t=0.4, scale=dados.get("escala", 4.2), custom=locked.get(ch), mouth=0.2 if dados.get("emocao") in ("cry", "shock") else 0)
    topo = spr.getbbox()[1] if spr.getbbox() else 0
    luz = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(luz)
    dl.ellipse([W / 2 - 520, 380, W / 2 + 520, 1500], fill=(150, 160, 190, 70)); img = img.convert("RGBA")
    img.alpha_composite(luz.filter(ImageFilter.GaussianBlur(90)))
    img.alpha_composite(spr, (int(W / 2 - anc[0]), int(dados.get("cabeca_y", 760) - topo)))
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sombra)
    for y in range(H):
        a = int(200 * max(0, (y - 1350) / 570) ** 1.2) if y > 1350 else int(140 * max(0, (700 - y) / 500))
        ds.line([(0, y), (W, y)], fill=(4, 6, 12, min(230, a)))
    img.alpha_composite(sombra); img = img.convert("RGB"); d = ImageDraw.Draw(img)
    _pilula(d, W / 2, 470, "⚠ " + dados.get("tag", "AVISO").upper() if False else dados.get("tag", "AVISO").upper(), font("mono", 40), cor, pad=40, esp=6)
    linhas = _quebra(d, dados.get("titulo", "O EPISÓDIO DE HOJE É PESADO").upper(), font("title", 130), 900)
    for i, l in enumerate(linhas): _titulo(d, l, 590 + i * 140, 130)
    yq = 1430
    nome = (dados.get("nome_serie") or _titulo_serie(dados, pasta)).upper()
    if nome: _espacado(d, nome, W / 2, yq - 70, font("mono", 34), (210, 214, 225), 8)
    for i, l in enumerate(_quebra(d, dados.get("pergunta", "VOCÊ TÁ PREPARADO PRO QUE VAI VER?").upper(), font("title", 104), 900)):
        _titulo(d, l, yq + 30 + i * 108, 104, cor)
    return img


def meta(dados):
    pasta, _ = _serie(dados); cor = tuple(dados.get("cor", AMARELO))
    img = _blueprint(); d = ImageDraw.Draw(img)
    nome = (dados.get("nome_serie") or _titulo_serie(dados, pasta)).upper()
    _cabecalho(d, f"{nome} · META", dados.get("folha", "CAIXA DA COMUNIDADE"))
    _pilula(d, W / 2, 360, "META DA COMUNIDADE", font("sansb", 40), cor, pad=60, esp=8)
    _titulo(d, dados.get("titulo", "1.000 SALVAMENTOS").upper(), 500, 130)
    _titulo(d, dados.get("prazo", "ATÉ AS 18H").upper(), 625, 130, cor)
    d.rounded_rectangle([90, 730, W - 90, 1200], 16, fill=(30, 36, 50), outline=(130, 150, 190), width=3)
    _espacado_esq(d, ("ITEM 01 · " + dados.get("item_nome", "CAIXA DA COMUNIDADE")).upper(), 120, 765, font("mono", 26), (200, 210, 230), 3)
    cx = caixa(False, 560); img.paste(cx, (int(W / 2 - cx.width / 2), 1185 - (170 + int(560 * 0.62))), cx); d = ImageDraw.Draw(img)
    ys = 1230; cols = [("TRAVA", dados.get("trava", "1.000")), ("PRAZO", dados.get("prazo_curto", "HOJE 18H")), ("DENTRO", dados.get("dentro", "SURPRESA"))]
    d.rounded_rectangle([90, ys, W - 90, ys + 140], 16, fill=(12, 16, 30), outline=(80, 96, 140), width=3)
    cw = (W - 180) / 3
    for i, (a, b) in enumerate(cols):
        x = 90 + cw * i + cw / 2
        if i: d.line([(90 + cw * i, ys), (90 + cw * i, ys + 140)], fill=(80, 96, 140), width=3)
        _espacado(d, a, x, ys + 40, font("sansb", 26), (170, 180, 200), 5)
        f = font("title", 62)
        while d.textbbox((0, 0), b.upper(), font=f)[2] > cw - 30: f = font("title", f.size - 4)
        text_center(d, b.upper(), x, ys + 96, f, BRANCO)
    _espacado(d, dados.get("legenda_marcos", "CADA SALVAMENTO DESTRAVA UM POUCO").upper(), W / 2, 1430, font("sansb", 32), (190, 205, 235), 6)
    marcos = dados.get("marcos", [[0, "TRANCADA"], [50, "ACENDE"], [80, "DESTRAVA"], [100, "ABRE"]])
    xa, xb, yl = 150, W - 150, 1530
    d.line([(xa, yl), (xb, yl)], fill=(90, 120, 180), width=4)
    for p, lab in marcos:
        x = xa + (xb - xa) * p / 100; c = VERDE if p >= 100 else (cor if p > 0 else (170, 180, 200))
        d.ellipse([x - 50, yl - 50, x + 50, yl + 50], fill=(14, 20, 40), outline=c, width=5)
        text_center(d, f"{p}%", x, yl, font("title", 34 if p >= 100 else 40), c)
        _espacado(d, lab.upper(), x, yl + 86, font("sansb", 28), c, 4)
    _paragrafo(d, dados.get("texto", "Se a gente bater, eu libero *o que tem dentro*."), 1680, font("sansb", 40))
    if dados.get("texto2"): _paragrafo(d, dados["texto2"], 1790, font("sansb", 32), (210, 215, 230), entre=42)
    return img


def resultado(dados):
    cor = tuple(dados.get("cor", AMARELO)); atual, alvo = dados.get("atual", 0), max(1, dados.get("meta", 1000))
    p = min(100, round(100 * atual / alvo)); ok = atual >= alvo
    img = _fundo_cena(dados, 0.62, 2) if dados.get("cenario") else _blueprint((14, 18, 30)); d = ImageDraw.Draw(img)
    _pilula(d, W / 2, 380, ("CONSEGUIMOS!" if ok else "NÃO FOI DESSA VEZ"), font("sansb", 40), VERDE if ok else VERMELHO, BRANCO, pad=60, esp=8)
    _titulo(d, f"{p}%", 590, 280)
    _titulo(d, dados.get("titulo", "A CAIXA ABRIU" if ok else "A CAIXA SEGUE TRANCADA").upper(), 790, 104)
    cx = caixa(ok, 740); img.paste(cx, (int(W / 2 - cx.width / 2), 880), cx); d = ImageDraw.Draw(img)
    yb = 1500; d.rounded_rectangle([110, yb, W - 110, yb + 50], 25, fill=(40, 40, 52), outline=VERMELHO if not ok else VERDE, width=3)
    d.rounded_rectangle([110, yb, 110 + (W - 220) * p / 100, yb + 50], 25, fill=VERMELHO if not ok else VERDE)
    f = font("sansb", 30)
    d.text((112, yb + 70), "0", font=f, fill=BRANCO)
    unid = dados.get("unidade", "SALVAMENTOS").upper()
    text_center(d, f"{atual:,}".replace(",", ".") + " " + unid, W / 2, yb + 88, f, BRANCO)
    tb = d.textbbox((0, 0), f"{alvo:,}".replace(",", "."), font=f); d.text((W - 112 - tb[2], yb + 70), f"{alvo:,}".replace(",", "."), font=f, fill=BRANCO)
    txt = dados.get("texto", (f"{atual} de vocês {dados.get('verbo', 'salvaram')}. Valeu demais. " +
                              ("*O que tinha dentro sai hoje.*" if ok else "A caixa volta na próxima missão. *Fica de olho.*")))
    _paragrafo(d, txt, 1660, font("sansb", 40))
    return img


def ranking(dados):
    pasta, _ = _serie(dados); cor = tuple(dados.get("cor", AMARELO))
    img = _blueprint(); d = ImageDraw.Draw(img)
    nome = (dados.get("nome_serie") or _titulo_serie(dados, pasta)).upper()
    _cabecalho(d, f"{nome} · RANKING", dados.get("folha", "MENÇÃO HONROSA"))
    _pilula(d, W / 2, 360, f"MENÇÃO HONROSA · {dados.get('data', '')}".strip(" ·"), font("sansb", 40), cor, pad=50, esp=8)
    tit = dados.get("titulo", "OS 10 DE ONTEM").upper(); partes = tit.rsplit(" ", 1)
    f = font("title", 140); w1 = d.textbbox((0, 0), partes[0] + " ", font=f)[2]; w2 = d.textbbox((0, 0), partes[-1], font=f)[2] if len(partes) > 1 else 0
    x = W / 2 - (w1 + w2) / 2
    d.text((x, 410), partes[0] + " ", font=f, fill=BRANCO, stroke_width=4, stroke_fill=(0, 0, 0))
    if len(partes) > 1: d.text((x + w1, 410), partes[-1], font=f, fill=cor, stroke_width=4, stroke_fill=(0, 0, 0))
    _espacado(d, dados.get("sub", "RANKING DO DIA · TOP 10").upper(), W / 2, 640, font("sansb", 30), (200, 210, 235), 6)
    lista = sorted(dados.get("lista", []), key=lambda e: -e.get("pontos", 0))
    pos = []; ult = None
    for i, e in enumerate(lista):
        r = pos[-1] if pos and e.get("pontos") == ult else i + 1; pos.append(r); ult = e.get("pontos")
    lim = dados.get("top", 10)
    lista = [(p, e) for p, e in zip(pos, lista) if p <= lim]
    # empatados na última posição (3 ou mais) vão para o bloco de baixo
    ultima = lista[-1][0] if lista else 0
    bloco = [e for p, e in lista if p == ultima] if sum(1 for p, _ in lista if p == ultima) >= 3 and ultima > 1 else []
    linhas = [(p, e) for p, e in lista if not (bloco and p == ultima)]
    y = 700; alt = 88 if len(linhas) > 6 else 100
    for p, e in linhas:
        primeiro = p == 1
        box = [70, y, W - 70, y + alt - 12]
        d.rounded_rectangle(box, 14, fill=(26, 22, 8) if primeiro else (10, 16, 32), outline=cor if primeiro else (40, 56, 96), width=4 if primeiro else 2)
        cy = (box[1] + box[3]) / 2
        _ordinal(d, p, 100, cy, font("title", 64 if primeiro else 56))
        fn = font("title" if primeiro else "sansb", 56 if primeiro else 38)
        d.text((200, (cy - 44 if primeiro else cy - 30) if e.get("time") else cy - 22), e.get("nome", "")[:18], font=fn, fill=BRANCO, anchor=None)
        if e.get("time"):
            tc = tuple(e.get("cor_time", VERMELHO if e.get("time_letra", "A") == "B" else (255, 140, 60)))
            d.text((202, cy + (28 if primeiro else 22)), e["time"].upper(), font=font("sansb", 22), fill=tc)
        d.text((560, cy - 16), e.get("perfil", ""), font=font("sansb", 30), fill=(210, 215, 230))
        fp = font("title", 76 if primeiro else 62); tb = d.textbbox((0, 0), str(e.get("pontos", "")), font=fp)
        d.text((box[2] - 34 - tb[2], cy - (tb[1] + tb[3]) / 2), str(e.get("pontos", "")), font=fp, fill=cor)
        y += alt
    if bloco:
        y += 10; n = len(bloco); rows = (n + 1) // 2; hb = 120 + rows * 100
        d.rounded_rectangle([70, y, W - 70, y + hb], 22, outline=cor, width=4, fill=(10, 16, 32))
        _ordinal(d, ultima, W / 2 - 250, y + 60, font("title", 64))
        _espacado(d, "EMPATADOS COM", W / 2 + 10, y + 62, font("sansb", 30), (210, 215, 230), 6)
        text_center(d, str(bloco[0].get("pontos", "")), W / 2 + 250, y + 60, font("title", 70), cor)
        for i, e in enumerate(bloco):
            cx = W / 2 - 220 + (i % 2) * 440 if not (i == n - 1 and n % 2) else W / 2
            cy = y + 150 + (i // 2) * 100
            text_center(d, e.get("nome", "")[:16], cx, cy, font("sansb", 40), BRANCO)
            text_center(d, e.get("perfil", ""), cx, cy + 40, font("sansb", 28), (190, 200, 220))
        y += hb
    _paragrafo(d, dados.get("texto", "Hoje ainda dá tempo. *Bora pro top 10?*"), max(y + 40, 1700), font("sansb", 40))
    return img


def _ordinal(d, n, x, cy, f):
    t = str(n); tb = d.textbbox((0, 0), t, font=f)
    d.text((x - (tb[2] - tb[0]) / 2 - 10, cy - (tb[1] + tb[3]) / 2), t, font=f, fill=BRANCO)
    fo = font("title", int(f.size * 0.45)); d.text((x + (tb[2] - tb[0]) / 2 - 8, cy - (tb[3] - tb[1]) / 2 - 4), "º", font=fo, fill=BRANCO)


TIPOS = {"agenda": agenda, "maratona": agenda, "aviso": aviso, "meta": meta, "resultado": resultado, "ranking": ranking}


def gerar(dados, saida):
    img = TIPOS[dados.get("tipo", "agenda")](dados)
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    img.save(saida); return saida


if __name__ == "__main__":
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    print(gerar(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2]))
