"""Retenção por plano: mostra em que ponto do episódio o público sai.

    python3 -m lofi.retencao importar series/<serie>/epNN.json curva.csv tiktok   -> cruza a curva com os planos e grava
    python3 -m lofi.retencao relatorio series/<serie>                              -> resumo da série e o que repetir

A curva vem do painel da rede: CSV/TXT com "segundo,percentual" por linha, ou JSON [[segundo, percentual], ...].
Sem exportação, ponha num arquivo os pontos lidos do gráfico (print): quanto mais pontos, melhor. Percentual de 0 a 100.
Nada é inventado: sem curva, não há relatório. Queda mostra associação, não causa.
"""
import json, os, re, sys


def ler_curva(caminho):
    txt = open(caminho, encoding="utf-8").read().strip()
    if txt.startswith("["): pts = [(float(a), float(b)) for a, b in json.loads(txt)]
    else: pts = [(float(a), float(b.replace(",", "."))) for a, b in re.findall(r"^\s*([\d.]+)\s*[,;\t ]\s*([\d.,]+?)\s*%?\s*$", txt, re.M)]
    pts = sorted(pts)
    if len(pts) < 3: raise ValueError("a curva precisa de pelo menos 3 pontos (segundo, percentual)")
    return pts


def _valor(pts, t):
    if t <= pts[0][0]: return pts[0][1]
    for (a, va), (b, vb) in zip(pts, pts[1:]):
        if a <= t <= b: return va + (vb - va) * (t - a) / (b - a or 1)
    return pts[-1][1]


def _rotulo(s):
    return s.get("scene") or s.get("subject") or (s.get("cenario", {}).get("base") or s.get("cenario", {}).get("close")) or s.get("type", "scene")


def _tipo(s):
    t = s.get("type", "scene")
    if t != "scene": return t
    p = s.get("camera", {}).get("plano", "")
    return "lembranca" if s.get("lembranca") else (p or "cena")


def por_plano(sp, pts):
    subs = sp.get("subs", []); clips = sp.get("clips", []); out = []
    for s in sorted(sp.get("shots", []), key=lambda x: x["start"]):
        a, b = s["start"], s["end"]
        if a >= pts[-1][0]: break
        ini, fim = _valor(pts, a), _valor(pts, min(b, pts[-1][0]))
        txt = ""
        for c in clips:
            if a <= c["at"] < b and not c.get("gancho"):
                sub = next((x for x in subs if x["voice"] == c["voice"] and x["src"] == c["src"]), None)
                if sub: txt += " " + " ".join(sub["text"]).replace("*", "")
        queda = round(ini - fim, 2); dur = max(0.1, b - a)
        out.append({"inicio": a, "fim": b, "plano": _rotulo(s), "tipo": _tipo(s), "fala": txt.strip(), "retencao": round(fim, 1),
                    "queda": queda, "queda_por_s": round(queda / dur, 2)})
    return out


def importar(spec_path, curva, plataforma):
    sp = json.load(open(spec_path, encoding="utf-8")); pts = ler_curva(curva); planos = por_plano(sp, pts)
    pasta = os.path.dirname(os.path.abspath(spec_path)); p = os.path.join(pasta, "retencao.json")
    d = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    d.setdefault(str(sp.get("episode", 0)), {})[plataforma] = {"curva": pts, "planos": planos}
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return planos


def piores(planos, n=3):
    return sorted([p for p in planos if p["queda"] > 0], key=lambda p: -p["queda_por_s"])[:n]


def relatorio(pasta):
    p = os.path.join(pasta, "retencao.json")
    if not os.path.exists(p): return "Sem curva de retenção importada."
    d = json.load(open(p, encoding="utf-8")); L = []; tipos = {}
    for ep in sorted(d, key=int):
        for rede, r in d[ep].items():
            pts = [tuple(x) for x in r["curva"]]
            L.append(f"Ep. {ep} · {rede}: {_valor(pts, 3):.0f}% aos 3 s · {_valor(pts, pts[-1][0]):.0f}% no fim")
            for q in piores(r["planos"]):
                L.append(f"  queda de {q['queda']:.1f} pontos em {q['inicio']:.0f}–{q['fim']:.0f} s ({q['plano']}): {q['fala'] or 'sem fala'}")
            for q in r["planos"]:
                t = tipos.setdefault(q["tipo"], [0.0, 0.0]); t[0] += q["queda"]; t[1] += q["fim"] - q["inicio"]
    if tipos:
        L.append("Queda média por segundo, por tipo de plano:")
        for k, (q, s) in sorted(tipos.items(), key=lambda kv: kv[1][0] / max(0.1, kv[1][1])):
            L.append(f"  {k}: {q / max(0.1, s):.2f}")
    return "\n".join(L)


if __name__ == "__main__":
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    if sys.argv[1] == "importar":
        ps = importar(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "tiktok")
        print(f"{len(ps)} planos cruzados com a curva")
        for q in piores(ps): print(f"queda de {q['queda']:.1f} pontos em {q['inicio']:.0f}–{q['fim']:.0f} s ({q['plano']}): {q['fala'] or 'sem fala'}")
    else: print(relatorio(sys.argv[2]))
