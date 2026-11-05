"""Revisão narrativa do roteiro (epNN_roteiro.md) e da montagem (epNN.json), com correção localizada.

Complementa tests/validar_roteiro.py (formato, nomes, ritmo) e lofi/continuidade.py (mapa, relógio, inventário).
Aqui entram os problemas de HISTÓRIA:
  gancho_desconectado     o gancho da CENA 0 não está na cena que ele promete (ou em cena nenhuma)
  transicao_sem_contexto  troca de lugar sem LIGAÇÃO/INSERÇÃO e sem a narração dizer onde estamos
  salto_de_tempo          pulo de horas sem o tempo passar na tela (vem do lofi.continuidade)
  personagem_ausente      quem a memória diz que não está (morto, preso, longe) aparece sem ser lembrança
  informacao_indevida     a narração conta o que a série guarda para um episódio futuro (memoria.json)
  cena_redundante         duas cenas contando a mesma coisa
  fala_artificial         fala que explica para o público ("como você sabe...")
  exposicao               frase longa demais / explicação em sequência
  consequencia_ignorada   pendência da memória que vence neste episódio e não aparece
  escolha_artificial      opção da pergunta final que não nasce de nada que aconteceu
  av_*                    continuidade audiovisual no JSON: luz pulando no mesmo lugar, cenário gerado diferente no
                          mesmo lugar, figurino redefinido fora da ficha travada

Correção (`corrigir`): só para o que tem conserto mecânico seguro (LIGAÇÃO pela rota do mapa, "O TEMPO PASSA",
referência do gancho apontando a cena certa). Reescreve só as linhas afetadas, valida de novo, no máximo 3 rodadas,
e nunca grava em arquivo travado (lofi/protecao.py).

    python3 -m lofi.validador_narrativo series/x/ep02_roteiro.md
    python3 -m lofi.validador_narrativo series/x/ep02_roteiro.md --corrigir
    python3 -m lofi.validador_narrativo series/x/ep02.json
"""
import json, os, re, sys
from .narrativa import norm, palavras, carregar_memoria

EXPOSICAO_FALA = (r"como voce sabe", r"como eu (ja )?(te )?disse", r"deixa eu (te )?explicar", r"lembra que (nos|a gente)", r"como (todo mundo|voces) sabe",
                  r"vou te contar (tudo|o que)", r"o que significa que")
MAX_PALAVRAS_FRASE = 12


def _cenas(md):
    """[(n, titulo, corpo, inicio_linha)] das cenas (inclui a 0)."""
    linhas = md.split("\n"); out = []; atual = None
    for i, l in enumerate(linhas):
        m = re.match(r"^#+\s*CENA\s+(\d+)\b(.*)$", l)
        if m:
            if atual: out.append(atual)
            atual = [int(m.group(1)), m.group(2), [], i]
        elif atual is not None:
            if re.match(r"^##\s+(?!CENA)", l) or l.startswith("---"): out.append(atual); atual = None
            else: atual[2].append(l)
    if atual: out.append(atual)
    return [(n, t, "\n".join(c), i) for n, t, c, i in out]


def _campo(corpo, nome):
    m = re.search(rf"^{nome}[^:\n]*:\s*(.+)$", corpo, re.M | re.I)
    return m.group(1).strip() if m else ""


def _narracao(corpo):
    return re.sub(r"\[[^\]]*\]", "", _campo(corpo, "NARRAÇÃO")).replace("*", "").replace(" / ", " ")


CAMPOS = {"CENÁRIO", "CENARIO", "PERSONAGENS", "PLANO", "LUZ E DETALHES", "SOM", "IMAGENS", "VIRADA", "LIGAÇÃO", "INSERÇÃO", "IMAGEM (CHATGPT)",
          "ANIMAÇÃO", "NARRAÇÃO", "LEGENDA", "IMAGENS POR FRASE", "PEGA", "LARGA", "ENTRA", "SAI", "TEXTO", "FALA DO GANCHO", "PLANO DE DETALHE", "INSERTO"}
CAMPOS.update({'CAUSA', 'ACONTECIMENTO', 'CONSEQUÊNCIA', 'CONFLITO PESSOAL', 'FALA',
               'PLANTA', 'REVELA', 'PAGA', 'RESOLVE', 'ABRE', 'ENCERRAMENTO', 'SUJEITO', 'DESTINATÁRIO', 'MARCA', 'RECORTES'})


