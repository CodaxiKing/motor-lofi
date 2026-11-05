"""Planejamento narrativo, memória da história e continuidade entre cenas e episódios.

O roteiro nasce de um PLANO (series/<serie>/planos/epNN.json), escrito antes das cenas, e a série guarda uma MEMÓRIA
(series/<serie>/memoria.json) com o que é verdade, o que é suspeita e o que ninguém sabe ainda. O validador confere o
plano contra a memória e contra o mapa da cidade (mundo.json) antes de qualquer cena ser escrita.

PLANO (cadeia causal: situação → acontecimento → reação → consequência → decisão → próximo acontecimento)
{
  "serie": "o-ultimo-estoque", "episodio": 2, "titulo": "A CÂMARA FRIA",
  "estado_inicial": {"por_voto": {"A": {"lugar": "beco", "dia": 0, "hora": "19:20", "presentes": ["leo"], "inventario": {"leo": ["radio"]}},
                                  "B": {...}}},          # ou direto {"lugar": ..., ...} quando não depende de voto
  "objetivo": "...", "conflito": "...", "obstaculos": ["..."],
  "gancho": {"estrategia": "revelacao_parcial", "texto": "...", "cena": 9},       # o lofi.ganchos preenche
  "cadeia": [{"n": 1, "voto": "A" | "B" | null, "lugar": "loja", "cenario": "loja", "dia": 0, "hora": "19:16",
              "presentes": ["leo"], "entram": [], "saem": [], "pega": {"leo": ["chave"]}, "larga": {},
              "situacao": "...", "acontecimento": "...", "reacao": "...", "consequencia": "...", "decisao": "...",
              "transicao": {"tipo": "continuacao|deslocamento|passagem_tempo|perspectiva|revelacao|montagem", "justificativa": "..."},
              "revela": ["fato_id"], "resolve": ["pendencia_id"], "ferimentos": {"leo": "corte na mão"}, "narracao": ["frase", ...]}],
  "virada": 5, "consequencias": ["..."], "pergunta": {"A": "...", "B": "..."},
  "estado_final": {"por_voto": {...}} ou {...}, "ponte": {"A": "como o próximo abre se A", "B": "..."}
}

MEMÓRIA
{
  "personagens": {"leo": {"estado": "vivo", "ferimentos": [], "objetivo": "...", "relacoes": {"sergio": "..."}}},
  "fatos": [{"id": "sergio_mordido", "texto": "...", "status": "fato|suspeita|desconhecido", "quem_sabe": ["sergio"],
             "publico_sabe": false, "palavras": ["mordido", "mordida"], "desde_ep": 1, "revelar_no_ep": 2}],
  "misterios": [{"id": "...", "pergunta": "...", "pistas": ["..."], "resolver_no_ep": 4}],
  "pendencias": [{"id": "portao_22h", "texto": "...", "ate_ep": 2, "palavras": ["portão", "22h"]}],
  "objetos": {"cracha_sergio": {"onde": "deposito", "com": null}},
  "locais": {"porta_fundos": "trancada"},
  "fim": {"1": {"lugar": "mezanino", "dia": 0, "hora": "19:15", "presentes": ["leo"], "inventario": {"leo": ["radio"]}, "pergunta": {...}}}
}

    python3 -m lofi.narrativa validar series/o-ultimo-estoque/planos/ep02.json
    python3 -m lofi.narrativa fechar  series/o-ultimo-estoque/planos/ep02.json A    (grava o fim no memoria.json)
    python3 -m lofi.narrativa resumo  series/o-ultimo-estoque                        (o que a memória sabe)
"""
import copy, json, os, re, sys, unicodedata

TRANSICOES = ("continuacao", "deslocamento", "passagem_tempo", "perspectiva", "revelacao", "montagem")
SEM_DESLOCAR = ("perspectiva", "revelacao", "montagem")        # trocas de lugar que não exigem caminho no mapa
CAMPOS_PLANO = ("objetivo", "conflito", "cadeia", "pergunta")
CAMPOS_CENA = ("situacao", "acontecimento", "consequencia")
GENERICOS = ("zombie", "zombie_corredor", "zombie_enfermeiro", "zombie_policial", "zombie_rastejante", "vultos", "multidao", "narrador")


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(c) != "Mn")


