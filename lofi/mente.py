"""Cenas que mostram o que o personagem pensa e o que ele planeja.

PENSAMENTO  {"type": "pensamento", "quem": "roberta", "emotion": "fear", "estilo": "memoria" | "imaginacao" | "medo",
             "cena": {...plano de cena normal: scene, actors, props...}, "texto": "E SE ELA NÃO ESTIVER LÁ?"}
    O personagem fica em close embaixo (fundo escuro e desfocado da cena atual ou do "fundo") e um balão de pensamento
    sai da cabeça dele com a cena de dentro: uma lembrança (sépia, granulada), uma imaginação (azulada, sonhadora) ou um
    medo (vermelho, tremendo). "texto" aparece no balão em caixa alta. O balão cresce em 0,4 s e some nos 0,3 s finais.

PLANO       {"type": "plano", "titulo": "O PLANO", "fundo": "papel" | "quadro" | "mapa",
             "lugares": [{"id": "posto", "nome": "POSTO", "x": 260, "y": 1300, "icone": "casa"}, ...],
             "setas": [{"de": "posto", "para": "ponte", "t": 1.0, "dur": 1.2, "cor": "vermelho", "tracejado": false}],
             "passos": [{"t": 0.6, "texto": "1. ALARME NO CARRO"}, ...],
             "fichas": [{"char": "roberta", "caminho": ["posto", "rua", "ponte"], "t": [1.5, 4.0]}],
             "perigos": [{"x": 600, "y": 900, "t": 2.0, "texto": "HORDA"}]}
    Um mapa desenhado à mão (papel quadriculado, quadro-negro ou mapa) onde as setas se desenham, os passos aparecem
    numerados, as cabecinhas dos personagens andam pelo caminho e os perigos ganham um X vermelho. Tempos relativos ao plano.
    Ícones: casa, predio, ponte, carro, hospital, loja, porta, estrela, caveira, radio.
"""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance, ImageChops
from .core import W, H, font, text_center, ease, ease_out, c01

TINTA = (34, 30, 40)
CORES = {"vermelho": (214, 52, 46), "azul": (40, 90, 200), "verde": (40, 150, 80), "amarelo": (236, 186, 30),
         "preto": (34, 30, 40), "branco": (240, 238, 230)}
ESTILOS = {"memoria": dict(cor=(232, 196, 140), sat=0.25, k=0.45), "imaginacao": dict(cor=(150, 190, 255), sat=0.7, k=0.3),
           "medo": dict(cor=(220, 40, 40), sat=0.5, k=0.4)}
_CACHE = {}


def sons(shot):
    s = shot["start"]; typ = shot.get("type")
    if typ == "pensamento":
        return [{"t": s + 0.05, "name": "whoosh", "gain": 0.6}] + ([{"t": s + 0.2, "name": "heartbeat", "dur": 1.2}] if shot.get("estilo") == "medo" else [])
    if typ == "plano":
        out = [{"t": s + 0.05, "name": "click", "gain": 0.7}]
        out += [{"t": s + p.get("t", 0), "name": "click", "gain": 0.5} for p in shot.get("passos", [])]
        out += [{"t": s + p.get("t", 0), "name": "impact", "gain": 0.35} for p in shot.get("perigos", [])]
        return out
    return []


# ---------------------------------------------------------------- pensamento
def _nuvem(w, h, seed=3):
    """Máscara de nuvem (balão de pensamento) w×h."""
    m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
    cx, cy = w / 2, h / 2; rx, ry = w * 0.34, h * 0.31
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    n = 14
    for i in range(n):
        a = 2 * math.pi * i / n; r = (0.135 + 0.025 * math.sin(i * 2.3 + seed)) * min(w, h)
        x, y = cx + math.cos(a) * rx * 0.98, cy + math.sin(a) * ry * 0.98
        d.ellipse([x - r, y - r * 0.9, x + r, y + r * 0.9], fill=255)
    return m


