"""Valida o roteiro (epNN_roteiro.md) antes de entregar ao usuário.

    python3 tests/validar_roteiro.py series/dia-zero/ep03_roteiro.md [--final]

Estrutura: gancho no início, abertura com carimbo, 12 cenas ou mais, pergunta A/B + "CONTINUA NO EPISÓDIO"
(ou "FIM" no último), narração ElevenLabs por personagem, legendas com até 4 palavras por pedaço, duração mínima de 2 min (sem máximo).

Nomes do motor: nas linhas CENÁRIO, PERSONAGENS, PLANO/TRANSIÇÃO, LUZ e SOM, todo nome entre crases (`bang`, `escada`,
`fear`...) precisa existir no motor (CATALOGO.md) ou em personagens.json da série. Nome errado é ERRO, com sugestão.
O CENÁRIO também é conferido pela primeira palavra, mesmo sem crases.
"""
import re, sys, os, json, difflib, unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

# Campos e valores do roteiro técnico que podem aparecer entre crases nas linhas de direção (SPEC.md).
CAMPOS_ATOR = {"crowd", "walk", "run", "tremble", "hold", "carried_by", "flashlight", "fg", "lift", "rot", "gesture", "nod", "shake",
               "down", "look", "facing", "enter", "exit", "sniff", "breath", "prop", "scale", "blur", "voice", "lipsync", "gestures"}
CAMPOS_PLANO = {"close", "travelling", "follow", "focus", "handheld", "vertigo", "slowmo", "scare", "lens_drops", "dark", "wall_shadow", "lights",
                "cold", "dust", "crowd", "fog", "rain", "snow", "time", "tint", "peephole", "shake", "lightning", "hook", "bloom",
                "style", "desenho", "acoustic", "detail", "recap", "moments", "choice", "title", "effect", "camera", "zoom",
                "flicker", "plano", "aberto", "conjunto", "medio", "geral", "alvo", "tv", "static", "fan", "wind", "train", "door", "locks", "under_door_light", "feet", "on", "level"}


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def carregar_nomes(caminho_roteiro):
    try:
        from lofi.catalogo import catalogo
        c = catalogo()
    except Exception as e:  # sem dependências do motor: só a estrutura é validada
        return None, f"catálogo do motor indisponível ({e}); nomes não conferidos"
    locked = set()
    pasta = os.path.dirname(os.path.abspath(caminho_roteiro))
    for p in (os.path.join(pasta, "personagens.json"), os.path.join(os.path.dirname(pasta), "personagens.json")):
        if os.path.isfile(p):
            locked = {k for k in json.load(open(p, encoding="utf-8")) if not k.startswith("_")}; break
    clima = set(c["clima"]["rain"]) | set(c["clima"]["time"])
    from lofi.mapa import MAPA
    marcas = {n for m in MAPA.values() for n in m["marcas"]}
    from lofi.partes import POSICOES
    maos = {"hand", "of", "at"} | {n for ps in POSICOES.values() for n in ps}
    personagens = set(c["personagens"]) | locked
    nomes = {
        "CENARIO": set(c["cenarios"]) | set(c["detalhes"]) | CAMPOS_PLANO | clima | maos | personagens,
        "PERSONAGENS": personagens | set(c["poses"]) | set(c["emocoes"]) | set(c["vistas"]) | set(c["objetos"])
                       | set(c["corpos"]) | CAMPOS_ATOR | marcas | {"mark"} | maos,
        "PLANO": set(c["transicoes"]) | set(c["detalhes"]) | CAMPOS_PLANO | clima | personagens | set(c["acusticas"]) | maos,
        "SOM": set(c["sons"]),
    }
    nomes["LUZ"] = nomes["PLANO"] | {"flashlight"}
    return {"nomes": nomes, "cenarios": set(c["cenarios"])}, None


