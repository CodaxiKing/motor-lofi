"""Editor do episódio: prévia leve com áudio + edição por plano, antes do render final.

    python3 -m lofi.editor preparar series/<serie>/epNN.json   -> series/<serie>/_editor/ (página, prévia e dados)
    python3 -m lofi.editor aplicar  series/<serie>/epNN.json edits.json -> grava as mudanças no JSON e lista os pedidos livres

A prévia usa 2 quadros por segundo e reaproveita os planos que não mudaram. O render final só roda depois do botão "Gerar vídeo".
"""
import json, os, shutil, subprocess, sys

from .render import Episode, W, H

PASSO = 0.5
LARG, ALT = 540, 960
EMOCOES = ["neutral", "fear", "shock", "angry", "sad", "determined", "happy", "suspicious", "cry", "panting"]
POSES = ["idle", "sit", "phone", "point", "scared", "ouvir", "pensativo", "reach", "hide", "mao_na_boca", "proteger_rosto", "espiar_longe", "desespero", "chest"]
PLANOS = ["close", "medio", "conjunto", "aberto"]


def _valor(v):
    if isinstance(v, list) and v: return v[-1][-1] if isinstance(v[-1], list) else v[-1]
    return v


def _rotulo(s):
    if s.get("type") == "detail": return {"celular": "Celular", "relogio": "Relógio", "macaneta": "Maçaneta", "olho": "Olho", "chave": "Chave"}.get(s.get("subject"), "Detalhe")
    n = s.get("type", "scene")
    if n != "scene": return {"choice": "Escolha A/B", "pausa": "Pausa para seguir", "pensamento": "Pensamento", "loop": "Volta ao início", "recap": "Anteriormente", "placar": "Placar"}.get(n, n)
    c = s.get("cenario", {}); nome = s.get("scene") or c.get("base") or c.get("close") or "cena"
    return ("Lembrança · " if s.get("lembranca") else "") + nome.replace("_", " ").capitalize()


def _tela(s):
    p = s.get("params", {})
    if s.get("subject") != "celular": return None
    if p.get("chat"): return [m["txt"] for m in p["chat"].get("msgs", [])]
    return list(p.get("text", []))


def dados(sp, base_url=""):
    subs = sp.get("subs", []); planos = []
    for i, s in enumerate(sorted(sp["shots"], key=lambda x: x["start"])):
        frases = []
        for n, x in enumerate(subs):
            c = next((c for c in sp.get("clips", []) if c["voice"] == x["voice"] and c["src"] == x["src"] and not c.get("gancho") and s["start"] <= c["at"] < s["end"]), None)
            if c: frases.append({"sub": n, "voz": x["voice"], "texto": " / ".join(x["text"])})
        at = next(iter(s.get("actors") or []), None)
        planos.append({"id": i, "inicio": s["start"], "fim": s["end"], "rotulo": _rotulo(s), "frases": frases, "tela": _tela(s),
                       "ator": at.get("char") if at else None, "emotion": _valor(at.get("emotion", "neutral")) if at else None,
                       "pose": _valor(at.get("pose", "idle")) if at else None, "plano": (s.get("camera") or {}).get("plano") if at else None})
    return {"titulo": sp.get("series_title", ""), "episodio": sp.get("episode"), "total_eps": sp.get("episodes_total"), "nome_ep": sp.get("episode_title", ""),
            "duracao": sp["total"], "planos": planos, "opcoes": {"emotion": EMOCOES, "pose": POSES, "plano": PLANOS}, "estado": "aguardando"}