def palavras(s):
    return set(w for w in re.findall(r"[a-z0-9]+", norm(s)) if len(w) > 3)


def identificadores(itens):
    return [p.get('id') if isinstance(p, dict) else p for p in itens]


def minutos(dia, hora):
    h, m = (int(x) for x in str(hora).split(":")); return int(dia) * 1440 + h * 60 + m


# ============================== MEMÓRIA ==============================
def carregar_memoria(pasta):
    p = os.path.join(pasta, "memoria.json")
    m = json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else {}
    for k, v in (("personagens", {}), ("fatos", []), ("misterios", []), ("pendencias", []), ("objetos", {}), ("locais", {}), ("fim", {})):
        m.setdefault(k, v)
    return m


def salvar_memoria(pasta, m):
    p = os.path.join(pasta, "memoria.json")
    from .protecao import bloquear
    bloquear(p)
    json.dump(m, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)


def carregar_plano(caminho):
    return json.load(open(caminho, encoding="utf-8"))


def pasta_da_serie(caminho):
    d = os.path.dirname(os.path.abspath(caminho))
    return os.path.dirname(d) if os.path.basename(d) == "planos" else d


def estados_iniciais(plano):
    """{voto: estado} (voto None quando o episódio não depende de voto)."""
    ei = plano.get("estado_inicial") or {}
    return dict(ei["por_voto"]) if "por_voto" in ei else {None: ei}


def ramos(plano):
    """Para cada voto, a sequência de cenas daquele caminho (cenas comuns + as do voto)."""
    votos = [v for v in estados_iniciais(plano)] or [None]
    vs = sorted({c.get("voto") for c in plano.get("cadeia", []) if c.get("voto")} | {v for v in votos if v})
    if not vs: vs = [None]
    return {v: [c for c in plano.get("cadeia", []) if c.get("voto") in (None, v)] for v in vs}


