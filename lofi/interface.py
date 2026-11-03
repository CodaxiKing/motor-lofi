"""Interface de jogo de sobrevivência desenhada por cima da cena (inclusive sobre "video_clip").

No episódio ("interface"):
  {"status": [{"rotulo": "ÁGUA", "valor": 1.0, "texto": "CHEIA"}, {"rotulo": "CEL", "valor": 0.58}],
   "relogio": {"dia": "SÁB", "inicio": "06:20", "seg_por_min": 8},
   "missao": {"titulo": "PREPARE O ABRIGO", "prazo": "90:00"},
   "cor": [126, 200, 255]}

No plano (opcionais):
  "status": {"CEL": 0.4, "ÁGUA": [0.9, "MEIA"]}   muda valores a partir deste plano
  "hora": "07:00"                                acerta o relógio no começo do plano
  "missao": {...} | null                         troca ou esconde a missão
  "dialogo": {"nome": "PAI · ÁUDIO", "texto": "Não saiam agora.", "retrato": "imagens/ref_pai.png"}
  "notificacao": {"app": "FAMÍLIA", "titulo": "Pai", "texto": "Mensagem de voz (0:12)"}
  "alerta": {"titulo": "PERMANEÇA EM CASA!", "texto": "Feche portas e janelas."}
  "cartela": {"titulo": "SÁBADO", "sub": "07:00"}
  "interface": false                             esconde tudo neste plano
"""
import math
import os

from PIL import Image, ImageDraw

from .core import H, W, ease, font

INK = (236, 238, 242)
DIM = (150, 158, 172)
PANEL = (12, 16, 24, 196)
RED = (226, 72, 64)


def _u():
    return min(W, H) / 1080


def _clamp01(x):
    return max(0.0, min(1.0, x))


def _status_now(ep, t):
    base = {s["rotulo"]: [float(s.get("valor", 1.0)), s.get("texto")] for s in ep.spec["interface"].get("status", [])}
    for sh in ep.shots:
        if sh["start"] > t:
            break
        for k, v in (sh.get("status") or {}).items():
            val, txt = (v if isinstance(v, (list, tuple)) else [v, None])
            base[k] = [float(val), txt]
    return base


def _clock_now(ep, t):
    cfg = ep.spec["interface"].get("relogio")
    if not cfg:
        return None
    ref_t, ref = 0.0, cfg.get("inicio", "00:00")
    for sh in ep.shots:
        if sh["start"] > t:
            break
        if sh.get("hora"):
            ref_t, ref = sh["start"], sh["hora"]
    hh, mm = map(int, ref.split(":"))
    mins = hh * 60 + mm + int((t - ref_t) / cfg.get("seg_por_min", 8))
    return cfg.get("dia", ""), f"{(mins // 60) % 24:02d}:{mins % 60:02d}"


def _mission_now(ep, t):
    m = ep.spec["interface"].get("missao")
    for sh in ep.shots:
        if sh["start"] > t:
            break
        if "missao" in sh:
            m = sh["missao"]
    return m


def _panel(layer, box, radius, fill=PANEL, outline=None, width=2):
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(box, radius, fill=fill, outline=outline, width=width)
    return d


def _text_w(d, txt, f):
    return d.textbbox((0, 0), txt, font=f)[2]


