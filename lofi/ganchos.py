"""Hook Engine: três aberturas (primeiros 3–5 s) para o mesmo episódio, com estratégias diferentes, avaliadas por
critérios explicáveis, e a troca do gancho sem mexer no resto do roteiro.

O gancho nunca é inventado: cada alternativa sai de uma cena do próprio episódio (um flash-forward da frase mais forte
daquela cena), então nenhuma contradiz o que vem depois. Só entram cenas comuns a todos os caminhos de voto.

Estratégias: lacuna_curiosidade, antecipacao, incongruencia, conflito_imediato, misterio_contextualizado, identificacao,
revelacao_parcial. Notas (0–1): clareza, relevancia, originalidade, continuidade, duracao. Quando há experimentos
com resultado conclusivo na série (lofi/experimentos.py) e as recomendações estão ligadas, a estratégia com evidência
ganha um bônus pequeno e a explicação diz de onde ele veio; sem dados, só os critérios narrativos contam.

    python3 -m lofi.ganchos gerar   series/o-ultimo-estoque/planos/ep02.json          -> ganchos/ep02.json (3 alternativas)
    python3 -m lofi.ganchos gerar   series/x/planos/ep02.json --regenerar             -> 3 novas, sem repetir as anteriores
    python3 -m lofi.ganchos ver     series/x/planos/ep02.json
    python3 -m lofi.ganchos escolher series/x/planos/ep02.json B                     -> integra B no plano/roteiro/JSON
    python3 -m lofi.ganchos escolher series/x/planos/ep02.json auto                  -> a de maior nota (critério impresso)
    python3 -m lofi.ganchos avaliar "AS BATIDAS / VÊM DE DENTRO"                      -> notas de um gancho escrito à mão
"""
import json, os, re, sys, datetime
from .narrativa import norm, palavras, carregar_memoria, pasta_da_serie, ramos

WPS = 2.4            # palavras por segundo da narração da casa (docs/narracao_estilo.md)
MAX_S = 5.0          # janela do gancho
ESTRATEGIAS = {
    "lacuna_curiosidade": "uma informação intrigante que faz uma pergunta específica",
    "antecipacao": "o risco ou o prazo antes do acontecimento (relógio correndo)",
    "incongruencia": "algo fora do lugar dentro das regras do mundo",
    "conflito_imediato": "uma situação que exige reação agora",
    "misterio_contextualizado": "informação incompleta, mas compreensível",
    "identificacao": "uma situação humana com a qual o espectador se liga",
    "revelacao_parcial": "a consequência sem a explicação",
}
GENERICOS = ("voce nao vai acreditar", "assista ate o fim", "isso mudou tudo", "ninguem esperava", "o que aconteceu depois",
             "voce precisa ver", "parte 2", "fica ate o final", "nao pule", "chocante")
SINAIS = {   # pistas lexicais de cada estratégia (texto sem acento)
    "antecipacao": r"\b\d{1,2}\s*(h|horas?|min|minutos?|segundos?)\b|\bfaltam?\b|\bate as\b|\bfecha\b|\bantes de\b|\bprazo\b|\bvai\b|\bultim[oa]\b",
    "incongruencia": r"\bnao e\b|\bnao abre\b|\bninguem\b|\bvazi[oa]\b|\bde dentro\b|\berro\b|\bmesmo ritmo\b|\bparad[oa]s?\b|\bsozinh[oa]\b|\bao contrario\b",
    "conflito_imediato": r"\bcorr|\bbate|\bquebr|\bexplod|\bpux|\bgrit|\bataca|\bderrub|\bfoge|\bfuga|\bseguranca|\bsegura\b|\bagora\b",
    "lacuna_curiosidade": r"\bpor que\b|\bquem\b|\bo que\b|\bcracha\b|\boculos\b|\bbilhete\b|\bchamada\b|\bnome\b|\bfoto\b|\?",
    "misterio_contextualizado": r"\balguem\b|\balguma coisa\b|\bvoz\b|\bsombra\b|\bvulto\b|\bbatid|\bmarca\b|\bgravacao\b|\bsinal\b",
    "identificacao": r"\bvoce\b|\bsua? (avo|mae|filha|casa)\b|\bningu[e]m pra\b|\bmedo\b|\bsozinh|\bfamilia\b|\bamigo\b",
    "revelacao_parcial": r"\bja\b|\btarde\b|\bmorto\b|\bmordid|\babert[oa]\b|\bsumiu\b|\bvaz[io]|\bdentro\b",
}
PRONOMES_SOLTOS = ("ele", "ela", "eles", "elas", "dele", "dela", "isso", "aquilo", "la")
SOM = {"antecipacao": "click", "conflito_imediato": "impact", "incongruencia": "static", "revelacao_parcial": "bang",
       "lacuna_curiosidade": "heartbeat", "misterio_contextualizado": "breath", "identificacao": "heartbeat"}   # nomes de lofi/audio.py