ROTULOS = {"CENARIO": "CENARIO", "PLANO DE DETALHE": "CENARIO", "PERSONAGENS": "PERSONAGENS", "PERSONAGEM": "PERSONAGENS",
           "PLANO": "PLANO", "TRANSICAO": "PLANO", "CAMERA": "PLANO", "LUZ": "LUZ", "LUZ E DETALHES": "LUZ", "SOM": "SOM", "SONS": "SOM"}
RE_LINHA = re.compile(r"^[\s\-*>]*\**\s*(PLANO DE DETALHE|LUZ E DETALHES|CEN[AÁ]RIO|PERSONAGENS?|PLANO|TRANSI[CÇ][AÃ]O|C[AÂ]MERA|LUZ|SONS|SOM)\b[^:\n]*:\**\s*(.*)$", re.I)


def conferir_nomes(txt, cat):
    erros, avisos = [], []
    for n, linha in enumerate(txt.splitlines(), 1):
        m = RE_LINHA.match(linha)
        if not m: continue
        tipo = ROTULOS[sem_acento(m.group(1)).upper()]
        resto = m.group(2)
        validos = cat["nomes"][tipo]
        crases = re.findall(r"`([^`]+)`", resto)
        for nome in crases:
            nome = nome.strip()
            if nome in validos or not re.fullmatch(r"[a-z0-9_çãéíóúâêô]+", nome): continue
            sug = difflib.get_close_matches(nome, validos, 1, 0.6)
            erros.append(f"linha {n}: '{nome}' não existe no motor ({tipo.lower()})" + (f" — quis dizer '{sug[0]}'?" if sug else ""))
        if tipo == "CENARIO" and not sem_acento(m.group(1)).upper().startswith("PLANO DE DETALHE"):
            primeira = re.findall(r"[\wÀ-ÿ]+", sem_acento(resto.replace("`", "")))
            if primeira and primeira[0] not in cat["cenarios"] and not crases:
                sug = difflib.get_close_matches(primeira[0], cat["cenarios"], 1, 0.6)
                avisos.append(f"linha {n}: cenário '{primeira[0]}' não está na biblioteca" +
                              (f" — quis dizer '{sug[0]}'?" if sug else " (será preciso criá-lo no motor)"))
        if tipo == "SOM" and not crases and resto.strip() and not re.search(r"\b(sil[eê]ncio|nenhum)\b", resto, re.I):
            avisos.append(f"linha {n}: SOM sem nomes do motor entre crases (ex.: `bang` 3 s)")
    return erros, avisos


def conferir_continuidade(txt, cat):
    """Pulo de lugar sem LIGAÇÃO e objeto fora do lugar (rádio de casa no carro, rádio do carro fora dele)."""
    from lofi.mapa import lugar, OBJETO_DO_LUGAR
    erros = []
    partes = re.split(r"^#+\s*CENA\s+(\d+)[^\n]*$", txt, flags=re.M)
    atual = None
    for k in range(1, len(partes) - 1, 2):
        n, corpo = int(partes[k]), partes[k + 1]
        m = re.search(r"CEN[AÁ]RIO[^:\n]*:\**\s*`([^`]+)`", corpo, re.I)
        if n == 0 or not m: continue                     # gancho e planos de detalhe não mudam o lugar
        cena = m.group(1).strip()
        if cena not in cat["cenarios"]: continue
        insercao = re.search(r"INSER[ÇC][ÃA]O", corpo, re.I)
        ligacao = re.search(r"LIGA[ÇC][ÃA]O\s*:", corpo, re.I)
        dono = OBJETO_DO_LUGAR.get(cena)
        if dono and atual and dono != atual and not insercao:
            alt = {"casa": "`radio_carro` (no carro) ou `radio_portatil` (na mão)", "carro": "`radio` (em casa) ou `radio_portatil` (na mão)"}[dono]
            erros.append(f"CENA {n}: `{cena}` é um objeto de {dono}, mas a história está em '{atual}'. Use {alt}")
            continue
        novo = lugar(cena)
        if novo is None or insercao: continue
        if atual is not None and novo != atual and not ligacao:
            erros.append(f"CENA {n}: pulo de lugar ('{atual}' → '{novo}') sem mostrar o caminho. Escreva uma linha "
                         f"LIGAÇÃO: dizendo como eles chegam lá (e mostre a passagem na cena), ou marque INSERÇÃO se for só um corte para outro lugar")
        atual = novo
    return erros