def _contorno(mask, larg=10):
    grande = mask.filter(ImageFilter.MaxFilter(larg * 2 + 1)) if larg < 12 else mask.resize((mask.width // 2, mask.height // 2)).filter(ImageFilter.MaxFilter(larg + 1)).resize(mask.size)
    return ImageChops.subtract(grande, mask)


def pensamento(ep, shot, t):
    from .rig import render_char
    rel = t - shot["start"]; dur = shot["end"] - shot["start"]
    est = ESTILOS.get(shot.get("estilo", "imaginacao"), ESTILOS["imaginacao"])
    # fundo: a cena atual (ou "fundo") bem escura e desfocada
    fundo = shot.get("fundo")
    if fundo:
        base = ep.scene_frame(_sub(shot, fundo), t, t)
    else:
        base = Image.new("RGB", (W, H), (20, 22, 30))
    base = ImageEnhance.Brightness(base.filter(ImageFilter.GaussianBlur(14))).enhance(0.38)
    img = base.copy()
    # personagem em close, embaixo à esquerda
    quem = shot.get("quem")
    head = (300, 1420)
    if quem:
        custom = ep.locked.get(quem) if hasattr(ep, "locked") else None
        spr, anc = render_char(quem, view=shot.get("view", "3q"), emotion=shot.get("emotion", "neutral"), t=t, scale=4.2,
                               facing=1, custom=custom, look=-18)
        x = shot.get("x", 300); y = H + spr.height * 0.52
        img.paste(spr, (int(x - anc[0]), int(y - anc[1])), spr)
        top = y - anc[1]; head = (x + spr.width * 0.12, top + spr.height * 0.12)
    # balão
    k = ease_out(c01(rel / 0.4)) * (1 - ease(c01((rel - (dur - 0.3)) / 0.3)))
    if k <= 0.01: return img
    bw, bh = 1000, 900; bx, by = W / 2 + 30, 820
    mask = _cache(("nuvem", bw, bh), lambda: _nuvem(bw, bh))
    inner = shot.get("cena")
    if inner:
        n0 = len(ep._heads)
        cena = ep.scene_frame(_sub(shot, inner), t, t)
        cabs = ep._heads[n0:]; del ep._heads[n0:]
        # centraliza o balão em quem está na lembrança (cabeças + um pouco do corpo)
        cy_ = (sum((c[2] + c[3]) / 2 for c in cabs) / len(cabs) + H * 0.10) / H if cabs else 0.5
        zc = 1.0 + 0.05 * rel / max(0.5, dur)
        cw, ch = int(bw * 1.15 * zc), int(bw * 1.15 * zc * H / W)
        cx_ = sum((c[0] + c[1]) / 2 for c in cabs) / len(cabs) / W if cabs else 0.5
        y0c = int(min(max(0, ch * cy_ - bh / 2), ch - bh)); x0c = int(min(max(0, cw * cx_ - bw / 2), cw - bw))
        cena = cena.resize((cw, ch), Image.BILINEAR).crop((x0c, y0c, x0c + bw, y0c + bh))
    else:
        cena = Image.new("RGB", (bw, bh), (60, 64, 80))
    g = ImageOps.grayscale(cena).convert("RGB")
    cena = Image.blend(g, cena, est["sat"])
    cena = Image.blend(cena, Image.new("RGB", cena.size, est["cor"]), est["k"] * 0.5)
    if shot.get("estilo") == "memoria":
        cena = ImageChops.multiply(cena, Image.new("RGB", cena.size, (255, 236, 205)))
    if shot.get("estilo") == "medo":
        j = int(6 * math.sin(t * 40)); cena = ImageChops.offset(cena, j, 0)
    sc = 0.55 + 0.45 * k
    mw, mh = int(bw * sc), int(bh * sc)
    m2 = mask.resize((mw, mh)); c2 = cena.resize((mw, mh))
    borda = _contorno(m2, 9)
    ox, oy = int(bx - mw / 2), int(by - mh / 2 + (1 - k) * 120)
    sombra = m2.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.5))
    img.paste((0, 0, 0), (ox + 10, oy + 16), sombra)
    img.paste(c2, (ox, oy), m2)
    img.paste((246, 244, 236), (ox, oy), borda)
    # bolinhas da cabeça até o balão
    d = ImageDraw.Draw(img)
    alvo = (bx - mw * 0.28, by + mh * 0.40)
    for i, r in enumerate((16, 26, 38)):
        f = (i + 1) / 4
        px = head[0] + (alvo[0] - head[0]) * f; py = head[1] + (alvo[1] - head[1]) * f
        if k > 0.15 + i * 0.15:
            d.ellipse([px - r, py - r, px + r, py + r], fill=(246, 244, 236), outline=TINTA, width=4)
    tx = shot.get("texto")
    if tx and k > 0.6:
        f = font("title", 74); linhas = tx.upper().split("\n")
        for i, l in enumerate(linhas):
            yy = oy + mh - 110 - (len(linhas) - 1 - i) * 82
            text_center(d, l, bx, yy, f, (255, 255, 255), stroke=7, sfill=(0, 0, 0))
    rot = {"memoria": "LEMBRANÇA", "imaginacao": "E SE...", "medo": "MEDO"}.get(shot.get("estilo"))
    if rot and shot.get("rotulo", True) and k > 0.5:
        f = font("mono", 34); bb = d.textbbox((0, 0), rot, font=f); w_ = bb[2] - bb[0] + 36
        xr = ox + mw - 170 - w_
        d.rounded_rectangle([xr, oy + 110, xr + w_, oy + 162], 14, fill=(20, 20, 26))
        d.text((xr + 18, oy + 116), rot, font=f, fill=est["cor"])
    return img


