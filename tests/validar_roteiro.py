"""Valida o roteiro (epNN_roteiro.md) antes de entregar ao usuário.

    python3 tests/validar_roteiro.py series/dia-zero/ep03_roteiro.md [--final]

Estrutura: gancho no início, abertura com carimbo, 12–20 cenas, pergunta A/B + "CONTINUA NO EPISÓDIO"
(ou "FIM" no último), narração ElevenLabs por personagem, legendas com até 4 palavras por pedaço, duração 2–3 min.

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
CAMPOS_PLANO = {"close", "follow", "focus", "handheld", "vertigo", "slowmo", "scare", "lens_drops", "dark", "wall_shadow", "lights",
                "cold", "dust", "crowd", "fog", "rain", "snow", "time", "tint", "peephole", "shake", "lightning", "hook", "bloom",
                "style", "desenho", "acoustic", "detail", "recap", "moments", "choice", "title", "effect", "camera", "zoom",
                "flicker", "tv", "static", "fan", "wind", "train", "door", "locks", "under_door_light", "feet", "on", "level"}


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


def validar(txt, final=False, caminho=None):
    erros, avisos = [], []
    up = txt.upper()
    if "GANCHO" not in up: erros.append("falta a CENA 0 · GANCHO")
    if "A MAIORIA ESCOLHEU" not in up and "EPISÓDIO 1/" not in up: erros.append("falta o carimbo 'A MAIORIA ESCOLHEU'")
    cenas = set(int(n) for n in re.findall(r"^[#\s*\-]*CENA\s+(\d+)", up, re.M) if int(n) > 0)
    if not (12 <= len(cenas) <= 20): erros.append(f"{len(cenas)} cenas (padrão 12–20)")
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
    if tempos and not (110 <= max(tempos) <= 190): avisos.append(f"maior tempo citado {max(tempos):.0f}s (esperado 120–180 s)")
    cat, motivo = carregar_nomes(caminho or ".")
    if cat is None: avisos.append(motivo)
    else:
        e, a = conferir_nomes(txt, cat); erros += e; avisos += a
    return erros, avisos


if __name__ == "__main__":
    caminho = sys.argv[1]
    e, a = validar(open(caminho, encoding="utf-8").read(), "--final" in sys.argv, caminho)
    for x in e: print("[ERRO]", x)
    for x in a: print("[AVISO]", x)
    print("OK" if not e else f"{len(e)} erro(s)")
    sys.exit(1 if e else 0)