def validar_extra(txt, caminho=None):
    """Episódio extra de curiosidades: 45–100 s, gancho, 5+ cenas, sem votação, chamada para o episódio/votação."""
    erros, avisos = [], []
    up = txt.upper()
    if "GANCHO" not in up: erros.append("falta a CENA 0 · GANCHO")
    if "EXTRA" not in up: erros.append("o título precisa dizer EXTRA")
    cenas = set(int(n) for n in re.findall(r"^[#\s*\-]*CENA\s+(\d+)", up, re.M) if int(n) > 0)
    if len(cenas) < 5: erros.append(f"{len(cenas)} cenas (mínimo 5 no extra)")
    if "CHAMADA" not in up: erros.append("falta a CHAMADA final (ex.: 'A VOTAÇÃO DO EP. 3 CONTINUA ABERTA' ou 'TEMPORADA 2?')")
    if re.search(r"^\s*A\)", txt, re.M) and re.search(r"^\s*B\)", txt, re.M): avisos.append("extra não tem votação A/B")
    if "ELEVENLABS" not in up: erros.append("falta a narração para o ElevenLabs")
    for m in re.finditer(r"LEGENDA[^:\n]*:\s*(.+)", txt, re.I):
        for piece in re.split(r"\s*/\s*", m.group(1)):
            if len(piece.split()) > 4: avisos.append(f"legenda com mais de 4 palavras: '{piece.strip()}'")
    tempos = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*s\b", re.sub(r"(\d),(\d)", r"\1.\2", txt))]
    if tempos and not (45 <= max(tempos) <= 100): erros.append(f"maior tempo citado {max(tempos):.0f}s: o extra tem de 45 a 100 s")
    cat, motivo = carregar_nomes(caminho or ".")
    if cat is None: avisos.append(motivo)
    else:
        e, a = conferir_nomes(txt, cat); erros += e; avisos += a
    return erros, avisos


