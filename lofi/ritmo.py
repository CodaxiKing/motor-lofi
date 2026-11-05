"""Ritmo da narração: mede a velocidade real das vozes e estima a duração de um roteiro antes de gravar.

    python3 -m lofi.ritmo medir series/<serie>/epNN.json        -> palavras por segundo de cada voz (grava em ritmo.json)
    python3 -m lofi.ritmo roteiro series/<serie>/epNN_roteiro.md -> tempo de voz previsto, cena a cena

Sem medição, usa 3,0 palavras/s (o ElevenLabs costuma falar mais rápido que os 2,4 de uma leitura humana).
"""
import json, os, re, sys

PADRAO = 3.0
MIN_OCUPACAO = 0.60      # a voz deve ocupar ao menos 60% do tempo planejado; o resto são pausas com ação
PAUSA_RETICENCIAS = 0.35
PAUSAS_TAG = {"pause": 0.8, "short pause": 0.4, "long pause": 1.5}


def _falante(voz):
    return re.sub(r"[^a-z]", "", voz.lower().split("_")[0].rstrip("0123456789"))


def medir(spec_path, salvar=True):
    sp = json.load(open(spec_path, encoding="utf-8")); pal, seg = {}, {}
    for s in sp.get("subs", []):
        v = _falante(s["voice"]); pal[v] = pal.get(v, 0) + len(" ".join(s["text"]).replace("*", "").split())
        seg[v] = seg.get(v, 0.0) + s["src"][1] - s["src"][0]
    r = {v: round(pal[v] / seg[v], 2) for v in pal if seg[v] > 0}
    if salvar:
        p = os.path.join(os.path.dirname(os.path.abspath(spec_path)), "ritmo.json")
        ant = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
        ant.update(r); json.dump(ant, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return r


def velocidades(pasta):
    p = os.path.join(pasta, "ritmo.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def segundos_fala(fala, vel=PADRAO):
    """Tempo previsto de uma fala: palavras / velocidade + pausas escritas (reticências e tags)."""
    pausas = sum(t * len(re.findall(r"\[" + n + r"\]", fala, re.I)) for n, t in PAUSAS_TAG.items())
    limpo = re.sub(r"\[[^\]]*\]", " ", fala)
    pausas += PAUSA_RETICENCIAS * limpo.count("...")
    return len(re.sub(r"[^\w\s]", " ", limpo).split()) / max(0.5, vel) + pausas


def cenas(txt):
    """[(n, início, fim, [(voz, fala)])] das cenas do roteiro."""
    out = []
    for m in re.finditer(r"^## CENA (\d+) — ([\d.]+) s a ([\d.]+) s[^\n]*\n(.*?)(?=^## |\Z)", txt, re.M | re.S):
        falas = re.findall(r"^(NARRAÇÃO|[A-ZÇÃÉÍÓÚÂÊ_]{2,})(?: \(([^)]*)\))?: *(\[.*)$", m.group(4), re.M)
        fs = []
        for nome, det, fala in falas:
            if nome == "NARRAÇÃO": voz = _falante(det.split(",")[0]) if det else "narrador"
            else: voz = _falante(nome)
            fs.append((voz, fala))
        out.append((int(m.group(1)), float(m.group(2)), float(m.group(3)), fs))
    return out


def analisar(txt, vel=None):
    vel = vel or {}; linhas = []; voz_total = plano_total = 0.0
    for n, a, b, fs in cenas(txt):
        v = sum(segundos_fala(f, vel.get(q, PADRAO)) for q, f in fs); d = b - a
        voz_total += v; plano_total += d; linhas.append((n, d, round(v, 1)))
    return {"cenas": linhas, "voz": round(voz_total, 1), "planejado": round(plano_total, 1),
            "ocupacao": round(voz_total / plano_total, 2) if plano_total else 0}


def conferir(txt, caminho=None):
    """Avisos para o validador de roteiro."""
    pasta = os.path.dirname(os.path.abspath(caminho)) if caminho else "."
    r = analisar(txt, velocidades(pasta)); av = []
    if r["planejado"] and r["ocupacao"] < MIN_OCUPACAO:
        av.append(f"RITMO: voz prevista de {r['voz']:.0f} s para {r['planejado']:.0f} s de cenas ({r['ocupacao']:.0%}); "
                  f"o áudio vai sair curto. Acrescente falas, pausas escritas ([pause], [long pause], ...) ou encurte as cenas")
    for n, d, v in r["cenas"]:
        if v > d + 0.5: av.append(f"RITMO: a fala da cena {n} leva ~{v:.1f} s e a cena tem {d:.1f} s")
    return av


if __name__ == "__main__":
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    if sys.argv[1] == "medir": print(json.dumps(medir(sys.argv[2]), ensure_ascii=False))
    else:
        cam = sys.argv[2]; txt = open(cam, encoding="utf-8").read()
        vel = velocidades(os.path.dirname(os.path.abspath(cam))); r = analisar(txt, vel)
        print(f"velocidades: {vel or 'padrão ' + str(PADRAO) + ' palavras/s'}")
        for n, d, v in r["cenas"]: print(f"cena {n:2d}: {d:5.1f} s de cena · ~{v:4.1f} s de voz")
        print(f"total: ~{r['voz']} s de voz em {r['planejado']} s de cenas ({r['ocupacao']:.0%})")
        for a in conferir(txt, cam): print("[AVISO]", a)
