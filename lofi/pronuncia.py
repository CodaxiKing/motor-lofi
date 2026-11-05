"""Confere a pronúncia antes da montagem: compara o que foi gravado com a narração do roteiro.

    python3 -m lofi.pronuncia series/<serie>/epNN_roteiro.md [pasta_das_vozes]

Lê a seção "NARRAÇÃO PARA O ELEVENLABS" (### <voz>), transcreve series/<serie>/epNN/<voz>.* e lista as falas que não batem.
Transcrição erra, então o resultado é "confira de ouvido": número e nome próprio diferentes têm prioridade (ALTA).
"""
import difflib, glob, json, os, re, sys, unicodedata

UN = "zero um dois tres quatro cinco seis sete oito nove dez onze doze treze quatorze quinze dezesseis dezessete dezoito dezenove".split()
DZ = {20: "vinte", 30: "trinta", 40: "quarenta", 50: "cinquenta", 60: "sessenta", 70: "setenta", 80: "oitenta", 90: "noventa"}
NUMEROS = set(UN) | set(DZ.values()) | {"catorze", "cem", "mil"}
ALIAS = {"catorze": "quatorze", "uma": "um", "duas": "dois", "e": ""}


def por_extenso(n):
    n = int(n)
    if n < 20: return UN[n]
    if n < 100: return DZ[n - n % 10] + (" " + UN[n % 10] if n % 10 else "")
    return " ".join(UN[int(c)] for c in str(n))


def palavras(txt):
    txt = re.sub(r"\[[^\]]*\]", " ", txt)
    txt = unicodedata.normalize("NFD", txt.lower()); txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    txt = re.sub(r"\b(\d{1,2})\s*[h:]\s*(\d{2})\b", lambda m: por_extenso(m[1]) + " " + por_extenso(m[2]), txt)
    txt = re.sub(r"\d+", lambda m: " " + por_extenso(m[0]) + " ", txt)
    out = []
    for w in re.findall(r"[a-z]+", txt):
        w = ALIAS.get(w, w)
        if w: out.append(w)
    return out


def narracao(txt):
    """{voz: [falas]} da seção de narração do roteiro."""
    m = re.search(r"^## NARRAÇÃO PARA O ELEVENLABS.*?(?=^## |\Z)", txt, re.M | re.S)
    if not m: return {}
    out = {}
    for b in re.finditer(r"^### *([^\n]+)\n(.*?)(?=^### |\Z)", m.group(0), re.M | re.S):
        out[b.group(1).split()[0].lower()] = [l.strip() for l in b.group(2).splitlines() if l.strip().startswith("[")]
    return out


def comparar(falas, trechos):
    """Alinha as palavras do roteiro às transcritas. trechos = [{"s", "e", "t"}]. Devolve os problemas por fala."""
    ouvido = []
    for s in trechos:
        for w in palavras(s["t"]): ouvido.append((w, s["s"]))
    ord_ = [w for w, _ in ouvido]; rot = []; idx = []
    for i, f in enumerate(falas):
        for w in palavras(f): rot.append(w); idx.append(i)
    sm = difflib.SequenceMatcher(None, rot, ord_, autojunk=False)
    probs = {}
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal" or a0 == a1: continue
        i = idx[a0]; esperado = rot[a0:a1]; escutado = ord_[b0:b1]
        if len(esperado) == 1 and escutado and difflib.SequenceMatcher(None, esperado[0], "".join(escutado)).ratio() > 0.8: continue
        alta = any(w in NUMEROS for w in esperado + escutado)
        t = ouvido[min(b0, len(ouvido) - 1)][1] if ouvido else 0
        probs.setdefault(i, []).append({"esperado": " ".join(esperado), "ouvido": " ".join(escutado), "t": t, "alta": alta})
    return [{"fala": falas[i], "problemas": p} for i, p in sorted(probs.items())]


def _audio(pasta, voz):
    for f in sorted(glob.glob(os.path.join(pasta, voz + ".*"))):
        if not f.endswith((".json", ".wav")) or f.endswith(voz + ".wav"): return f


def conferir(roteiro, pasta=None):
    from . import transcribe as T
    txt = open(roteiro, encoding="utf-8").read()
    pasta = pasta or os.path.splitext(roteiro)[0].replace("_roteiro", ""); res = {}
    rec = None
    for voz, falas in narracao(txt).items():
        a = _audio(pasta, voz)
        if not a: print(f"[FALTA] sem áudio de {voz} em {pasta}"); continue
        cache = a + ".json"
        if os.path.exists(cache) and os.path.getmtime(cache) >= os.path.getmtime(a): trechos = json.load(open(cache, encoding="utf-8"))
        else:
            if rec is None: rec, _ = T.load_recognizer("pt")
            trechos, _ = T.transcribe(a, rec=rec)
        if not any(t.get("t") for t in trechos): print(f"[ERRO] {voz}: transcrição só com tempos"); continue
        res[voz] = comparar(falas, trechos)
        for r in res[voz]:
            for p in r["problemas"]:
                print(f"[{'ALTA' if p['alta'] else 'CONFIRA'}] {voz} ~{p['t']:.1f} s: roteiro \"{p['esperado']}\" · ouvido \"{p['ouvido'] or '(nada)'}\"")
    n = sum(len(r["problemas"]) for v in res.values() for r in v)
    print(f"{n} trecho(s) para conferir de ouvido" if n else "todas as falas batem com o roteiro")
    return res


if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    conferir(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