def _wrap(d, txt, f, width):
    lines, cur = [], ""
    for word in txt.split():
        test = (cur + " " + word).strip()
        if _text_w(d, test, f) <= width or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def desenhar(ep, img, shot, t):
    """Desenha a interface; devolve a imagem (RGB)."""
    if shot.get("interface") is False:
        return img
    cfg = ep.spec.get("interface") or {}
    accent = tuple(cfg.get("cor", (126, 200, 255)))
    u = _u()
    rel = t - shot["start"]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    top = int(150 * u) if H > W else int(40 * u)
    if H > W and getattr(ep, "redes", False) and ep.spec.get("episode"):
        top = int(330 * u)          # abaixo do selo "EP X" do modo redes (canto superior direito)

    if cfg.get("status"):                       # painel de status (canto superior direito)
        items = list(_status_now(ep, t).items())
        fw, row = int(300 * u), int(44 * u)
        x0, y0 = W - fw - int(36 * u), top
        _panel(layer, [x0, y0, x0 + fw, y0 + row * len(items) + int(16 * u)], int(14 * u))
        f, fs = font("mono", int(19 * u)), font("sansb", int(17 * u))
        for i, (name, (val, txt)) in enumerate(items):
            y = y0 + int(10 * u) + i * row
            d.text((x0 + int(16 * u), y + int(8 * u)), name.upper(), font=f, fill=DIM)
            bx0, bx1 = x0 + int(118 * u), x0 + fw - int(80 * u)
            by = y + int(17 * u)
            d.rounded_rectangle([bx0, by, bx1, by + int(8 * u)], int(4 * u), fill=(255, 255, 255, 40))
            col = accent if val > 0.5 else ((236, 190, 80) if val > 0.2 else RED)
            d.rounded_rectangle([bx0, by, bx0 + max(int(8 * u), int((bx1 - bx0) * _clamp01(val))), by + int(8 * u)],
                                int(4 * u), fill=col + (255,))
            label = txt or f"{int(round(val * 100))}%"
            d.text((x0 + fw - int(16 * u) - _text_w(d, label, fs), y + int(7 * u)), label, font=fs, fill=col + (255,))

    m = _mission_now(ep, t) if cfg else None
    if m:                                       # missão (canto superior esquerdo)
        f1, f2 = font("mono", int(16 * u)), font("sansb", int(22 * u))
        x0, y0 = int(36 * u), top
        w = max(_text_w(d, m["titulo"], f2), _text_w(d, "MISSÃO", f1)) + int(130 * u)
        _panel(layer, [x0, y0, x0 + w, y0 + int(74 * u)], int(14 * u), outline=accent + (120,))
        d.text((x0 + int(18 * u), y0 + int(10 * u)), "MISSÃO", font=f1, fill=accent + (255,))
        d.text((x0 + int(18 * u), y0 + int(32 * u)), m["titulo"].upper(), font=f2, fill=INK + (255,))
        if m.get("prazo"):
            d.text((x0 + w - int(18 * u) - _text_w(d, m["prazo"], f1), y0 + int(12 * u)), m["prazo"], font=f1, fill=DIM + (255,))

    clock = _clock_now(ep, t) if cfg else None
    if clock:                                   # relógio (canto inferior esquerdo)
        day, hm = clock
        f1, f2 = font("mono", int(16 * u)), font("mono", int(40 * u))
        x0, y1 = int(36 * u), H - (int(300 * u) if H > W else int(40 * u))
        w = _text_w(d, hm, f2) + int(80 * u)
        _panel(layer, [x0, y1 - int(84 * u), x0 + w, y1], int(14 * u), outline=accent + (90,))
        d.ellipse([x0 + int(18 * u), y1 - int(52 * u), x0 + int(38 * u), y1 - int(32 * u)], outline=accent + (255,), width=max(2, int(3 * u)))
        d.text((x0 + int(50 * u), y1 - int(78 * u)), day, font=f1, fill=DIM + (255,))
        d.text((x0 + int(50 * u), y1 - int(62 * u)), hm, font=f2, fill=accent + (255,))

    if shot.get("notificacao"):                 # notificação deslizando do topo
        n = shot["notificacao"]
        p = ease(_clamp01(rel / 0.35)) * (1 - ease(_clamp01((rel - (shot["end"] - shot["start"]) + 0.35) / 0.35)))
        w, h = int(760 * u), int(150 * u)
        below = top + (int(44 * u) * len(cfg.get("status", [])) + int(36 * u) if cfg.get("status") else 0)
        x0, y0 = (W - w) // 2, int(-h + (below + h + int(20 * u)) * p)     # abaixo do painel de status
        _panel(layer, [x0, y0, x0 + w, y0 + h], int(26 * u), fill=(24, 28, 36, 235))
        d.rounded_rectangle([x0 + int(22 * u), y0 + int(26 * u), x0 + int(76 * u), y0 + int(80 * u)], int(14 * u), fill=accent + (255,))
        d.text((x0 + int(96 * u), y0 + int(22 * u)), n.get("app", "MENSAGEM").upper(), font=font("mono", int(17 * u)), fill=DIM + (255,))
        d.text((x0 + int(96 * u), y0 + int(46 * u)), n.get("titulo", ""), font=font("sansb", int(28 * u)), fill=INK + (255,))
        d.text((x0 + int(96 * u), y0 + int(86 * u)), n.get("texto", ""), font=font("sans", int(24 * u)), fill=INK + (220,))

    if shot.get("dialogo"):                     # caixa de diálogo com retrato e texto letra por letra
        g = shot["dialogo"]
        w = int(960 * u) if H > W else int(1300 * u)
        h = int(210 * u)
        x0 = (W - w) // 2
        y0 = H - h - (int(420 * u) if H > W else int(70 * u))
        _panel(layer, [x0, y0, x0 + w, y0 + h], int(18 * u), fill=(10, 13, 20, 225), outline=accent + (160,))
        px = x0 + int(20 * u)
        side = h - int(40 * u)
        retrato = g.get("retrato")
        if retrato:
            path = retrato if os.path.isabs(retrato) else os.path.join(ep.base, retrato)
            if os.path.exists(path):
                im = Image.open(path).convert("RGBA")
                s = min(im.width, im.height)
                im = im.crop(((im.width - s) // 2, 0, (im.width + s) // 2, s)).resize((side, side), Image.LANCZOS)
                layer.alpha_composite(im, (px, y0 + int(20 * u)))
                d.rounded_rectangle([px, y0 + int(20 * u), px + side, y0 + int(20 * u) + side], int(10 * u), outline=accent + (200,), width=max(2, int(3 * u)))
        tx = px + (side + int(24 * u) if retrato else int(8 * u))
        fname, ftxt = font("mono", int(20 * u)), font("sansb", int(32 * u))
        name = g.get("nome", "")
        if name:
            nw = _text_w(d, name.upper(), fname) + int(24 * u)
            d.rounded_rectangle([tx, y0 + int(18 * u), tx + nw, y0 + int(50 * u)], int(8 * u), fill=accent + (255,))
            d.text((tx + int(12 * u), y0 + int(22 * u)), name.upper(), font=fname, fill=(10, 13, 20, 255))
        txt = g.get("texto", "")
        n_chars = int(rel * g.get("cps", 28))
        shown = txt[:n_chars]
        lines = _wrap(d, shown, ftxt, x0 + w - tx - int(24 * u))
        for i, line in enumerate(lines[:3]):
            d.text((tx, y0 + int(64 * u) + i * int(42 * u)), line, font=ftxt, fill=INK + (255,))
        if n_chars < len(txt) or int(rel * 2) % 2 == 0:   # cursor piscando
            last = lines[-1] if lines else ""
            cx = tx + _text_w(d, last, ftxt) + int(6 * u)
            cy = y0 + int(64 * u) + (max(0, min(2, len(lines) - 1))) * int(42 * u)
            d.rectangle([cx, cy + int(4 * u), cx + int(14 * u), cy + int(36 * u)], fill=accent + (255,))

    out = Image.alpha_composite(img.convert("RGBA"), layer)

    if shot.get("alerta"):                      # alerta de emergência (borda vermelha pulsando + cartão)
        a = shot["alerta"]
        pulse = 0.5 + 0.5 * math.sin(rel * 2 * math.pi * 1.6)
        edge = Image.new("RGBA", out.size, (0, 0, 0, 0))
        ed = ImageDraw.Draw(edge)
        for k in range(12):
            ed.rectangle([k * 6 * u, k * 6 * u, W - k * 6 * u, H - k * 6 * u], outline=RED + (int((90 - k * 7) * pulse),), width=int(6 * u))
        out = Image.alpha_composite(out, edge)
        card = Image.new("RGBA", out.size, (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        p = ease(_clamp01(rel / 0.25))
        w, h = int(820 * u), int(330 * u)
        x0, y0 = (W - w) // 2, int(H * 0.36 + (1 - p) * 60 * u)
        cd.rounded_rectangle([x0, y0, x0 + w, y0 + h], int(22 * u), fill=(20, 8, 10, int(235 * p)), outline=RED + (int(255 * p),), width=max(2, int(4 * u)))
        cx = W // 2
        cd.ellipse([cx - int(36 * u), y0 - int(36 * u), cx + int(36 * u), y0 + int(36 * u)], fill=RED + (int(255 * p),))
        cd.text((cx, y0 + int(70 * u)), "ALERTA DE EMERGÊNCIA", font=font("mono", int(20 * u)), fill=RED + (int(255 * p),), anchor="mm")
        ft = font("title", int(64 * u))
        for i, line in enumerate(_wrap(cd, a.get("titulo", "").upper(), ft, w - int(60 * u))[:2]):
            cd.text((cx, y0 + int(140 * u) + i * int(70 * u)), line, font=ft, fill=INK + (int(255 * p),), anchor="mm")
        cd.text((cx, y0 + h - int(46 * u)), a.get("texto", ""), font=font("sans", int(26 * u)), fill=INK + (int(220 * p),), anchor="mm")
        out = Image.alpha_composite(out, card)

    if shot.get("cartela"):                     # cartela de título (escurece e mostra dia/hora)
        c = shot["cartela"]
        dur = shot["end"] - shot["start"]
        p = ease(_clamp01(rel / 0.5)) * (1 - ease(_clamp01((rel - dur + 0.5) / 0.5)))
        dark = Image.new("RGBA", out.size, (0, 0, 0, int(120 * p)))
        out = Image.alpha_composite(out, dark)
        cd = ImageDraw.Draw(out)
        cd.text((W // 2, int(H * 0.46)), c.get("titulo", "").upper(), font=font("title", int(150 * u)),
                fill=INK + (int(255 * p),), anchor="mm", stroke_width=int(3 * u), stroke_fill=(0, 0, 0, int(160 * p)))
        if c.get("sub"):
            cd.text((W // 2, int(H * 0.46) + int(120 * u)), c["sub"], font=font("mono", int(56 * u)),
                    fill=accent + (int(255 * p),), anchor="mm")
    return out.convert("RGB")


def ativa(ep, shot):
    return bool(ep.spec.get("interface")) or any(k in shot for k in ("dialogo", "notificacao", "alerta", "cartela"))
