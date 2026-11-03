"""Mapa de cada cenário: área de chão (onde os pés podem ficar) e marcas nomeadas para posicionar personagens.

No roteiro técnico, use a marca no lugar de x/y:
    {"char": "roberta", "mark": "porta"}                         -> fica na porta (x, y e vista padrão da marca)
    {"char": "rafa", "mark": [[0, "fundo"], [3.5, "frente"]]}    -> anda de uma marca até a outra
    {"char": "lia", "mark": "sofa", "dx": -60}                   -> 60 px à esquerda da marca
x/y escritos à mão continuam valendo (e vencem a marca). Campos padrão da marca (vista, pose, escala...) só entram se o
ator não os definir.

    python3 -m lofi.mapa                 -> regrava examples/mapa_cenarios.png (todas as marcas, com a Roberta em cada uma)
    python3 -m lofi.mapa escada telhado  -> folhas só desses cenários em _mapa_<cena>.png
    python3 -m lofi.mapa --listar        -> lista cenários e marcas (texto)
"""
import sys, os, copy

# chão: polígono (x, y) em coordenadas de tela com a câmera parada (zoom 1). marcas: x, y + padrões opcionais.
MAPA = {
    "apartamento": {
        "chao": [(0, 1420), (1080, 1420), (1080, 1880), (0, 1880)],
        "marcas": {
            "centro": {"x": 540, "y": 1700, "nota": "no meio do tapete"},
            "tapete_esq": {"x": 330, "y": 1700}, "tapete_dir": {"x": 760, "y": 1700},
            "janela": {"x": 540, "y": 1470, "nota": "em frente à janela, mais longe da câmera"},
            "abajur": {"x": 250, "y": 1560, "nota": "ao lado do abajur, à esquerda"},
            "sofa": {"x": 860, "y": 1520, "nota": "na frente do sofá (use pose sit para sentar)"},
        }},
    "entrada": {
        "chao": [(0, 1500), (1080, 1500), (1080, 1900), (0, 1900)],
        "marcas": {
            "porta": {"x": 690, "y": 1560, "view": "back", "nota": "colada na porta, de costas (espiar, trancar, bater)"},
            "frente_porta": {"x": 690, "y": 1760, "nota": "de frente para a câmera, diante da porta"},
            "lado_esq": {"x": 300, "y": 1720, "nota": "perto do cabideiro"},
            "lado_dir": {"x": 950, "y": 1740},
            "chao_porta": {"x": 430, "y": 1700, "pose": "chao", "nota": "sentada no chão encostada na parede"},
        }},
    "corredor": {
        "chao": [(410, 1080), (670, 1080), (1050, 1900), (30, 1900)],
        "marcas": {
            "fundo": {"x": 540, "y": 1150, "nota": "no fim do corredor (bem pequeno)"},
            "meio": {"x": 540, "y": 1450}, "frente": {"x": 540, "y": 1790},
            "frente_esq": {"x": 360, "y": 1780}, "frente_dir": {"x": 720, "y": 1780},
            "olho_magico": {"x": 540, "y": 1250, "scale": 0.6, "nota": "visto pelo olho mágico (effect peephole): dentro do círculo"},
            "olho_magico_fundo": {"x": 600, "y": 1150, "scale": 0.45, "nota": "atrás de quem está no olho mágico"},
        }},
    "rua": {
        "chao": [(0, 1250), (1080, 1250), (1080, 1900), (0, 1900)],
        "marcas": {
            "centro": {"x": 540, "y": 1720}, "calcada_esq": {"x": 280, "y": 1740}, "calcada_dir": {"x": 800, "y": 1740},
            "longe": {"x": 540, "y": 1340, "nota": "lá no fundo da rua (pequeno)"},
            "longe_esq": {"x": 180, "y": 1360}, "longe_dir": {"x": 880, "y": 1360},
            "carro": {"x": 300, "y": 1480, "nota": "ao lado do carro estacionado, à esquerda"},
        }},
    "janela": {
        "chao": [(0, 760), (1080, 760), (1080, 1700), (0, 1700)],
        "marcas": {
            "rua_longe": {"x": 540, "y": 900, "nota": "na rua, vista de cima (minúsculo)"},
            "rua_perto": {"x": 540, "y": 1500, "nota": "na rua, vista de cima"},
            "na_janela": {"x": 330, "y": 2350, "fg": True, "view": "back", "scale": 3.0, "blur": 4,
                          "nota": "quem olha pela janela, de costas, em primeiro plano"},
            "na_janela_dir": {"x": 760, "y": 2350, "fg": True, "view": "back", "scale": 3.0, "blur": 4},
        }},
    "escada": {
        "chao": [(0, 1480), (1080, 1480), (1080, 1840), (0, 1840)],
        "marcas": {
            "degrau_baixo": {"x": 300, "y": 1760}, "degrau_meio": {"x": 560, "y": 1650}, "degrau_alto": {"x": 800, "y": 1540},
            "patamar": {"x": 540, "y": 1740, "nota": "no patamar, de frente"},
        }},
    "telhado": {
        "chao": [(0, 1360), (1080, 1360), (1080, 1900), (0, 1900)],
        "marcas": {
            "centro": {"x": 540, "y": 1720}, "parapeito_esq": {"x": 200, "y": 1660, "nota": "na beirada esquerda"},
            "parapeito_dir": {"x": 880, "y": 1660, "nota": "na beirada direita"},
            "fundo": {"x": 380, "y": 1420, "nota": "longe, perto da caixa d'água"},
        }},
    "ponte": {
        "chao": [(470, 1200), (610, 1200), (960, 1900), (120, 1900)],
        "marcas": {
            "barreira": {"x": 540, "y": 1260, "scale": 0.5, "nota": "na barreira do exército, lá no fundo"},
            "meio": {"x": 540, "y": 1500}, "frente_esq": {"x": 420, "y": 1770}, "frente_dir": {"x": 680, "y": 1770},
        }},
    "radio": {
        "chao": [(0, 1500), (1080, 1500), (1080, 1900), (0, 1900)],
        "marcas": {
            "mesa_esq": {"x": 170, "y": 1760, "nota": "cenário de objeto: o rádio é o destaque; personagem pequeno no canto"},
            "mesa_dir": {"x": 930, "y": 1760},
        }},
    "hospital": {
        "chao": [(430, 1090), (640, 1090), (1080, 1700), (1080, 1900), (0, 1900), (0, 1700)],
        "marcas": {
            "fundo": {"x": 540, "y": 1180}, "meio": {"x": 520, "y": 1450}, "frente": {"x": 540, "y": 1790},
            "maca": {"x": 820, "y": 1560, "nota": "ao lado da maca, à direita"},
        }},
    "mercado": {
        "chao": [(450, 1140), (640, 1140), (1040, 1900), (40, 1900)],
        "marcas": {
            "fundo": {"x": 540, "y": 1220}, "meio": {"x": 540, "y": 1500},
            "frente_esq": {"x": 380, "y": 1780}, "frente_dir": {"x": 700, "y": 1780},
        }},
    "metro": {
        "chao": [(600, 1250), (1080, 1250), (1080, 1900), (740, 1900)],
        "marcas": {
            "plataforma": {"x": 900, "y": 1760}, "plataforma_longe": {"x": 820, "y": 1360},
            "beira": {"x": 770, "y": 1640, "nota": "na beira da plataforma, perto da faixa amarela"},
        }},
    "escola": {
        "chao": [(420, 1090), (650, 1090), (1080, 1800), (1080, 1900), (0, 1900), (0, 1800)],
        "marcas": {
            "fundo": {"x": 540, "y": 1180}, "meio": {"x": 540, "y": 1450}, "frente": {"x": 540, "y": 1780},
            "armario_esq": {"x": 220, "y": 1700, "nota": "encostado nos armários da esquerda"},
            "armario_dir": {"x": 860, "y": 1700},
        }},
    "delegacia": {
        "chao": [(0, 1310), (1080, 1310), (1080, 1900), (0, 1900)],
        "marcas": {
            "mesa": {"x": 300, "y": 1520, "nota": "na frente da mesa, à esquerda"},
            "cela": {"x": 780, "y": 1430, "nota": "na frente das grades"},
            "centro": {"x": 540, "y": 1750},
        }},
    "posto": {
        "chao": [(0, 1300), (1080, 1300), (1080, 1900), (0, 1900)],
        "marcas": {
            "bomba_esq": {"x": 340, "y": 1380, "nota": "ao lado da bomba da esquerda"},
            "bomba_dir": {"x": 720, "y": 1380},
            "frente": {"x": 540, "y": 1760}, "frente_esq": {"x": 360, "y": 1760}, "frente_dir": {"x": 720, "y": 1760},
        }},
    "floresta": {
        "chao": [(0, 1250), (1080, 1250), (1080, 1900), (0, 1900)],
        "marcas": {
            "trilha": {"x": 540, "y": 1720}, "longe": {"x": 540, "y": 1330}, "arvore": {"x": 760, "y": 1640, "nota": "ao lado do tronco grande"},
        }},
    "carro": {
        "chao": [(0, 1500), (1080, 1500), (1080, 1720), (0, 1720)],
        "marcas": {
            "motorista": {"x": 280, "y": 2250, "fg": True, "view": "back", "scale": 2.6,
                          "nota": "dirigindo, de costas para a câmera, atrás do volante"},
            "carona": {"x": 790, "y": 2250, "fg": True, "view": "back", "scale": 2.6, "nota": "banco do passageiro, de costas"},
        }},
    "esgoto": {
        "chao": [(440, 1250), (640, 1250), (900, 1900), (180, 1900)],
        "marcas": {"fundo": {"x": 540, "y": 1300}, "meio": {"x": 540, "y": 1550}, "frente": {"x": 540, "y": 1800}},
        },
    "igreja": {
        "chao": [(0, 1150), (1080, 1150), (1080, 1900), (0, 1900)],
        "marcas": {
            "altar": {"x": 540, "y": 1200, "nota": "no altar, lá no fundo"}, "corredor": {"x": 540, "y": 1550},
            "frente": {"x": 540, "y": 1800}, "banco_esq": {"x": 240, "y": 1700}, "banco_dir": {"x": 840, "y": 1700},
        }},
}
MAPA["rua_amanhecer"] = copy.deepcopy(MAPA["rua"])
MAPA["entrada_metro"] = {
    "chao": [(0, 1250), (1080, 1250), (1080, 1900), (0, 1900)],
    "marcas": {
        "calcada_esq": {"x": 220, "y": 1760, "nota": "na calçada, à esquerda"},
        "frente": {"x": 480, "y": 1780, "nota": "na calçada, perto da câmera"},
        "escada_topo": {"x": 780, "y": 1700, "nota": "no primeiro degrau, perto da câmera (prestes a descer ou acabando de subir)"},
        "escada_baixo": {"x": 780, "y": 1340, "nota": "lá embaixo na escada, entrando na estação (pequeno, longe)"},
        "longe": {"x": 300, "y": 1320, "nota": "lá no fundo da calçada"},
    }}