def conferir_fluxo(txt, caminho=None):
    """Fluxo entre cenas: ninguém aparece ou some do nada, o tempo das cenas emenda, a fala cabe na cena e o gancho acontece."""
    erros, avisos = [], []
    pasta = os.path.dirname(os.path.abspath(caminho)) if caminho else "."
    nomes = set()
    pj = os.path.join(pasta, "personagens.json")
    if os.path.exists(pj):
        nomes = {k for k in json.load(open(pj, encoding="utf-8")) if not k.startswith("_") and not k.startswith("zombie")}
    partes = re.split(r"^#+\s*(CENA\s+\d+[^\n]*)$", txt, flags=re.M)
    cenas = []
    for k in range(1, len(partes) - 1, 2):
        cab, corpo = partes[k], re.split(r"\n---|\n##\s", partes[k + 1])[0]
        n = int(re.search(r"CENA\s+(\d+)", cab).group(1))
        tm = re.search(r"(\d+(?:[.,]\d+)?)\s*s?\s*(?:a|–|-)\s*(\d+(?:[.,]\d+)?)\s*s", cab)
        a, b = (float(tm.group(1).replace(",", ".")), float(tm.group(2).replace(",", "."))) if tm else (None, None)
        cen = re.search(r"CEN[AÁ]RIO[^:\n]*:\**\s*`([^`]+)`", corpo, re.I)
        pl = re.search(r"PERSONAGENS?[^:\n]*:(.*)", corpo, re.I)
        quem = {x for x in re.findall(r"`([^`]+)`", pl.group(1))} & nomes if pl and nomes else set()
        cenas.append(dict(n=n, a=a, b=b, cen=cen.group(1) if cen else None, quem=quem, corpo=corpo,
                          detalhe=bool(re.search(r"PLANO DE DETALHE|^\s*PENSAMENTO\s*:|^\s*O PLANO\s*:", corpo, re.I | re.M)) and not cen,
                          insercao=bool(re.search(r"INSER[ÇC][ÃA]O", corpo, re.I)),
                          objeto=bool(cen and cen.group(1).startswith("radio")),
                          liga=bool(re.search(r"LIGA[ÇC][ÃA]O\s*:", corpo, re.I)),
                          entra=bool(re.search(r"\bENTRA\s*:", corpo)), sai=bool(re.search(r"\bSAI\s*:", corpo))))
    # tempo emendado
    ant = None
    for c in cenas:
        if c["n"] == 0 or c["a"] is None: continue
        if ant and ant["b"] is not None and abs(c["a"] - ant["b"]) > 0.6:
            avisos.append(f"CENA {c['n']}: começa em {c['a']:g} s, mas a cena {ant['n']} termina em {ant['b']:g} s (buraco ou sobreposição)")
        ant = c
        if c["b"] and c["b"] > c["a"]:
            pal = 0
            for linha in c["corpo"].split("\n"):
                m = re.match(r"^\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ ]{1,30}(?:\s*\([^)]*\))?)\s*:\s*(.+)$", linha)
                if not m: continue
                rot = m.group(1).strip()
                if re.match(r"^(CEN|PERSON|PLANO|LUZ|SOM|LEGENDA|TEXTO|TRANSI|LIGA|INSER|ENTRA|SAI|PEGA|LARGA|ABERTURA|PERGUNTA|O TEMPO|CONSEQ|VIRADA|PENSAMENTO|O PLANO|NO BAL|PASSOS|SETAS|MAPA)", rot): continue
                pal += len(re.sub(r"\[[^\]]*\]", "", m.group(2)).split())
            wps = pal / (c["b"] - c["a"])
            if wps > 3.3: avisos.append(f"CENA {c['n']}: {pal} palavras em {c['b'] - c['a']:g} s ({wps:.1f}/s) — fala demais para o tempo; aumente a cena ou corte texto")
    # entrada e saída de personagens: quem está no lugar continua presente (mesmo fora do quadro) até SAI: ou trocar de lugar
    presentes, lugar_ant = set(), None
    for c in cenas:
        if c["n"] == 0 or c["detalhe"] or c["insercao"] or not c["cen"]: continue
        if c["objeto"] or c["cen"] in ("cftv",):          # close de objeto/monitor: só a mão de quem já está ali
            novos = c["quem"] - presentes
            if novos and presentes and not c["entra"]:
                erros.append(f"CENA {c['n']}: a mão de {', '.join(sorted(novos))} aparece, mas essa pessoa não está no lugar (ENTRA:)")
            continue
        if c["liga"] and lugar_ant is not None:
            pass                                             # mudou de lugar ou de canto: quem aparece veio junto
        else:
            novos = c["quem"] - presentes
            if novos and presentes and not c["entra"]:
                erros.append(f"CENA {c['n']}: {', '.join(sorted(novos))} aparece sem entrar (não estava no lugar). "
                             f"Escreva uma linha ENTRA: dizendo de onde vem, ou LIGAÇÃO: se foi outro lugar")
        presentes |= c["quem"]
        for quem in re.findall(r"\bSAI\s*:\s*`?(\w+)`?", c["corpo"]): presentes.discard(quem.lower())
        lugar_ant = c["cen"]
    # gancho acontece de verdade
    g = next((c for c in cenas if c["n"] == 0), None)
    if g and g["cen"] and not any(c["cen"] == g["cen"] for c in cenas if c["n"] > 0):
        avisos.append(f"GANCHO: o cenário `{g['cen']}` do gancho não aparece em nenhuma cena; o gancho tem que ser um momento real do episódio")
    if not re.search(r"^#+\s*ESCALETA", txt, re.M | re.I):
        avisos.append("falta a ESCALETA (6–10 batidas antes das cenas)")
    return erros, avisos