# ============================== VALIDAÇÃO DO PLANO ==============================
def validar_plano(plano, memoria=None, mundo=None, personagens=None):
    """Lista de problemas [(nível, código, cena, mensagem)]. nível: ERRO | AVISO."""
    P = []
    def e(cod, cena, msg): P.append(("ERRO", cod, cena, msg))
    def w(cod, cena, msg): P.append(("AVISO", cod, cena, msg))
    memoria = memoria or {"fatos": [], "pendencias": [], "fim": {}}
    ep = int(plano.get("episodio", 0))
    for c in CAMPOS_PLANO:
        if c == "pergunta" and plano.get("final"): continue          # último episódio: fecha com FIM, sem pergunta
        if not plano.get(c): e("plano_incompleto", None, f"o plano não define '{c}'")
    cadeia = plano.get("cadeia", [])
    ns = [c.get("n") for c in cadeia]
    if len(set(ns)) != len(ns): e("cena_repetida", None, "números de cena repetidos na cadeia")
    # ---------------- cada cena existe por uma razão ----------------
    for c in cadeia:
        for k in CAMPOS_CENA:
            if not str(c.get(k, "")).strip(): e("cadeia_quebrada", c.get("n"), f"cena {c.get('n')} sem '{k}' (situação → acontecimento → consequência)")
        if not (c.get("reacao") or c.get("decisao")): w("sem_reacao", c.get("n"), f"cena {c.get('n')}: sem reação nem decisão do protagonista")
        tr = (c.get("transicao") or {}).get("tipo")
        if tr and tr not in TRANSICOES: e("transicao_invalida", c.get("n"), f"cena {c.get('n')}: transição '{tr}' (use {', '.join(TRANSICOES)})")
        if personagens is not None:
            for p in c.get("presentes", []):
                if p not in personagens and p not in GENERICOS: e("personagem_desconhecido", c.get("n"), f"cena {c.get('n')}: '{p}' não está em personagens.json")
    # ---------------- continuidade por caminho (voto) ----------------
    ini = estados_iniciais(plano)
    fim_ant = memoria.get("fim", {}).get(str(ep - 1)) if ep > 1 else None
    if fim_ant and fim_ant.get("pergunta"):
        faltam = [v for v in fim_ant["pergunta"] if v not in ini]
        if faltam: e("voto_ignorado", None, f"o ep. {ep - 1} terminou com a escolha {'/'.join(fim_ant['pergunta'])}; o plano não abre o caminho {', '.join(faltam)}")
    for voto, cenas in ramos(plano).items():
        est = copy.deepcopy(ini.get(voto) or ini.get(None) or {})
        tag = f" (caminho {voto})" if voto else ""
        if fim_ant and est:
            base = (fim_ant.get("por_voto") or {}).get(voto, fim_ant) if voto else fim_ant
            if base.get("dia") is not None and est.get("hora") and base.get("hora"):
                if minutos(est.get("dia", 0), est["hora"]) < minutos(base["dia"], base["hora"]):
                    e("tempo_volta", None, f"o episódio começa{tag} às {est['hora']}, antes do fim do ep. {ep - 1} ({base['hora']})")
        inv = {k: list(v) for k, v in (est.get("inventario") or {}).items()}
        pres = set(est.get("presentes") or []); lugar = est.get("lugar"); t = minutos(est["dia"], est["hora"]) if est.get("hora") else None
        conhece = {f["id"] for f in memoria.get("fatos", []) if f.get("publico_sabe") or f.get("status") == "fato" and f.get("revelar_no_ep") is None}
        for i, c in enumerate(cenas):
            n = c.get("n"); tr = c.get("transicao") or {}; tipo = tr.get("tipo", "continuacao" if i == 0 else None)
            if i > 0 and not tipo: e("transicao_sem_contexto", n, f"cena {n}{tag}: troca de cena sem 'transicao' (como saímos da cena anterior)")
            # lugar
            if lugar and c.get("lugar") and c["lugar"] != lugar:
                if tipo == "continuacao": e("salto_de_lugar", n, f"cena {n}{tag}: de '{lugar}' para '{c['lugar']}' como 'continuacao' (use deslocamento, perspectiva...)")
                elif tipo == "deslocamento":
                    if not tr.get("justificativa"): e("transicao_sem_contexto", n, f"cena {n}{tag}: deslocamento sem justificativa (por onde/por quê)")
                    if mundo is not None:
                        from .continuidade import rota
                        if rota(mundo, lugar, c["lugar"]) is None: e("caminho_inexistente", n, f"cena {n}{tag}: não há caminho de '{lugar}' até '{c['lugar']}' no mundo.json")
                elif tipo in SEM_DESLOCAR and not tr.get("justificativa"): w("transicao_sem_contexto", n, f"cena {n}{tag}: {tipo} sem dizer o que liga as cenas")
            # tempo
            if c.get("hora"):
                tc = minutos(c.get("dia", (est.get("dia") or 0)), c["hora"])
                if t is not None and tc < t and tipo not in ("perspectiva", "revelacao", "montagem"):
                    e("tempo_volta", n, f"cena {n}{tag}: {c['hora']} vem antes da cena anterior")
                if t is not None and tc - t > 180 and tipo != "passagem_tempo" and not tr.get("passa_tempo"):
                    e("salto_de_tempo", n, f"cena {n}{tag}: pulo de {(tc - t) // 60} h sem 'passagem_tempo'")
                if tipo not in ("perspectiva", "revelacao", "montagem"): t = tc
            # personagens
            entram = set(c.get("entram", [])); agora = set(c.get("presentes", []))
            if pres and agora and tipo in ("continuacao", None):
                surgem = {p for p in agora - pres - entram if p not in GENERICOS}
                if surgem: e("personagem_surge", n, f"cena {n}{tag}: {', '.join(sorted(surgem))} aparece sem entrar (use 'entram')")
            if tipo not in ("perspectiva", "revelacao", "montagem"):
                pres = (agora or pres) - set(c.get("saem", [])); lugar = c.get("lugar") or lugar
            # objetos
            for quem, itens in (c.get("pega") or {}).items(): inv.setdefault(quem, []).extend(itens)
            for quem, itens in (c.get("usa") or {}).items():
                for it in itens:
                    if it not in inv.get(quem, []): e("objeto_sumido", n, f"cena {n}{tag}: {quem} usa '{it}', que não está com ele (falta um 'pega')")
            for quem, itens in (c.get("larga") or {}).items():
                for it in itens:
                    if it in inv.get(quem, []): inv[quem].remove(it)
                    else: e("objeto_sumido", n, f"cena {n}{tag}: {quem} larga '{it}' que não carregava")
            # conhecimento: o público não pode saber antes da hora
            texto = " ".join([c.get("acontecimento", ""), c.get("consequencia", "")] + list(c.get("narracao", [])))
            for f in memoria.get("fatos", []):
                if f["id"] in conhece or f["id"] in identificadores(c.get("revela", [])): continue
                alvo = f.get("revelar_no_ep")
                if f.get("status") in ("desconhecido", "fato") and alvo and alvo > ep and f.get("palavras"):
                    if any(re.search(r"\b" + re.escape(norm(p)) + r"\b", norm(texto)) for p in f["palavras"]):
                        e("informacao_indevida", n, f"cena {n}{tag}: conta '{f['id']}' (só revelado no ep. {alvo})")
            conhece |= set(identificadores(c.get("revela", [])))
        # estado final coerente com a última cena
        ef = estados_iniciais({"estado_inicial": plano.get("estado_final") or {}})
        fimv = ef.get(voto) or ef.get(None)
        if fimv and cenas and fimv.get("lugar") and cenas[-1].get("lugar") and fimv["lugar"] != cenas[-1]["lugar"]:
            e("estado_final", None, f"estado_final{tag} diz '{fimv['lugar']}', mas a última cena é em '{cenas[-1]['lugar']}'")
    # ---------------- virada, consequências, pendências e ponte ----------------
    if plano.get("virada") not in ns: e("sem_virada", None, "o plano não aponta a cena da virada ('virada': n)")
    if not plano.get("consequencias"): w("sem_consequencia", None, "o plano não diz o que muda depois do episódio ('consequencias')")
    resolvidas = {r for c in cadeia for r in identificadores(c.get("resolve", []))}
    tudo = norm(json.dumps(cadeia, ensure_ascii=False))
    for pd in memoria.get("pendencias", []):
        if pd.get("ate_ep") == ep and pd["id"] not in resolvidas and not any(norm(p) in tudo for p in pd.get("palavras", [])):
            e("consequencia_ignorada", None, f"pendência '{pd['id']}' vence no ep. {ep} e o plano não trata ({pd['texto']})")
    perg = plano.get("pergunta") or {}
    if perg and plano.get("ponte") is not None and set(perg) - set(plano.get("ponte") or {}):
        e("ponte_incompleta", None, "a 'ponte' não diz como o próximo episódio abre em cada opção da pergunta")
    if perg:
        for v, txt in perg.items():
            if not palavras(txt) & palavras(tudo): w("escolha_desconectada", None, f"a opção {v} ('{txt}') não aparece em nenhuma cena: a escolha precisa nascer da história")
    g = plano.get("gancho")
    if g:
        alvo = next((c for c in cadeia if c.get("n") == g.get("cena")), None)
        if not alvo: e("gancho_desconectado", None, f"o gancho aponta a cena {g.get('cena')}, que não existe")
        elif not palavras(g.get("texto", "")) & palavras(json.dumps(alvo, ensure_ascii=False)):
            e("gancho_desconectado", None, f"o gancho '{g.get('texto')}' não tem nada da cena {g.get('cena')}")
    from .dramaturgia import avaliar_plano
    for a in avaliar_plano(plano, memoria)['findings']:
        P.append(('ERRO' if a['severity'] == 'error' else 'AVISO', 'drama_' + a['code'], a['scene'],
                  a['message'] + (' (caminho ' + str(a['branch']) + ')' if a.get('branch') else '') + ': ' + a['suggestion']))
    return P