# closes de objeto: sem chão nem marcas (só a mão do personagem; ver lofi/partes.py)
MAPA["radio_carro"] = {"chao": None, "marcas": {}}
MAPA["radio_portatil"] = {"chao": None, "marcas": {}}

# Continuidade: a que LUGAR cada cenário pertence. Cenários do mesmo lugar podem se alternar sem explicação;
# mudar de lugar pede uma passagem (LIGAÇÃO no roteiro). Closes de objeto valem só dentro do lugar deles.
LUGAR = {
    "apartamento": "casa", "entrada": "casa", "radio": "casa", "janela": "casa", "corredor": "predio",
    "carro": "carro", "radio_carro": "carro",
    "rua": "rua", "rua_amanhecer": "rua", "entrada_metro": "rua", "portao": "rua", "beco": "rua", "viaduto": "rua", "vagao": "metro",
    "radio_portatil": None,          # vai junto com o personagem: não muda o lugar
}
OBJETO_DO_LUGAR = {"radio": "casa", "radio_carro": "carro"}   # rádio de mesa só em casa; rádio do painel só no carro


MAPA["portao"] = {
    "chao": [(0, 1380), (1080, 1380), (1080, 1900), (0, 1900)],
    "marcas": {"portao": {"x": 540, "y": 1400, "nota": "no portão, saindo ou entrando no prédio"},
               "calcada_esq": {"x": 220, "y": 1760}, "calcada_dir": {"x": 860, "y": 1760},
               "frente": {"x": 540, "y": 1820, "nota": "na calçada, perto da câmera"}}}
