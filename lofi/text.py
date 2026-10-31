
"""HUD (contador fixo) e legendas estilo Reels (palavra por palavra, com a palavra falada destacada)."""
from PIL import Image, ImageDraw
from .core import W, H, RED, CREAM, font, text_center, c01, ease_out

SUB_Y = 1500                       # faixa fixa de legenda (terço inferior)
HIGHLIGHT = (255, 214, 60)         # cor da palavra que está sendo dita

def hud(img, t, day="DIA 1", clock="23:40", place="APTO 904", flash=0.0):
    d = ImageDraw.Draw(img)
    if int(t * 2) % 2 == 0: d.ellipse([64, 214, 92, 242], fill=RED)
    d.text((108, 198), day, font=font("mono", 44), fill=RED, stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((60, 248), clock, font=font("mono", 104), fill=(230, 230, 224), stroke_width=4, stroke_fill=(0, 0, 0))
    d.line([(64, 392), (400, 392)], fill=(170, 170, 170), width=3)
    d.text((64, 402), place, font=font("mono", 32), fill=(175, 175, 175), stroke_width=3, stroke_fill=(0, 0, 0))
    if flash > 0:
        d.rectangle([50, 190, 430, 452], outline=(255, 255, 255), width=int(2 + 7 * flash))

def _word_times(txt, a, b):
    words = txt.split(); tot = sum(len(w) + 1 for w in words) or 1; t = a; out = []
    for w in words:
        dd = (b - a - 0.12) * (len(w) + 1) / tot; out.append((w, t, t + dd)); t += dd
    return out

def subtitle(img, t, subs, speakers, y=None, words=True):
    """subs: lista de (ini, fim, texto, voz). speakers: {voz: {"label": "RAFA", "color": (r,g,b)}}."""
    y0 = y or SUB_Y
    d = ImageDraw.Draw(img)
    for a, b, txt, voice in subs:
        if not (a <= t < b): continue
        n = len(txt)
        f = font("title", 112 if n <= 16 else (90 if n <= 22 else 72))
        sp = speakers.get(voice, {})
        base = tuple(sp.get("color", (250, 250, 248)))
        if sp.get("label"):
            text_center(d, sp["label"], W / 2, y0 - 92, font("mono", 32), base, 4)
        wt = _word_times(txt, a, b)
        space = d.textbbox((0, 0), " ", font=f)[2]
        widths = [d.textbbox((0, 0), w, font=f)[2] - d.textbbox((0, 0), w, font=f)[0] for w, _, _ in wt]
        total = sum(widths) + space * (len(wt) - 1)
        if total > W - 70:
            f = font("title", int(f.size * (W - 70) / total)); space = d.textbbox((0, 0), " ", font=f)[2]
            widths = [d.textbbox((0, 0), w, font=f)[2] - d.textbbox((0, 0), w, font=f)[0] for w, _, _ in wt]
            total = sum(widths) + space * (len(wt) - 1)
        x = W / 2 - total / 2
        for (w, ws, we), wd in zip(wt, widths):
            active = words and ws <= t < we + 0.05
            seen = t >= ws
            col = (HIGHLIGHT if voice not in speakers or sp.get("color") is None else base) if active else (base if seen or not words else tuple(int(c * 0.78) for c in base))
            if active and voice in speakers and sp.get("color"): col = HIGHLIGHT
            pop = ease_out(c01((t - ws) / 0.1)) if words and active else 1.0
            if active and pop < 1:
                tmp = Image.new("RGBA", (wd + 60, 200), (0, 0, 0, 0)); td = ImageDraw.Draw(tmp)
                text_center(td, w, tmp.width / 2, 100, f, col + (255,), 9, (0, 0, 0, 255))
                sc = 0.8 + 0.3 * pop
                tmp = tmp.resize((int(tmp.width * sc), int(tmp.height * sc)))
                img.paste(tmp, (int(x + wd / 2 - tmp.width / 2), int(y0 - tmp.height / 2)), tmp)
            else:
                yy = y0 - (6 if active else 0)
                text_center(d, w, x + wd / 2, yy, f, col, 9)
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