def _falas(corpo):
    """Falas de personagem ("JOÃO: [tags] texto") da cena."""
    out = []
    for m in re.finditer(r"^([A-ZÀ-Ú_ ]{2,30}):\s*(.+)$", corpo, re.M):
        if m.group(1).strip() in CAMPOS or m.group(1).strip().startswith("IMAGEM"): continue
        out.append(re.sub(r"\[[^\]]*\]", "", m.group(2)).strip())
    return out


def _dito(corpo):
    """Tudo o que se ouve/lê na cena: narração, falas e legendas."""
    return " ".join([_narracao(corpo)] + _falas(corpo) + [_campo(corpo, "LEGENDA").replace("*", "").replace(" / ", " ")])


def _cenario(corpo):
    m = re.search(r"CEN[AÁ]RIO[^:\n]*:\**\s*`([^`]+)`", corpo, re.I)
    return m.group(1).strip() if m else None


def _ep(caminho):
    m = re.search(r"ep(\d+)", os.path.basename(caminho)); return int(m.group(1)) if m else None


def validar_roteiro(caminho, txt=None):
    """[(nível, código, cena, mensagem)]"""
    txt = txt if txt is not None else open(caminho, encoding="utf-8").read()
    pasta = os.path.dirname(os.path.abspath(caminho)); ep = _ep(caminho)
    mem = carregar_memoria(pasta)
    from .continuidade import carregar, lugar_de
    mundo = carregar(pasta)
    P = []
    def e(c, n, m): P.append(("ERRO", c, n, m))
    def w(c, n, m): P.append(("AVISO", c, n, m))
    cenas = _cenas(txt); corpo_de = {n: c for n, _, c, _ in cenas}
    tudo = " ".join(_dito(c) for n, _, c, _ in cenas if n > 0)
    # gancho
    c0 = corpo_de.get(0, "")
    fala = re.search(r'FALA DO GANCHO:[^"\n]*"([^"]+)"', c0)
    if fala:
        g = fala.group(1); ref = re.search(r"a mesma da CENA (\d+)", c0)
        alvo = int(ref.group(1)) if ref else None
        if alvo is not None and alvo in corpo_de:
            if not palavras(g) <= palavras(_dito(corpo_de[alvo])) | {"voce"}:
                dono = next((n for n, _, c, _ in cenas if n > 0 and palavras(g) <= palavras(_dito(c)) | {"voce"}), None)
                e("gancho_desconectado", 0, f"o gancho '{g}' diz ser da CENA {alvo}, mas não está nela" + (f" (está na CENA {dono})" if dono else ""))
        elif not palavras(g) & palavras(tudo):
            e("gancho_desconectado", 0, f"o gancho '{g}' não aparece em nenhuma cena: o episódio não paga a promessa")
    # transições, presença, informação, exposição
    ant_lugar = None; ant_n = None
    ausentes = {k: v.get("estado") for k, v in mem.get("personagens", {}).items() if v.get("estado") in ("morto", "ausente", "preso", "longe")}
    proibidos = [(f["id"], f.get("revelar_no_ep"), p) for f in mem.get("fatos", []) if ep and (f.get("revelar_no_ep") or 0) > ep and not f.get("publico_sabe") for p in f.get("palavras", [])]
    for n, tit, corpo, _ in cenas:
        if n == 0: continue
        cen = _cenario(corpo); ins = bool(re.search(r"INSER[ÇC][ÃA]O", corpo)); lemb = bool(re.search(r"lembran|pensamento|s[ée]pia", corpo, re.I))
        from .mapa import OBJETO_DO_LUGAR
        from .continuidade import ITEM_DE
        lug = lugar_de(mundo, cen) if cen and cen not in OBJETO_DO_LUGAR and cen not in ITEM_DE else None   # rádio na mão/na mesa: não muda o lugar
        if lug and ant_lugar and lug != ant_lugar and not ins:
            tem_lig = bool(re.search(r"^(LIGA[ÇC][ÃA]O|TRANSI[ÇC][ÃA]O DE LUGAR)\s*:", corpo, re.M | re.I))
            if not tem_lig: w("transicao_sem_contexto", n, f"CENA {n}: de '{ant_lugar}' para '{lug}' sem LIGAÇÃO (como ele chegou lá?)")
        if lug and not ins: ant_lugar = lug
        ant_n = n
        for quem, est in ausentes.items():
            if re.search(rf"`{quem}`", corpo) and not lemb: e("personagem_ausente", n, f"CENA {n}: `{quem}` está {est} na memória da série e aparece sem ser lembrança")
        nar = norm(_dito(corpo))
        for fid, alvo, p in proibidos:
            if re.search(r"\b" + re.escape(norm(p)) + r"\b", nar): e("informacao_indevida", n, f"CENA {n}: '{p}' entrega '{fid}', que a série guarda para o ep. {alvo}")
        for frase in re.split(r"(?<=[.!?…])\s+", _narracao(corpo)):
            if len(frase.split()) > MAX_PALAVRAS_FRASE: w("exposicao", n, f"CENA {n}: frase de {len(frase.split())} palavras ('{frase[:50]}...'): quebre em passos")
        for fl in _falas(corpo):
            if any(re.search(rx, norm(fl)) for rx in EXPOSICAO_FALA): w("fala_artificial", n, f"CENA {n}: fala explicando para o público: '{fl[:60]}'")
    # redundância
    nars = [(n, palavras(_dito(c))) for n, _, c, _ in cenas if n > 0]
    for i in range(len(nars)):
        for j in range(i + 1, len(nars)):
            a, b = nars[i][1], nars[j][1]
            if len(a) >= 6 and len(b) >= 6 and len(a & b) / len(a | b) >= 0.6:
                w("cena_redundante", nars[j][0], f"CENA {nars[j][0]} repete a CENA {nars[i][0]} ({round(100 * len(a & b) / len(a | b))}% das palavras)")
    # pendências e escolha
    if ep:
        for pd in mem.get("pendencias", []):
            if pd.get("ate_ep") == ep and not any(re.search(r"\b" + re.escape(norm(p)) + r"\b", norm(txt)) for p in pd.get("palavras", [])):
                e("consequencia_ignorada", None, f"pendência '{pd['id']}' vence no ep. {ep} e o roteiro não trata ({pd['texto']})")
    esc = next(((n, c) for n, t, c, _ in reversed(cenas) if re.search(r"escolha|pergunta", t + c, re.I)), None)
    if esc:
        for op, texto in re.findall(r"\b([AB])\)\s*([^·\n]+)", esc[1]):
            ws = palavras(texto) - {"voce", "ficar", "sair"}
            if ws and not ws & palavras(tudo): w("escolha_artificial", esc[0], f"a opção {op}) '{texto.strip()}' não nasce de nada que aconteceu no episódio")
    # salto de tempo (texto do lofi.continuidade, com cena)
    from .continuidade import conferir
    for err in conferir(caminho, txt):
        m = re.match(r"CENA (\d+): pulo de", err)
        if m: e("salto_de_tempo", int(m.group(1)), err)
    from .dramaturgia import avaliar_texto
    for a in avaliar_texto(txt)['findings']:
        P.append(('ERRO' if a['severity'] == 'error' else 'AVISO', 'drama_' + a['code'], a['scene'],
                  a['message'] + ': ' + a['suggestion']))
    return P