# ---------------- material do episódio ----------------
PERGUNTA_FINAL = r"\be voce\?|\bou \w+(ava|ia|eria|aria)\b|\bvoce \w+(ava|ia)\b.*\?|\be voce\b.*\?"   # "você X-ava... ou Y-ava?"
INCOMPLETO = ("diz", "repete", "e", "de", "do", "da", "pra", "com", "o", "a", "um", "uma", "que", "no", "na", "ou", "mas")


def frases_de(fragmentos):
    """Junta pedaços de legenda em frases completas (até o ponto) e pares curtos de frases seguidas."""
    frases = []; atual = ""
    for f in fragmentos:
        f = re.sub(r"\[[^\]]*\]", "", str(f)).replace("*", "").strip()
        if not f: continue
        atual = (atual + " " + f).strip()
        if re.search(r"[.!?…:]$", f): frases.append(atual.rstrip(":")); atual = ""
    if atual: frases.append(atual)
    pares = [a + " " + b for a, b in zip(frases, frases[1:]) if len((a + " " + b).split()) <= 8]
    return frases + pares


def fontes_do_plano(plano):
    """[(cena, texto, peso_posicao, eh_virada, eh_final)] só de cenas comuns a todos os caminhos.
    A cena da pergunta ao público fica de fora: pergunta não é gancho."""
    cad = plano.get("cadeia", []); n = len(cad) or 1
    comuns = [c for c in cad if not c.get("voto")]
    def eh_pergunta(c): return bool(re.search(PERGUNTA_FINAL, norm(" ".join(c.get("narracao") or [])))) or c.get("decisao", "").strip().upper() == "FIM."
    corpo = [c for c in comuns if not eh_pergunta(c)]
    out = []
    for i, c in enumerate(cad):
        if c.get("voto") or c not in corpo: continue
        frs = frases_de(c.get("narracao") or []) or [c.get("acontecimento", ""), c.get("consequencia", "")]
        for f in frs:
            if f: out.append((c.get("n"), f, (i + 1) / n, c.get("n") == plano.get("virada"), c is corpo[-1]))
    return out


def fontes_do_roteiro(md):
    """Mesmo formato, a partir de um epNN_roteiro.md (linhas NARRAÇÃO de cada CENA)."""
    from .contexto import _cenas
    cenas = [(t, b) for t, b in _cenas(md) if not re.search(r"CENA\s+0\b", t)]
    n = len(cenas) or 1; out = []
    for i, (tit, bloco) in enumerate(cenas):
        num = int(re.search(r"CENA\s+(\d+)", tit).group(1))
        m = re.search(r"^NARRAÇÃO:\s*(.+)$", bloco, re.M)
        if not m: continue
        frases = [x.strip() for x in re.sub(r"\[[^\]]*\]", "", m.group(1)).replace("*", "").split(" / ") if x.strip()]
        txt = []; atual = ""
        for f in frases:                         # junta pedaços de legenda numa frase (até o ponto)
            atual = (atual + " " + f).strip()
            if re.search(r"[.!?…:]$", f): txt.append(atual); atual = ""
        if atual: txt.append(atual)
        vir = bool(re.search(r"^VIRADA:\s*(?!nenhuma)", bloco, re.M | re.I))
        for f in txt: out.append((num, f, (i + 1) / n, vir, i == n - 1))
    return out


