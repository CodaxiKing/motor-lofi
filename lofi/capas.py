"""Capas (miniaturas) dos episódios: TikTok e Instagram (1080x1920) e YouTube (1280x720).

Estilo "miniatura de YouTube": o protagonista grande, em close, com a emoção do momento mais forte, contorno branco
para destacar do fundo; a ameaça do episódio (zumbi, vilão, criatura) atrás, escura e com brilho; o cenário do
gancho desfocado e escurecido na cor do episódio; a frase do gancho em letras grandes e o selo do episódio.

    python3 -m lofi.capas ep05.json                  -> ep05_capa_tiktok.png, ep05_capa_instagram.png, ep05_capa_youtube.png
    python3 -m lofi.capas ep05.json --youtube        -> só a do YouTube

Ajustes opcionais no JSON do episódio:
    "capa": {"quem": "roberta", "emocao": "shock", "pose": "mao_na_boca", "vista": "3q",
             "frase": "ELES ESTÃO\\nOUVINDO", "ameaca": "zombie" (ou false), "tempo": 42.5}
"""
import os, sys, json, re
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
from .core import RED, font

PERIGO = ("zombie", "fantasma", "bruxa", "monstro", "criatura", "vulto", "sombra", "scp")
ESCUROS = ("dark", "silhouette")


# ---------------- escolhas a partir do episódio ----------------
def _protagonista(ep):
    """Quem mais fala no episódio (soma do tempo das legendas); sem falas, o primeiro personagem em cena."""
    cap = ep.spec.get("capa", {})
    if cap.get("quem"): return cap["quem"]
    tempo = {}
    falam = {k for k, v in ep.spec.get("speakers", {}).items() if v.get("label") not in ("RÁDIO", "MEGAFONE", "NARRADOR")}
    for a, b, _, v in ep.subs:
        if not falam or v in falam: tempo[v] = tempo.get(v, 0) + (b - a)
    chars = {a["char"] for s in ep.shots for a in s.get("actors", [])}
    for v in sorted(tempo, key=tempo.get, reverse=True):
        if v in chars: return v
    for s in ep.shots:
        for a in s.get("actors", []):
            if not any(p in a["char"] for p in PERIGO) and not a.get("fg"): return a["char"]
    return "roberta"


def _ameaca(ep, quem):
    cap = ep.spec.get("capa", {})
    if "ameaca" in cap: return cap["ameaca"] or None
    cont = {}
    for s in ep.shots:
        for a in s.get("actors", []):
            c = a["char"]
            if c != quem and any(p in c for p in PERIGO): cont[c] = cont.get(c, 0) + 1
        cr = s.get("crowd")
        for cs in (cr if isinstance(cr, list) else [cr] if cr else []):
            c = cs.get("char", "zombie") if isinstance(cs, dict) else "zombie"
            cont[c] = cont.get(c, 0) + 3
    return max(cont, key=cont.get) if cont else None


def _gancho(ep):
    return next((s for s in ep.shots if s.get("hook")), None)


def _frase(ep):
    cap = ep.spec.get("capa", {})
    if cap.get("frase"): return cap["frase"]
    g = _gancho(ep)
    if g:
        hk = g["hook"]; txt = hk.get("text") if isinstance(hk, dict) else str(hk)
        if not txt and isinstance(hk, dict) and isinstance(hk.get("fala"), str): txt = hk["fala"]
        if txt: return txt.replace("*", "")
    return (ep.spec.get("episode_title") or ep.spec.get("series_title", "")).upper()


def _emocao(ep, quem):
    cap = ep.spec.get("capa", {})
    if cap.get("emocao"): return cap["emocao"]
    from .render import val
    for s in [_gancho(ep)] + list(ep.shots):
        if not s: continue
        for a in s.get("actors", []):
            if a["char"] == quem and a.get("emotion"):
                e = val(a["emotion"], 0.5, 0.5) if not isinstance(a["emotion"], str) else a["emotion"]
                if e in ("fear", "shock", "angry", "cry", "determined", "sad", "suspicious"): return e
    return "shock"