MAPA["beco"] = {
    "chao": [(470, 1260), (610, 1260), (1080, 1840), (1080, 1900), (0, 1900), (0, 1840)],
    "marcas": {"fundo": {"x": 540, "y": 1300, "nota": "no fim do beco (pequeno)"}, "meio": {"x": 540, "y": 1520},
               "frente": {"x": 540, "y": 1800}, "lixeira": {"x": 420, "y": 1760, "nota": "escondido atrás da lixeira"}}}
MAPA["viaduto"] = {
    "chao": [(500, 1240), (580, 1240), (1080, 1800), (1080, 1900), (0, 1900), (0, 1800)],
    "marcas": {"longe": {"x": 540, "y": 1280, "nota": "lá no fim do viaduto, perto da ponte"}, "meio": {"x": 540, "y": 1500},
               "frente": {"x": 540, "y": 1800}, "mureta": {"x": 260, "y": 1700, "nota": "junto à mureta, olhando a cidade"}}}
MAPA["estacionamento"] = {
    "chao": [(320, 1280), (760, 1280), (1080, 1720), (1080, 1900), (0, 1900), (0, 1720)],
    "marcas": {"fundo": {"x": 540, "y": 1320}, "meio": {"x": 540, "y": 1560}, "frente": {"x": 540, "y": 1800},
               "pilar": {"x": 760, "y": 1760, "nota": "escondido atrás do pilar"}}}