def _sub(shot, cena):
    from .mapa import resolver_plano
    key = (id(shot), id(cena))
    if key not in _CACHE:
        sub = dict(cena); sub.setdefault("type", "scene")
        sub["start"] = shot["start"]; sub["end"] = shot["end"]
        sub["actors"] = [dict(a, lipsync=a.get("lipsync", False)) for a in sub.get("actors", [])]   # lembrança é muda
        sub.setdefault("camera", {"plano": "conjunto", "cortes": False}); sub["hud"] = False
        _CACHE[key] = resolver_plano(sub)
    return _CACHE[key]


def _cache(k, fn):
    if k not in _CACHE: _CACHE[k] = fn()
    return _CACHE[k]


# ---------------------------------------------------------------- plano
def _papel(tipo):
    if tipo == "quadro":
        im = Image.new("RGB", (W, H), (36, 52, 46)); d = ImageDraw.Draw(im)
        for i in range(0, W, 7): d.line([(i, 0), (i + 40, H)], fill=(40, 57, 50))
        d.rectangle([0, 0, W - 1, H - 1], outline=(110, 74, 40), width=40)
        return im, (236, 236, 226)
    if tipo == "mapa":
        im = Image.new("RGB", (W, H), (220, 204, 168)); d = ImageDraw.Draw(im)
        for y in range(0, H, 140): d.line([(0, y), (W, y + 30)], fill=(206, 188, 150), width=3)
        d.rectangle([24, 24, W - 24, H - 24], outline=(150, 120, 80), width=6)
        return im, TINTA
    im = Image.new("RGB", (W, H), (240, 236, 222)); d = ImageDraw.Draw(im)
    for x in range(0, W, 54): d.line([(x, 0), (x, H)], fill=(214, 222, 232), width=2)
    for y in range(0, H, 54): d.line([(0, y), (W, y)], fill=(214, 222, 232), width=2)
    d.line([(110, 0), (110, H)], fill=(232, 160, 160), width=3)
    return im, TINTA


