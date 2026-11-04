"""Ao pé da letra: confere se cada frase da narração (o que o áudio diz) está na tela no mesmo segundo, e conserta.

Para cada legenda do roteiro técnico (subs: voz + trecho do áudio), o módulo:
  1. acha os objetos e lugares citados (milho, lata, caixa de papelão, crachá, telefone, porta de aço, cozinha...),
     pelo vocabulário da biblioteca de móveis (lofi/moveis.py) e dos ambientes (lofi/cenario_gen.py);
  2. vê o que o plano daquele segundo mostra (móveis do cenário gerado, inventário dos cenários desenhados, planos de
     detalhe e closes);
  3. aponta cada frase cujo objeto não aparece e, com --aplicar, abre um close do objeto (cenário generativo "close")
     exatamente no tempo da frase, cortando o plano em volta sem perder as animações dele. Frases só de número logo depois
     de um close ("Duas." "Três.") viram contagem no mesmo close (n = 2, 3).

    python3 -m lofi.literal series/o-ultimo-estoque/ep01.json                 -> relatório
    python3 -m lofi.literal series/o-ultimo-estoque/ep01.json --aplicar       -> grava ep01.json com os closes
    python3 -m lofi.literal ep01.json --aplicar --saida ep01_literal.json     -> grava em outro arquivo

O verificador (python3 -m lofi.check) mostra o resumo: "literal: 87% das frases com a imagem do que é dito".
"""
import copy, json, os, re, sys, unicodedata
from . import moveis as MV
from . import cenario_gen as CG

# ---------------- vocabulário ----------------
def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


# palavras que são objeto mas não pedem close (genéricas demais ou já são o lugar)
IGNORAR = {"caixa", "porta", "luz", "chão", "chao", "data", "fogo", "folha", "torre", "box", "banco", "grade", "lixo", "faixa", "leito",
           "comida", "pasta", "mato", "tronco", "galho", "música", "musica", "lá fora", "barril", "rádio", "radio", "câmera", "camera"}
# famílias: tudo que mostra o mesmo objeto para quem assiste
FAMILIA = {"lata": "lata", "lata_caida": "lata", "milho": "lata", "latas": "lata", "prateleira": "prateleira", "relogio_parede": "relogio",
           "relogio": "relogio", "celular": "celular", "celular_mesa": "celular", "telefone": "telefone", "porta": "porta",
           "radinho": "radio", "radio": "radio", "radio_portatil": "radio", "radio_carro": "radio", "chave": "chave", "macaneta": "porta",
           "cracha": "cracha", "cadeado": "cadeado", "caixa": "caixa", "pilha_caixas": "caixa", "palete": "caixa", "papel": "papel", "prancheta": "papel",
           "carro": "carro", "viatura": "carro", "geladeira": "geladeira", "expositor": "geladeira", "freezer": "geladeira",
           "janela": "janela", "lampada": "luz", "fluorescente": "luz", "abajur": "luz", "abajur_mesa": "luz"}

# frases com objeto específico que o vocabulário automático não pega bem
EXTRA = {"milho em lata": "lata", "lata de milho": "lata", "caixa de milho": "caixa", "caixa de papelão": "caixa", "porta de aço": "porta",
         "porta de vidro": "porta", "porta dos fundos": "porta", "porta vaivém": "porta", "chamada perdida": "telefone",
         "telefone do mercado": "telefone", "fone de ouvido": "radinho", "radinho": "radinho", "luz de emergência": "lampada",
         "lâmpada": "lampada", "crachá": "cracha", "cadeado": "cadeado", "câmara fria": "geladeira", "relógio": "relogio_parede",
         "ponteiro": "relogio_parede", "celular": "celular", "chave": "chave", "maçaneta": "porta", "prancheta": "prancheta",
         "janela basculante": "janela", "vidro": "janela", "caixa registradora": "caixa_registradora", "prateleira": "prateleira",
         "gôndola": "prateleira", "lata": "lata", "latas": "lata"}