def conferir_retencao(txt, final=False):
    """Prende quem assiste: gancho escolhido entre 3, virada a cada <=30 s, pouca narração, escolha com custo, consequência
    do voto logo na 1ª cena, motivação dos personagens, pistas plantadas/pagas, pergunta do meio curta e fim em suspense."""
    av = []
    up = txt.upper()
    ep = re.search(r"EPIS[ÓO]DIO\s+(\d+)\s*/", up); n_ep = int(ep.group(1)) if ep else 1
    if not re.search(r"^#+\s*GANCHOS", txt, re.M | re.I) or len(re.findall(r"^\s*[1-3][.)]", txt.split("GANCHOS", 1)[-1][:1500], re.M)) < 3:
        av.append("faltam as 3 opções de GANCHO (seção ## GANCHOS com 1., 2., 3. e ESCOLHIDO:); o gancho bom é uma pergunta sem resposta")
    partes = re.split(r"^#+\s*(CENA\s+\d+[^\n]*)$", txt, flags=re.M)
    cenas = []
    for k in range(1, len(partes) - 1, 2):
        cab, corpo = partes[k], re.split(r"\n---|\n##\s", partes[k + 1])[0]
        n = int(re.search(r"CENA\s+(\d+)", cab).group(1))
        tm = re.search(r"(\d+(?:[.,]\d+)?)\s*s?\s*(?:a|–|-)\s*(\d+(?:[.,]\d+)?)\s*s", cab)
        if n and tm: cenas.append((n, float(tm.group(1).replace(",", ".")), float(tm.group(2).replace(",", ".")), corpo))
    if cenas:
        viradas = [a for n, a, b, c in cenas if re.search(r"^\s*VIRADA\s*:", c, re.M)]
        marcos = [cenas[0][1]] + viradas + [cenas[-1][2]]
        for x, y in zip(marcos, marcos[1:]):
            if y - x > 30: av.append(f"de {x:g} s a {y:g} s ({y - x:g} s) sem VIRADA (susto, revelação, decisão ou ameaça nova): ponha uma a cada 20–30 s")
        if not re.search(r"^\s*VIRADA\s*:", cenas[-1][3], re.M):
            av.append(f"a última cena ({cenas[-1][0]}) precisa de uma VIRADA: termine no meio da ação, com uma informação nova que complica a escolha")
        if n_ep > 1 and not re.search(r"CONSEQU[ÊE]NCIA\s*:", cenas[0][3], re.I):
            av.append("a CENA 1 precisa de uma linha CONSEQUÊNCIA: mostrando algo concreto que mudou por causa do voto")
        dur = max(1.0, cenas[-1][2] - cenas[0][1])
        narr = sum(len(re.sub(r"\[[^\]]*\]", "", m).split()) for m in re.findall(r"^\s*NARRA[ÇC][ÃA]O[^:]*:\s*(.+)$", txt, re.M))
        if narr / dur > 1.3:
            av.append(f"narração demais ({narr} palavras em {dur:.0f} s): narre só o que a imagem não mostra (pensamento, medo, memória); o resto vira ação, som e rosto")
    if not re.search(r"^\s*(PENSAMENTO|O PLANO)\s*:", txt, re.M | re.I):
        av.append("nenhuma cena de PENSAMENTO (balão com lembrança, imaginação ou medo) ou O PLANO (mapa desenhado com setas e passos): "
                  "mostre pelo menos uma vez o que o personagem pensa ou planeja, em vez de narrar")
    esc = re.search(r"^#+\s*ESCALETA.*?(?=^#+\s*(?:GANCHOS|PISTAS|CENA)|\Z)", txt, re.M | re.S | re.I)
    if esc and not re.search(r"DESEJO|MEDO|SEGREDO", esc.group(0), re.I):
        av.append("a ESCALETA não mexe em nenhum DESEJO, MEDO ou SEGREDO de personagem (veja a bíblia): cada episódio move pelo menos um")
    if not re.search(r"^#+\s*PISTAS", txt, re.M | re.I) or not re.search(r"PLANTA\s*:", txt) :
        av.append("falta a seção ## PISTAS com PLANTA: (pista nova para pagar depois) e PAGA: (pista antiga paga agora, se houver)")
    pq = re.search(r"PERGUNTA NO MEIO\s*:\s*([^(\n]+)", txt, re.I)
    if pq:
        q = pq.group(1).strip(" .*")
        if len(q.split()) > 7 or "?" not in q:
            av.append(f"pergunta do meio longa ou aberta ('{q}'): use até 7 palavras com resposta curta (sim/não ou X ou Y)")
    if not final:
        bloco = re.search(r"O que acontece em cada op[çc][ãa]o.*?(?=\n\*\*Resumo|\n---|\Z)", txt, re.S | re.I)
        b = bloco.group(0).upper() if bloco else ""
        if b.count("GANHA") < 2 or b.count("PERDE") < 2:
            av.append("a escolha A/B precisa custar algo dos dois lados: em 'O que acontece em cada opção' escreva GANHA: e PERDE: para A e para B")
    return av