# ============================== FECHAR O EPISÓDIO NA MEMÓRIA ==============================
def fechar(plano, memoria, voto=None):
    """Nova memória com o fim do episódio (não grava; use salvar_memoria)."""
    m = copy.deepcopy(memoria); ep = str(plano["episodio"])
    cenas = ramos(plano).get(voto) or ramos(plano).get(None) or plano.get("cadeia", [])
    ini = estados_iniciais(plano); est = copy.deepcopy(ini.get(voto) or ini.get(None) or {})
    inv = {k: list(v) for k, v in (est.get("inventario") or {}).items()}
    for c in cenas:
        for q, its in (c.get("pega") or {}).items(): inv.setdefault(q, []).extend(its)
        for q, its in (c.get("larga") or {}).items():
            for it in its:
                if it in inv.get(q, []): inv[q].remove(it)
        for q, fer in (c.get("ferimentos") or {}).items():
            m["personagens"].setdefault(q, {}).setdefault("ferimentos", []).append({"ep": int(ep), "texto": fer})
        for fid in identificadores(c.get("revela", [])):
            for f in m["fatos"]:
                if f["id"] == fid: f["publico_sabe"] = True; f["status"] = "fato"; f["revelado_no_ep"] = int(ep)
        for pid in identificadores(c.get("resolve", [])):
            m["pendencias"] = [p for p in m["pendencias"] if p["id"] != pid]
        for pista in c.get('planta', []):
            p = pista if isinstance(pista, dict) else {'id': pista, 'texto': c.get('consequencia', '')}
            if not any(x['id'] == p['id'] for x in m.setdefault('pistas', [])):
                m['pistas'].append(dict(p, publico_sabe=True, plantada_no_ep=int(ep)))
        for pid in identificadores(c.get('paga', [])):
            for p in m.get('pistas', []):
                if p['id'] == pid:
                    p['paga_no_ep'] = int(ep)
    ult = cenas[-1] if cenas else {}
    m["fim"][ep] = {"lugar": ult.get("lugar", est.get("lugar")), "dia": ult.get("dia", est.get("dia")), "hora": ult.get("hora", est.get("hora")),
                    "presentes": ult.get("presentes", est.get("presentes")), "inventario": inv, "voto_de_entrada": voto,
                    "pergunta": plano.get("pergunta"), "ponte": plano.get("ponte")}
    for nova in plano.get("novas_pendencias", []): m["pendencias"].append(nova)
    return m