def validar_json(caminho):
    """Continuidade audiovisual da montagem."""
    sp = json.load(open(caminho, encoding="utf-8")); pasta = os.path.dirname(os.path.abspath(caminho)); P = []
    from .continuidade import carregar, lugar_de
    mundo = carregar(pasta)
    locked = {}
    pj = os.path.join(pasta, "personagens.json")
    if os.path.isfile(pj): locked = json.load(open(pj, encoding="utf-8"))
    for nome in sp.get("characters", {}):
        if nome in locked: P.append(("ERRO", "av_figurino", None, f"'{nome}' redefinido no roteiro técnico: a ficha travada vale"))
    cenas = [s for s in sorted(sp.get("shots", []), key=lambda s: s["start"]) if s.get("type", "scene") == "scene" and isinstance(s.get("scene"), str)]
    for a, b in zip(cenas, cenas[1:]):
        if abs(a["end"] - b["start"]) > 0.05: continue
        la, lb = lugar_de(mundo, a["scene"]), lugar_de(mundo, b["scene"])
        if not la or la != lb: continue
        if a.get("light") and b.get("light") and a["light"] != b["light"] and not any(k in b.get("props", {}) for k in ("luz", "emergencia", "flicker")):
            P.append(("AVISO", "av_luz", b["start"], f"{b['start']}s: a luz muda de '{a['light']}' para '{b['light']}' no mesmo lugar sem motivo na cena (props luz/emergencia)"))
        ca, cb = a.get("cenario"), b.get("cenario")
        if isinstance(ca, dict) and isinstance(cb, dict) and not ca.get("close") and not cb.get("close") and ca.get("base") != cb.get("base") and a["scene"] != b["scene"]:
            P.append(("AVISO", "av_cenario", b["start"], f"{b['start']}s: o mesmo lugar com cenário gerado de base diferente ({ca.get('base')} → {cb.get('base')}); reuse a mesma descrição"))
    return P