def _icone(d, nome, x, y, cor):
    w = 6
    if nome in ("casa", "loja"):
        d.polygon([(x - 50, y - 6), (x, y - 56), (x + 50, y - 6)], outline=cor, width=w)
        d.rectangle([x - 40, y - 6, x + 40, y + 50], outline=cor, width=w)
        if nome == "loja": d.line([(x - 40, y + 14), (x + 40, y + 14)], fill=cor, width=w)
        else: d.rectangle([x - 12, y + 16, x + 12, y + 50], outline=cor, width=4)
    elif nome in ("predio", "hospital"):
        d.rectangle([x - 40, y - 70, x + 40, y + 50], outline=cor, width=w)
        for yy in range(-52, 40, 30):
            for xx in (-20, 6): d.rectangle([x + xx, y + yy, x + xx + 14, y + yy + 14], outline=cor, width=3)
        if nome == "hospital":
            d.line([(x, y - 104), (x, y - 76)], fill=CORES["vermelho"], width=8); d.line([(x - 14, y - 90), (x + 14, y - 90)], fill=CORES["vermelho"], width=8)
    elif nome == "ponte":
        d.arc([x - 80, y - 50, x + 80, y + 70], 180, 360, fill=cor, width=w)
        d.line([(x - 90, y + 10), (x + 90, y + 10)], fill=cor, width=w)
        for xx in (-50, 0, 50): d.line([(x + xx, y + 10), (x + xx, y - 30 + abs(xx) * 0.4)], fill=cor, width=3)
    elif nome == "carro":
        d.rounded_rectangle([x - 60, y - 14, x + 60, y + 24], 10, outline=cor, width=w)
        d.polygon([(x - 34, y - 14), (x - 20, y - 40), (x + 24, y - 40), (x + 38, y - 14)], outline=cor, width=4)
        for xx in (-34, 34): d.ellipse([x + xx - 14, y + 14, x + xx + 14, y + 42], outline=cor, width=w)
    elif nome == "porta":
        d.rectangle([x - 30, y - 60, x + 30, y + 50], outline=cor, width=w); d.ellipse([x + 12, y - 4, x + 22, y + 6], fill=cor)
    elif nome == "caveira":
        d.ellipse([x - 34, y - 40, x + 34, y + 20], outline=cor, width=w)
        for xx in (-14, 14): d.ellipse([x + xx - 9, y - 18, x + xx + 9, y], fill=cor)
        d.rectangle([x - 18, y + 18, x + 18, y + 36], outline=cor, width=4)
    elif nome == "radio":
        d.rounded_rectangle([x - 40, y - 26, x + 40, y + 34], 8, outline=cor, width=w); d.line([(x + 20, y - 26), (x + 34, y - 70)], fill=cor, width=4)
        d.ellipse([x - 26, y - 10, x + 2, y + 18], outline=cor, width=4)
    else:   # estrela
        pts = [(x + math.cos(math.radians(-90 + i * 36)) * (44 if i % 2 == 0 else 18), y + math.sin(math.radians(-90 + i * 36)) * (44 if i % 2 == 0 else 18)) for i in range(10)]
        d.polygon(pts, outline=cor, width=w)