def resumo(memoria):
    out = []
    for f in memoria["fatos"]:
        out.append(f"[{f.get('status')}{' · público sabe' if f.get('publico_sabe') else ''}] {f['id']}: {f['texto']}")
    for p in memoria["pendencias"]: out.append(f"[pendência até o ep. {p.get('ate_ep')}] {p['id']}: {p['texto']}")
    for k, v in sorted(memoria["fim"].items()): out.append(f"[fim do ep. {k}] {v.get('lugar')} · DIA {v.get('dia')} · {v.get('hora')} · {v.get('inventario')}")
    return "\n".join(out)


def contexto(caminho_plano):
    pasta = pasta_da_serie(caminho_plano)
    mem = carregar_memoria(pasta)
    mundo = None
    if os.path.isfile(os.path.join(pasta, "mundo.json")):
        from .continuidade import carregar
        mundo = carregar(pasta)
    pers = None
    if os.path.isfile(os.path.join(pasta, "personagens.json")):
        pers = {k for k in json.load(open(os.path.join(pasta, "personagens.json"), encoding="utf-8")) if not k.startswith("_")}
        from .rig import CHARS
        pers |= set(CHARS)
    return pasta, mem, mundo, pers


def validar_arquivo(caminho):
    pasta, mem, mundo, pers = contexto(caminho)
    return validar_plano(carregar_plano(caminho), mem, mundo, pers)


