
"""Verificador automático antes do render: estrutura do roteiro + problemas visuais nos quadros.

    python3 -m lofi.check series/dia-zero/ep03.json
Gera `_revisao.png` (folha de quadros para o revisor) e imprime a lista de problemas.
Código de saída 1 se houver ERRO.
"""
import sys, os, json
from PIL import Image, ImageDraw
from .core import W, H, font
from . import scenes, detail, text
from .rig import CHARS, POSES, EMOTIONS
from .render import Episode, val, change

def check(path, frames=True):
    ep = Episode(path); sp = ep.spec; probs = []
    def err(m): probs.append(("ERRO", m))
    def warn(m): probs.append(("AVISO", m))
    shots = ep.shots
    # ---------- estrutura ----------
    if not (115 <= ep.total <= 185): warn(f"duração {ep.total:.0f}s fora do padrão de 2–3 min")
    if not any(s.get("hook") and s["start"] < 0.5 for s in shots): err("falta o gancho (plano com 'hook' no início)")
    if not any(s.get("type") == "title" for s in shots): err("falta o plano de título com carimbo")
    final = any("FIM" in json.dumps(s.get("overlay", []), ensure_ascii=False) for s in shots)
    if not any(s.get("type") == "choice" for s in shots) and not final: err("falta a escolha A/B (ou 'FIM' no último episódio)")
    for a, b in zip(shots, shots[1:]):
        if abs(a["end"] - b["start"]) > 0.05: err(f"buraco/sobreposição entre planos em {a['end']:.2f}s e {b['start']:.2f}s")
    n_scene = sum(1 for s in shots if s.get("type", "scene") in ("scene", "detail"))
    if n_scene < 12: warn(f"só {n_scene} cenas (padrão 12–20)")
    for s in shots:
        typ = s.get("type", "scene")
        if typ == "scene" and s.get("scene") not in scenes.REGISTRY: err(f"cenário inexistente: {s.get('scene')} ({s['start']}s)")
        if typ == "detail" and s.get("subject") not in detail.SUBJECTS: err(f"plano de detalhe inexistente: {s.get('subject')}")
        if typ == "recap" and not os.path.exists(os.path.join(ep.base, s.get("from", ""))): err(f"recap aponta para arquivo inexistente: {s.get('from')}")
        for a in s.get("actors", []) + sum(([s[k]] if False else s.get(k, {}).get("actors", []) for k in ("a", "b")), []):
            if a["char"] not in CHARS and a["char"] not in ep.custom: err(f"personagem desconhecido: {a['char']} ({s['start']}s)")
            for key, allowed in (("pose", POSES), ("emotion", EMOTIONS)):
                v = a.get(key)
                vals = [x[1] for x in v] if isinstance(v, list) else ([v] if v else [])
                for x in vals:
                    if x not in allowed: err(f"{key} inválida '{x}' para {a['char']} ({s['start']}s)")
    for v, pth in ep.voices.items():
        if not os.path.exists(pth): err(f"áudio não encontrado: {pth}")
    for s in sp.get("subs", []):
        for piece in s["text"]:
            if len(piece.split()) > 4: warn(f"legenda com mais de 4 palavras: '{piece}'")
    cl = sorted(ep.clips, key=lambda c: c["at"])
    for a, b in zip(cl, cl[1:]):
        if a["at"] + (a["src"][1] - a["src"][0]) > b["at"] + 0.1: warn(f"falas sobrepostas em {b['at']:.1f}s ({a['voice']} / {b['voice']})")
    # ---------- quadros ----------
    sheet_frames = []
    if frames:
        try: ep.build_audio()
        except Exception as e: warn(f"áudio não montado ({e}); boca não será testada")
        times = sorted(set([round((s["start"] + s["end"]) / 2, 2) for s in shots] + [round((a + b) / 2, 2) for a, b, _, _ in ep.subs]))
        for t in times:
            img = ep.frame(t)
            shot = next((s for s in shots if s["start"] <= t < s["end"]), shots[-1])
            sub = next((x for x in ep.subs if x[0] <= t < x[1]), None)
            if shot.get("type", "scene") == "scene":
                sy = ep.pick_sub_y(shot)
                for (x0, x1, top, bot) in ep._heads:
                    face = (top + (bot - top) * 0.35, bot)
                    if sub and face[0] < sy + 55 and face[1] > sy - 55 and x1 > 160 and x0 < W - 160:
                        err(f"legenda cobrindo rosto em {t:.1f}s ('{sub[2]}')")
                    if x1 < 40 or x0 > W - 40: warn(f"personagem fora do quadro em {t:.1f}s")
                    elif (x0 < -60 or x1 > W + 60) and not shot.get("camera", {}).get("close") is not None: warn(f"personagem cortado na lateral em {t:.1f}s")
                    if top < 450 and x0 < 430 and shot.get("hud", True): warn(f"cabeça embaixo do contador em {t:.1f}s")
                    if top > 1640: warn(f"personagem na área da interface do Reels (embaixo) em {t:.1f}s")
            sheet_frames.append((t, img))
        cols = 6; tw, th = 270, 480
        rows = (len(sheet_frames) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * (th + 30)), (255, 255, 255)); d = ImageDraw.Draw(sheet)
        for i, (t, img) in enumerate(sheet_frames):
            x, y = (i % cols) * tw, (i // cols) * (th + 30)
            sheet.paste(img.resize((tw, th)), (x, y)); d.text((x + 6, y + th + 4), f"{t:.1f}s", font=font("mono", 20), fill=(0, 0, 0))
        out = os.path.join(ep.base, "_revisao.png"); sheet.save(out)
        probs.append(("INFO", f"folha de revisão: {out} ({len(sheet_frames)} quadros)"))
    return probs

if __name__ == "__main__":
    ps = check(sys.argv[1], frames="--rapido" not in sys.argv)
    for lvl, m in ps: print(f"[{lvl}] {m}")
    n_err = sum(1 for l, _ in ps if l == "ERRO")
    print(f"\n{n_err} erro(s), {sum(1 for l, _ in ps if l == 'AVISO')} aviso(s)")
    sys.exit(1 if n_err else 0)
