
"""Cortes extras a partir do episódio pronto.

    python3 -m lofi.extras pacote  ep03.json ep03.mp4            -> corte curto + capas TikTok, Instagram e YouTube (o padrão de entrega)
    python3 -m lofi.extras teaser  ep03.json ep03.mp4            -> ep03_teaser.mp4 (15 s; fora da entrega padrão, só se pedirem)
    python3 -m lofi.extras capa    ep03.json [tempo] [--tiktok|--instagram] [--guias]
                                   -> ep03_capa_tiktok.png e ep03_capa_instagram.png (1080x1920, texto na área segura)
    python3 -m lofi.extras corte   ep03.json ep03.mp4 [alvo_s]   -> ep03_corte.mp4: versão curta (60–75 s) só com os picos
    python3 -m lofi.extras temporada saida.mp4 "DIA ZERO" ep1.mp4 ep2.mp4 ...   -> compilação 16:9 + capítulos
"""
import sys, os, json, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFilter
from .core import W, H, RED, CREAM, font, text_center, ease
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
    if spec.get("formato") == "extra": ep_n = ""; end_text = end_text or "EXTRA NO PERFIL"
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
    """Escolhe (tempo, câmera) para a capa. Testa o meio de cada cena com quem fala no episódio, no enquadramento original
    e num close no protagonista da cena; fica com o quadro de rostos maiores, todos inteiros, entre o selo e o nome do
    episódio e dentro da área segura. Devolve a câmera a usar (None = a do próprio plano)."""
    sp = ep.spec
    scen = [s for s in ep.shots if s.get("type", "scene") == "scene" and s.get("actors") and not s.get("hook")]
    falam = set(sp.get("voices", {})) - {k for k, v in sp.get("speakers", {}).items() if v.get("label") in ("RÁDIO", "MEGAFONE")}
    x0, _, x1, _ = cfg["seguro"]; topo, base = cfg["selo_y"] + 60, cfg["nome_y"] - 90
    melhor, nota_melhor = (None, None), -1
    for s in scen:
        idx = [i for i, a in enumerate(s["actors"]) if a.get("char") in falam and not a.get("fg")]
        if not idx: continue
        original = s.get("camera")
        for cam in (None, {"close": idx[0], "close_zoom": 1.9, "close_in": 0.01, "handheld": False}):
            if cam is not None: s["camera"] = cam
            for k in (0.5, 0.3, 0.75):
                t = s["start"] + (s["end"] - s["start"]) * k
                ep.frame(t)
                cab = [h for h in ep._heads if h[1] > 0 and h[0] < W and h[3] - h[2] > 40]
                if cab and all(h[0] >= x0 and h[1] <= x1 and h[2] >= topo and h[3] <= base for h in cab):
                    nota = sum(h[3] - h[2] for h in cab)
                    if nota > nota_melhor: melhor, nota_melhor = (t, cam), nota
            if original is None: s.pop("camera", None)
            else: s["camera"] = original
    if melhor[0] is not None: return melhor
    s = scen[0] if scen else None
    return ((s["start"] + s["end"]) / 2 if s else ep.total * 0.4), None


def _texto_ajustado(d, txt, cx, cy, tamanho, largura, cor, contorno=6):
    f = font("title", tamanho)
    while tamanho > 40 and d.textbbox((0, 0), txt, font=f)[2] > largura:
        tamanho -= 6; f = font("title", tamanho)
    text_center(d, txt, cx, cy, f, cor, contorno)
    return f


def capa(spec_path, t=None, out=None, plataforma="tiktok", guias=False, camera=None):
    """Capa do episódio para TikTok ou Instagram, com título, selo do episódio e nome do episódio dentro da área segura.
    guias=True desenha as áreas seguras (só para conferência, não para postar)."""
    from .render import Episode
    cfg = PLATAFORMAS[plataforma]
    ep = Episode(spec_path); sp = ep.spec
    ep.subs = []; ep.hud_state = lambda _t: None; ep.draw_redes = lambda *a: None   # capa sem legenda, contador, selo nem cartões
    if t is None: t, camera = _escolher_tempo(ep, cfg)
    if camera is not None:
        plano = next((s for s in ep.shots if s["start"] <= float(t) < s["end"]), None)
        if plano is not None: plano["camera"] = camera
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
    elif sp.get("formato") == "extra":
        lab = "EXTRA"; n = os.path.splitext(os.path.basename(spec_path))[0]
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
    """Tudo o que vai para as redes a partir do episódio pronto: corte curto + capas do TikTok, do Instagram e do
    YouTube (lofi/capas.py; ajustes em "capa" no JSON). Sem teaser (só com `teaser`, se pedirem)."""
    from . import capas
    if t is not None:
        sp = json.load(open(spec_path, encoding="utf-8"))
        if float(t) != sp.get("capa", {}).get("tempo"):
            print(f"dica: para fixar o fundo da capa, ponha \"capa\": {{\"tempo\": {t}}} no JSON", file=sys.stderr)
    res = {"video": video, "corte": corte(spec_path, video)}
    res.update(capas.todas(spec_path))
    return res