MAPA["vagao"] = {
    "chao": [(400, 1320), (680, 1320), (1080, 1840), (1080, 1900), (0, 1900), (0, 1840)],
    "marcas": {"porta": {"x": 540, "y": 1360, "nota": "na porta do fundo"}, "meio": {"x": 540, "y": 1560},
               "frente": {"x": 540, "y": 1800}, "banco_esq": {"x": 260, "y": 1740, "nota": "perto do banco da esquerda"},
               "banco_dir": {"x": 820, "y": 1740}}}

# Travelling lateral (lofi/travelling.py): o chão é a faixa da calçada/piso, igual em todos os cenários.
MAPA["_travelling"] = {
    "chao": [(-200, 1560), (1280, 1560), (1280, 1900), (-200, 1900)],
    "marcas": {"esq": {"x": 330, "y": 1740, "nota": "atrás na corrida (quem persegue/segue)"},
               "centro": {"x": 540, "y": 1740}, "dir": {"x": 750, "y": 1740, "nota": "à frente na corrida"},
               "fundo": {"x": 540, "y": 1620, "nota": "junto à parede/fachada"},
               "frente": {"x": 540, "y": 1840, "nota": "na beira da calçada, perto da câmera"}},
}

# Loja de conveniência 24h (lofi/scenes_loja.py)
MAPA["loja"] = {
    "chao": [(0, 1190), (1080, 1190), (1080, 1900), (0, 1900)],
    "marcas": {"caixa": {"x": 210, "y": 1420, "nota": "atrás do balcão do caixa (o balcão tapa da cintura para baixo)"},
               "balcao": {"x": 590, "y": 1470, "facing": -1, "nota": "cliente na frente do balcão, à direita dele"},
               "porta": {"x": 630, "y": 1200, "nota": "entrando pela porta de vidro (pequeno, no fundo)"},
               "geladeira": {"x": 800, "y": 1560, "nota": "na frente das geladeiras, à direita"},
               "centro": {"x": 620, "y": 1650}, "frente": {"x": 600, "y": 1820, "nota": "perto da câmera"}}}