def validar(txt, final=False, caminho=None):
    if "--extra" in sys.argv or (caminho and os.path.basename(caminho).startswith("extra")):
        return validar_extra(txt, caminho)
    erros, avisos = [], []
    up = txt.upper()
    if "GANCHO" not in up: erros.append("falta a CENA 0 · GANCHO")
    if "A MAIORIA ESCOLHEU" not in up and "EPISÓDIO 1/" not in up: erros.append("falta o carimbo 'A MAIORIA ESCOLHEU'")
    cenas = set(int(n) for n in re.findall(r"^[#\s*\-]*CENA\s+(\d+)", up, re.M) if int(n) > 0)
    if len(cenas) < 12: erros.append(f"{len(cenas)} cenas (mínimo 12)")
    elif sorted(cenas) != list(range(1, max(cenas) + 1)): avisos.append(f"numeração das cenas com falhas: {sorted(cenas)}")
    if final:
        if "FIM" not in up: erros.append("último episódio sem 'FIM'")
    else:
        if not re.search(r"\bA\)", txt) or not re.search(r"\bB\)", txt): erros.append("falta a pergunta com opções A) e B)")
        if "CONTINUA NO EPISÓDIO" not in up: erros.append("falta 'CONTINUA NO EPISÓDIO'")
    if "ELEVENLABS" not in up: erros.append("falta a narração para o ElevenLabs")
    if not re.search(r"\[(whispers|sighs|nervous|pause|scared|firm|angry|crying|breathing heavily|excited|sad|laughs|shouting)", txt, re.I):
        avisos.append("narração sem tags de voz em inglês")
    for m in re.finditer(r"LEGENDA[^:\n]*:\s*(.+)", txt, re.I):
        for piece in re.split(r"\s*/\s*", m.group(1)):
            if len(piece.split()) > 4: avisos.append(f"legenda com mais de 4 palavras: '{piece.strip()}'")
    tempos = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*s\b", re.sub(r"(\d),(\d)", r"\1.\2", txt))]
    if tempos and max(tempos) < 120: erros.append(f"maior tempo citado {max(tempos):.0f}s: o episódio precisa ter no mínimo 2 min")
    cat, motivo = carregar_nomes(caminho or ".")
    if cat is None: avisos.append(motivo)
    else:
        e, a = conferir_nomes(txt, cat); erros += e; avisos += a
        erros += conferir_continuidade(txt, cat)
    e, a_ = conferir_fluxo(txt, caminho); erros += e; avisos += a_
    avisos += conferir_retencao(txt, final)
    if caminho and os.path.isfile(caminho):     # mapa da cidade, inventário e relógio da série (mundo.json)
        from lofi.continuidade import conferir as conferir_mundo
        erros += conferir_mundo(caminho, txt)
    return erros, avisos


if __name__ == "__main__":
    caminho = sys.argv[1]
    e, a = validar(open(caminho, encoding="utf-8").read(), "--final" in sys.argv, caminho)
    for x in e: print("[ERRO]", x)
    for x in a: print("[AVISO]", x)
    print("OK" if not e else f"{len(e)} erro(s)")
    sys.exit(1 if e else 0)