def _nota_plano(sp, s, subs):
    """Quanto um plano "segura" o público: sustos, closes, detalhes, cenário revelando algo e fala."""
    cam = s.get("camera", {}); pr = s.get("props", {}); dur = max(0.1, s["end"] - s["start"])
    fala = sum(max(0.0, min(b, s["end"]) - max(a, s["start"])) for a, b, _ in subs) / dur
    dialogo = any(v in (sp.get("speakers") or {}) and min(b, s["end"]) > max(a, s["start"]) for a, b, v in subs)   # outro personagem fala
    return (3 * len(s.get("scare", [])) + 2 * (cam.get("close") is not None or cam.get("plano") == "close")
            + 1.5 * (s.get("type") == "detail") + 2 * any(pr.get(k) for k in ("reflexo", "vulto", "porta", "rosto", "batida", "duplo"))
            + 1.5 * bool(s.get("shake")) + 1.2 * fala + (0.8 if cam.get("handheld") else 0) + 2.5 * dialogo)


def corte(spec_path, video, alvo=68.0, minimo=60.0, maximo=75.0, out=None):
    """Versão curta do episódio só com os planos mais fortes, em ordem: gancho, a 1ª cena (contexto), os picos,
    a última cena antes da escolha, a tela A/B e o quadro de loop. Para testar qual versão segura mais em cada rede."""
    from .render import Episode
    ep = Episode(spec_path)
    shots = sorted(ep.shots, key=lambda s: s["start"])
    subs = [(a, b, v) for a, b, _, v in ep.subs]
    fixos = set()
    gancho = [i for i, s in enumerate(shots) if s.get("hook")]; fixos.update(gancho)
    cenas = [i for i, s in enumerate(shots) if s.get("type", "scene") in ("scene", "detail") and not s.get("hook")]
    if cenas: fixos.add(cenas[0])
    ch = [i for i, s in enumerate(shots) if s.get("type") == "choice"]
    if ch:
        fixos.update(ch); antes = [i for i in cenas if i < ch[0]]
        if antes: fixos.add(antes[-1])
    fixos.update(i for i, s in enumerate(shots) if s.get("type") in ("loop", "title", "recap") and s["start"] < 12 or s.get("type") == "loop")
    dur = lambda i: shots[i]["end"] - shots[i]["start"]
    escolhidos = set(fixos); total = sum(dur(i) for i in escolhidos)
    for i in sorted((i for i in cenas if i not in escolhidos), key=lambda i: -_nota_plano(ep.spec, shots[i], subs)):
        if total >= alvo: break
        if total + dur(i) <= maximo: escolhidos.add(i); total += dur(i)
    if total < minimo:   # ainda curto: completa pela ordem do episódio
        for i in cenas:
            if i not in escolhidos and total + dur(i) <= maximo: escolhidos.add(i); total += dur(i)
    trechos = [(shots[i]["start"], shots[i]["end"]) for i in sorted(escolhidos)]
    out = out or os.path.splitext(video)[0] + "_corte.mp4"
    tmp = tempfile.mkdtemp(); partes = []; n = len(trechos)
    for k, (a, b) in enumerate(trechos):   # um pedaço por vez (vários trims no mesmo filtro estouram a memória)
        pt = os.path.join(tmp, f"p{k:02d}.mp4"); fd = max(0.0, (b - a) - 0.04)
        _run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", video,
              "-af", f"afade=t=in:d=0.03,afade=t=out:st={fd:.3f}:d=0.04", "-c:v", "libx264", "-preset", "medium", "-crf", "24",
              "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", pt])
        partes.append(pt)
    lst = os.path.join(tmp, "lista.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in partes))
    _run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out])
    print(f"corte: {out} ({total:.1f} s, {n} planos)"); return out


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

def ler_escolhas(biblia):
    """Linhas da tabela de episódios da bíblia: [(nº, opção A, opção B, voto, placar A, placar B)]."""
    import re
    out = []
    for linha in open(biblia, encoding="utf-8"):
        c = [x.strip() for x in linha.strip().strip("|").split("|")]
        if len(c) < 6 or not c[0].isdigit(): continue
        m = re.match(r"A\)\s*(.+?)\s*·\s*B\)\s*(.+)", c[4])
        if not m or not c[5] or c[5].startswith("("): continue
        a, b = m.group(1), m.group(2); voto = c[5].upper(); pa = pb = None
        pl = c[6] if len(c) > 6 else ""
        mx = re.match(r"(\d+)\s*[xX×]\s*(\d+)", pl); mp = re.match(r"(\d+)\s*%", pl)
        venceu_a = voto in a.upper() or a.upper() in voto
        if mx: va, vb = int(mx.group(1)), int(mx.group(2)); pa = round(100 * va / max(1, va + vb)); pb = 100 - pa
        elif mp: w = int(mp.group(1)); pa, pb = (w, 100 - w) if venceu_a else (100 - w, w)
        out.append((int(c[0]), a, b, "A" if venceu_a else "B", pa, pb))
    return out