def preparar(spec_path, saida=None, tarefa=None, url=None):
    ep = Episode(spec_path); saida = saida or os.path.join(ep.base, "_editor")
    os.makedirs(os.path.join(saida, "miniaturas"), exist_ok=True); cache = os.path.join(ep.base, "_editor_cache"); os.makedirs(cache, exist_ok=True)
    ep.build_audio(); lista = []; usados = set(); refeitos = 0
    chaves = [c for c in ep._chaves_planos() if c[2] > c[1]]
    for k, a, b in chaves:
        pasta = os.path.join(cache, k); usados.add(k); t0 = a / ep.fps; t1 = b / ep.fps
        tempos = [t0 + j * PASSO for j in range(max(1, int((t1 - t0) / PASSO)))]
        if not os.path.exists(os.path.join(pasta, "ok")):
            os.makedirs(pasta, exist_ok=True); refeitos += 1
            for j, t in enumerate(tempos):
                ep.frame(t + 1e-3).convert("RGB").resize((LARG, ALT)).save(os.path.join(pasta, f"{j:04d}.jpg"), quality=78)
            open(os.path.join(pasta, "ok"), "w").close()
        for j, t in enumerate(tempos):
            fim = tempos[j + 1] if j + 1 < len(tempos) else t1
            lista.append((os.path.join(pasta, f"{j:04d}.jpg"), fim - t))
    for f in os.listdir(cache):
        if f not in usados: shutil.rmtree(os.path.join(cache, f), ignore_errors=True)
    txt = os.path.join(saida, "_quadros.txt")
    with open(txt, "w") as f:
        for p, d in lista: f.write(f"file '{os.path.abspath(p)}'\nduration {d:.4f}\n")
        f.write(f"file '{os.path.abspath(lista[-1][0])}'\n")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", txt, "-i", ep.mix_path, "-map", "0:v", "-map", "1:a",
                    "-vf", "fps=12,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-c:a", "aac", "-b:a", "96k", "-shortest",
                    "-movflags", "+faststart", os.path.join(saida, "previa.mp4")], check=True)
    os.remove(txt)
    sp = json.load(open(spec_path, encoding="utf-8")); d = dados(sp)
    d["planos"] = [p for p in d["planos"] if p["fim"] > p["inicio"]]
    d["serie"] = os.path.basename(os.path.abspath(ep.base)); d["tarefa"] = tarefa; d["url"] = url
    for p, (k, a, b) in zip(d["planos"], chaves):
        qs = sorted(f for f in os.listdir(os.path.join(cache, k)) if f.endswith(".jpg"))
        from PIL import Image
        Image.open(os.path.join(cache, k, qs[len(qs) // 2])).resize((108, 192)).save(os.path.join(saida, "miniaturas", f"{p['id']:03d}.jpg"), quality=70)
    json.dump(d, open(os.path.join(saida, "dados.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"status": "editando", "planos": {}}, open(os.path.join(saida, "edits.json"), "w", encoding="utf-8"), ensure_ascii=False)
    pag = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "editor_modelo.html"), encoding="utf-8").read()
    open(os.path.join(saida, "index.html"), "w", encoding="utf-8").write(pag.replace("<title>Editor do Episódio</title>", f"<title>Editor {sp.get('series_title', '').title()} {sp.get('episode', '')}</title>", 1))
    os.makedirs(os.path.join(saida, "vozes"), exist_ok=True)       # o render final precisa delas, e áudio não vai para o Git
    for v in {os.path.join(ep.base, f) for f in (sp.get("voices") or {}).values()}:
        if os.path.exists(v): shutil.copy(v, os.path.join(saida, "vozes", os.path.basename(v)))
    print(f"editor pronto em {saida}: {refeitos} de {len(chaves)} planos refeitos")
    return saida


def _desloca(sp, depois_de, extra):
    """Abre `extra` segundos depois do instante `depois_de`, mantendo fala, som e legenda em sincronia."""
    for s in sp["shots"]:
        if s["start"] >= depois_de - 1e-6:
            s["start"] = round(s["start"] + extra, 3); s["end"] = round(s["end"] + extra, 3)
            for o in s.get("overlay", []):
                if "t" in o: o["t"] = [round(v + extra, 3) for v in o["t"]]
            ec = s.get("end_card")
            if ec: ec["t"] = round(ec["t"] + extra, 3)
        elif s["end"] >= depois_de - 1e-6: s["end"] = round(s["end"] + extra, 3)
    for c in sp.get("clips", []):
        if c["at"] >= depois_de - 1e-6: c["at"] = round(c["at"] + extra, 3)
    for x in sp.get("sfx", []):
        if x["t"] >= depois_de - 1e-6: x["t"] = round(x["t"] + extra, 3)
    for m in sp.get("music", []):
        if m["start"] >= depois_de - 1e-6: m["start"] = round(m["start"] + extra, 3)
        if m["end"] >= depois_de - 1e-6: m["end"] = round(m["end"] + extra, 3)
    hud = sp.get("hud") or {}
    for d in hud.get("days", []):
        if d[0] >= depois_de - 1e-6: d[0] = round(d[0] + extra, 3)
    pq = sp.get("pergunta")
    if isinstance(pq, dict) and pq.get("t", -1) >= depois_de: pq["t"] = round(pq["t"] + extra, 3)
    sp["total"] = round(sp["total"] + extra, 3)


def aplicar(spec_path, edits_path):
    sp = json.load(open(spec_path, encoding="utf-8")); ed = json.load(open(edits_path, encoding="utf-8"))
    shots = sorted(sp["shots"], key=lambda x: x["start"]); pedidos = []; extras = []
    for sid, e in ed.get("planos", {}).items():
        s = shots[int(sid)]
        for n, txt in (e.get("frases") or {}).items():
            pedacos = [p.strip() for p in txt.split("/") if p.strip()]
            if pedacos: sp["subs"][int(n)]["text"] = pedacos
        if e.get("tela") is not None and s.get("subject") == "celular":
            p = s["params"]; ls = [l for l in e["tela"] if l.strip()]
            if p.get("chat"):
                for m, l in zip(p["chat"].get("msgs", []), ls): m["txt"] = l
            else: p["text"] = ls
        at = next(iter(s.get("actors") or []), None)
        if at:
            if e.get("emotion"): at["emotion"] = e["emotion"]
            if e.get("pose"): at["pose"] = e["pose"]
        if e.get("plano") and at: s["camera"] = dict({k: v for k, v in s.get("camera", {}).items() if k not in ("zoom", "close")}, plano=e["plano"], cortes=False)
        if float(e.get("extra") or 0) > 0: extras.append((s["end"], float(e["extra"])))
        if (e.get("pedido") or "").strip(): pedidos.append({"plano": int(sid), "inicio": s["start"], "pedido": e["pedido"].strip()})
    for fim, x in sorted(extras, reverse=True): _desloca(sp, fim, x)
    json.dump(sp, open(spec_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"status": ed.get("status"), "pedidos": pedidos, "mudancas": len(ed.get("planos", {}))}


if __name__ == "__main__":
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    if sys.argv[1] == "preparar":
        opt = lambda n: sys.argv[sys.argv.index(n) + 1] if n in sys.argv else None
        preparar(sys.argv[2], tarefa=opt("--tarefa"), url=opt("--url"))
    else: print(json.dumps(aplicar(sys.argv[2], sys.argv[3]), ensure_ascii=False, indent=1))
