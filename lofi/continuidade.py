"""Mapa da cidade da série e estado da história (onde estão, o que carregam, que horas são).

Arquivo da série: series/<serie>/mundo.json
{
  "lugares":  {"rua": {"cenarios": ["rua", "rua_amanhecer", "beco"], "nota": "..."}, ...},
  "ligacoes": [["rua", "metro", "pela escada da estação Sé"], ...],          # caminhos que existem (ida e volta)
  "fim": {"4": {"lugar": "carro", "dia": 5, "hora": "05:20",                   # como cada episódio terminou
                "inventario": {"roberta": ["radio", "lanterna"], "rafa": ["mochila"]}, "nota": "..."}}
}

No roteiro:
  - CENÁRIO com "DIA 4 · 22:10" marca a hora; o relógio só anda para frente. Pulo de mais de 3 h precisa de um
    PLANO DE DETALHE `relogio` (ou a linha "O TEMPO PASSA") entre as cenas.
  - "PEGA: roberta lanterna" e "LARGA: roberta radio" mudam o inventário.
  - cenário `radio_portatil` exige alguém com "radio"; lanterna (`flashlight`) exige "lanterna".

Comandos:
  python3 -m lofi.continuidade conferir series/dia-zero/ep05_roteiro.md    (o validador de roteiro já chama)
  python3 -m lofi.continuidade fechar   series/dia-zero/ep05_roteiro.md    grava o "fim" do episódio no mundo.json
  python3 -m lofi.continuidade rota     series/dia-zero rua ponte           caminho entre dois lugares
"""
import json, os, re, sys
from collections import deque

ITEM_DE = {"radio_portatil": "radio"}            # cenário que exige um item com alguém
PROP_ITEM = {"flashlight": "lanterna"}           # campo do ator que exige um item
JANELA_H = 3 * 60                                # pulo maior que isso (min) precisa de relógio / "o tempo passa"


from .mapa import OBJETO_DO_LUGAR