def escolhas(serie_dir, out=None, titulo=None):
    """Vídeo vertical "todas as escolhas do público": cada episódio com a pergunta, as duas opções e o voto vencedor
    (com barras de porcentagem quando o placar está na bíblia), e no fim o gancho da próxima temporada."""
    biblia = os.path.join(serie_dir, "biblia.md"); itens = ler_escolhas(biblia)
    if not itens: raise SystemExit("nenhum voto registrado na tabela da bíblia")
    titulo = titulo or os.path.basename(os.path.abspath(serie_dir)).replace("-", " ").upper()
    out = out or os.path.join(serie_dir, "escolhas.mp4"); fps = 30
    cenas = [("intro", 2.5)] + [(it, 3.6) for it in itens] + [("fim", 3.5)]
    total = sum(d for _, d in cenas)
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                          "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{total:.2f}", "-c:v", "libx264", "-crf", "24",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    fundo = Image.new("RGB", (W, H), (14, 12, 18)); dd = ImageDraw.Draw(fundo)
    for y in range(0, H, 6): dd.line((0, y, W, y), fill=(18, 16, 24))
    f_t, f_m, f_s = font("title", 120), font("title", 74), font("title", 52)
    for cena, dur in cenas:
        for i in range(int(dur * fps)):
            t = i / fps; k = min(1.0, t / 0.5); im = fundo.copy(); d = ImageDraw.Draw(im)
            if cena == "intro":
                text_center(d, titulo, W // 2, 760, f_t, CREAM); text_center(d, "VOCÊS ESCOLHERAM", W // 2, 940, f_m, RED)
                text_center(d, "TODAS AS DECISÕES DA TEMPORADA", W // 2, 1060, f_s, CREAM)
            elif cena == "fim":
                text_center(d, "TEMPORADA 2?", W // 2, 820, f_t, RED)
                text_center(d, "COMENTA O QUE VOCÊ", W // 2, 1000, f_m, CREAM); text_center(d, "QUER VER", W // 2, 1090, f_m, CREAM)
            else:
                n, a, b, v, pa, pb = cena
                text_center(d, f"EPISÓDIO {n}", W // 2, 560, f_m, RED)
                for j, (lab, op, pc) in enumerate((("A", a, pa), ("B", b, pb))):
                    y = 760 + j * 300; ganhou = lab == v; cor = RED if ganhou else (90, 86, 96)
                    larg = 860 * ((pc or (78 if ganhou else 22)) / 100) * ease(min(1, max(0, (t - 0.4) / 1.2)))
                    d.rounded_rectangle((110, y, 970, y + 170), 26, fill=(30, 28, 36))
                    d.rounded_rectangle((110, y, 110 + max(52, larg), y + 170), 26, fill=cor)
                    d.text((150, y + 30), f"{lab}) {op.upper()}"[:26], font=f_s, fill=CREAM)
                    if pc is not None: d.text((150, y + 100), f"{pc * min(1, max(0, (t - 0.4) / 1.2)):.0f}%", font=font("title", 44), fill=CREAM)
                if t > 1.8: text_center(d, "A MAIORIA ESCOLHEU", W // 2, 1420, f_s, CREAM); text_center(d, (a if v == "A" else b).upper(), W // 2, 1510, f_m, RED)
            if k < 1: im = Image.blend(Image.new("RGB", (W, H)), im, k)
            p.stdin.write(fx.grain(im).tobytes())
    p.stdin.close(); p.wait(); print("escolhas:", out); return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "teaser": teaser(sys.argv[2], sys.argv[3])
    elif cmd == "capa":
        args = [a for a in sys.argv[2:] if not a.startswith("--")]
        plats = [p for p in PLATAFORMAS if f"--{p}" in sys.argv] or list(PLATAFORMAS)
        for p in plats: capa(args[0], float(args[1]) if len(args) > 1 else None, plataforma=p, guias="--guias" in sys.argv)
    elif cmd == "escolhas": escolhas(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "pacote":
        args = [a for a in sys.argv[2:] if not a.startswith("--")]
        if len(args) < 2 or not args[1].endswith(".mp4"):   # vídeo omitido: usa o "out" do episódio
            spec = json.load(open(args[0])); args.insert(1, os.path.join(os.path.dirname(args[0]), spec.get("out", "")))
        r = pacote(args[0], args[1], float(args[2]) if len(args) > 2 else None)
        print("\n".join(f"{k}: {v}" for k, v in r.items()))
    elif cmd == "corte": corte(sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 68.0)
    elif cmd == "temporada": temporada(sys.argv[2], sys.argv[3], sys.argv[4:])