# ---------------- correção localizada ----------------
CORRIGIVEIS = ("transicao_sem_contexto", "salto_de_tempo", "gancho_desconectado")


def _rota_texto(mundo, a, b):
    from .continuidade import rota
    r = rota(mundo, a, b) if mundo else None
    if not r: return None
    trechos = []
    for x, y in zip(r, r[1:]):
        lig = next((l for l in mundo.get("ligacoes", []) if {l[0], l[1]} == {x, y}), None)
        trechos.append(lig[2] if lig and len(lig) > 2 else f"de {x} até {y}")
    return "; depois ".join(trechos)


def corrigir(caminho, max_rodadas=3):
    """Corrige o que tem conserto mecânico, linha a linha. Devolve {"rodadas", "mudancas": [(linha, antes, depois)], "restantes"}."""
    from .protecao import bloquear
    from .continuidade import carregar, lugar_de
    bloquear(caminho)
    pasta = os.path.dirname(os.path.abspath(caminho)); mundo = carregar(pasta)
    txt = open(caminho, encoding="utf-8").read(); mudancas = []; rodada = 0
    for rodada in range(1, max_rodadas + 1):
        probs = [p for p in validar_roteiro(caminho, txt) if p[1] in CORRIGIVEIS]
        if not probs: rodada -= 1; break
        linhas = txt.split("\n"); cenas = {n: (c, i) for n, _, c, i in _cenas(txt)}; feito = False
        # todos os consertos da rodada, de baixo para cima (inserir uma linha não desloca as cenas de cima)
        for nv, cod, n, msg in sorted(probs, key=lambda p: -(cenas.get(p[2], ("", -1))[1])):
            if n not in cenas: continue
            corpo, i0 = cenas[n]
            if cod == "transicao_sem_contexto":
                m = re.search(r"de '([^']+)' para '([^']+)'", msg); rt = _rota_texto(mundo, m.group(1), m.group(2)) if m else None
                if rt:
                    linhas.insert(i0 + 1, f"LIGAÇÃO: {rt}"); mudancas.append((n, None, f"LIGAÇÃO: {rt}")); feito = True
            elif cod == "salto_de_tempo":
                linhas.insert(i0 + 1, "O TEMPO PASSA (plano de detalhe `relogio` antes desta cena)")
                mudancas.append((n, None, linhas[i0 + 1])); feito = True
            elif cod == "gancho_desconectado":
                m = re.search(r"está na CENA (\d+)", msg)
                for k in range(i0, len(linhas)) if m else ():
                    if "a mesma da CENA" in linhas[k]:
                        antes = linhas[k]; linhas[k] = re.sub(r"a mesma da CENA \d+", f"a mesma da CENA {m.group(1)}", antes)
                        mudancas.append((n, antes, linhas[k])); feito = True; break
        if not feito: rodada -= 1; break
        txt = "\n".join(linhas)
    if mudancas:
        bloquear(caminho, txt); open(caminho, "w", encoding="utf-8", newline="\n").write(txt)
    return {"rodadas": rodada, "mudancas": mudancas, "restantes": validar_roteiro(caminho, txt)}


def validar(caminho):
    if caminho.endswith(".json"): return validar_json(caminho)
    return validar_roteiro(caminho)


if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    cam = sys.argv[1]
    if "--corrigir" in sys.argv:
        r = corrigir(cam)
        for cn, a, b in r["mudancas"]: print(f"CENA {cn}: {a!r} → {b!r}")
        probs = r["restantes"]; print(f"{len(r['mudancas'])} correção(ões) em {r['rodadas']} rodada(s)")
    else: probs = validar(cam)
    for nv, cod, n, msg in probs: print(f"[{nv}] {cod}: {msg}")
    print(f"{sum(1 for p in probs if p[0] == 'ERRO')} erro(s), {sum(1 for p in probs if p[0] == 'AVISO')} aviso(s)")
    sys.exit(1 if any(p[0] == "ERRO" for p in probs) else 0)