def _tempo_fundo(ep):
    """Um quadro do cenário mais marcante: o gancho; se ele for um close de objeto, a cena mais longa com a ameaça."""
    cap = ep.spec.get("capa", {})
    if cap.get("tempo") is not None: return float(cap["tempo"])
    g = _gancho(ep)
    from .mapa import MAPA
    cands = [s for s in ep.shots if s.get("type", "scene") == "scene" and isinstance(s.get("scene"), str)
             and MAPA.get(s["scene"], {}).get("chao") is not None]
    if g and g in cands: return (g["start"] + g["end"]) / 2
    if not cands: return ep.total * 0.4
    s = max(cands, key=lambda s: (any(any(p in a["char"] for p in PERIGO) for a in s.get("actors", [])) or bool(s.get("crowd")), s["end"] - s["start"]))
    return (s["start"] + s["end"]) / 2


# ---------------- peças da imagem ----------------
def _fundo(ep, t, w, h):
    ep.subs = []; ep.hud_state = lambda _t: None; ep.draw_redes = lambda *a: None; ep.draw_comments = lambda *a: None
    g = _gancho(ep)
    if g: g = dict(g);
    for s in ep.shots:
        if s.get("hook"): s["hook"] = dict(s["hook"], text=" ") if isinstance(s["hook"], dict) else " "
        if s["start"] <= t < s["end"]:            # só o cenário: personagem e ameaça entram desenhados por cima
            s["actors"] = [a for a in s.get("actors", []) if a.get("fg")]; s.pop("crowd", None)
            s.setdefault("camera", {}); s["camera"] = {"plano": "aberto"}
    img = ep.frame(float(t)).convert("RGB")
    fw, fh = img.size
    k = max(w / fw, h / fh); img = img.resize((int(fw * k) + 1, int(fh * k) + 1), Image.LANCZOS)
    x0 = (img.width - w) // 2; y0 = int((img.height - h) * 0.55)
    img = img.crop((x0, y0, x0 + w, y0 + h))
    img = img.resize((w // 3, h // 3)).filter(ImageFilter.GaussianBlur(2)).resize((w, h), Image.BICUBIC)
    img = ImageEnhance.Brightness(img).enhance(0.8); img = ImageEnhance.Color(img).enhance(1.25)
    tn = ep.spec.get("tint")
    cor = tuple(tn[:3]) if tn else (40, 60, 110)
    img = Image.blend(img, Image.new("RGB", (w, h), cor), 0.22)
    # vinheta forte: o centro respira, as bordas somem
    v = Image.radial_gradient("L").resize((w, h)).point(lambda p: int(min(255, p * 1.15)))
    img.paste((0, 0, 0), (0, 0), v.point(lambda p: int(p * 0.7)))
    return img


def _sprite(quem, ep, emocao, pose, vista, altura_cabeca, silhueta=False):
    from .rig import render_char, LIGHTS, char_def
    custom = ep.custom.get(quem)
    luz = LIGHTS["silhouette"] if silhueta else LIGHTS.get("night")
    spr, anc = render_char(quem, view=vista, emotion=emocao, pose=pose, t=0.4, scale=2.0, light=luz, custom=custom,
                           breath=0, sway=0, blink_force=False)
    bb = spr.getbbox() or (0, 0, spr.width, spr.height)
    # a cabeça ocupa ~ o terço de cima do corpo: mede pela largura no alto do sprite
    alpha = spr.split()[3]
    topo = bb[1]; lin = []
    for yy in range(topo, min(spr.height, topo + int((bb[3] - bb[1]) * 0.4)), 4):
        row = alpha.crop((0, yy, spr.width, yy + 1)).getbbox()
        if row: lin.append(row[2] - row[0])
    cab = max(lin) if lin else spr.width * 0.6
    k = altura_cabeca / max(1, cab)
    spr = spr.resize((max(2, int(spr.width * k)), max(2, int(spr.height * k))), Image.LANCZOS)
    spr = spr.filter(ImageFilter.UnsharpMask(radius=3, percent=120, threshold=2))
    return spr


def _contorno(spr, grossura, cor=(255, 255, 255)):
    """Contorno de destaque em volta do personagem + sombra projetada."""
    a = spr.split()[3]
    g = grossura | 1
    borda = a.filter(ImageFilter.MaxFilter(min(g, 31)))
    if g > 31: borda = borda.filter(ImageFilter.MaxFilter(min(g - 30, 31) | 1))
    pad = grossura * 3
    out = Image.new("RGBA", (spr.width + 2 * pad, spr.height + 2 * pad), (0, 0, 0, 0))
    sombra = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sombra.paste((0, 0, 0, 200), (pad + grossura, pad + grossura), borda)
    out.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(grossura)))
    out.paste(cor + (255,), (pad, pad), borda)
    out.alpha_composite(spr, (pad, pad))
    return out, pad