# ---------------- avaliação ----------------
def duracao(texto):
    ws = re.findall(r"\w+", texto)
    return round(len(ws) / WPS + 0.4 + 0.25 * texto.count("/"), 2)


def _linhas(texto, maxw=4):
    ws = texto.replace("/", " ").split()
    if len(ws) <= maxw: return [" ".join(ws).upper()]
    meio = (len(ws) + 1) // 2
    return [" ".join(ws[:meio]).upper(), " ".join(ws[meio:]).upper()]


def _curto(texto, maxw=8):
    """Corta no fim de uma oração para caber na janela do gancho."""
    t = texto.strip().rstrip(":")
    if len(t.split()) <= maxw: return t
    partes = re.split(r"(?<=[.,:;])\s+", t)
    acc = ""
    for p in partes:
        if len((acc + " " + p).split()) > maxw: break
        acc = (acc + " " + p).strip()
    return acc or " ".join(t.split()[:maxw])


def estrategias_de(texto):
    t = norm(texto)
    return {k: len(re.findall(rx, t)) for k, rx in SINAIS.items() if re.search(rx, t)}


def avaliar(texto, estrategia=None, cena_txt="", episodio_txt="", posicao=0.5, virada=False, final=False, anteriores=(), proibidas=(), evidencia=None):
    """Notas explicáveis de um gancho. Devolve (total, notas, explicacao)."""
    t = norm(texto); ws = re.findall(r"\w+", t); exp = []
    # clareza
    cl = 1.0 if len(ws) <= 7 else max(0.2, 1 - (len(ws) - 7) * 0.12)
    if ws and ws[0] in PRONOMES_SOLTOS: cl -= 0.35; exp.append("começa com pronome sem referência (quem é 'ele/ela'?)")
    elif any(x in PRONOMES_SOLTOS[:6] for x in ws): cl -= 0.2; exp.append("pronome sem nome: quem chega agora não sabe quem é 'ela/ele'")
    if re.match(r"(do|ao) lado\b|ali\b|dali\b", t): cl -= 0.3; exp.append("começa com referência a algo que o espectador ainda não viu ('do lado' de quê?)")
    if ws and ws[-1] in INCOMPLETO: cl -= 0.5; exp.append("frase incompleta (termina pendurada)")
    if len([x for x in ws if len(x) > 3]) < 2 or len(ws) < 3: cl -= 0.4; exp.append("pouca informação concreta para entender em 3 s")
    if re.search(PERGUNTA_FINAL, t): cl -= 0.6; exp.append("é a pergunta ao público, não um gancho")
    if len(ws) <= 7: exp.append(f"{len(ws)} palavras: lê em menos de 3 s")
    # relevância: de onde vem na história
    rel = 0.45 + 0.35 * posicao + (0.2 if virada else 0) + (0.15 if final else 0)
    if virada: exp.append("vem da virada do episódio")
    if final: exp.append("vem do fim do episódio (flash-forward da consequência)")
    rel = min(1.0, rel)
    # originalidade: não genérico, não repete os ganchos anteriores da série
    ori = 1.0
    if any(g in t for g in GENERICOS): ori = 0.0; exp.append("frase genérica de clickbait")
    rep = max((len(palavras(texto) & palavras(a)) / max(1, len(palavras(texto))) for a in anteriores), default=0)
    if rep > 0.5: ori -= 0.4; exp.append("repete palavras de um gancho anterior da série")
    # continuidade: precisa estar no episódio e não pode contar o que a série guarda para depois
    cont = 1.0
    if episodio_txt and not palavras(texto) <= palavras(episodio_txt) | {"voce"}:
        fora = palavras(texto) - palavras(episodio_txt)
        cont -= min(0.8, 0.3 * len(fora)); exp.append(f"palavras que não estão no episódio: {', '.join(sorted(fora))}")
    for p in proibidas:
        if re.search(r"\b" + re.escape(norm(p)) + r"\b", t): cont = 0.0; exp.append(f"conta '{p}' antes da hora (memória da série)")
    # duração
    d = duracao(texto); du = 1.0 if d <= 3.5 else (0.7 if d <= MAX_S else 0.2)
    exp.append(f"duração estimada {d:.1f} s")
    notas = {"clareza": round(max(0, cl), 2), "relevancia": round(rel, 2), "originalidade": round(max(0, ori), 2),
             "continuidade": round(max(0, cont), 2), "duracao": du}
    total = 0.0 + 0.25 * notas["clareza"] + 0.25 * notas["relevancia"] + 0.15 * notas["originalidade"] + 0.25 * notas["continuidade"] + 0.10 * du
    if evidencia and estrategia in evidencia:
        total += 0.05; exp.append(f"bônus pequeno: {evidencia[estrategia]}")
    return round(total, 3), notas, exp