NUMEROS = {"um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10}


def vocabulario():
    voc = {}
    for palavra, nome in MV.sinonimos().items():
        if palavra in IGNORAR or len(palavra) < 3: continue
        voc[palavra] = nome
    voc.update(EXTRA)
    for amb in CG.AMBIENTES:
        if "_" not in amb: voc.setdefault(amb, "@" + amb)
    voc.update({"cemitério": "@cemiterio", "cozinha": "@cozinha", "banheiro": "@banheiro", "quarto": "@quarto", "porão": "@porao",
                "sótão": "@sotao", "farmácia": "@farmacia", "estrada": "@estrada", "praia": "@praia", "praça": "@praca", "quintal": "@quintal"})
    itens = sorted(voc.items(), key=lambda kv: -len(kv[0]))
    return [(re.compile(r"(?<![\w])" + re.escape(_sem_acento(p)) + r"(?:s|es)?(?![\w])"), p, n) for p, n in itens]


_VOC = None
EXPRESSOES = ("fiquem em casa", "fique em casa", "em casa", "pra casa", "para casa", "de casa", "na frente do vidro", "do vidro pra fora")


def citados(texto):
    """Objetos (nomes de lofi/moveis.py) e ambientes ('@cozinha') citados na frase, sem repetir e sem sobrepor."""
    global _VOC
    if _VOC is None: _VOC = vocabulario()
    t = _sem_acento(texto.replace("*", "")); ocup = []; out = []
    for e in EXPRESSOES: t = t.replace(_sem_acento(e), " " * len(e))   # expressões que não pedem o objeto na tela
    for rx, palavra, nome in _VOC:
        for m in rx.finditer(t):
            if any(m.start() < b and m.end() > a for a, b in ocup): continue
            ocup.append((m.start(), m.end()))
            if nome not in [n for _, n in out]: out.append((m.start(), nome))
    return [n for _, n in sorted(out)]                        # na ordem em que aparecem na frase


def fam(nome): return FAMILIA.get(nome, nome)


# ---------------- o que cada plano mostra ----------------
INVENTARIO = {     # cenários desenhados à mão: o que se vê neles
    "apartamento": "janela sofa estante rack_tv abajur tapete mesa quadro planta ventilador_teto @sala_estar",
    "entrada": "porta cabideiro sapato", "corredor": "porta lampada", "rua": "carro poste predio", "rua_amanhecer": "carro poste predio",
    "janela": "janela predio", "escada": "lampada", "telhado": "caixa_dagua", "radio": "radinho mesa", "radio_portatil": "radinho",
    "radio_carro": "radinho carro", "hospital": "maca lampada porta", "mercado": "prateleira lata fluorescente placa",
    "metro": "lampada", "escola": "porta lampada", "delegacia": "mesa arquivo porta", "posto": "carro poste placa", "floresta": "arvore arbusto",
    "carro": "carro", "esgoto": "poca", "igreja": "cruz vela banco", "loja": "balcao caixa_registradora porta janela prateleira expositor relogio_parede telefone",
    "deposito": "porta janela pilha_caixas caixa gerador lampada palete geladeira", "camara_fria": "geladeira porta caixa", "cftv": "tv_parede camera_seguranca",
    "mezanino": "pilha_caixas caixa janela", "beco": "lixeira_rua muro poste", "portao": "portao predio", "viaduto": "poste carro",
    "estacionamento": "carro lampada", "vagao": "banco porta", "sala_aula": "quadro_avisos relogio_parede porta mesa cadeira janela", "quadra": "",
}
DETALHE = {"relogio": "relogio_parede", "celular": "celular", "chave": "chave", "macaneta": "porta", "olho": "olho"}
AMB_DE = {"mercado": "corredor_mercado", "loja": "corredor_mercado", "deposito": "porao", "camara_fria": "porao", "mezanino": "sotao", "apartamento": "sala_estar",
          "hospital": "quarto_hospital", "escola": "laboratorio", "rua": "rua_bairro", "beco": "terreno_baldio", "floresta": "acampamento"}


def mostra(shot):
    """Conjunto (famílias) do que aparece no plano."""
    out = set()
    tp = shot.get("type", "scene")
    if tp == "detail":
        out.add(fam(DETALHE.get(shot.get("subject"), shot.get("subject")))); return out
    if tp != "scene": return out
    cen = shot.get("cenario"); nome = shot.get("scene")
    if isinstance(cen, (dict, str)) or (isinstance(nome, str) and (nome in CG.AMBIENTES or nome.startswith("gen_"))):
        spec = cen if cen is not None else _spec_registrado(nome)
        if isinstance(spec, dict) and spec.get("close"):
            out.add(fam(spec["close"]))
            if spec.get("superficie") in ("prateleira", "balcao", "mesa"): out.add(fam(spec["superficie"]))
            o = spec.get("opts") or {}
            if "MILHO" in str(o.get("texto", "")) or o.get("conteudo") in ("milho", "latas"): out.add("lata")
            return out
        cfg = CG.expandir(spec if spec is not None else nome)
        base = spec.get("base") if isinstance(spec, dict) else (spec or nome)
        if base: out.add("@" + base)
        for m in cfg["moveis"]:
            out.add(fam(m["m"]))
            for c in (m.get("conteudo") if isinstance(m.get("conteudo"), list) else [m.get("conteudo")]):
                if c in ("latas", "milho"): out.add("lata")
            for it in m.get("itens", ["caixa_registradora"] if m["m"] == "balcao" else []):
                out.add(fam(it if isinstance(it, str) else it.get("m")))
        return out
    for o in INVENTARIO.get(nome, "").split(): out.add(fam(o))
    out.add("@" + str(nome))
    pr = shot.get("props", {})
    if "relogio" in pr: out.add("relogio")
    if pr.get("tv"): out.add("rack_tv")
    return out


def _spec_registrado(nome):
    from . import scenes
    cls = scenes.REGISTRY.get(nome)
    return getattr(cls, "SPEC", None) if cls else None


# ---------------- leitura do episódio ----------------
def frases(ep):
    """[(início, fim, texto)] no tempo do vídeo, uma por legenda do roteiro técnico."""
    out = []
    for s in ep.spec.get("subs", []):
        a, b = ep.to_video(s["voice"], s["src"][0]), ep.to_video(s["voice"], s["src"][1])
        if a is None or b is None: continue
        txt = " ".join(s["text"]) if isinstance(s["text"], list) else str(s["text"])
        out.append((round(a, 3), round(b, 3), txt))
    return sorted(out)


def plano_em(shots, t):
    return next((s for s in shots if s["start"] <= t < s["end"]), None)


def analisar(caminho):
    from .render import Episode
    ep = Episode(caminho)
    linhas = []
    for a, b, txt in frases(ep):
        meio = (a + b) / 2; sh = plano_em(ep.shots, meio)
        cit = citados(txt)
        if sh and sh.get("type", "scene") not in ("scene", "detail"): cit = []      # telas próprias (pensamento, escolha, regra...)
        vis = set()                                             # tudo o que aparece durante a frase (pode ter mais de um corte)
        for o in ep.shots:
            if o["start"] < b - 0.05 and o["end"] > a + 0.05 and o.get("type", "scene") in ("scene", "detail"): vis |= mostra(o)
        falta = [c for c in cit if fam(c) not in vis and not (c.startswith("@") and sh and sh.get("type", "scene") != "scene")]
        linhas.append({"t": a, "fim": b, "texto": txt, "cita": cit, "falta": falta, "plano": sh["start"] if sh else None,
                       "cena": (sh or {}).get("scene") or (sh or {}).get("subject") or (sh or {}).get("type")})
    longos = []
    for s in ep.shots:
        if s.get("type", "scene") != "scene" or s.get("hook"): continue
        n = sum(1 for l in linhas if s["start"] <= (l["t"] + l["fim"]) / 2 < s["end"])
        if s["end"] - s["start"] > 7 and n >= 4: longos.append((s["start"], s["end"], n))
    com = [l for l in linhas if l["cita"]]
    ok = sum(1 for l in com if not l["falta"])
    return {"frases": linhas, "com_objeto": len(com), "ok": ok, "nota": (ok / len(com)) if com else 1.0, "planos_longos": longos}


def resumo(rel):
    return f"literal: {round(rel['nota'] * 100)}% das frases com a imagem do que é dito ({rel['ok']}/{rel['com_objeto']})"


def relatorio(rel):
    out = [resumo(rel), ""]
    for l in rel["frases"]:
        if not l["cita"]: continue
        marca = "ok " if not l["falta"] else "FALTA"
        out.append(f"{l['t']:7.2f}s  {marca}  {l['texto'][:60]:<60}  cita: {', '.join(l['cita'])}" + (f"  → não aparece: {', '.join(l['falta'])}  (plano {l['cena']})" if l["falta"] else ""))
    if rel["planos_longos"]:
        out += ["", "Planos que cobrem muitas frases (cada frase pede a sua imagem):"]
        out += [f"  {a:.1f}–{b:.1f}s: {n} frases" for a, b, n in rel["planos_longos"]]
    return "\n".join(out)


# ---------------- conserto: closes no tempo da frase ----------------
def _desloca(v, dt, dur):
    """Keyframes [[t, valor], ...] deslocados em -dt (o plano foi cortado e recomeça dt segundos depois)."""
    if isinstance(v, list) and v and all(isinstance(k, list) and len(k) == 2 and isinstance(k[0], (int, float)) for k in v):
        novos = [[round(t - dt, 3), x] for t, x in v]
        antes = [k for k in novos if k[0] <= 0]; depois = [k for k in novos if k[0] > 0]
        base = [[0, antes[-1][1]]] if antes else []
        return base + depois if (base + depois) else [[0, v[-1][1]]]
    if isinstance(v, dict): return {k: _desloca(x, dt, dur) for k, x in v.items()}
    if isinstance(v, list): return [_desloca(x, dt, dur) for x in v]
    return v


def _continua(shot, t0):
    """Cópia do plano que começa em t0 (as animações seguem de onde estavam)."""
    s = copy.deepcopy(shot); dt = t0 - shot["start"]
    for k in list(s.keys()):
        if k in ("start", "end", "hook", "transition", "cenario", "scene"): continue
        if k in ("props", "camera", "actors", "crowd", "dark", "fog", "time", "lights"): s[k] = _desloca(s[k], dt, shot["end"] - t0)
    for a in s.get("actors", []):
        for k in ("enter", "exit"):
            if isinstance(a.get(k), (int, float)): a[k] = round(a[k] - dt, 3)
    s.pop("hook", None); s.pop("transition", None)
    s["start"] = round(t0, 3)
    return s


def _superficie(obj, shot):
    lug = MV.MOVEIS[obj].lugar
    if obj in ("lata", "garrafa", "caixa_remedio") and shot and fam_set(shot) & {"prateleira"}: return "prateleira"
    return {"chao": "chao", "parede": "parede", "cima": "balcao", "teto": "nenhuma", "fora": "nenhuma"}.get(lug, "chao")


def fam_set(shot):
    try: return mostra(shot)
    except Exception: return set()


def _ambiente(shot):
    if not shot: return None
    cen = shot.get("cenario")
    if isinstance(cen, dict) and not cen.get("close"): return cen.get("base")
    if isinstance(cen, str): return cen
    nome = shot.get("scene")
    if nome in CG.AMBIENTES: return nome
    return AMB_DE.get(nome)


def _protagonista(ep, shot):
    for a in (shot or {}).get("actors", []): return a["char"]
    return next(iter(ep.locked), None)


def aplicar(caminho, saida=None, min_dur=0.9):
    """Abre um close do objeto citado em cada frase que não o mostra. Devolve (n_closes, caminho gravado)."""
    from .protecao import bloquear
    bloquear(saida or caminho)                     # episódio travado (protegidos.json): recusa antes de qualquer coisa
    from .render import Episode
    ep = Episode(caminho)
    spec = json.load(open(caminho, encoding="utf-8"))
    shots = sorted(spec["shots"], key=lambda s: s["start"])
    rel = analisar(caminho); fr = rel["frases"]
    novos = 0; ultimo = None      # último close aberto: (shot, objeto, n)
    for i, l in enumerate(fr):
        palavras = [w for w in re.findall(r"\w+", _sem_acento(l["texto"].replace("*", "")))]
        # "Duas." "Três." logo depois do close de um objeto: conta no mesmo close
        if ultimo and palavras and all(w in NUMEROS for w in palavras) and l["t"] - ultimo[0]["end"] < 1.2:
            cs, obj, n = ultimo; n = NUMEROS[palavras[-1]]
            nxt = plano_em(shots, l["fim"] + 0.01)
            novo_fim = max(cs["end"], l["fim"] + 0.25)
            if nxt is not None and nxt is not cs and nxt.get("type", "scene") == "scene" and not nxt.get("hook"):
                if nxt["end"] - novo_fim > 0.6: _encolhe(shots, nxt, novo_fim)
                elif nxt["end"] - nxt["start"] < 1.6: novo_fim = nxt["end"]; shots.remove(nxt)     # sobra curta: o close vai até o fim
                else: novo_fim = cs["end"]
            elif nxt is not None and nxt is not cs: novo_fim = cs["end"]
            cs["props"].setdefault("n", [[0, 1]]).append([round(l["t"] - cs["start"], 3), n]); cs["end"] = round(novo_fim, 3)
            ultimo = (cs, obj, n); continue
        n0 = next((NUMEROS[w] for w in palavras if w in NUMEROS), None)
        contagem = n0 is not None and len(palavras) <= 3 and any(c in MV.MOVEIS for c in l["cita"])   # "Uma lata."
        objs = [c for c in (l["cita"] if contagem else l["falta"]) if not c.startswith("@") and c in MV.MOVEIS]
        objs = [c for c in objs if not any(c in _junto(o, l["texto"]) for o in objs if o != c)]     # caixa de milho: um close só
        if not objs: continue
        sh = plano_em(shots, (l["t"] + l["fim"]) / 2)
        if not sh or sh.get("type", "scene") != "scene" or sh.get("hook") or isinstance(sh.get("cenario"), dict) and sh["cenario"].get("close"):
            continue
        a = max(sh["start"], l["t"] - 0.1); b = min(sh["end"], max(l["fim"] + 0.15, a + min_dur))
        if b - a < 0.6: continue
        objs = objs[:2] if b - a >= 1.8 else objs[:1]                  # frase longa com dois objetos: dois closes
        fatias = [(a + (b - a) * k / len(objs), a + (b - a) * (k + 1) / len(objs)) for k in range(len(objs))]
        for obj, (fa, fb) in zip(objs, fatias):
            sh = plano_em(shots, (fa + fb) / 2)
            if not sh or sh.get("type", "scene") != "scene" or isinstance(sh.get("cenario"), dict) and sh["cenario"].get("close"): continue
            close = _close(ep, sh, obj, l, fa, fb, fr[i + 1]["texto"] if i + 1 < len(fr) else "", n0 if contagem else None)
            _encaixa(shots, sh, close)
            novos += 1; ultimo = (close, obj, n0 or 1)
    spec["shots"] = sorted(shots, key=lambda s: s["start"])
    out = saida or caminho
    json.dump(spec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return novos, out


ESTADOS = [   # verbo da frase -> estado do objeto no close
    (r"explod|quebr|estour|estilha|trinc", {"quebrada": True}),
    (r"\babr[ei]|\baberta|\baberto", {"aberta": 1, "aberto": True}),
    (r"\bacend|\bacesa|\baceso|\bliga", {"aceso": True, "acesa": True, "ligado": True}),
    (r"\bapag|\bdesliga", {"aceso": False, "acesa": False, "ligado": False}),
    (r"pisca", {"pisca": True}),
    (r"chiad", {"tv": "chiado"}),
]
PROPS_VERBO = [(r"trem|bate|batida|chacoalh|sacod", {"treme": 1}), (r"\bcai\b|caindo|derrub|despenc", {"cai": [[0, 0.0], [0.45, 1.0]]})]


def _junto(obj, texto):
    """Produtos que o close de `obj` já mostra (caixa de milho = caixa com o rótulo MILHO)."""
    return {"lata"} if obj in ("caixa", "prateleira") and re.search(r"milho|lata", _sem_acento(texto)) else set()


def _close(ep, sh, obj, l, a, b, prox="", n=None):
    """Monta o plano de close do objeto para a frase l, no intervalo [a, b]."""
    txt = l["texto"]; tn = _sem_acento(txt)
    cen = {"close": obj, "superficie": _superficie(obj, sh)}
    amb = _ambiente(sh)
    if amb: cen["ambiente"] = amb
    opts = {}; props = {}
    for rx, st in ESTADOS:
        if re.search(rx, tn): opts.update(st)
    for rx, st in PROPS_VERBO:
        if re.search(rx, tn): props.update(st)
    if obj in ("caixa", "pilha_caixas"):
        m = re.search(r"caixas? de ([a-z]+)", tn)
        if m and m.group(1) not in ("papelao",): opts["texto"] = m.group(1).upper()
        if "milho" in tn: opts["texto"] = "MILHO"
    hora = re.search(r"\b(\d{1,2})\s*[:h]\s*(\d{2})\b", tn) or re.search(r"\b(\d{1,2})\s*[:h]\s*(\d{2})\b", _sem_acento(prox))
    if hora and obj in ("telefone", "celular", "caixa_registradora", "relogio_parede"):
        hm = f"{int(hora.group(1)):02d}:{hora.group(2)}"
        opts["hora" if obj == "relogio_parede" else "visor"] = hm
    if obj == "telefone" and "perdida" in tn: opts["pisca"] = True
    if obj == "cracha":
        nomes = [k.upper() for k in ep.custom if k in tn] or [w.upper() for w in re.findall(r"\b(?:do|da) ([a-z]+)\b", tn) if w not in ("chao", "mercado")]
        if nomes: opts["nome"] = nomes[0]
    if opts: cen["opts"] = opts
    close = {"start": round(a, 3), "end": round(b, 3), "cenario": cen, "camera": {"handheld": 3, "zoom": [1.0, 1.05], "cortes": False},
             "props": props, "light": sh.get("light", "neutra"), "literal": txt}
    if n and n > 1: close["props"]["n"] = n
    prot = _protagonista(ep, sh)
    if prot and re.search(r"\bvoce\b", tn) and MV.MOVEIS[obj].lugar in ("cima", "chao", "piso") and obj not in ("prateleira", "pilha_caixas"):
        close["hand"] = prot; close["props"]["mao"] = [[0, 0.0], [min(0.5, (b - a) / 2), 1.0]]
    if obj == "caixa" and re.search(r"empurr|arrast", tn): close["props"]["desliza"] = [[0, 0.0], [round(b - a, 3), 1.0]]
    return close


def _encolhe(shots, sh, novo_inicio):
    """O plano seguinte começa mais tarde (as animações seguem do ponto certo)."""
    i = shots.index(sh); shots[i] = _continua(sh, novo_inicio); shots[i]["end"] = sh["end"]
    if sh.get("transition"): shots[i]["transition"] = sh["transition"]


def _encaixa(shots, sh, close):
    """Corta o plano `sh` em volta do close: [início, a] + close + [b, fim] (a continuação segue as animações)."""
    a, b = close["start"], close["end"]; i = shots.index(sh); partes = []
    if a - sh["start"] > 0.3:
        p1 = copy.deepcopy(sh); p1["end"] = a; partes.append(p1)
    else:
        close["start"] = sh["start"]
        if sh.get("transition"): close["transition"] = sh["transition"]
    partes.append(close)
    if sh["end"] - b > 0.3:
        p2 = _continua(sh, b); p2["end"] = sh["end"]; partes.append(p2)
    else:
        close["end"] = sh["end"]
    shots[i:i + 1] = partes


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Confere e conserta: cada frase da narração com a sua imagem, ao pé da letra.")
    ap.add_argument("roteiro"); ap.add_argument("--aplicar", action="store_true"); ap.add_argument("--saida")
    a = ap.parse_args()
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    if a.aplicar:
        n, out = aplicar(a.roteiro, a.saida)
        print(f"{n} closes literais inseridos → {out}")
        print(resumo(analisar(out)))
    else:
        print(relatorio(analisar(a.roteiro)))
