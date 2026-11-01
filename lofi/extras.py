
"""Cortes extras a partir do episódio pronto.

    python3 -m lofi.extras teaser  ep03.json ep03.mp4            -> ep03_teaser.mp4 (15 s, para Stories)
    python3 -m lofi.extras pacote  ep03.json ep03.mp4 [tempo]    -> teaser + capa TikTok + capa Instagram (o padrão de entrega)
    python3 -m lofi.extras capa    ep03.json [tempo] [--tiktok|--instagram] [--guias]
                                   -> ep03_capa_tiktok.png e ep03_capa_instagram.png (1080x1920, texto na área segura)
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

# Áreas seguras (1080x1920) de cada plataforma: o que fica fora delas é coberto pela interface ou cortado no grid.
#   TikTok: topo ~200 px (abas "Seguindo/Para você"), base ~480 px (legenda, música), coluna direita ~150 px (botões);
#           o grid do perfil mostra o recorte 3:4 central (y 240–1680).
#   Instagram: o Reels ocupa 9:16, mas o grid do perfil mostra o recorte 3:4 central (y 240–1680) e o feed, 4:5 (y 285–1635).
PLATAFORMAS = {
    "tiktok":    {"seguro": (60, 240, 930, 1430), "titulo_y": 380, "selo_y": 545, "nome_y": 1330, "cx": 495, "largura": 820},
    "instagram": {"seguro": (60, 320, 1020, 1600), "titulo_y": 470, "selo_y": 635, "nome_y": 1500, "cx": 540, "largura": 920},
}


def _escolher_tempo(ep, cfg):
    """Quadro para a capa: prefere closes e cenas com mais gente, mas só aceita um quadro em que todos os rostos
    aparecem inteiros, no meio da imagem (entre o selo e o nome do episódio) e dentro da área segura."""
    sp = ep.spec
    scen = [s for s in sp["shots"] if s.get("type", "scene") == "scene" and s.get("actors") and not s.get("hook")]
    ordem = sorted(scen, key=lambda s: (-(s.get("camera", {}).get("close") is not None), -len(s.get("actors", []))))
    x0, _, x1, _ = cfg["seguro"]; topo, base = cfg["selo_y"] + 60, cfg["nome_y"] - 80
    for s in ordem:
        for k in (0.5, 0.35, 0.7):
            t = s["start"] + (s["end"] - s["start"]) * k
            ep.frame(t)
            cabecas = [h for h in ep._heads if h[1] > 0 and h[0] < W]
            if cabecas and all(h[0] >= x0 and h[1] <= x1 and h[2] >= topo and h[2] <= base for h in cabecas):
                return t
    s = ordem[0] if ordem else None
    return (s["start"] + s["end"]) / 2 if s else ep.total * 0.4


def _texto_ajustado(d, txt, cx, cy, tamanho, largura, cor, contorno=6):
    f = font("title", tamanho)
    while tamanho > 40 and d.textbbox((0, 0), txt, font=f)[2] > largura:
        tamanho -= 6; f = font("title", tamanho)
    text_center(d, txt, cx, cy, f, cor, contorno)
    return f


def capa(spec_path, t=None, out=None, plataforma="tiktok", guias=False):
    """Capa do episódio para TikTok ou Instagram, com título, selo do episódio e nome do episódio dentro da área segura.
    guias=True desenha as áreas seguras (só para conferência, não para postar)."""
    from .render import Episode
    cfg = PLATAFORMAS[plataforma]
    ep = Episode(spec_path); sp = ep.spec
    ep.subs = []; ep.hud_state = lambda _t: None          # capa sem legenda e sem contador
    t = _escolher_tempo(ep, cfg) if t is None else t
    img = ep.frame(float(t)).filter(ImageFilter.GaussianBlur(0.5))
    # escurece em cima (título) e embaixo (nome do episódio) para o texto ler bem sobre qualquer cena
    topo = Image.linear_gradient("L").resize((W, cfg["selo_y"] + 260)).transpose(Image.FLIP_TOP_BOTTOM)
    img.paste((0, 0, 0), (0, 0), topo.point(lambda v: int(v * 0.88)))
    base = Image.linear_gradient("L").resize((W, H - cfg["nome_y"] + 260))
    img.paste((0, 0, 0), (0, cfg["nome_y"] - 260), base.point(lambda v: int(v * 0.8)))
    d = ImageDraw.Draw(img); cx = cfg["cx"]
    _texto_ajustado(d, sp.get("series_title", "SÉRIE"), cx, cfg["titulo_y"], 190, cfg["largura"], (242, 238, 228))
    n = sp.get("episode", "?"); tot = sp.get("episodes_total", "")
    if sp.get("formato") == "comentarios":
        lab = "VOCÊS COMENTARAM"; n = os.path.splitext(os.path.basename(spec_path))[0]
    else:
        lab = f"EPISÓDIO {n}" + (f"/{tot}" if tot else "")
    fl = font("title", 76); bb = d.textbbox((0, 0), lab, font=fl); w = bb[2] - bb[0]
    d.rectangle([cx - w / 2 - 30, cfg["selo_y"] - 50, cx + w / 2 + 30, cfg["selo_y"] + 50], fill=RED)
    text_center(d, lab, cx, cfg["selo_y"], fl, (255, 255, 255))
    if sp.get("episode_title"):
        _texto_ajustado(d, sp["episode_title"].upper(), cx, cfg["nome_y"], 104, cfg["largura"], (255, 214, 60), 8)
    if guias:
        x0, y0, x1, y1 = cfg["seguro"]
        d.rectangle([x0, y0, x1, y1], outline=(60, 255, 120), width=6)
        d.rectangle([0, 240, W, 1680], outline=(80, 180, 255), width=4)
    nome = f"ep{int(n):02d}" if str(n).isdigit() else (str(n) if n != "?" else "episodio")
    out = out or os.path.join(ep.base, f"{nome}_capa_{plataforma}.png")
    img.save(out); print(f"capa {plataforma}:", out); return out


def pacote(spec_path, video, t=None):
    """Tudo o que vai para as redes a partir do episódio pronto: teaser + capa do TikTok + capa do Instagram."""
    if t is None:   # mesmo quadro nas duas capas, escolhido pela área segura mais apertada (TikTok)
        from .render import Episode
        ep = Episode(spec_path); ep.subs = []; ep.hud_state = lambda _t: None
        t = _escolher_tempo(ep, PLATAFORMAS["tiktok"])
    return {"video": video, "teaser": teaser(spec_path, video),
            "capa_tiktok": capa(spec_path, t, plataforma="tiktok"),
            "capa_instagram": capa(spec_path, t, plataforma="instagram")}


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
    elif cmd == "capa":
        args = [a for a in sys.argv[2:] if not a.startswith("--")]
        plats = [p for p in PLATAFORMAS if f"--{p}" in sys.argv] or list(PLATAFORMAS)
        for p in plats: capa(args[0], float(args[1]) if len(args) > 1 else None, plataforma=p, guias="--guias" in sys.argv)
    elif cmd == "pacote":
        args = [a for a in sys.argv[2:] if not a.startswith("--")]
        r = pacote(args[0], args[1], float(args[2]) if len(args) > 2 else None)
        print("\n".join(f"{k}: {v}" for k, v in r.items()))
    elif cmd == "temporada": temporada(sys.argv[2], sys.argv[3], sys.argv[4:])