def _ameaca_img(quem, ep, altura_cabeca):
    spr = _sprite(quem, ep, "angry", "forward" if "zombie" in quem else "idle", "front", altura_cabeca)
    r_, g_, b_, a_ = spr.split()
    spr = Image.merge("RGBA", (ImageEnhance.Brightness(Image.merge("RGB", (r_, g_, b_))).enhance(0.62).split() + (a_,)))
    a = spr.split()[3]
    brilho = Image.new("RGBA", (spr.width + 160, spr.height + 160), (0, 0, 0, 0))
    brilho.paste((210, 30, 30, 170), (80, 80), a.filter(ImageFilter.MaxFilter(15)))
    brilho = brilho.filter(ImageFilter.GaussianBlur(34))
    brilho.alpha_composite(spr, (80, 80))
    return brilho


def _linhas(txt, n_max_palavras=3):
    if "\n" in txt: return [l.strip() for l in txt.split("\n") if l.strip()]
    ws = txt.split(); out, cur = [], []
    for w in ws:
        cur.append(w)
        if len(cur) >= n_max_palavras: out.append(" ".join(cur)); cur = []
    if cur: out.append(" ".join(cur))
    return out


def _texto_bloco(d, linhas, x, y, tam, largura, alinhamento="centro", destaque=(255, 214, 60)):
    """Frase grande com contorno grosso; a última linha em amarelo (a palavra que pesa)."""
    f = font("title", tam)
    while tam > 50 and max(d.textlength(l, font=f) for l in linhas) > largura:
        tam -= 6; f = font("title", tam)
    lh = int(tam * 1.06)
    for i, l in enumerate(linhas):
        cor = destaque if i == len(linhas) - 1 else (255, 255, 255)
        w_ = d.textlength(l, font=f)
        xx = x - w_ / 2 if alinhamento == "centro" else x
        yy = y + i * lh
        d.text((xx + 7, yy + 9), l, font=f, fill=(0, 0, 0), stroke_width=int(tam * 0.09), stroke_fill=(0, 0, 0))
        d.text((xx, yy), l, font=f, fill=cor, stroke_width=int(tam * 0.09), stroke_fill=(10, 10, 14))
    return y + len(linhas) * lh


def _selo(ep, spec_path):
    sp = ep.spec; n = sp.get("episode", "?"); tot = sp.get("episodes_total", "")
    if sp.get("formato") == "extra": return "EXTRA"
    if sp.get("formato") == "comentarios": return "VOCÊS COMENTARAM"
    return f"EPISÓDIO {n}" + (f"/{tot}" if tot else "")


def _pilula(d, txt, cx, cy, tam, alinhamento="centro"):
    f = font("title", tam); w_ = d.textlength(txt, font=f)
    x0 = cx - w_ / 2 - 26 if alinhamento == "centro" else cx
    d.rounded_rectangle([x0, cy - tam * 0.68, x0 + w_ + 52, cy + tam * 0.68], int(tam * 0.25), fill=RED)
    d.text((x0 + 26, cy), txt, font=f, fill=(255, 255, 255), anchor="lm")


# ---------------- capas ----------------
VERTICAL = {
    "tiktok":    {"titulo_y": 330, "selo_y": 470, "frase_y": 1270, "cx": 495, "largura": 840, "cabeca": 500, "cab_y": 860},
    "instagram": {"titulo_y": 400, "selo_y": 545, "frase_y": 1330, "cx": 540, "largura": 920, "cabeca": 520, "cab_y": 920},
}


def _montar(spec_path, plataforma):
    from .render import Episode
    ep = Episode(spec_path); sp = ep.spec; cap = sp.get("capa", {})
    quem = _protagonista(ep); amea = _ameaca(ep, quem); emo = _emocao(ep, quem)
    pose = cap.get("pose", "idle")
    vista = cap.get("vista", "3q")
    frase = _frase(ep); t = _tempo_fundo(ep)
    return ep, quem, amea, emo, pose, vista, frase, t


