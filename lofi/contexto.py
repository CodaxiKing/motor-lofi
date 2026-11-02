"""Dossiê de contexto para escrever o próximo roteiro sem perder nada da história.

    python3 -m lofi.contexto series/dia-zero 6          → series/dia-zero/_contexto_ep06.md (e imprime)
    python3 -m lofi.contexto series/dia-zero extra 5    → contexto para o extra que sai depois do ep. 5

Junta num arquivo só: cabeçalho e regras da série, finais e consequências registradas, votos e placares, resumos de todos os
episódios, como o episódio anterior terminou (lugar, dia/hora, quem carrega o quê, as últimas cenas do roteiro e a pergunta A/B),
os personagens (fichas travadas + o que a bíblia diz deles), os fios em aberto, o mapa da cidade e os cenários/marcas disponíveis.
Leia este arquivo inteiro antes de escrever a ESCALETA.
"""
import sys, os, re, json, glob


def _secoes(md):
    out, atual = {}, "_topo"
    for l in md.split("\n"):
        m = re.match(r"^##\s+(.+)", l)
        if m: atual = m.group(1).strip(); out[atual] = []
        else: out.setdefault(atual, []).append(l)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def _cenas(md):
    partes = re.split(r"^(#+\s*CENA\s+\d+[^\n]*)$", md, flags=re.M)
    return [(partes[i].strip("# ").strip(), re.split(r"\n---|\n##\s", partes[i + 1])[0].strip()) for i in range(1, len(partes) - 1, 2)]


