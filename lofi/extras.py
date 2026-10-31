
"""Cortes extras a partir do episódio pronto.

    python3 -m lofi.extras teaser  ep03.json ep03.mp4            -> ep03_teaser.mp4 (15 s, para Stories)
    python3 -m lofi.extras capa    ep03.json [tempo]             -> ep03_capa.png (1080x1920)
    python3 -m lofi.extras temporada saida.mp4 "DIA ZERO" ep1.mp4 ep2.mp4 ...   -> compilação 16:9 + capítulos
"""
import sys, os, json, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFilter
from .core import W, H, RED, CREAM, font, text_center
from . import fx

def _run(cmd): subprocess.run(cmd, check=True)

def _moments(spec, n=3, dur=3.2):
    """Escolhe momentos fortes: sustos, closes, tremores, relâmpagos."""
    cands = []
    for s in spec["shots"]:
        if s.get("type") in ("title", "choice", "recap"): continue
        score = 3 * len(s.get("scare", [])) + 2 * (s.get("camera", {}).get("close") is not None) + len(s.get("shake", [])) + (1 if s.get("type") == "detail" else 0)
        if score: cands.append((score, s["start"] + 0.2, min(dur, s["end"] - s["start"] - 0.2)))
    for th in spec.get("lightning", []): cands.append((2, max(0, th - 0.8), dur))
    cands.sort(key=lambda c: -c[0])
    picked = []
    for c in cands:
        if all(abs(c[1] - p[1]) > dur for p in picked): picked.append(c)
        if len(picked) == n: break
    return sorted(picked, key=lambda c: c[1])

def _card(path, lines, color=RED):
    img = Image.new("RGB", (W, H), (8, 8, 12)); d = ImageDraw.Draw(img)
    y = 820
    for i, l in enumerate(lines):
        if i == len(lines) - 1:
            bb = d.textbbox((0, 0), l, font=font("title", 96)); w = bb[2] - bb[0]
            d.rectangle([W / 2 - w / 2 - 30, y - 70, W / 2 + w / 2 + 30, y + 70], fill=color)
        text_center(d, l, W / 2, y, font("title", 110 if i == 0 else 96), CREAM if i < len(lines) - 1 else (255, 255, 255))
        y += 170
    img.save(path)