# ---------------- geração ----------------
def _historico(pasta, ep):
    """Ganchos escolhidos nos episódios anteriores (texto e estratégia)."""
    out = []; d = os.path.join(pasta, "ganchos")
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            m = re.match(r"ep(\d+)\.json$", f)
            if not m or int(m.group(1)) >= ep: continue
            g = json.load(open(os.path.join(d, f), encoding="utf-8")); e = g.get("escolhido")
            c = next((c for c in g.get("candidatos", []) if c["id"] == e), None)
            if c: out.append((c["texto"], c["estrategia"]))
    return out


def gerar(plano, pasta=None, fontes=None, excluir=(), evidencia=None, n=3):
    """Três alternativas (A, B, C) com estratégias diferentes, todas do mesmo episódio."""
    ep = int(plano.get("episodio", 0)); pasta = pasta or "."
    fontes = fontes if fontes is not None else fontes_do_plano(plano)
    mem = carregar_memoria(pasta) if os.path.isdir(pasta) else {"fatos": []}
    proibidas = [p for f in mem.get("fatos", []) if (f.get("revelar_no_ep") or 0) >= ep and not f.get("publico_sabe") for p in f.get("palavras", [])]
    # o gancho provoca; quem revela é o episódio: o que este episódio revela fica fora da abertura
    hist = _historico(pasta, ep) if os.path.isdir(pasta) else []
    anteriores = [h[0] for h in hist]; usadas = [h[1] for h in hist[-2:]]
    ep_txt = " ".join(f[1] for f in fontes) + " " + json.dumps(plano.get("cadeia", []), ensure_ascii=False)
    excl = {norm(x) for x in excluir}
    cand = []
    for cena, frase, pos, vir, fim in fontes:
        txt = _curto(frase)
        if len(txt.split()) < 2 or norm(txt) in excl: continue
        sig = dict(estrategias_de(txt))
        if vir or fim: sig.setdefault("revelacao_parcial", 1)
        for est, forca in sig.items():
            if est in excl: continue
            tot, notas, exp = avaliar(txt, est, episodio_txt=ep_txt, posicao=pos, virada=vir, final=fim, anteriores=anteriores, proibidas=proibidas, evidencia=evidencia)
            if usadas and est == usadas[-1]: tot -= 0.08; exp = exp + [f"estratégia '{est}' abriu o episódio anterior (variar o formato)"]
            elif est in usadas: tot -= 0.04; exp = exp + [f"estratégia '{est}' abriu um dos dois episódios anteriores"]
            tot = min(1.0, tot + 0.02 * min(forca, 3))
            cand.append({"estrategia": est, "texto": txt, "cena": cena, "total": round(tot, 3), "notas": notas, "explicacao": exp})
    cand.sort(key=lambda c: (-c["total"], c["cena"] or 0, c["texto"]))
    escolhidos = []
    def parecido(a, b):                              # mesma frase com outra roupa não conta como alternativa
        pa, pb = palavras(a), palavras(b)
        return bool(pa and pb) and len(pa & pb) / len(pa | pb) >= 0.4
    for rodada in (True, False):                     # 1ª rodada: cenas diferentes; 2ª: completa se faltar
        for c in cand:
            if len(escolhidos) == n: break
            if any(c["estrategia"] == x["estrategia"] or parecido(c["texto"], x["texto"]) for x in escolhidos): continue
            if rodada and any(c["cena"] == x["cena"] for x in escolhidos): continue
            escolhidos.append(c)
    cenas = {c.get("n"): c for c in plano.get("cadeia", [])}
    for i, c in enumerate(escolhidos):
        c["id"] = "ABC"[i]; c["linhas"] = _linhas(c["texto"]); c["duracao_s"] = duracao(c["texto"])
        c["descricao_estrategia"] = ESTRATEGIAS[c["estrategia"]]
        bt = cenas.get(c["cena"], {})
        c["visual"] = f"cenário `{bt.get('cenario')}` da cena {c['cena']}: {bt.get('acontecimento', '')}"[:160] if bt else f"a imagem da cena {c['cena']}"
        c["som"] = SOM.get(c["estrategia"], "heartbeat")
    return escolhidos