def esqueleto(plano, voto=None, mundo=None):
    """Esqueleto do epNN_roteiro.md a partir do plano, para um caminho de voto: CENA 0 com o gancho escolhido, uma CENA
    por passo da cadeia com CENÁRIO, DIA/hora, PERSONAGENS, LIGAÇÃO/O TEMPO PASSA, NARRAÇÃO e VIRADA, e a pergunta.
    O roteirista (skill serie-roteiro) completa plano de câmera, sons e imagens por frase; as decisões de história já vêm
    fechadas e validadas. Mesmo lugar = mesmo cenário (reaproveita a referência visual)."""
    cenas = ramos(plano).get(voto) or ramos(plano).get(None) or plano.get("cadeia", [])
    g = plano.get("gancho") or {}; L = [f"# {plano.get('titulo', '')} · EPISÓDIO {plano['episodio']}" + (f" · caminho do voto {voto}" if voto else ""), "",
                                       f"Objetivo: {plano.get('objetivo', '')}", f"Conflito: {plano.get('conflito', '')}", ""]
    alvo = next((i for i, c in enumerate(cenas, 1) if c.get("n") == g.get("cena")), None)
    ref = next((c for c in cenas if c.get("n") == g.get("cena")), {})
    L += ["## CENA 0 · GANCHO (0–3 s)", f"CENÁRIO: `{ref.get('cenario', '')}` · DIA {ref.get('dia', '')} · {ref.get('hora', '')}",
          f"FALA DO GANCHO: `narrador` \"{g.get('texto', '')}\"" + (f" (a mesma da CENA {alvo})" if alvo else ""),
          "TEXTO: " + " / ".join(g.get("linhas", [])), f"ESTRATÉGIA: {g.get('estrategia', '')}", "", "---", ""]
    ini = estados_iniciais(plano); lugar_cen = {}; ant = (ini.get(voto) or ini.get(None) or {}).get("lugar")
    referencia = {c.get('n'): i for i, c in enumerate(cenas, 1)}
    for i, c in enumerate(cenas, 1):
        cen = lugar_cen.setdefault((c.get("lugar"), c.get("cenario")), c.get("cenario"))
        tr = c.get("transicao") or {}
        L.append(f"## CENA {i} · {c.get('situacao', '')[:48]}")
        L.append(f"ACONTECIMENTO: {c.get('acontecimento', '')}")
        L.append(f"CONSEQUÊNCIA: {c.get('consequencia', '')}")
        causa = c.get('causa')
        if isinstance(causa, int): causa = {'cena': causa, 'texto': c.get('situacao', '')}
        if isinstance(causa, dict):
            L.append(f"CAUSA: CENA {referencia.get(causa.get('cena'), causa.get('cena'))} — {causa.get('texto', '')}")
        pessoal = c.get('conflito_pessoal') or {}
        if isinstance(pessoal, dict) and pessoal:
            L.append(f"CONFLITO PESSOAL: {pessoal.get('personagem', pessoal.get('texto', ''))} | DESEJO: {pessoal.get('desejo', '')} | CUSTO: {pessoal.get('custo', '')}")
        for campo in ('planta', 'revela', 'paga', 'resolve', 'abre'):
            for item in c.get(campo, []):
                identificador = item.get('id') if isinstance(item, dict) else item
                descricao = item.get('texto', '') if isinstance(item, dict) else c.get('consequencia', '')
                L.append(f"{campo.upper()}: {identificador} | {descricao}")
        for fala in c.get('falas', []):
            L.append(f"FALA: {fala.get('personagem', '')} | ALVO: {fala.get('alvo', '')} | INTENÇÃO: {fala.get('intencao', '')} | OBJETIVO: {fala.get('objetivo', '')} | TEXTO: {fala.get('texto', '')}")
        if tr.get("tipo") in ("passagem_tempo",) or tr.get("passa_tempo"): L.append(f"O TEMPO PASSA: {tr.get('justificativa', '')}")
        if ant and c.get("lugar") != ant and tr.get("tipo") == "deslocamento": L.append(f"LIGAÇÃO: {tr.get('justificativa', '')}")
        if tr.get("tipo") in ("perspectiva", "revelacao", "montagem"): L.append(f"INSERÇÃO: {tr.get('justificativa', '')}")
        L.append(f"CENÁRIO: `{cen}` · DIA {c.get('dia', '')} · {c.get('hora', '')}")
        L.append("PERSONAGENS: " + ", ".join(f"`{p}`" for p in c.get("presentes", [])))
        for q, its in (c.get("pega") or {}).items(): L += [f"PEGA: `{q}` {it}" for it in its]
        for q, its in (c.get("larga") or {}).items(): L += [f"LARGA: `{q}` {it}" for it in its]
        L.append("NARRAÇÃO: " + " / ".join(c.get("narracao", [])))
        L.append(f"VIRADA: {c.get('consequencia', '')}" if c.get("n") == plano.get("virada") else "VIRADA: nenhuma")
        L += [f"(acontecimento: {c.get('acontecimento', '')} · reação: {c.get('reacao', '')} · decisão: {c.get('decisao', '')})", ""]
        ant = c.get("lugar")
    if plano.get("pergunta"):
        L += ["## A ESCOLHA"]
        for k, v in plano['pergunta'].items():
            if isinstance(v, dict):
                v = v.get('texto', '') + ''.join(f' | {campo.upper()}: {v[campo]}' for campo in ('ganha', 'perde', 'motivo', 'origem') if campo in v)
            v = re.sub(r'(ORIGEM:\s*CENA\s+)(\d+)', lambda m: m[1] + str(referencia.get(int(m[2]), int(m[2]))), v, flags=re.I)
            L.append(f'{k}) {v}')
        L.append('')
    if plano.get('final'):
        L.append('ENCERRAMENTO: final')
    return "\n".join(L)