MAPA["deposito"] = {
    "chao": [(0, 1270), (1080, 1270), (1080, 1900), (0, 1900)],
    "marcas": {"porta_camara": {"x": 720, "y": 1330, "view": "back", "nota": "colado na porta da câmara fria, de costas"},
               "frente_porta": {"x": 720, "y": 1600, "nota": "de frente, diante da porta da câmara fria"},
               "gerador": {"x": 430, "y": 1330, "nota": "ao lado do gerador"},
               "centro": {"x": 540, "y": 1650}, "frente": {"x": 540, "y": 1820}}}
MAPA["camara_fria"] = {
    "chao": [(420, 1230), (660, 1230), (1040, 1900), (40, 1900)],
    "marcas": {"fundo": {"x": 540, "y": 1280, "nota": "lá no fundo, perto da porta"}, "meio": {"x": 540, "y": 1500},
               "frente": {"x": 540, "y": 1800}}}
MAPA["cftv"] = {"chao": None, "marcas": {}}
MAPA["mezanino"] = {
    "chao": [(0, 1250), (1080, 1250), (1080, 1640), (0, 1640)],
    "marcas": {"centro": {"x": 540, "y": 1480}, "esq": {"x": 300, "y": 1520}, "dir": {"x": 800, "y": 1520},
               "fundo": {"x": 540, "y": 1290, "view": "back", "nota": "na janela basculante do fundo, de costas"},
               "guarda_corpo": {"x": 540, "y": 1620, "nota": "no guarda-corpo, olhando o vão da escada lá embaixo"}}}
LUGAR.update({"loja": "loja", "deposito": "loja", "camara_fria": "loja", "cftv": "loja", "mezanino": "loja"})

# Portais e caçadores (lofi/scenes_fenda.py)
MAPA["fenda"] = {
    "chao": [(0, 1270), (1080, 1270), (1080, 1900), (0, 1900)],
    "marcas": {"portal": {"x": 540, "y": 1340, "view": "back", "nota": "diante da Fenda, de costas (prestes a entrar)"},
               "centro": {"x": 540, "y": 1660}, "esq": {"x": 280, "y": 1700}, "dir": {"x": 800, "y": 1700},
               "frente": {"x": 540, "y": 1820, "nota": "perto da câmera, com a Fenda atrás"}}}
MAPA["masmorra"] = {
    "chao": [(420, 1180), (660, 1180), (1060, 1900), (20, 1900)],
    "marcas": {"portal": {"x": 540, "y": 1220, "nota": "junto ao portal, lá no fundo (pequeno)"}, "fundo": {"x": 540, "y": 1340},
               "meio": {"x": 540, "y": 1540}, "esq": {"x": 340, "y": 1700}, "dir": {"x": 740, "y": 1700},
               "frente": {"x": 540, "y": 1820}}}
MAPA["associacao"] = {
    "chao": [(0, 1230), (1080, 1230), (1080, 1900), (0, 1900)],
    "marcas": {"balcao": {"x": 520, "y": 1480, "facing": -1, "nota": "de frente para o balcão, à direita dele"},
               "painel": {"x": 700, "y": 1290, "view": "back", "nota": "olhando o painel de ranks, de costas"},
               "centro": {"x": 620, "y": 1650}, "esq": {"x": 330, "y": 1740}, "dir": {"x": 820, "y": 1720},
               "frente": {"x": 560, "y": 1820}}}
