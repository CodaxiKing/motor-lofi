"""Teste de fumaça do motor (roda no CI e localmente).

    python3 tests/smoke.py            -> rápido: 1 quadro por plano de cada exemplo + verificador
    python3 tests/smoke.py --video    -> também renderiza o demo4 inteiro (confere áudio e ffmpeg)

Cria vozes sintéticas para os exemplos (os áudios reais não são versionados) e falha se algo lançar exceção.
Os exemplos são demos curtas: os ERROS de estrutura do verificador (duração, escolha A/B) são esperados e ignorados;
o que conta é o motor não quebrar.
"""
import os, sys, subprocess, traceback, json

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
EXEMPLOS = ["examples/demo4/demo4.json", "examples/demo3/demo3.json", "examples/exemplo_roteiro.json",
            "tests/fixtures/recap_moments.json", "tests/fixtures/comentarios.json", "tests/fixtures/maos.json"]


def vozes_falsas(path):
    spec = json.load(open(path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(path))
    for v in spec.get("voices", {}).values():
        dst = os.path.normpath(os.path.join(base, v))
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                            "sine=f=200:d=1.2,apad=pad_dur=0.5,aloop=loop=20:size=74970", "-t", "40", dst], check=True)


def main():
    from lofi.render import Episode
    from lofi.check import check
    falhas = []
    from lofi.mapa import conferir_mapa
    for e in conferir_mapa(): falhas.append("mapa: " + e)
    for ex in EXEMPLOS:
        path = os.path.join(RAIZ, ex)
        try:
            vozes_falsas(path)
            ep = Episode(path); ep.build_audio()
            for s in ep.shots: ep.frame((s["start"] + s["end"]) / 2)
            probs = check(path, frames=False)
            inesperados = [m for l, m in probs if l == "ERRO" and not any(
                k in m for k in ("escolha A/B", "gancho", "título", "recap aponta", "no mínimo 2 min",
                                  "selo EP X/Y", "palavra da escolha"))]   # selo e voto: estrutura de episódio real
            if inesperados: falhas.append(f"{ex}: " + "; ".join(inesperados))
            print(f"ok  {ex} ({len(ep.shots)} planos)")
        except Exception:
            falhas.append(f"{ex}:\n{traceback.format_exc()}")
            print(f"FALHOU {ex}")
    if "--video" in sys.argv and not falhas:
        r = subprocess.run([sys.executable, "-m", "lofi.render", "examples/demo4/demo4.json", "--jobs", "2"], cwd=RAIZ)
        if r.returncode != 0: falhas.append("render do demo4 falhou")
        else: print("ok  render completo do demo4")
    for f in falhas: print("[ERRO]", f)
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