def validar_serie(pasta):
    """Valida todos os planos em ordem, levando a memória adiante: o fim simulado de cada caminho do ep. N vira o
    começo do ep. N+1 (hora, fatos revelados, pendências). Devolve {ep: [(nível, código, cena, msg)]}."""
    _, mem, mundo, pers = contexto(os.path.join(pasta, "planos", "x.json"))
    d = os.path.join(pasta, "planos"); out = {}
    arqs = sorted(f for f in os.listdir(d) if re.match(r"ep\d+\.json$", f)) if os.path.isdir(d) else []
    memorias = [mem]                                   # uma memória por caminho percorrido até aqui
    for f in arqs:
        plano = carregar_plano(os.path.join(d, f)); ep = int(plano["episodio"]); probs = []; novas = []
        for m in memorias:
            for p in validar_plano(plano, m, mundo, pers):
                if p not in probs: probs.append(p)
            for voto in ramos(plano):
                novas.append(fechar(plano, m, voto))
        out[ep] = probs
        memorias = novas[:8]                           # limita a explosão de caminhos (2 por episódio)
    return out


if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    cmd = sys.argv[1]
    if cmd == "validar":
        probs = validar_arquivo(sys.argv[2])
        for nv, cod, n, msg in probs: print(f"[{nv}] {cod}: {msg}")
        print(f"{sum(1 for p in probs if p[0] == 'ERRO')} erro(s), {sum(1 for p in probs if p[0] == 'AVISO')} aviso(s)")
        sys.exit(1 if any(p[0] == "ERRO" for p in probs) else 0)
    elif cmd == "fechar":
        pasta, mem, _, _ = contexto(sys.argv[2])
        nova = fechar(carregar_plano(sys.argv[2]), mem, sys.argv[3] if len(sys.argv) > 3 else None)
        salvar_memoria(pasta, nova); print(f"memória atualizada: fim do ep. {carregar_plano(sys.argv[2])['episodio']}")
    elif cmd == "resumo":
        print(resumo(carregar_memoria(sys.argv[2])))
    elif cmd == "esqueleto":
        voto = sys.argv[3] if len(sys.argv) > 3 else None
        print(esqueleto(carregar_plano(sys.argv[2]), voto))
    elif cmd == "serie":
        res = validar_serie(sys.argv[2]); n_err = 0
        for ep, probs in res.items():
            print(f"ep. {ep}: " + ("ok" if not probs else ""))
            for nv, cod, n, msg in probs: print(f"  [{nv}] {cod}: {msg}")
            n_err += sum(1 for p in probs if p[0] == "ERRO")
        sys.exit(1 if n_err else 0)
