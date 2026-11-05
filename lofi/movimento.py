"""Verificador de movimento e corpo: confere no roteiro técnico o que o olho pegaria no vídeo.

    python3 -m lofi.movimento series/<serie>/epNN.json

Acusa personagem parado sem função, deslizando, andando no lugar, sentado sem assento, abraço de longe e postura ou objeto
que muda de um plano para o outro sem mostrar. Também roda dentro do `lofi.check`.
"""
import json, sys

PARADO_FALANDO = 5.0; PARADO_MUDO = 3.0
ASSENTO = ("sofa", "cadeira", "cama", "banco", "poltrona", "mesa_cozinha", "mesa", "maca", "chao_porta", "cadeira_rodas")
DESCONTA = ("mark", "x", "y", "pose", "emotion", "view", "tremble", "gesture", "look", "walk", "facing", "rot", "lift")


def _mudas(v): return isinstance(v, list) and len(v) > 1 and len({json.dumps(i[-1] if isinstance(i, list) else i, sort_keys=True, default=str) for i in v}) > 1
def _fim(v):
    if isinstance(v, list) and v: return v[-1][-1] if isinstance(v[-1], list) else v[-1]
    return v
def _ini(v):
    if isinstance(v, list) and v: return v[0][-1] if isinstance(v[0], list) else v[0]
    return v


def _viva(a):
    if a.get("tremble") and _ini(a["tremble"]): return True
    return any(_mudas(a.get(k)) for k in DESCONTA) or a.get("run") or bool(a.get("gesture"))


def _moveu(a): return _mudas(a.get("mark")) or _mudas(a.get("x")) or _mudas(a.get("y"))


def _fala(sp, a, s):
    voz = a.get("voice", a.get("char"))
    return sum(max(0, min(c["at"] + c["src"][1] - c["src"][0], s["end"]) - max(c["at"], s["start"])) for c in sp.get("clips", []) if c.get("voice") == voz)


def analisar(sp):
    avisos = []; ultimo = {}     # personagem -> como terminou no plano anterior do mesmo cenário
    shots = sorted(sp.get("shots", []), key=lambda s: s["start"])
    for s in shots:
        if s.get("type", "scene") != "scene": continue
        lug = s.get("scene") or json.dumps(s.get("cenario", {}).get("base"), default=str)
        d = s["end"] - s["start"]; t = s["start"]; trav = bool(s.get("travelling")); mem = bool(s.get("lembranca") or s.get("insercao"))
        atores = [a for a in s.get("actors", []) if not a.get("_crowd")]
        for a in atores:
            q = a.get("char", "?")
            if not _viva(a) and not trav:
                fala = _fala(sp, a, s); lim = PARADO_FALANDO if fala > 0.4 else PARADO_MUDO
                if d > lim: avisos.append((t, f"{q} parado por {d:.1f} s (sem gesto, olhar ou mudança de pose)"))
            andando = a.get("walk")
            if _moveu(a) and not andando and not trav and not a.get("livre"):
                avisos.append((t, f"{q} muda de lugar sem andar (vai deslizar)"))
            if andando and _ini(andando) and not _moveu(a) and not trav:
                avisos.append((t, f"{q} anda sem sair do lugar"))
            if _ini(a.get("pose")) == "sit" and not any(k in str(a.get("mark", "")) for k in ASSENTO) and not a.get("livre"):
                avisos.append((t, f"{q} sentado sem assento (marca {a.get('mark')})"))
            ant = ultimo.get((lug, q))
            if ant and not mem and not trav and not _mudas(a.get("pose")):
                if ant["pose"] == "sit" and _ini(a.get("pose")) != "sit" and not _moveu(a) and a.get("mark") == ant["mark"]:
                    avisos.append((t, f"{q} estava sentado e aparece de pé sem levantar"))
                if ant["prop"] and not a.get("prop") and t - ant["fim"] < 0.5:
                    avisos.append((t, f"{q} perdeu o objeto ({ant['prop']}) de um plano para o outro"))
            if not mem:
                ultimo[(lug, q)] = {"pose": _fim(a.get("pose")), "prop": _fim(a.get("prop")), "fim": s["end"], "mark": _fim(a.get("mark"))}
        abr = [a for a in atores if _ini(a.get("pose")) == "hug"]
        if len(abr) == 2:
            dx = abs((abr[0].get("dx") or 0) - (abr[1].get("dx") or 0))
            if abr[0].get("mark") == abr[1].get("mark") and dx > 220: avisos.append((t, f"abraço com {dx} px de distância (use ~140)"))
    return avisos


if __name__ == "__main__":
    av = analisar(json.load(open(sys.argv[1], encoding="utf-8")))
    for t, m in av: print(f"[AVISO] {t:6.1f} s: {m}")
    print(f"{len(av)} aviso(s) de movimento")