MAPA["trono"] = {
    "chao": [(260, 1250), (820, 1250), (1080, 1900), (0, 1900)],
    "marcas": {"trono": {"x": 540, "y": 1260, "nota": "ao pé do trono, lá no fundo"}, "meio": {"x": 540, "y": 1500},
               "esq": {"x": 320, "y": 1720}, "dir": {"x": 760, "y": 1720}, "frente": {"x": 540, "y": 1820}}}
LUGAR.update({"masmorra": "masmorra", "fenda": "fenda", "associacao": "associacao", "trono": "trono"})


# Escola (lofi/scenes_escola.py)
MAPA["sala_aula"] = {
    "chao": [(0, 1270), (1080, 1270), (1080, 1900), (0, 1900)],
    "marcas": {"quadro": {"x": 540, "y": 1290, "view": "back", "nota": "diante do quadro, de costas (lendo as regras)"},
               "mesa_prof": {"x": 790, "y": 1300, "nota": "atrás da mesa do professor"},
               "porta": {"x": 120, "y": 1320, "nota": "na porta da sala, à esquerda"},
               "carteira_esq": {"x": 250, "y": 1560}, "carteira_dir": {"x": 830, "y": 1560},
               "meio": {"x": 540, "y": 1600, "nota": "no corredor entre as carteiras"}, "frente": {"x": 540, "y": 1820}}}
MAPA["quadra"] = {
    "chao": [(0, 1190), (1080, 1190), (1080, 1900), (0, 1900)],
    "marcas": {"gol": {"x": 540, "y": 1250, "nota": "na frente do gol, lá no fundo"}, "area": {"x": 540, "y": 1420},
               "arquibancada": {"x": 200, "y": 1500, "nota": "ao pé da arquibancada"}, "centro": {"x": 600, "y": 1650},
               "dir": {"x": 860, "y": 1700}, "frente": {"x": 540, "y": 1830}}}
LUGAR.update({"sala_aula": "escola", "quadra": "escola", "escola": "escola"})


def lugar(cena):
    """Lugar de um cenário (o próprio nome quando não há grupo). None = não muda o lugar (ex.: rádio portátil)."""
    return LUGAR.get(cena, cena)


PADROES = ("view", "facing", "pose", "scale", "fg", "blur")


def marcas(cena):
    return MAPA.get(cena, {}).get("marcas", {})


def no_chao(cena, x, y, folga=30):
    """True se (x, y) está dentro do chão do cenário (com folga em px). Cenário sem mapa → sempre True."""
    pol = MAPA.get(cena, {}).get("chao")
    if not pol: return True
    if _dentro(pol, x, y): return True
    return any(_dentro(pol, x + dx, y + dy) for dx in (-folga, 0, folga) for dy in (-folga, 0, folga))