def compativel(candidato, plano):
    """O gancho é de uma cena comum a todos os caminhos e tem palavras dela."""
    cena = next((c for c in plano.get("cadeia", []) if c.get("n") == candidato.get("cena")), None)
    if cena is None or cena.get("voto"): return False
    return bool(palavras(candidato["texto"]) & palavras(json.dumps(cena, ensure_ascii=False)))


# ---------------- arquivo de ganchos e integração ----------------
def arquivo(caminho_plano):
    pasta = pasta_da_serie(caminho_plano); ep = int(json.load(open(caminho_plano, encoding="utf-8"))["episodio"])
    return os.path.join(pasta, "ganchos", f"ep{ep:02d}.json")


def gerar_arquivo(caminho_plano, regenerar=False):
    from .experimentos import evidencia_por_estrategia
    plano = json.load(open(caminho_plano, encoding="utf-8")); pasta = pasta_da_serie(caminho_plano)
    dest = arquivo(caminho_plano); antigo = json.load(open(dest, encoding="utf-8")) if os.path.isfile(dest) else None
    excluir = []
    if regenerar and antigo:
        for c in antigo["candidatos"]: excluir += [c["texto"], c["estrategia"]]
    ev = evidencia_por_estrategia(pasta)
    cands = gerar(plano, pasta, excluir=excluir, evidencia=ev)
    if len(cands) < 3 and regenerar:                 # acabou o material com estratégias novas: libera as estratégias
        cands = gerar(plano, pasta, excluir=[c["texto"] for c in antigo["candidatos"]], evidencia=ev)
    hist = (antigo or {}).get("historico", [])
    if antigo: hist.append({"candidatos": antigo["candidatos"], "escolhido": antigo.get("escolhido"), "substituido_em": _agora()})
    dado = {"serie": os.path.basename(pasta), "episodio": plano["episodio"], "gerado_em": _agora(), "candidatos": cands,
            "escolhido": None, "criterio": None, "evidencia_usada": ev or None, "historico": hist}
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    json.dump(dado, open(dest, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    return dado


def _agora():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def escolher(caminho_plano, qual="auto", registrar=True):
    """Integra a alternativa escolhida no plano (e no roteiro .md e no JSON, se existirem e não estiverem travados).
    Só as linhas do gancho mudam; devolve {"escolhido", "criterio", "alterados": [arquivos]}."""
    from .protecao import bloquear
    dest = arquivo(caminho_plano); g = json.load(open(dest, encoding="utf-8"))
    cands = g["candidatos"]
    if qual == "auto":
        c = max(cands, key=lambda c: c["total"])
        criterio = f"maior nota ({c['total']}): " + "; ".join(c["explicacao"][:3])
    else:
        c = next(x for x in cands if x["id"] == qual); criterio = "escolha do autor"
    plano = json.load(open(caminho_plano, encoding="utf-8"))
    if not compativel(c, plano): raise ValueError(f"o gancho {c['id']} não é compatível com o episódio (cena {c['cena']})")
    alterados = []
    novo = dict(plano); novo["gancho"] = {"estrategia": c["estrategia"], "texto": c["texto"], "cena": c["cena"], "linhas": c["linhas"], "id": c["id"]}
    bloquear(caminho_plano)
    json.dump(novo, open(caminho_plano, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1); alterados.append(caminho_plano)
    pasta = pasta_da_serie(caminho_plano); ep = int(plano["episodio"])
    md = os.path.join(pasta, f"ep{ep:02d}_roteiro.md")
    if os.path.isfile(md):
        txt = open(md, encoding="utf-8").read(); novo_md = trocar_no_roteiro(txt, c)
        if novo_md != txt: bloquear(md, novo_md); open(md, "w", encoding="utf-8", newline="\n").write(novo_md); alterados.append(md)
    js = os.path.join(pasta, f"ep{ep:02d}.json")
    if os.path.isfile(js):
        sp = json.load(open(js, encoding="utf-8")); novo_js = trocar_no_json(sp, c)
        if novo_js != sp: bloquear(js); json.dump(novo_js, open(js, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1); alterados.append(js)
    g["escolhido"] = c["id"]; g["criterio"] = criterio
    json.dump(g, open(dest, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    if registrar:
        from .experimentos import registrar_variantes
        registrar_variantes(pasta, ep, cands, c["id"], criterio)
    return {"escolhido": c["id"], "criterio": criterio, "alterados": alterados}


def trocar_no_roteiro(md, c):
    """Troca só o gancho no roteiro: a linha ESCOLHIDO, a FALA DO GANCHO e o TEXTO da CENA 0. O resto fica igual."""
    linhas = md.split("\n"); out = []; na_cena0 = False
    for l in linhas:
        if re.match(r"^##\s*CENA\s+0\b", l): na_cena0 = True
        elif l.startswith("## "): na_cena0 = False
        if na_cena0 and l.startswith("FALA DO GANCHO:"):
            l = re.sub(r'"[^"]*"', '"' + c["texto"].rstrip(".") + '."', l, count=1)
            l = re.sub(r"\(a mesma da CENA \d+\)", f"(a mesma da CENA {c['cena']})", l)
        elif na_cena0 and l.startswith("TEXTO:"):
            l = "TEXTO: " + " / ".join(c["linhas"])
        elif l.startswith("ESCOLHIDO:"):
            l = f"ESCOLHIDO: {c['id']} ({c['estrategia']}) — {c['texto']}"
        out.append(l)
    return "\n".join(out)


def trocar_no_json(sp, c):
    """Troca só o texto do gancho no plano com "hook" (a fala, o vídeo e o resto do episódio ficam iguais)."""
    import copy
    sp = copy.deepcopy(sp)
    for s in sp.get("shots", []):
        if s.get("hook"):
            h = s["hook"] if isinstance(s["hook"], dict) else {}
            h["text"] = "\n".join(c["linhas"]); s["hook"] = h
            break
    return sp


def mostrar(g):
    out = [f"Ganchos do ep. {g['episodio']} (escolhido: {g.get('escolhido') or '—'})"]
    for c in g["candidatos"]:
        out.append(f"\n{c['id']} · {c['estrategia']} · cena {c['cena']} · {c['duracao_s']} s · nota {c['total']}")
        out.append("   " + " / ".join(c["linhas"]))
        out.append("   " + "; ".join(c["explicacao"]))
    if g.get("criterio"): out.append(f"\ncritério: {g['criterio']}")
    return "\n".join(out)


if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    cmd = sys.argv[1]
    if cmd == "gerar": print(mostrar(gerar_arquivo(sys.argv[2], regenerar="--regenerar" in sys.argv)))
    elif cmd == "ver": print(mostrar(json.load(open(arquivo(sys.argv[2]), encoding="utf-8"))))
    elif cmd == "escolher":
        r = escolher(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "auto")
        print(f"escolhido {r['escolhido']} — {r['criterio']}\nalterados: {', '.join(r['alterados'])}")
    elif cmd == "avaliar":
        tot, notas, exp = avaliar(sys.argv[2]); print(tot, notas); print("; ".join(exp))