def capa_vertical(spec_path, plataforma="tiktok", out=None):
    ep, quem, amea, emo, pose, vista, frase, t = _montar(spec_path, plataforma)
    c = VERTICAL[plataforma]; W_, H_ = 1080, 1920
    img = _fundo(ep, t, W_, H_).convert("RGBA")
    if amea:
        am = _ameaca_img(amea, ep, int(c["cabeca"] * 0.62))
        img.alpha_composite(am, (int(c["cx"] + 150 - am.width / 2), int(c["cab_y"] - c["cabeca"] * 0.9 - 80)))
    spr = _sprite(quem, ep, emo, pose, vista, c["cabeca"])
    spr, pad = _contorno(spr, 14)
    img.alpha_composite(spr, (int(c["cx"] - 40 - spr.width / 2), int(c["cab_y"] - c["cabeca"] * 0.5 - pad - c["cabeca"] * 0.12)))
    # faixas escuras atrás do texto (em cima e na frase)
    som = Image.new("L", (W_, H_), 0); ds = ImageDraw.Draw(som)
    ds.rectangle([0, 0, W_, c["selo_y"] + 120], fill=170)
    ds.rectangle([0, c["frase_y"] - 40, W_, H_], fill=165)
    img.paste((0, 0, 0, 255), (0, 0), som.filter(ImageFilter.GaussianBlur(70)))
    d = ImageDraw.Draw(img)
    _texto_bloco(d, [ep.spec.get("series_title", "SÉRIE").upper()], c["cx"], c["titulo_y"] - 105, 150, c["largura"], destaque=(242, 238, 228))
    _pilula(d, _selo(ep, spec_path), c["cx"], c["selo_y"], 66)
    _texto_bloco(d, _linhas(frase, 2), c["cx"], c["frase_y"], 170, c["largura"])
    return _salvar(img.convert("RGB"), ep, spec_path, plataforma, out)


def capa_youtube(spec_path, out=None):
    ep, quem, amea, emo, pose, vista, frase, t = _montar(spec_path, "youtube")
    W_, H_ = 1280, 720
    img = _fundo(ep, t, W_, H_).convert("RGBA")
    if amea:
        am = _ameaca_img(amea, ep, 230)
        img.alpha_composite(am, (int(760 - am.width / 2), int(140 - 80)))
    spr = _sprite(quem, ep, emo, pose, vista, 400)
    spr, pad = _contorno(spr, 11)
    img.alpha_composite(spr, (int(1010 - spr.width / 2), int(290 - 200 - pad - 50)))
    som = Image.new("L", (W_, H_), 0); ds = ImageDraw.Draw(som)
    ds.rectangle([0, 0, 700, H_], fill=165)
    img.paste((0, 0, 0, 255), (0, 0), som.filter(ImageFilter.GaussianBlur(90)))
    d = ImageDraw.Draw(img)
    titulo = ep.spec.get("series_title", "SÉRIE").upper()
    f = font("title", 64); d.text((56, 52), titulo, font=f, fill=(242, 238, 228), stroke_width=5, stroke_fill=(0, 0, 0))
    _pilula(d, _selo(ep, spec_path), 56 + d.textlength(titulo, font=f) + 26, 96, 40, alinhamento="esq")
    linhas = _linhas(frase, 2)
    tam = 150 if len(linhas) <= 2 else 118
    y0 = 360 - len(linhas) * tam * 1.06 / 2 + 30
    _texto_bloco(d, linhas, 56, int(y0), tam, 640, alinhamento="esq")
    return _salvar(img.convert("RGB"), ep, spec_path, "youtube", out)


def _salvar(img, ep, spec_path, plataforma, out):
    nome = os.path.splitext(os.path.basename(spec_path))[0]
    out = out or os.path.join(ep.base, f"{nome}_capa_{plataforma}.png")
    img.save(out); print(f"capa {plataforma}:", out); return out


def todas(spec_path):
    return {"capa_tiktok": capa_vertical(spec_path, "tiktok"), "capa_instagram": capa_vertical(spec_path, "instagram"),
            "capa_youtube": capa_youtube(spec_path)}


if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    p = sys.argv[1]
    if "--youtube" in sys.argv: capa_youtube(p)
    elif "--tiktok" in sys.argv: capa_vertical(p, "tiktok")
    elif "--instagram" in sys.argv: capa_vertical(p, "instagram")
    else: todas(p)