def _dentro(pol, x, y):
    ins = False; n = len(pol)
    for i in range(n):
        (x1, y1), (x2, y2) = pol[i], pol[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1: ins = not ins
    return ins


def conferir_mapa():
    """Erros do próprio mapa: marca comum (sem fg) fora do chão do seu cenário, cenário sem mapa."""
    from . import scenes
    erros = [f"cenário '{c}' sem mapa em lofi/mapa.py" for c in scenes.REGISTRY if c not in MAPA]
    for c, m in MAPA.items():
        for n, mk in m["marcas"].items():
            if not mk.get("fg") and not no_chao(c, mk["x"], mk["y"], folga=0):
                erros.append(f"marca '{c}.{n}' ({mk['x']}, {mk['y']}) fora do chão do cenário")
    return erros


def resolver(ator, cena):
    """Devolve uma cópia do ator com x/y (e padrões) preenchidos a partir de "mark". Marca desconhecida fica em "_mark_erro"."""
    m = ator.get("mark")
    if m is None: return ator
    a = dict(ator); ms = marcas(cena); dx = ator.get("dx", 0); dy = ator.get("dy", 0)
    if isinstance(m, str):
        if m not in ms: a["_mark_erro"] = m; return a
        mk = ms[m]
        a.setdefault("x", mk["x"] + dx); a.setdefault("y", mk["y"] + dy)
        for k in PADROES:
            if k in mk: a.setdefault(k, mk[k])
        return a
    # keyframes [[t, "marca"], ...] → x e y animados (anda entre as marcas)
    xs, ys = [], []
    for t, nome in m:
        if nome not in ms: a["_mark_erro"] = nome; return a
        xs.append([t, ms[nome]["x"] + dx]); ys.append([t, ms[nome]["y"] + dy])
    a.setdefault("x", xs); a.setdefault("y", ys)
    return a


def resolver_plano(shot):
    """Aplica as marcas em todos os atores de um plano (e dos lados A/B de uma escolha). Não altera o original.
    Plano com "travelling" usa as marcas do travelling lateral (TRAVELLING), iguais em qualquer cenário."""
    s = dict(shot)
    cena = "_travelling" if s.get("travelling") else s.get("scene")
    if "actors" in s: s["actors"] = [resolver(a, cena) for a in s["actors"]]
    for lado in ("a", "b"):
        if isinstance(s.get(lado), dict) and "actors" in s[lado]:
            s[lado] = dict(s[lado]); s[lado]["actors"] = [resolver(a, s[lado].get("scene")) for a in s[lado]["actors"]]
    return s


def folha(cenas, saida):
    """Folha de conferência: cada cenário com o chão (contorno verde) e a Roberta em cada marca."""
    import json, tempfile
    from PIL import Image, ImageDraw
    from .core import font
    from .render import Episode
    shots = []
    for i, c in enumerate(cenas):
        atores = []
        for nome, mk in marcas(c).items():
            atores.append({"char": "roberta", "mark": nome, "emotion": "neutral"})
        shots.append({"start": i * 2, "end": i * 2 + 2, "scene": c, "hud": False, "bloom": False,
                      "camera": {"zoom": 1.0, "handheld": False}, "actors": atores, "gestures": False})
    sp = {"out": "x.mp4", "fps": 30, "total": max(2, len(cenas) * 2), "voices": {}, "shots": shots, "gestures": False}
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(sp, tmp); tmp.close()
    ep = Episode(tmp.name); os.unlink(tmp.name)
    imgs = []
    for i, c in enumerate(cenas):
        im = ep.frame(i * 2 + 1).convert("RGB"); d = ImageDraw.Draw(im)
        pol = MAPA.get(c, {}).get("chao")
        if pol: d.line(pol + [pol[0]], fill=(60, 255, 120), width=6)
        for nome, mk in marcas(c).items():
            x, y = mk["x"], min(mk["y"], 1890)
            d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=(255, 220, 40), outline=(0, 0, 0), width=3)
            d.text((x + 16, y - 10), nome, font=font("mono", 34), fill=(255, 230, 60), stroke_width=4, stroke_fill=(0, 0, 0))
        d.text((30, 40), c, font=font("title", 96), fill=(255, 90, 90), stroke_width=6, stroke_fill=(0, 0, 0))
        imgs.append(im.resize((360, 640)))
    cols = min(5, len(imgs)); rows = (len(imgs) + cols - 1) // cols
    sh = Image.new("RGB", (360 * cols, 640 * rows), (0, 0, 0))
    for j, im in enumerate(imgs): sh.paste(im, ((j % cols) * 360, (j // cols) * 640))
    sh.save(saida); return saida


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--listar" in sys.argv:
        for c, m in MAPA.items():
            print(f"{c}: " + ", ".join(f"{n}" + (f" ({v['nota']})" if v.get("nota") else "") for n, v in m["marcas"].items()))
        sys.exit()
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if args:
        for c in args: print(folha([c], os.path.join(raiz, f"_mapa_{c}.png")))
    else:
        from . import scenes
        print(folha(list(scenes.REGISTRY), os.path.join(raiz, "examples", "mapa_cenarios.png")))