def gerar(pasta, n, extra=False):
    bib = open(os.path.join(pasta, "biblia.md"), encoding="utf-8").read(); sec = _secoes(bib)
    L = [f"# CONTEXTO · {'EXTRA depois do ep. ' + str(n) if extra else 'EPISÓDIO ' + str(n)}", ""]
    L += ["## 1. A série", sec.get("_topo", "")]
    for k in sec:
        if re.search(r"resumo$|mistério|regras|finais|cor de cada", k, re.I) and k != "Resumos": L += ["", f"### {k}", sec[k]]
    L += ["", "## 2. Votos e placares (tabela de episódios)"]
    L += [sec.get(k, "") for k in sec if k.lower().startswith("episódios")]
    L += ["", "## 3. O que já aconteceu (resumos)", sec.get("Resumos", "(sem resumos)")]
    for k in sec:
        if k.lower().startswith("extras"): L += ["", "### Extras já feitos", sec[k]]
    # episódio anterior
    ant = n if extra else n - 1
    L += ["", f"## 4. Onde a história parou (fim do ep. {ant})"]
    mundo_p = os.path.join(pasta, "mundo.json")
    if os.path.exists(mundo_p):
        mundo = json.load(open(mundo_p, encoding="utf-8")); fim = mundo.get("fim", {}).get(str(ant))
        if fim:
            L.append(f"- Lugar: **{fim.get('lugar')}** · {fim.get('rotulo', 'DIA')} {fim.get('dia') or fim.get('noite')} · {fim.get('hora')}")
            for quem, itens in fim.get("inventario", {}).items(): L.append(f"- {quem} carrega: {', '.join(itens) or 'nada'}")
            if fim.get("nota"): L.append(f"- Nota: {fim['nota']}")
    cont = [k for k in sec if k.lower().startswith("continuidade")]
    for k in cont: L += ["", sec[k]]
    rp = os.path.join(pasta, f"ep{ant:02d}_roteiro.md")
    if os.path.exists(rp):
        md = open(rp, encoding="utf-8").read(); cs = _cenas(md)
        if cs:
            L += ["", f"### Últimas cenas do ep. {ant} (o próximo começa exatamente daqui)"]
            for tit, corpo in cs[-3:]: L += [f"**{tit}**", corpo, ""]
        m = re.search(r"\*\*O que acontece em cada opção.*?(?=\n\*\*Resumo|\n---|\Z)", md, re.S)
        if m: L += ["### O que cada opção prometeu", m.group(0).strip()]
    # personagens
    L += ["", "## 5. Personagens"]
    for k in sec:
        if k.lower().startswith("personagens"): L.append(sec[k])
    pj = os.path.join(pasta, "personagens.json")
    if os.path.exists(pj):
        fichas = {k: v for k, v in json.load(open(pj, encoding="utf-8")).items() if not k.startswith("_")}
        L.append("Fichas travadas (visual não muda): " + ", ".join(sorted(fichas)))
    for k in sec:
        if re.match(r"pistas", k, re.I): L += ["", f"## 5b. {k} (pague as pendentes, plante novas)", sec[k]]
    # fios em aberto: linhas da bíblia com consequências ("→") ou perguntas
    fios = [l.strip() for l in bib.split("\n") if ("→" in l or l.strip().endswith("?")) and len(l.strip()) > 8]
    if fios: L += ["", "## 6. Fios em aberto e consequências registradas (honre todos)"] + [f"- {f.lstrip('- ')}" for f in fios]
    # mapa
    if os.path.exists(mundo_p):
        mundo = json.load(open(mundo_p, encoding="utf-8"))
        L += ["", "## 7. Mapa da cidade (só ande por estas ligações)"]
        for nome, l in mundo.get("lugares", {}).items(): L.append(f"- **{nome}**: {', '.join('`'+c+'`' for c in l.get('cenarios', []))} — {l.get('nota', '')}")
        L.append("Ligações:")
        for a, b, como in mundo.get("ligacoes", []): L.append(f"- {a} ↔ {b}: {como}")
    # cenários e marcas
    try:
        from .mapa import MAPA
        usados = set()
        if os.path.exists(mundo_p):
            for l in json.load(open(mundo_p, encoding="utf-8")).get("lugares", {}).values(): usados |= set(l.get("cenarios", []))
        L += ["", "## 8. Marcas de posição dos cenários da série"]
        for c in sorted(usados):
            ms = MAPA.get(c, {}).get("marcas", {})
            if ms: L.append(f"- `{c}`: " + ", ".join(f"`{k}`" for k in ms))
    except Exception:
        pass
    L += ["", "## 9. Checklist antes de escrever",
          "- A 1ª cena começa no lugar, hora e estado em que o episódio anterior terminou (seção 4) e mostra a consequência do voto.",
          "- Escreva a ESCALETA (6–10 batidas) antes das cenas; cada cena serve a uma batida.",
          "- Toda cena começa onde a anterior terminou: quem entra ganha `ENTRA:`, quem sai ganha `SAI:`, mudança de lugar ganha `LIGAÇÃO:`.",
          "- Cada fio da seção 6 que este episódio toca precisa ser pago ou avançado; nenhum personagem esquece o que viveu.",
          "- O gancho (cena 0) mostra um momento que acontece de verdade mais adiante no episódio.",
          "- Escreva 3 opções de GANCHO (perguntas sem resposta) e escolha a mais estranha.",
          "- Uma VIRADA a cada 20–30 s; narração só para o que a imagem não mostra; cada personagem fala do jeito dele (seção 5).",
          "- Mexa em pelo menos um DESEJO, MEDO ou SEGREDO; pague uma pista pendente e plante uma nova (seção 5b).",
          "- A escolha A/B custa algo dos dois lados (GANHA/PERDE); termine no meio da ação, com uma informação nova."]
    txt = "\n".join(L).strip() + "\n"
    out = os.path.join(pasta, f"_contexto_{'extra' if extra else 'ep'}{n:02d}.md")
    open(out, "w", encoding="utf-8").write(txt)
    return out, txt


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(1)
    extra = len(a) > 2 and a[1] == "extra"
    out, txt = gerar(a[0], int(a[-1]), extra)
    print(txt); print(f"(salvo em {out})")
