"""Partes do corpo em cena: o braço e a mão que entram no quadro quando o personagem não aparece inteiro
(rádio, maçaneta, chave, celular). A manga, o punho e a pele vêm da ficha do personagem (personagens.json),
então a mão da Roberta tem a manga do puffer dela e a do Rafa, a manga verde dele.

No roteiro técnico:
    {"scene": "radio", "hand": "roberta"}                              -> mão da Roberta no dial (posição padrão do cenário)
    {"scene": "radio", "hand": {"of": "lia", "at": "antena"}}          -> mão da Lia mexendo na antena
    {"type": "detail", "subject": "chave", "hand": "rafa"}             -> mão do Rafa girando a chave
    {"type": "detail", "subject": "olho", "hand": "roberta"}           -> no olho: a pele em volta é a da Roberta
    "hand": false                                                      -> sem mão
Sem "hand", os cenários que sempre mostram uma mão (rádio, chave) usam uma mão genérica e o verificador avisa.
"""
import math
from PIL import ImageDraw

OUT = (22, 24, 34)

# onde a mão pode estar em cada cenário/plano de detalhe: ombro (de onde o braço entra, fora da tela) e mão
POSICOES = {
    "radio": {
        "dial": {"ombro": (1140, 1660), "mao": (786, 1300), "nota": "girando o dial (padrão)"},
        "antena": {"ombro": (1160, 560), "mao": (884, 760), "nota": "segurando a antena"},
        "botao": {"ombro": (1150, 1760), "mao": (842, 1372), "nota": "apertando o botão de ligar"},
        "repouso": {"ombro": (1150, 1820), "mao": (930, 1470), "nota": "mão parada na mesa, ao lado do rádio"},
    },
    "radio_carro": {
        "dial": {"ombro": (1150, 1900), "mao": (860, 1395), "nota": "girando a sintonia do rádio do carro (padrão)"},
        "volume": {"ombro": (-80, 1900), "mao": (232, 1395), "nota": "no botão de volume (braço vindo da esquerda: motorista)"},
    },
    "radio_portatil": {
        "segurando": {"ombro": (1160, 1990), "mao": (560, 1470), "nota": "segurando o rádio por baixo (padrão)"},
        "dial": {"ombro": (1160, 1600), "mao": (712, 1046), "nota": "girando a sintonia"},
    },
    "chave": {"girando": {"ombro": (1180, 2020), "mao": None, "nota": "segurando a cabeça da chave, acompanha o giro (padrão)"}},
    "macaneta": {"girando": {"ombro": (1180, 1700), "mao": None, "nota": "na ponta da maçaneta, acompanha o giro (padrão)"}},
    "celular": {
        "segurando": {"ombro": (1180, 1980), "mao": (900, 1560), "nota": "segurando o celular pela borda (padrão)"},
        "dedo": {"ombro": (1180, 1980), "mao": (640, 1180), "dedo": True, "nota": "dedo tocando a tela"},
    },
}
# áreas importantes do quadro (a legenda evita cobrir): objeto em destaque de cada cenário/plano de detalhe
FOCO = {
    "radio": [(200, 1000, 880, 1380), (230, 560, 870, 1000)],
    "radio_carro": [(190, 980, 890, 1420)],
    "radio_portatil": [(320, 700, 760, 1460)],
    "celular": [(200, 640, 880, 1060)],
    "chave": [(380, 760, 700, 1140)],
    "macaneta": [(300, 640, 760, 1300)],
    "olho": [(120, 640, 960, 1240)],
    "relogio": [(130, 510, 950, 1330)],
}
PADRAO = {"radio": "dial", "radio_carro": "dial", "radio_portatil": "segurando", "chave": "girando", "macaneta": "girando", "celular": "segurando"}
SEMPRE = {"radio", "radio_carro", "radio_portatil", "chave"}        # mostram mão mesmo sem "hand" (mão genérica)