def _seta(d, a, b, p, cor, tracejado=False, w=9):
    """Seta levemente curva de a até b, desenhada até a fração p."""
    if p <= 0: return
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    nx, ny = -(b[1] - a[1]) * 0.18, (b[0] - a[0]) * 0.18
    ctrl = (mx + nx, my + ny); n = 40; pts = []
    for i in range(int(n * p) + 1):
        u = i / n; pts.append(((1 - u) ** 2 * a[0] + 2 * (1 - u) * u * ctrl[0] + u * u * b[0], (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * ctrl[1] + u * u * b[1]))
    if len(pts) < 2: return
    if tracejado:
        for i in range(0, len(pts) - 1, 2): d.line([pts[i], pts[i + 1]], fill=cor, width=w)
    else: d.line(pts, fill=cor, width=w, joint="curve")
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    for s_ in (2.6, -2.6):
        d.line([(x2, y2), (x2 + math.cos(ang + s_) * 34, y2 + math.sin(ang + s_) * 34)], fill=cor, width=w)


def _cabeca(ep, char, d_px=110):
    from .rig import render_char
    def faz():
        custom = ep.locked.get(char) if hasattr(ep, "locked") else None
        spr, _ = render_char(char, view="front", emotion="determined", scale=1.5, custom=custom, breath=0, sway=0)
        hh = int(spr.height * 0.36); cab = spr.crop((0, 0, spr.width, hh))
        cab.thumbnail((d_px, d_px))
        out = Image.new("RGBA", (d_px + 16, d_px + 16), (0, 0, 0, 0)); od = ImageDraw.Draw(out)
        od.ellipse([0, 0, d_px + 15, d_px + 15], fill=(255, 255, 255, 255), outline=TINTA + (255,), width=5)
        out.alpha_composite(cab, ((out.width - cab.width) // 2, (out.height - cab.height) // 2 + 4))
        return out
    return _cache(("cab", char, d_px), faz)


def plano(ep, shot, t):
    rel = t - shot["start"]
    tipo = shot.get("fundo", "papel")
    base, tinta = _cache(("papel", tipo), lambda: _papel(tipo))
    img = base.copy(); d = ImageDraw.Draw(img)
    # título
    tit = shot.get("titulo", "O PLANO")
    text_center(d, tit, W / 2, 330, font("title", 120), tinta if tipo != "papel" else TINTA)
    d.line([(W / 2 - 230, 400), (W / 2 + 230 * min(1, rel / 0.5), 404)], fill=CORES["vermelho"], width=8)
    lug = {l["id"]: l for l in shot.get("lugares", [])}
    for i, l in enumerate(shot.get("lugares", [])):
        ap = c01((rel - 0.1 - i * 0.12) / 0.25)
        if ap <= 0: continue
        x, y = l["x"], l["y"]
        _icone(d, l.get("icone", "estrela"), x, y, tinta)
        f = font("mono", 40); text_center(d, l.get("nome", l["id"]).upper(), x, y + 92, f, tinta)
    for s in shot.get("setas", []):
        a, b = lug.get(s["de"]), lug.get(s["para"])
        if not a or not b: continue
        p = ease(c01((rel - s.get("t", 0.5)) / s.get("dur", 1.0)))
        _seta(d, (a["x"], a["y"] - 10), (b["x"], b["y"] - 10), p, CORES.get(s.get("cor", "vermelho"), CORES["vermelho"]), s.get("tracejado", False))
    for pg in shot.get("perigos", []):
        ap = c01((rel - pg.get("t", 1.0)) / 0.25)
        if ap <= 0: continue
        x, y, r = pg["x"], pg["y"], 46 * ease_out(ap)
        d.line([(x - r, y - r), (x + r, y + r)], fill=CORES["vermelho"], width=12); d.line([(x - r, y + r), (x + r, y - r)], fill=CORES["vermelho"], width=12)
        if pg.get("texto") and ap >= 1: text_center(d, pg["texto"].upper(), x, y + 74, font("title", 52), CORES["vermelho"])
    # passos numerados, embaixo
    passos = [p for p in shot.get("passos", []) if rel >= p.get("t", 0)]
    y0 = shot.get("passos_y", 1520)
    for i, p in enumerate(passos):
        f = font("title", 62)
        ap = ease_out(c01((rel - p.get("t", 0)) / 0.25))
        x = 140 - (1 - ap) * 60
        d.text((x, y0 + i * 80), p["texto"].upper(), font=f, fill=TINTA if tipo == "papel" else tinta)
    # fichas (cabecinhas) andando pelo caminho
    for fi in shot.get("fichas", []):
        cam = [lug[c] for c in fi.get("caminho", []) if c in lug]
        if not cam: continue
        t0, t1 = fi.get("t", [0.5, 3.0])
        u = ease(c01((rel - t0) / max(0.1, t1 - t0))) * (len(cam) - 1)
        i = min(int(u), len(cam) - 2) if len(cam) > 1 else 0; f = u - i
        if len(cam) == 1: x, y = cam[0]["x"], cam[0]["y"]
        else: x = cam[i]["x"] + (cam[i + 1]["x"] - cam[i]["x"]) * f; y = cam[i]["y"] + (cam[i + 1]["y"] - cam[i]["y"]) * f
        cab = _cabeca(ep, fi["char"])
        dy = -abs(math.sin(rel * 9)) * 10 if 0 < u < len(cam) - 1 else 0
        img.paste(cab, (int(x - cab.width / 2 + fi.get("dx", 0)), int(y - 150 + dy)), cab)
    # mão que segura a caneta (opcional): quem planeja
    return img
