
"""HUD (contador fixo) e legendas estilo Reels (palavra por palavra, com a palavra falada destacada)."""
from PIL import Image, ImageDraw
from .core import W, H, DEITADO, RED, CREAM, font, text_center, c01, ease_out

SUB_Y = 1500                       # faixa fixa de legenda (terço inferior)
HIGHLIGHT = (255, 214, 60)         # cor da palavra que está sendo dita
KEYWORD = (255, 92, 70)            # palavra-chave do trecho (modo redes): maior e em vermelho
REDES = False                      # modo redes: legenda na área segura do TikTok/Instagram + palavra-chave
SAFE_CX, SAFE_W, SAFE_Y_MAX = W / 2, W - 70, 1700


def set_redes(on):
    """Área segura das redes: fora da faixa de baixo (descrição/música, ~480 px) e da coluna de botões à direita (~150 px)."""
    global REDES, SUB_Y, SAFE_CX, SAFE_W, SAFE_Y_MAX
    REDES = bool(on)
    SUB_Y, SAFE_CX, SAFE_W, SAFE_Y_MAX = (1330, W / 2 - 40, W - 210, 1400) if on else (1500, W / 2, W - 70, 1700)
    if DEITADO: SUB_Y, SAFE_CX, SAFE_W, SAFE_Y_MAX = H - 150, W / 2, W * 0.72, H - 110      # tela larga: legenda embaixo, no centro


def palavras(txt):
    """[(palavra limpa, é_chave)]. *palavra* no roteiro marca a chave; sem marca, no modo redes, a mais longa (6+ letras)."""
    ws = txt.split(); out = [(w.replace("*", ""), w.startswith("*") or w.rstrip(".,!?…:;").endswith("*")) for w in ws]
    if REDES and not any(k for _, k in out) and len(out) >= 2:
        letras = [sum(ch.isalpha() for ch in w) for w, _ in out]
        i = max(range(len(out)), key=lambda j: letras[j])
        if letras[i] >= 6: out[i] = (out[i][0], True)
    return out