def visual(nome, locked=None, custom=None):
    """Cores da manga, do punho e da pele do personagem, a partir da ficha travada (ou do personagem pronto)."""
    from .rig import char_def
    ficha = dict((custom or {}).get(nome) or {}); ficha.update((locked or {}).get(nome) or {})
    d = char_def(nome, ficha)
    manga = d["top"]
    punho = d["inner"] if d.get("top_style") in ("suit", "labcoat", "trench", "leather") else tuple(int(c * 0.8) for c in manga)
    return {"de": nome, "manga": manga, "punho": punho, "pele": d["skin"], "curta": d.get("sleeves") == "short",
            "fantasma": bool(d.get("ghost"))}


GENERICA = {"de": None, "manga": (210, 212, 220), "punho": (180, 182, 190), "pele": (220, 220, 214), "curta": False, "fantasma": False}


def resolver(spec, cena, locked=None, custom=None):
    """spec = valor de "hand" no plano. Devolve (visual, posição) ou (None, None) se não há mão."""
    if spec is False or (spec is None and cena not in SEMPRE): return None, None
    de, at = (spec, None) if isinstance(spec, str) else ((spec or {}).get("of"), (spec or {}).get("at"))
    v = visual(de, locked, custom) if de else dict(GENERICA)
    pos = POSICOES.get(cena, {}).get(at or PADRAO.get(cena, ""), None)
    return v, pos


def braco(img, ombro, mao, v, larg=92, dedo=False):
    """Desenha o braço do ombro (fora da tela) até a mão. Devolve o retângulo ocupado (para a legenda desviar)."""
    d = ImageDraw.Draw(img)
    (x0, y0), (x1, y1) = ombro, mao
    ang = math.atan2(y1 - y0, x1 - x0); L = math.hypot(x1 - x0, y1 - y0)
    def pt(k, off=0):   # ponto a k*L do ombro, deslocado 'off' na perpendicular
        return (x0 + math.cos(ang) * L * k - math.sin(ang) * off, y0 + math.sin(ang) * L * k + math.cos(ang) * off)
    manga_fim = 0.62 if v["curta"] else 0.9
    d.line([(x0, y0), (x1, y1)], fill=OUT, width=larg + 12)
    d.line([(x0, y0), pt(manga_fim)], fill=v["manga"], width=larg)
    if v["curta"]:
        d.line([pt(manga_fim), (x1, y1)], fill=v["pele"], width=int(larg * 0.7))
    else:
        d.line([pt(manga_fim - 0.06), pt(manga_fim)], fill=v["punho"], width=larg)               # punho da manga
        d.line([pt(manga_fim), (x1, y1)], fill=v["pele"], width=int(larg * 0.62))              # pulso
    # mão: palma + polegar (+ dedo esticado)
    r = larg * 0.44
    d.ellipse([x1 - r, y1 - r, x1 + r, y1 + r], fill=v["pele"], outline=OUT, width=5)
    tx, ty = pt(1.0, -r * 0.9)
    d.ellipse([tx - r * 0.42, ty - r * 0.42, tx + r * 0.42, ty + r * 0.42], fill=v["pele"], outline=OUT, width=4)
    if dedo:
        fx, fy = x1 + math.cos(ang) * r * 1.7, y1 + math.sin(ang) * r * 1.7
        d.line([(x1, y1), (fx, fy)], fill=OUT, width=int(r * 0.7) + 8); d.line([(x1, y1), (fx, fy)], fill=v["pele"], width=int(r * 0.7))
    return ("braco", (x0, y0), (x1, y1), larg * 0.5 + r * 0.6)


def bate_retangulo(item, r):
    """True se o item (retângulo (x0,y0,x1,y1) ou braço ("braco", ombro, mão, raio)) encosta no retângulo r."""
    if item and item[0] == "braco":
        _, (x0, y0), (x1, y1), rad = item
        for k in range(25):
            px, py = x0 + (x1 - x0) * k / 24, y0 + (y1 - y0) * k / 24
            if r[0] - rad < px < r[2] + rad and r[1] - rad < py < r[3] + rad: return True
        return False
    return item[1] < r[3] and item[3] > r[1] and item[0] < r[2] and item[2] > r[0]


def listar():
    return {c: {n: p["nota"] for n, p in ps.items()} for c, ps in POSICOES.items()}