def teaser(spec_path, video, out=None, end_text=None):
    spec = json.load(open(spec_path)); base = os.path.splitext(video)[0]
    out = out or base + "_teaser.mp4"
    tmp = tempfile.mkdtemp()
    segs = []
    hook = next((s for s in spec["shots"] if s.get("hook")), None)
    if hook: segs.append((hook["start"], min(2.4, hook["end"] - hook["start"])))
    segs += [(m[1], m[2]) for m in _moments(spec, 3)]
    parts = []
    for i, (a, d) in enumerate(segs):
        p = os.path.join(tmp, f"s{i}.mp4"); parts.append(p)
        _run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{a:.2f}", "-t", f"{d:.2f}", "-i", video, "-vf", "scale=1080:1920,fps=30",
              "-c:v", "libx264", "-crf", "24", "-preset", "veryfast", "-c:a", "aac", "-ar", "44100", "-ac", "2", p])
    ep_n = spec.get("episode", ""); title = spec.get("series_title", "")
    card = os.path.join(tmp, "card.png"); _card(card, [title or "NOVO EPISÓDIO", end_text or (f"EPISÓDIO {ep_n} NO PERFIL" if ep_n else "JÁ NO PERFIL")])
    cv = os.path.join(tmp, "card.mp4"); parts.append(cv)
    _run(["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-t", "2.5", "-i", card, "-f", "lavfi", "-t", "2.5", "-i", "anullsrc=r=44100:cl=stereo",
          "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "24", "-c:a", "aac", "-shortest", cv])
    lst = os.path.join(tmp, "l.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    _run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-crf", "26", "-preset", "medium",
          "-c:a", "aac", "-movflags", "+faststart", out])
    print("teaser:", out); return out

def capa(spec_path, t=None, out=None):
    from .render import Episode
    ep = Episode(spec_path); sp = ep.spec
    if t is None:
        scen = [s for s in sp["shots"] if s.get("type", "scene") == "scene" and s.get("actors") and not s.get("hook")]
        close = [s for s in scen if s.get("camera", {}).get("close") is not None]
        pick = (close or sorted(scen, key=lambda s: -len(s.get("actors", [])))[:1] or [None])[0]
        t = (pick["start"] + pick["end"]) / 2 if pick else ep.total * 0.4
    ep.subs = []
    img = ep.frame(float(t))
    img = img.filter(ImageFilter.GaussianBlur(0.5)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 520], fill=(0, 0, 0))
    img = Image.blend(img, img, 1.0); d = ImageDraw.Draw(img)
    grad = Image.linear_gradient("L").resize((W, 700)).transpose(Image.FLIP_TOP_BOTTOM)
    img.paste((0, 0, 0), (0, 0), grad.point(lambda v: int(v * 0.85)))
    text_center(d, sp.get("series_title", "SÉRIE"), W / 2, 260, font("title", 200), (242, 238, 228), 6)
    n = sp.get("episode", "?"); tot = sp.get("episodes_total", "")
    lab = f"EPISÓDIO {n}" + (f"/{tot}" if tot else "")
    bb = d.textbbox((0, 0), lab, font=font("title", 76)); w = bb[2] - bb[0]
    d.rectangle([W / 2 - w / 2 - 30, 400, W / 2 + w / 2 + 30, 500], fill=RED)
    text_center(d, lab, W / 2, 450, font("title", 76), (255, 255, 255))
    if sp.get("episode_title"): text_center(d, sp["episode_title"].upper(), W / 2, 1560, font("title", 96), (255, 214, 60), 8)
    out = out or os.path.join(ep.base, f"ep{int(n):02d}_capa.png" if str(n).isdigit() else "capa.png")
    img.save(out); print("capa:", out); return out

def temporada(out, title, videos):
    tmp = tempfile.mkdtemp(); parts = []; chapters = []; tpos = 0.0
    for i, v in enumerate(videos, 1):
        card = os.path.join(tmp, f"c{i}.png")
        im = Image.new("RGB", (1920, 1080), (8, 8, 12)); d = ImageDraw.Draw(im)
        text_center(d, title, 960, 440, font("title", 140), CREAM); text_center(d, f"EPISÓDIO {i}", 960, 620, font("title", 90), RED)
        im.save(card)
        cv = os.path.join(tmp, f"c{i}.mp4")
        _run(["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-t", "2.5", "-i", card, "-f", "lavfi", "-t", "2.5", "-i", "anullsrc=r=44100:cl=stereo",
              "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "24", "-c:a", "aac", "-shortest", cv])
        ev = os.path.join(tmp, f"e{i}.mp4")
        _run(["ffmpeg", "-loglevel", "error", "-y", "-i", v, "-filter_complex",
              "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=30:3,eq=brightness=-0.15[bg];"
              "[0:v]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0,fps=30,format=yuv420p[v]",
              "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "24", "-preset", "veryfast", "-c:a", "aac", "-ar", "44100", "-ac", "2", ev])
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", ev], capture_output=True, text=True).stdout)
        chapters.append(f"{int(tpos // 60):02d}:{int(tpos % 60):02d} Episódio {i}")
        parts += [cv, ev]; tpos += 2.5 + dur
    lst = os.path.join(tmp, "l.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    _run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out])
    ch = os.path.splitext(out)[0] + "_capitulos.txt"; open(ch, "w").write("\n".join(chapters) + "\n")
    print("temporada:", out, "| capítulos:", ch); return out, ch

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "teaser": teaser(sys.argv[2], sys.argv[3])
    elif cmd == "capa": capa(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else None)
    elif cmd == "temporada": temporada(sys.argv[2], sys.argv[3], sys.argv[4:])