def hud(img, t, day="DIA 1", clock="23:40", place="APTO 904", flash=0.0):
    dy = 150 if DEITADO else 0          # tela larga: o contador sobe para o canto
    d = ImageDraw.Draw(img)
    if int(t * 2) % 2 == 0: d.ellipse([64, 214 - dy, 92, 242 - dy], fill=RED)
    d.text((108, 198 - dy), day, font=font("mono", 44), fill=RED, stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((60, 248 - dy), clock, font=font("mono", 104), fill=(230, 230, 224), stroke_width=4, stroke_fill=(0, 0, 0))
    d.line([(64, 392 - dy), (400, 392 - dy)], fill=(170, 170, 170), width=3)
    d.text((64, 402 - dy), place, font=font("mono", 32), fill=(175, 175, 175), stroke_width=3, stroke_fill=(0, 0, 0))
    if flash > 0:
        d.rectangle([50, 190 - dy, 430, 452 - dy], outline=(255, 255, 255), width=int(2 + 7 * flash))

def barras(img, t, barras):
    """Barras de recurso embaixo do contador (ENERGIA, BATERIA, FOME...). value: 0–1 ou [[tempo, valor], ...] no tempo do episódio."""
    d = ImageDraw.Draw(img, "RGBA"); dy = 150 if DEITADO else 0
    y = 470 - dy
    for b in barras:
        v = b.get("value", b.get("valor", 1.0))
        if isinstance(v, list):
            ks = sorted(v); v = ks[0][1]
            for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
                if t0 <= t <= t1: v = v0 + (v1 - v0) * (t - t0) / max(1e-6, t1 - t0); break
            else:
                if t > ks[-1][0]: v = ks[-1][1]
        v = max(0.0, min(1.0, float(v)))
        cor = tuple(b.get("color", b.get("cor", (110, 210, 110))))[:3]
        if v < 0.25 and int(t * 3) % 2 == 0: cor = (230, 70, 60)          # pouco: pisca em vermelho
        x0, w, h = 64, 336, 18
        d.text((x0, y), str(b.get("label", b.get("rotulo", "")))[:20].upper(), font=font("mono", 26), fill=(230, 230, 224), stroke_width=3, stroke_fill=(0, 0, 0))
        d.rounded_rectangle([x0, y + 36, x0 + w, y + 36 + h], 6, fill=(0, 0, 0, 170), outline=(200, 200, 200, 200), width=2)
        if v > 0: d.rounded_rectangle([x0 + 3, y + 39, x0 + 3 + (w - 6) * v, y + 33 + h], 4, fill=cor + (240,))
        y += 74


def _word_times(txt, a, b):
    words = txt.split(); tot = sum(len(w) + 1 for w in words) or 1; t = a; out = []
    for w in words:
        dd = (b - a - 0.12) * (len(w) + 1) / tot; out.append((w, t, t + dd)); t += dd
    return out

def sub_width(t, subs):
    """Largura (px) da legenda ativa em t, ou 0. Mesmo cálculo de tamanho de subtitle()."""
    d = ImageDraw.Draw(Image.new("L", (8, 8)))
    for a, b, txt, voice in subs:
        if not (a <= t < b): continue
        n = len(txt); f = font("title", 112 if n <= 16 else (90 if n <= 22 else 72))
        return min(SAFE_W, d.textbbox((0, 0), txt.replace("*", ""), font=f)[2])
    return 0


def subtitle(img, t, subs, speakers, y=None, words=True):
    """subs: lista de (ini, fim, texto, voz). speakers: {voz: {"label": "RAFA", "color": (r,g,b)}}."""
    y0 = min(y or SUB_Y, SAFE_Y_MAX)
    d = ImageDraw.Draw(img)
    for a, b, txt, voice in subs:
        if not (a <= t < b): continue
        pw = palavras(txt); limpo = " ".join(w for w, _ in pw)
        n = len(limpo)
        f = font("title", 112 if n <= 16 else (90 if n <= 22 else 72))
        sp = speakers.get(voice, {})
        base = tuple(sp.get("color", (250, 250, 248)))
        if sp.get("label"):
            text_center(d, sp["label"], SAFE_CX, y0 - 92, font("mono", 32), base, 4)
        wt = _word_times(limpo, a, b)
        def fontes(f):
            fk = font("title", int(f.size * 1.2))
            return [fk if k else f for _, k in pw]
        fs = fontes(f)
        space = d.textbbox((0, 0), " ", font=f)[2] + 18          # + o contorno (9 px de cada lado), senão as palavras grudam
        widths = [d.textbbox((0, 0), w, font=ff)[2] - d.textbbox((0, 0), w, font=ff)[0] for (w, _, _), ff in zip(wt, fs)]
        total = sum(widths) + space * (len(wt) - 1)
        if total > SAFE_W:
            f = font("title", int(f.size * SAFE_W / total)); fs = fontes(f); space = d.textbbox((0, 0), " ", font=f)[2] + 18
            widths = [d.textbbox((0, 0), w, font=ff)[2] - d.textbbox((0, 0), w, font=ff)[0] for (w, _, _), ff in zip(wt, fs)]
            total = sum(widths) + space * (len(wt) - 1)
        x = SAFE_CX - total / 2
        for (w, ws, we), wd, ff, (_, chave) in zip(wt, widths, fs, pw):
            active = words and ws <= t < we + 0.05
            seen = t >= ws
            col = (HIGHLIGHT if voice not in speakers or sp.get("color") is None else base) if active else (base if seen or not words else tuple(int(c * 0.78) for c in base))
            if active and voice in speakers and sp.get("color"): col = HIGHLIGHT
            if chave and not active and (seen or not words): col = KEYWORD
            pop = ease_out(c01((t - ws) / 0.1)) if words and active else 1.0
            if active and pop < 1:
                tmp = Image.new("RGBA", (wd + 60, 240), (0, 0, 0, 0)); td = ImageDraw.Draw(tmp)
                text_center(td, w, tmp.width / 2, 120, ff, col + (255,), 9, (0, 0, 0, 255))
                sc = 0.8 + 0.3 * pop
                tmp = tmp.resize((int(tmp.width * sc), int(tmp.height * sc)))
                img.paste(tmp, (int(x + wd / 2 - tmp.width / 2), int(y0 - tmp.height / 2)), tmp)
            else:
                yy = y0 - (6 if active else 0)
                text_center(d, w, x + wd / 2, yy, ff, col, 9)
            x += wd + space
        break

def split_subs(entries, to_video):
    """entries: (voz, src_ini, src_fim, [pedaços]) -> (ini, fim, texto, voz) no tempo do vídeo."""
    out = []
    for voice, a, b, parts in entries:
        A, B = to_video(voice, a), to_video(voice, b)
        tot = sum(len(p) for p in parts) or 1; t = A
        for p in parts:
            dd = (B - A) * len(p) / tot
            out.append((t, t + dd + 0.12, p, voice)); t += dd
    return out


# ------------------- cartão de comentário (vídeos de resposta a comentários) -------------------
def _limpa(txt):
    """Tira emojis e símbolos que a fonte não desenha (viram quadradinhos)."""
    return "".join(ch for ch in txt if ord(ch) < 0x2190 or 0x2E80 <= ord(ch) < 0xD800).strip()


def _quebra(d, txt, f, largura):
    linhas, atual = [], ""
    for w in txt.split():
        prova = (atual + " " + w).strip()
        if d.textlength(prova, font=f) <= largura or not atual: atual = prova
        else: linhas.append(atual); atual = w
    if atual: linhas.append(atual)
    return linhas


def comment_card(img, o, p):
    """Cartão estilo app: 'Respondendo a @usuario', texto do comentário e curtidas.
    o = {"user": "@ana", "text": "...", "likes": 128, "y": 520, "label": "Respondendo a"}; p = 0..1 (entrada/saída)."""
    from PIL import ImageFilter
    if p <= 0: return
    user = _limpa(o.get("user", "@seguidor")); user = user if user.startswith("@") else "@" + user
    corpo = _limpa(o.get("text", ""))
    fb, fu, fl = font("sans", 46), font("sansb", 36), font("sansb", 30)
    largura = 820; x0 = (W - largura - 80) // 2
    d0 = ImageDraw.Draw(img)
    linhas = _quebra(d0, corpo, fb, largura - 40)[:6]
    if len(_quebra(d0, corpo, fb, largura - 40)) > 6: linhas[-1] = linhas[-1].rstrip(".,!? ") + "…"
    alt = 150 + len(linhas) * 60 + (54 if o.get("likes") is not None else 10)
    y0 = int(max(470, o.get("y", 700) - alt / 2) + (1 - p) * 60)   # abaixo do contador
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    alpha = int(255 * min(1, p * 1.3))
    sombra = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle([x0 + 6, y0 + 14, x0 + largura + 86, y0 + alt + 14], 38, fill=(0, 0, 0, int(alpha * 0.45)))
    lay = Image.alpha_composite(lay, sombra.filter(ImageFilter.GaussianBlur(16))); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x0, y0, x0 + largura + 80, y0 + alt], 38, fill=(255, 255, 255, alpha))
    # avatar com a inicial, cor estável por usuário
    hue = sum(map(ord, user)) % 6
    cor = [(232, 92, 74), (66, 133, 244), (52, 168, 83), (171, 71, 188), (255, 152, 0), (0, 150, 136)][hue]
    ax, ay = x0 + 40, y0 + 34
    d.ellipse([ax, ay, ax + 68, ay + 68], fill=cor + (alpha,))
    ini = (user[1:2] or "?").upper()
    bb = d.textbbox((0, 0), ini, font=fu); d.text((ax + 34 - (bb[2] - bb[0]) / 2 - bb[0], ay + 34 - (bb[3] - bb[1]) / 2 - bb[1]), ini, font=fu, fill=(255, 255, 255, alpha))
    d.text((ax + 90, ay + 2), o.get("label", "Respondendo a"), font=fl, fill=(130, 130, 140, alpha))
    d.text((ax + 90, ay + 34), user, font=fu, fill=(20, 20, 26, alpha))
    yy = y0 + 128
    for ln in linhas:
        d.text((x0 + 40, yy), ln, font=fb, fill=(28, 28, 34, alpha)); yy += 60
    if o.get("likes") is not None:
        lk = o["likes"]; txt = f"{lk/1000:.1f} mil".replace(".", ",") if isinstance(lk, (int, float)) and lk >= 1000 else str(lk)
        hx, hy = x0 + 44, yy + 14
        d.ellipse([hx, hy, hx + 16, hy + 16], fill=(232, 60, 70, alpha)); d.ellipse([hx + 12, hy, hx + 28, hy + 16], fill=(232, 60, 70, alpha))
        d.polygon([(hx, hy + 10), (hx + 28, hy + 10), (hx + 14, hy + 28)], fill=(232, 60, 70, alpha))
        d.text((hx + 40, hy - 4), txt, font=fl, fill=(110, 110, 120, alpha))
    base = img.convert("RGBA"); base.alpha_composite(lay); img.paste(base.convert("RGB"))