def carregar(pasta):
    p = os.path.join(pasta, "mundo.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def lugar_de(mundo, cena):
    from .mapa import lugar
    for nome, l in (mundo or {}).get("lugares", {}).items():
        if cena in l.get("cenarios", []): return nome
    return lugar(cena)


def vizinhos(mundo):
    v = {}
    for lig in mundo.get("ligacoes", []):
        a, b = lig[0], lig[1]
        v.setdefault(a, set()).add(b); v.setdefault(b, set()).add(a)
    return v


def rota(mundo, a, b):
    """Menor caminho de lugares de a até b (lista) ou None."""
    v = vizinhos(mundo); ant = {a: None}; q = deque([a])
    while q:
        x = q.popleft()
        if x == b:
            r = []
            while x is not None: r.append(x); x = ant[x]
            return r[::-1]
        for y in v.get(x, ()):
            if y not in ant: ant[y] = x; q.append(y)
    return None


def _minutos(dia, hora):
    h, m = map(int, hora.split(":")); return int(dia) * 1440 + h * 60 + m


def cenas(txt):
    """[(n, corpo)] das cenas numeradas do roteiro."""
    partes = re.split(r"^#+\s*CENA\s+(\d+)[^\n]*$", txt, flags=re.M)
    return [(int(partes[k]), partes[k + 1]) for k in range(1, len(partes) - 1, 2)]


def _ep_num(caminho):
    m = re.search(r"ep(\d+)", os.path.basename(caminho or ""))
    return int(m.group(1)) if m else None


def percorrer(txt, mundo, inicio=None):
    """Anda pelo roteiro cena a cena. Devolve (erros, estado_final)."""
    erros = []
    est = json.loads(json.dumps(inicio or {}))
    inv = {k: list(v) for k, v in est.get("inventario", {}).items()}
    atual = est.get("lugar"); relogio = _minutos(est["dia"], est["hora"]) if est.get("dia") and est.get("hora") else None
    viu_relogio = False; primeira = True; dia_hora = (est.get("dia"), est.get("hora"))
    for n, corpo in cenas(txt):
        if n == 0: continue                                                        # gancho é flash-forward
        for quem, item in re.findall(r"PEGA\s*:\s*`?(\w+)`?\s+`?(\w+)`?", corpo, re.I):
            inv.setdefault(quem.lower(), []).append(item.lower())
        for quem, item in re.findall(r"LARGA\s*:\s*`?(\w+)`?\s+`?(\w+)`?", corpo, re.I):
            if item.lower() in inv.get(quem.lower(), []): inv[quem.lower()].remove(item.lower())
        if re.search(r"`relogio`|O TEMPO PASSA", corpo, re.I): viu_relogio = True
        insercao = bool(re.search(r"INSER[ÇC][ÃA]O", corpo, re.I))
        for d, h, mi in re.findall(r"DIA\s*(\d+)\s*[·\-,]?\s*(\d{1,2}):(\d{2})", corpo):
            t = _minutos(d, f"{h}:{mi}")
            if relogio is not None and not insercao:
                if t < relogio:
                    erros.append(f"CENA {n}: o relógio voltou no tempo (DIA {d} {h}:{mi} depois de DIA {dia_hora[0]} {dia_hora[1]})")
                elif t - relogio > JANELA_H and not viu_relogio:
                    erros.append(f"CENA {n}: pulo de {(t - relogio) // 60} h sem mostrar o tempo passando. Ponha antes um "
                                 f"PLANO DE DETALHE `relogio` (ou a linha \"O TEMPO PASSA\")")
            if not insercao: relogio = t; dia_hora = (int(d), f"{int(h):02d}:{mi}"); viu_relogio = False
        m = re.search(r"CEN[AÁ]RIO[^:\n]*:\**\s*`([^`]+)`", corpo, re.I)
        if not m: continue
        cena = m.group(1).strip()
        if cena in ITEM_DE and not insercao and not any(ITEM_DE[cena] in v for v in inv.values()):
            erros.append(f"CENA {n}: `{cena}` precisa de alguém com '{ITEM_DE[cena]}', mas ninguém carrega. "
                         f"Inventário: {inv or 'vazio'}. Mostre alguém pegando (linha PEGA: <personagem> {ITEM_DE[cena]})")
        for campo, item in PROP_ITEM.items():
            if re.search(rf"`{campo}`", corpo) and not insercao and not any(item in v for v in inv.values()):
                erros.append(f"CENA {n}: `{campo}` precisa de alguém com '{item}' (PEGA: <personagem> {item})")
        if insercao or cena in OBJETO_DO_LUGAR: continue          # objeto do lugar: o validador geral confere
        novo = lugar_de(mundo, cena)
        if novo is None: continue
        if atual and novo != atual:
            r = rota(mundo, atual, novo) if mundo else [atual, novo]
            if primeira and not re.search(r"LIGA[ÇC][ÃA]O\s*:", corpo, re.I):
                erros.append(f"CENA {n}: o episódio anterior terminou em '{atual}', mas esta cena já está em '{novo}'. "
                             f"Comece em '{atual}' ou mostre o caminho (LIGAÇÃO:)")
            elif r is None:
                erros.append(f"CENA {n}: não existe caminho de '{atual}' para '{novo}' no mapa da cidade (mundo.json)")
            elif len(r) > 2:
                erros.append(f"CENA {n}: '{atual}' não liga direto com '{novo}'. Pelo mapa o caminho é {' → '.join(r)}: "
                             f"mostre a passagem por {', '.join(r[1:-1])}")
        atual = novo; primeira = False
    fim = {"lugar": atual, "inventario": inv}
    if dia_hora[0]: fim["dia"], fim["hora"] = dia_hora
    return erros, fim


def conferir(caminho, txt=None):
    """Erros de continuidade do roteiro contra o mapa e o fim do episódio anterior (se a série tiver mundo.json)."""
    pasta = os.path.dirname(os.path.abspath(caminho)); mundo = carregar(pasta)
    if not mundo: return []
    txt = txt if txt is not None else open(caminho, encoding="utf-8").read()
    n = _ep_num(caminho); inicio = mundo.get("fim", {}).get(str(n - 1)) if n else None
    erros, _ = percorrer(txt, mundo, inicio)
    return erros


def fechar(caminho):
    pasta = os.path.dirname(os.path.abspath(caminho)); p = os.path.join(pasta, "mundo.json"); mundo = carregar(pasta)
    n = _ep_num(caminho); inicio = mundo.get("fim", {}).get(str(n - 1))
    erros, fim = percorrer(open(caminho, encoding="utf-8").read(), mundo, inicio)
    mundo.setdefault("fim", {})[str(n)] = fim
    json.dump(mundo, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return erros, fim


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "conferir":
        e = conferir(sys.argv[2]); print("\n".join("[ERRO] " + x for x in e) or "OK"); sys.exit(1 if e else 0)
    elif cmd == "fechar":
        e, fim = fechar(sys.argv[2]); print(json.dumps(fim, ensure_ascii=False))
        for x in e: print("[AVISO]", x)
    elif cmd == "rota":
        print(" → ".join(rota(carregar(sys.argv[2]), sys.argv[3], sys.argv[4]) or ["sem caminho"]))
    else:
        print(__doc__)
