"""Biblioteca de móveis e objetos para o cenário generativo (lofi/cenario_gen.py) e os closes literais (lofi/literal.py).

Cada objeto é desenhado em coordenadas locais em CENTÍMETROS: x = 0 no meio da base, y = 0 no chão e y cresce para
cima. Um `Pincel` converte para o cenário (ponto de apoio x, y em px do cenário e k = px por cm), então o mesmo desenho
serve para o móvel pequeno no fundo da sala e para o close de 1 metro de altura na tela.

    from lofi.moveis import MOVEIS, desenhar
    desenhar(draw, "geladeira", x=300, y=1500, k=2.2, P=scenes.P, opts={"cor": (200, 200, 205)})

MOVEIS[nome] = Movel(func, lugar, larg, alt, sinonimos, nota)
    lugar: "piso" (no chão, encostado ou solto), "parede" (pendurado na parede do fundo), "teto", "chao" (objeto pequeno
    caído no chão) ou "fora" (externo: árvore, poste, carro...).
    sinonimos: palavras da narração que pedem esse objeto (lofi/literal.py usa para conferir o roteiro ao pé da letra).
"""
import math, random
from dataclasses import dataclass, field
from .core import font

K_CM = 2.43          # px do cenário por cm para um personagem em escala 1.0 (≈ 1,70 m = 413 px com escala_personagens 1.18)


def esc(c, f):
    """Cor escurecida (f < 1) ou clareada (f > 1)."""
    if f <= 1: return tuple(int(v * f) for v in c[:3])
    return tuple(int(v + (255 - v) * (f - 1)) for v in c[:3])


class Pincel:
    """Desenha em cm locais. y para cima. Guarda as luzes que o objeto acende (o cenário aplica depois)."""
    def __init__(self, d, x, y, k, P, rng=None, alpha=True, ss=2):
        self.d, self.x, self.y, self.k, self.P, self.ss = d, x, y, k, P, ss
        self.r = rng or random.Random(1); self.luzes = []; self.a = alpha
    def _c(self, c):
        if c is None: return None
        c = tuple(int(v) for v in c)
        return c + (255,) if self.a and len(c) == 3 else c
    def pt(self, cx, cy):
        return self.P(self.x + cx * self.k, self.y - cy * self.k)
    def px(self, v): return max(1, int(v * self.k * self.ss))
    def _box(self, x0, y0, x1, y1):
        a, b = self.pt(x0, y0), self.pt(x1, y1)
        return [min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])]
    def rect(self, x0, y0, x1, y1, fill=None, outline=None, w=1):
        bx = self._box(x0, y0, x1, y1)
        if bx[2] - bx[0] < 1 or bx[3] - bx[1] < 1: return
        self.d.rectangle(bx, fill=self._c(fill), outline=self._c(outline), width=self.px(w) if outline else 0)
    def rrect(self, x0, y0, x1, y1, r, fill=None, outline=None, w=1):
        bx = self._box(x0, y0, x1, y1)
        rr = min(int(r * self.k * self.ss), (bx[2] - bx[0]) // 2, (bx[3] - bx[1]) // 2)
        if bx[2] - bx[0] < 2 or bx[3] - bx[1] < 2: return
        self.d.rounded_rectangle(bx, max(0, rr), fill=self._c(fill), outline=self._c(outline), width=self.px(w) if outline else 0)
    def ell(self, cx, cy, rx, ry, fill=None, outline=None, w=1):
        bx = self._box(cx - rx, cy - ry, cx + rx, cy + ry)
        if bx[2] - bx[0] < 1 or bx[3] - bx[1] < 1: return
        self.d.ellipse(bx, fill=self._c(fill), outline=self._c(outline), width=self.px(w) if outline else 0)
    def poly(self, pts, fill=None, outline=None):
        self.d.polygon([self.pt(*p) for p in pts], fill=self._c(fill), outline=self._c(outline))
    def line(self, pts, fill, w=1):
        self.d.line([self.pt(*p) for p in pts], fill=self._c(fill), width=self.px(w))
    def arc(self, cx, cy, rx, ry, a0, a1, fill, w=1):
        bx = self._box(cx - rx, cy - ry, cx + rx, cy + ry)
        if bx[2] - bx[0] < 2: return
        self.d.arc(bx, a0, a1, fill=self._c(fill), width=self.px(w))
    def text(self, cx, cy, s, size, fill, fonte="sansb", anchor="mm"):
        sz = max(6, int(size * self.k * self.ss))
        self.d.text(self.pt(cx, cy), str(s), font=font(fonte, sz), fill=self._c(fill), anchor=anchor)
    def luz(self, cx, cy, raio, cor=(255, 220, 160), alpha=120):
        x, y = self.x + cx * self.k, self.y - cy * self.k
        self.luzes.append((x, y, raio * self.k, cor, alpha))


@dataclass
class Movel:
    func: object
    lugar: str
    larg: float
    alt: float
    sinonimos: tuple = ()
    nota: str = ""


MOVEIS = {}


def movel(nome, lugar, larg, alt, sinonimos=(), nota=""):
    def dec(f):
        MOVEIS[nome] = Movel(f, lugar, larg, alt, tuple(sinonimos), nota); return f
    return dec


def desenhar(d, nome, x, y, k, P, opts=None, seed=1, alpha=True, ss=2):
    """Desenha o objeto `nome` com a base em (x, y) do cenário e k px/cm. Devolve as luzes [(x, y, raio, cor, alpha)]."""
    m = MOVEIS[nome]; p = Pincel(d, x, y, k, P, random.Random(seed), alpha=alpha, ss=ss)
    m.func(p, dict(opts or {}))
    return p.luzes


# ============================== CONTEÚDO DE PRATELEIRA ==============================
PRODUTOS = {
    "latas":     dict(forma="lata", cores=[(200, 60, 50), (230, 190, 60), (60, 140, 200), (90, 170, 90)], rot=None),
    "milho":     dict(forma="lata", cores=[(232, 200, 60), (60, 140, 70)], rot="MILHO"),
    "feijao":    dict(forma="pacote", cores=[(120, 60, 40), (200, 60, 50)], rot="FEIJÃO"),
    "arroz":     dict(forma="pacote", cores=[(236, 236, 230), (60, 120, 200)], rot="ARROZ"),
    "agua":      dict(forma="garrafa", cores=[(150, 200, 240)], rot=None),
    "garrafas":  dict(forma="garrafa", cores=[(70, 150, 80), (150, 90, 60), (200, 200, 210)], rot=None),
    "refri":     dict(forma="garrafa", cores=[(200, 40, 40), (40, 40, 40), (60, 160, 70)], rot=None),
    "caixas":    dict(forma="caixa", cores=[(196, 150, 96), (220, 200, 160), (200, 80, 60)], rot=None),
    "cereal":    dict(forma="caixa", cores=[(230, 160, 40), (200, 60, 50), (70, 130, 200)], rot=None),
    "remedios":  dict(forma="caixinha", cores=[(240, 240, 240), (80, 160, 220), (230, 80, 80)], rot=None),
    "livros":    dict(forma="livro", cores=[(120, 50, 50), (50, 80, 120), (60, 100, 60), (160, 130, 70), (80, 70, 90)], rot=None),
    "potes":     dict(forma="pote", cores=[(220, 200, 150), (180, 120, 70)], rot=None),
    "ferramentas": dict(forma="ferramenta", cores=[(160, 160, 170), (200, 60, 40)], rot=None),
    "papel":     dict(forma="pacote", cores=[(240, 240, 245), (120, 170, 220)], rot=None),
    "biscoito":  dict(forma="pacote", cores=[(220, 120, 40), (180, 60, 40)], rot=None),
    "racao":     dict(forma="pacote", cores=[(200, 60, 40), (240, 200, 60)], rot=None),
    "vazia":     dict(forma=None, cores=[(0, 0, 0)], rot=None),
}


def produto(p, forma, x, y, w, h, cor, rot=None):
    """Um produto em pé com a base em (x, y) cm, largura w e altura h."""
    if forma == "lata":
        p.rect(x - w / 2, y, x + w / 2, y + h, fill=esc(cor, 0.85)); p.rect(x - w / 2, y + h * 0.25, x + w / 2, y + h * 0.75, fill=cor)
        p.rect(x - w / 2, y + h - h * 0.08, x + w / 2, y + h, fill=(190, 190, 196)); p.rect(x - w / 2, y, x + w / 2, y + h * 0.07, fill=(170, 170, 176))
        if rot and w * p.k > 18: p.text(x, y + h * 0.5, rot, h * 0.16, (40, 60, 30))
        p.rect(x - w / 2 + w * 0.1, y + h * 0.1, x - w / 2 + w * 0.22, y + h * 0.9, fill=esc(cor, 1.25))
    elif forma == "garrafa":
        p.rrect(x - w / 2, y, x + w / 2, y + h * 0.7, w * 0.3, fill=cor)
        p.poly([(x - w / 2, y + h * 0.66), (x + w / 2, y + h * 0.66), (x + w * 0.18, y + h * 0.86), (x - w * 0.18, y + h * 0.86)], fill=cor)
        p.rect(x - w * 0.18, y + h * 0.86, x + w * 0.18, y + h, fill=esc(cor, 0.7)); p.rect(x - w / 2, y + h * 0.25, x + w / 2, y + h * 0.45, fill=(240, 240, 240))
    elif forma in ("caixa", "caixinha"):
        p.rect(x - w / 2, y, x + w / 2, y + h, fill=cor); p.rect(x - w / 2, y + h * 0.55, x + w / 2, y + h * 0.75, fill=esc(cor, 0.75))
        if rot and w * p.k > 20: p.text(x, y + h * 0.4, rot, h * 0.13, (30, 30, 30))
    elif forma == "pacote":
        p.poly([(x - w / 2, y), (x + w / 2, y), (x + w * 0.45, y + h), (x - w * 0.45, y + h)], fill=cor)
        p.rect(x - w * 0.4, y + h * 0.35, x + w * 0.4, y + h * 0.6, fill=esc(cor, 1.4))
        if rot and w * p.k > 20: p.text(x, y + h * 0.47, rot, h * 0.13, (30, 30, 30))
    elif forma == "livro":
        p.rect(x - w / 2, y, x + w / 2, y + h, fill=cor); p.rect(x - w / 2, y + h * 0.8, x + w / 2, y + h * 0.85, fill=esc(cor, 1.5))
    elif forma == "pote":
        p.rrect(x - w / 2, y, x + w / 2, y + h * 0.85, w * 0.15, fill=cor); p.rect(x - w * 0.45, y + h * 0.85, x + w * 0.45, y + h, fill=esc(cor, 0.6))
    elif forma == "ferramenta":
        p.rect(x - w * 0.08, y, x + w * 0.08, y + h * 0.7, fill=(120, 80, 50)); p.rect(x - w / 2, y + h * 0.7, x + w / 2, y + h, fill=cor)


def encher(p, conteudo, x0, x1, y, h, seed=0, cheio=0.9, rot=None):
    """Enche uma prateleira (de x0 a x1 cm, base y, altura livre h) com o produto."""
    info = PRODUTOS.get(conteudo, PRODUTOS["latas"])
    if not info["forma"]: return
    r = random.Random(seed); f = info["forma"]
    wd = {"lata": 9, "garrafa": 8, "caixa": 18, "caixinha": 8, "pacote": 14, "livro": 4, "pote": 10, "ferramenta": 6}[f]
    hd = {"lata": 12, "garrafa": 30, "caixa": 26, "caixinha": 12, "pacote": 22, "livro": 24, "pote": 14, "ferramenta": 20}[f]
    hh = min(h * 0.92, hd); x = x0 + 1.5
    while x + wd < x1:
        ww = wd * (r.uniform(0.6, 1.0) if f == "livro" else 1)
        hh2 = hh * (r.uniform(0.75, 1.0) if f == "livro" else 1)
        if r.random() < cheio:
            produto(p, f, x + ww / 2, y, ww, hh2, r.choice(info["cores"]), rot or info["rot"])
            if f == "lata" and h > hh * 2.1: produto(p, f, x + ww / 2, y + hh, ww, hh, r.choice(info["cores"]), rot or info["rot"])
        x += ww + (0.6 if f == "livro" else 1.4)


# ============================== MÓVEIS DE PISO ==============================
@movel("sofa", "piso", 200, 85, ("sofá", "sofa"))
def _sofa(p, o):
    c = o.get("cor", (70, 84, 120)); w = 100
    p.rrect(-w, 0, w, 85, 12, fill=esc(c, 0.8)); p.rrect(-w + 18, 30, w - 18, 80, 10, fill=c)
    p.rrect(-w, 0, -w + 22, 62, 8, fill=esc(c, 0.9)); p.rrect(w - 22, 0, w, 62, 8, fill=esc(c, 0.9))
    p.rrect(-w + 20, 22, -2, 46, 6, fill=esc(c, 1.15)); p.rrect(2, 22, w - 20, 46, 6, fill=esc(c, 1.15))
    p.rect(-w + 6, -4, -w + 14, 2, fill=(30, 22, 18)); p.rect(w - 14, -4, w - 6, 2, fill=(30, 22, 18))


@movel("poltrona", "piso", 90, 100, ("poltrona", "cadeira de balanço"))
def _poltrona(p, o):
    c = o.get("cor", (130, 70, 60))
    p.rrect(-45, 0, 45, 100, 14, fill=esc(c, 0.8)); p.rrect(-32, 34, 32, 94, 12, fill=c)
    p.rrect(-45, 0, -30, 64, 8, fill=esc(c, 0.9)); p.rrect(30, 0, 45, 64, 8, fill=esc(c, 0.9)); p.rrect(-30, 22, 30, 40, 6, fill=esc(c, 1.15))


@movel("cama", "piso", 160, 110, ("cama", "colchão", "lençol", "travesseiro", "cobertor"))
def _cama(p, o):
    c = o.get("cor", (90, 110, 150)); mad = o.get("madeira", (110, 76, 50))
    p.rect(-82, 0, 82, 110, fill=mad); p.rect(-74, 50, 74, 102, fill=esc(mad, 0.85))
    p.rrect(-78, 18, 78, 58, 6, fill=(232, 230, 222)); p.rrect(-60, 50, -8, 70, 8, fill=(244, 244, 240)); p.rrect(8, 50, 60, 70, 8, fill=(244, 244, 240))
    p.rrect(-80, 6, 80, 44, 6, fill=c); p.line([(-80, 30), (80, 30)], esc(c, 0.8), 1.2)
    if o.get("ocupada"): p.ell(0, 46, 50, 12, fill=esc(c, 0.9))


@movel("beliche", "piso", 100, 170, ("beliche",))
def _beliche(p, o):
    mad = o.get("madeira", (120, 84, 54))
    for x in (-50, 46): p.rect(x, 0, x + 6, 170, fill=mad)
    for y in (20, 100):
        p.rect(-48, y, 48, y + 14, fill=esc(mad, 0.85)); p.rrect(-46, y + 12, 46, y + 26, 4, fill=(220, 220, 230)); p.rrect(-46, y + 10, 30, y + 24, 4, fill=(90, 120, 170))
    for y in range(40, 160, 22): p.line([(40, y), (52, y)], mad, 1.5)


@movel("berco", "piso", 110, 95, ("berço", "berco"))
def _berco(p, o):
    c = o.get("cor", (236, 232, 226))
    p.rect(-55, 0, 55, 10, fill=esc(c, 0.8)); p.rect(-55, 30, 55, 36, fill=c); p.rect(-55, 88, 55, 95, fill=c)
    for x in range(-52, 56, 9): p.rect(x, 30, x + 3, 92, fill=c)
    p.rect(-58, 0, -52, 95, fill=esc(c, 0.85)); p.rect(52, 0, 58, 95, fill=esc(c, 0.85))
    if o.get("movel"): p.line([(0, 95), (0, 130)], (60, 60, 60), 0.6); p.ell(0, 132, 14, 4, fill=(200, 180, 220))


@movel("mesa", "piso", 120, 76, ("mesa", "mesinha", "escrivaninha"))
def _mesa(p, o):
    c = o.get("cor", (120, 84, 54)); w = o.get("larg", 120) / 2
    if o.get("toalha"):
        tc = o["toalha"] if isinstance(o["toalha"], (list, tuple)) else (200, 60, 60)
        p.poly([(-w - 4, 76), (w + 4, 76), (w + 8, 40), (-w - 8, 40)], fill=tc)
        for x in range(int(-w), int(w), 12): p.line([(x, 76), (x * 1.06, 40)], esc(tc, 1.3), 0.8)
    else:
        p.rect(-w, 70, w, 76, fill=c); p.rect(-w, 66, w, 70, fill=esc(c, 0.7))
    for x in (-w + 4, w - 10): p.rect(x, 0, x + 6, 68, fill=esc(c, 0.75))
    itens(p, o.get("itens", []), -w + 10, w - 10, 76)


@movel("mesa_cozinha", "piso", 110, 76, ("mesa da cozinha", "mesa de jantar"))
def _mesa_cozinha(p, o):
    o.setdefault("toalha", (200, 70, 70)); o.setdefault("larg", 110); _mesa(p, o)


@movel("cadeira", "piso", 45, 92, ("cadeira",))
def _cadeira(p, o):
    c = o.get("cor", (110, 76, 50))
    p.rect(-21, 0, -17, 92, fill=esc(c, 0.8)); p.rect(17, 0, 21, 92, fill=esc(c, 0.8))
    p.rect(-22, 44, 22, 50, fill=c); p.rect(-20, 70, 20, 90, fill=c); p.rect(-20, 56, 20, 62, fill=esc(c, 0.9))


@movel("cadeira_escritorio", "piso", 60, 105, ("cadeira de escritório", "cadeira giratória"))
def _cadeira_esc(p, o):
    c = o.get("cor", (40, 42, 50))
    p.line([(-28, 2), (28, 2)], (30, 30, 34), 2); p.rect(-2, 2, 2, 46, fill=(60, 60, 66))
    p.rrect(-26, 44, 26, 56, 4, fill=c); p.rrect(-22, 58, 22, 104, 8, fill=esc(c, 1.2))


@movel("banco", "piso", 140, 45, ("banco", "banquinho"))
def _banco(p, o):
    c = o.get("cor", (120, 84, 54)); w = o.get("larg", 140) / 2
    p.rect(-w, 38, w, 45, fill=c); p.rect(-w + 6, 0, -w + 12, 38, fill=esc(c, 0.7)); p.rect(w - 12, 0, w - 6, 38, fill=esc(c, 0.7))


@movel("estante", "piso", 90, 190, ("estante", "livros", "livro", "biblioteca"))
def _estante(p, o):
    c = o.get("cor", (96, 66, 44)); w = o.get("larg", 90) / 2; h = o.get("alt", 190)
    p.rect(-w, 0, w, h, fill=c); p.rect(-w + 4, 4, w - 4, h - 4, fill=esc(c, 0.55))
    n = 5
    for i in range(n):
        y = 4 + i * (h - 8) / n
        p.rect(-w + 4, y, w - 4, y + 3, fill=esc(c, 0.9))
        encher(p, o.get("conteudo", "livros"), -w + 4, w - 4, y + 3, (h - 8) / n - 4, seed=i * 7 + 3, cheio=o.get("cheio", 0.92))


@movel("prateleira", "piso", 150, 175, ("prateleira", "gôndola", "gondola", "corredor de", "enlatados", "lata", "latas", "milho"),
       "gôndola de mercado; opts conteudo: " + ", ".join(PRODUTOS))
def _prateleira(p, o):
    c = o.get("cor", (206, 210, 216)); w = o.get("larg", 150) / 2; h = o.get("alt", 175); n = o.get("niveis", 5)
    p.rect(-w, 0, w, h, fill=esc(c, 0.45)); p.rect(-w, 0, -w + 4, h, fill=c); p.rect(w - 4, 0, w, h, fill=c)
    p.rect(-w, h - 10, w, h, fill=o.get("cor_topo", (200, 50, 50)))
    if o.get("texto"): p.text(0, h - 5, o["texto"], 6.5, (255, 245, 230))
    cont = o.get("conteudo", "latas"); conts = cont if isinstance(cont, list) else [cont]
    for i in range(n):
        y = 4 + i * (h - 16) / n
        p.rect(-w, y, w, y + 4, fill=c); p.rect(-w, y - 3, w, y, fill=(240, 236, 120))     # etiqueta de preço
        encher(p, conts[i % len(conts)], -w + 4, w - 4, y + 4, (h - 16) / n - 6, seed=i * 13 + o.get("seed", 1), cheio=o.get("cheio", 0.85))


@movel("geladeira", "piso", 72, 182, ("geladeira", "refrigerador"))
def _geladeira(p, o):
    c = o.get("cor", (226, 228, 232))
    p.rrect(-36, 0, 36, 182, 6, fill=c); p.line([(-36, 120), (36, 120)], esc(c, 0.7), 1)
    p.rect(26, 128, 30, 170, fill=esc(c, 0.6)); p.rect(26, 70, 30, 112, fill=esc(c, 0.6))
    p.rect(-30, 4, -24, 180, fill=esc(c, 1.15))
    for k in range(o.get("imas", 3)): p.rect(-20 + k * 12, 140 + (k % 2) * 14, -12 + k * 12, 150 + (k % 2) * 14, fill=[(220, 60, 60), (60, 140, 220), (240, 200, 60)][k % 3])
    if o.get("aberta"):
        p.rect(-36, 0, 36, 182, fill=(250, 250, 240)); p.luz(0, 100, 90, (240, 245, 255), 120)
        for y in (40, 80, 120, 160): p.rect(-32, y, 32, y + 2, fill=(200, 210, 220))
        encher(p, "potes", -30, 30, 42, 36, seed=4); encher(p, "garrafas", -30, 30, 122, 36, seed=5)


@movel("freezer", "piso", 140, 90, ("freezer", "congelador", "sorvete"))
def _freezer(p, o):
    c = o.get("cor", (236, 238, 240))
    p.rrect(-70, 0, 70, 86, 4, fill=c); p.rect(-66, 70, 66, 90, fill=(150, 190, 220)); p.rect(-66, 86, 66, 90, fill=esc(c, 0.8))
    p.rect(-70, 30, 70, 40, fill=o.get("faixa", (40, 90, 170)))
    if o.get("texto", "SORVETES"): p.text(0, 35, o.get("texto", "SORVETES"), 7, (255, 255, 255))


@movel("expositor", "piso", 150, 200, ("expositor", "geladeira de bebidas", "refrigerador de vidro", "bebidas", "cerveja", "refrigerante"))
def _expositor(p, o):
    c = o.get("cor", (40, 42, 48)); w = 75
    p.rect(-w, 0, w, 200, fill=c); p.rect(-w, 186, w, 200, fill=o.get("faixa", (200, 40, 40)))
    for k in range(3):
        x0 = -w + 4 + k * (2 * w - 8) / 3; x1 = x0 + (2 * w - 8) / 3 - 3
        p.rect(x0, 8, x1, 182, fill=(150, 196, 220))
        for y in range(16, 180, 34):
            p.rect(x0, y, x1, y + 2, fill=(200, 210, 220)); encher(p, "refri" if k != 1 else "agua", x0, x1, y + 2, 30, seed=k * 9 + y)
        p.rect(x1 - 5, 80, x1 - 3, 120, fill=(220, 220, 220))
    p.luz(0, 100, 110, (190, 230, 255), 90)


@movel("fogao", "piso", 60, 88, ("fogão", "fogao", "panela", "boca do fogão"))
def _fogao(p, o):
    c = o.get("cor", (232, 232, 234))
    p.rect(-30, 0, 30, 86, fill=c); p.rect(-26, 10, 26, 60, fill=(40, 40, 46)); p.rect(-20, 56, 20, 58, fill=(160, 160, 170))
    p.rect(-30, 86, 30, 88, fill=(30, 30, 32))
    for x in (-18, -6, 6, 18): p.ell(x, 72, 3, 3, fill=(40, 40, 40))
    if o.get("panela"): p.rrect(-24, 88, 0, 104, 3, fill=(150, 150, 160)); p.rect(-28, 100, -22, 102, fill=(60, 60, 60))
    if o.get("aceso"): p.ell(14, 89, 8, 2.5, fill=(80, 140, 255)); p.luz(14, 90, 25, (60, 110, 255), 80)


@movel("pia_cozinha", "piso", 120, 92, ("pia", "torneira", "louça"))
def _pia(p, o):
    mad = o.get("cor", (180, 160, 130))
    p.rect(-60, 0, 60, 86, fill=mad); p.rect(-60, 86, 60, 92, fill=(200, 200, 205))
    for x in (-58, 2): p.rect(x, 6, x + 56, 80, outline=esc(mad, 0.7), w=1); p.rect(x + 46, 40, x + 50, 52, fill=esc(mad, 0.5))
    p.rect(-30, 92, -26, 112, fill=(170, 170, 180)); p.line([(-28, 112), (-14, 112), (-14, 104)], (170, 170, 180), 2)
    if o.get("louca"):
        for k in range(4): p.ell(12 + k * 6, 98 + k * 2, 10, 3, fill=(236, 236, 240), outline=(170, 170, 180), w=0.5)


@movel("armario", "piso", 90, 190, ("armário", "armario"))
def _armario(p, o):
    c = o.get("cor", (150, 110, 70)); w = o.get("larg", 90) / 2; h = o.get("alt", 190)
    p.rect(-w, 0, w, h, fill=c); p.line([(0, 4), (0, h - 4)], esc(c, 0.6), 1)
    p.rect(-6, h * 0.45, -3, h * 0.55, fill=(200, 190, 150)); p.rect(3, h * 0.45, 6, h * 0.55, fill=(200, 190, 150))
    if o.get("aberto"):
        p.rect(0, 4, w - 3, h - 4, fill=(24, 20, 18)); p.poly([(w, 0), (w + 18, -6), (w + 18, h + 6), (w, h)], fill=esc(c, 0.85))


@movel("guarda_roupa", "piso", 140, 200, ("guarda-roupa", "guarda roupa", "roupeiro"))
def _guarda_roupa(p, o):
    c = o.get("cor", (130, 92, 60)); w = 70
    p.rect(-w, 0, w, 200, fill=c)
    for x in (-w / 3, w / 3): p.line([(x, 4), (x, 196)], esc(c, 0.6), 1)
    p.rect(-w / 3 - 18, 60, -w / 3 + 18, 170, fill=(150, 170, 190))           # espelho no meio
    for x in (-w / 3 - 4, w / 3 + 4): p.rect(x - 1.5, 90, x + 1.5, 110, fill=(210, 200, 160))
    if o.get("aberto"):
        p.rect(w / 3, 4, w - 3, 196, fill=(20, 18, 16))
        for k in range(4): p.rect(w / 3 + 4 + k * 6, 110, w / 3 + 9 + k * 6, 170, fill=[(160, 50, 50), (60, 90, 140), (220, 220, 210), (80, 80, 80)][k])


@movel("comoda", "piso", 100, 90, ("cômoda", "comoda", "gaveta", "gaveteiro"))
def _comoda(p, o):
    c = o.get("cor", (140, 100, 66))
    p.rect(-50, 0, 50, 90, fill=c)
    for i in range(3):
        y = 6 + i * 28; p.rect(-46, y, 46, y + 24, fill=esc(c, 1.08)); p.rect(-6, y + 10, 6, y + 13, fill=(210, 200, 160))
    if o.get("aberta"): p.rect(-46, 62, 46, 86, fill=(30, 24, 20))
    itens(p, o.get("itens", []), -40, 40, 90)


@movel("criado_mudo", "piso", 45, 58, ("criado-mudo", "criado mudo", "mesa de cabeceira"))
def _criado(p, o):
    c = o.get("cor", (130, 92, 60))
    p.rect(-22, 0, 22, 56, fill=c); p.rect(-18, 30, 18, 50, fill=esc(c, 1.1)); p.rect(-3, 38, 3, 41, fill=(210, 200, 160))
    itens(p, o.get("itens", ["abajur_mesa"]), -16, 16, 56)


@movel("rack_tv", "piso", 150, 110, ("televisão", "televisao", "tv", "telinha"))
def _rack(p, o):
    c = o.get("cor", (60, 48, 40))
    p.rect(-75, 0, 75, 46, fill=c); p.rect(-70, 8, -4, 38, fill=esc(c, 0.7)); p.rect(4, 8, 70, 38, fill=esc(c, 0.7))
    p.rect(-6, 46, 6, 52, fill=(20, 20, 24)); p.rect(-20, 50, 20, 53, fill=(20, 20, 24))
    tela(p, -50, 54, 50, 112, o.get("tv", "desligada"))


def tela(p, x0, y0, x1, y1, estado="desligada"):
    p.rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2, fill=(14, 14, 16))
    if estado == "chiado":
        for k in range(160):
            xx = p.r.uniform(x0, x1); yy = p.r.uniform(y0, y1); v = p.r.randint(60, 230)
            p.rect(xx, yy, xx + (x1 - x0) / 30, yy + (y1 - y0) / 30, fill=(v, v, v))
        p.luz((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) * 1.2, (120, 120, 140), 110)
    elif estado in ("ligada", "noticia", "alerta"):
        p.rect(x0, y0, x1, y1, fill=(60, 110, 200) if estado != "alerta" else (190, 30, 30))
        if estado == "noticia": p.rect(x0, y0, x1, y0 + (y1 - y0) * 0.22, fill=(200, 40, 40)); p.ell((x0 + x1) / 2, (y0 + y1) / 2 + 4, (x1 - x0) * 0.12, (y1 - y0) * 0.22, fill=(40, 40, 50))
        if estado == "alerta": p.text((x0 + x1) / 2, (y0 + y1) / 2, "ALERTA", (y1 - y0) * 0.22, (255, 255, 255))
        p.luz((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) * 1.3, (60, 100, 220) if estado != "alerta" else (220, 40, 40), 120)
    else:
        p.rect(x0, y0, x1, y1, fill=(24, 28, 34)); p.line([(x0 + 6, y1 - 6), (x0 + (x1 - x0) * 0.4, y0 + 6)], (44, 50, 60), 1.5)


@movel("abajur", "piso", 40, 155, ("abajur", "luminária de chão"))
def _abajur(p, o):
    p.ell(0, 1, 14, 3, fill=(40, 34, 30)); p.rect(-1.5, 0, 1.5, 130, fill=(50, 44, 40))
    lc = o.get("cor", (236, 214, 170))
    p.poly([(-20, 125), (20, 125), (13, 155), (-13, 155)], fill=lc)
    if o.get("aceso", True): p.luz(0, 135, 90, (255, 200, 120), 130)


@movel("planta", "piso", 50, 110, ("planta", "vaso de planta", "samambaia"))
def _planta(p, o):
    vc = o.get("vaso", (170, 90, 60)); g = o.get("cor", (54, 110, 64)); h = o.get("alt", 110)
    for k in range(9):
        a = -1.2 + k * 0.3; L = h * (0.6 + 0.4 * math.cos(a))
        p.ell(math.sin(a) * L * 0.45, 30 + L * 0.7, 9, 22, fill=esc(g, 0.8 + 0.06 * (k % 4)))
    p.poly([(-18, 0), (18, 0), (22, 34), (-22, 34)], fill=vc); p.rect(-23, 30, 23, 36, fill=esc(vc, 0.8))


@movel("tapete", "chao", 200, 2, ("tapete",))
def _tapete(p, o):
    c = o.get("cor", (130, 50, 50)); w = o.get("larg", 200) / 2; dp = o.get("prof", 30)
    p.poly([(-w * 0.85, dp), (w * 0.85, dp), (w, 0), (-w, 0)], fill=c)
    p.poly([(-w * 0.78, dp - 4), (w * 0.78, dp - 4), (w * 0.9, 4), (-w * 0.9, 4)], outline=esc(c, 1.3))


@movel("caixa", "piso", 50, 40, ("caixa de papelão", "caixa", "caixas", "papelão"))
def _caixa(p, o):
    c = o.get("cor", (190, 140, 86)); w = o.get("larg", 50) / 2; h = o.get("alt", 40)
    p.rect(-w, 0, w, h, fill=c); p.rect(-w, h - 4, w, h, fill=esc(c, 0.85)); p.rect(-3, 0, 3, h, fill=esc(c, 1.2))
    p.poly([(-w, h), (w, h), (w - 4, h + 6), (-w + 4, h + 6)], fill=esc(c, 1.1))
    if o.get("aberta"): p.poly([(-w, h), (-w - 8, h + 14), (-4, h + 10), (0, h)], fill=esc(c, 0.9)); p.poly([(w, h), (w + 8, h + 14), (4, h + 10), (0, h)], fill=esc(c, 0.9))
    if o.get("texto"): p.text(0, h * 0.45, o["texto"], h * 0.16, (60, 40, 24))
    if o.get("conteudo") and o.get("aberta"): encher(p, o["conteudo"], -w + 3, w - 3, h - 8, 14, seed=2)


@movel("pilha_caixas", "piso", 110, 150, ("pilha de caixas", "caixas até o teto", "estoque", "caixotes"))
def _pilha(p, o):
    r = random.Random(o.get("seed", 3)); y = 0; alt = o.get("alt", 150)
    while y < alt - 20:
        x = -50
        while x < 46:
            w = r.uniform(26, 40); h = r.uniform(22, 32); c = r.choice([(190, 140, 86), (176, 128, 78), (204, 160, 104)])
            p.rect(x, y, min(50, x + w), y + h, fill=c, outline=esc(c, 0.7), w=0.6); p.rect(x + w / 2 - 2, y, x + w / 2 + 2, y + h, fill=esc(c, 1.15))
            x += w + 1
        y += 30


@movel("palete", "chao", 120, 15, ("palete", "pallet", "estrado"))
def _palete(p, o):
    c = (176, 140, 92); p.rect(-60, 0, 60, 15, fill=esc(c, 0.6))
    for x in (-60, -6, 48): p.rect(x, 0, x + 12, 10, fill=c)
    p.rect(-60, 10, 60, 15, fill=c)
    if o.get("conteudo"): _pilha(Pincel(p.d, p.x, p.y - 15 * p.k, p.k, p.P, p.r, p.a, p.ss), {"alt": o.get("alt", 90)})


@movel("balcao", "piso", 200, 105, ("balcão", "balcao", "caixa do mercado", "caixa registradora"))
def _balcao(p, o):
    c = o.get("cor", (170, 60, 50)); w = o.get("larg", 200) / 2
    p.rect(-w, 0, w, 100, fill=c); p.rect(-w, 96, w, 106, fill=o.get("tampo", (220, 220, 214)))
    p.rect(-w, 0, w, 8, fill=esc(c, 0.6))
    if o.get("texto"): p.text(0, 55, o["texto"], 14, (255, 240, 220))
    itens(p, o.get("itens", ["caixa_registradora"]), -w + 14, w - 14, 106)


@movel("lixeira", "piso", 40, 70, ("lixeira", "lixo", "cesto de lixo"))
def _lixeira(p, o):
    c = o.get("cor", (60, 110, 70))
    p.poly([(-18, 0), (18, 0), (21, 66), (-21, 66)], fill=c); p.rect(-23, 64, 23, 72, fill=esc(c, 0.8))
    for x in (-10, 0, 10): p.line([(x, 6), (x * 1.1, 60)], esc(c, 0.8), 1)
    if o.get("cheia"): p.ell(0, 74, 22, 8, fill=(40, 40, 44))


@movel("extintor", "piso", 20, 60, ("extintor",))
def _extintor(p, o):
    p.rrect(-8, 0, 8, 48, 6, fill=(200, 30, 30)); p.rect(-4, 48, 4, 54, fill=(40, 40, 40)); p.line([(4, 52), (12, 40), (12, 20)], (30, 30, 30), 1.5)
    p.rect(-8, 18, 8, 28, fill=(240, 240, 240))


@movel("gerador", "piso", 110, 80, ("gerador",))
def _gerador(p, o):
    c = o.get("cor", (230, 180, 40))
    p.rect(-55, 6, 55, 70, fill=c); p.rect(-55, 0, 55, 8, fill=(40, 40, 44)); p.rect(-48, 14, 0, 60, fill=(50, 50, 54))
    for y in range(18, 58, 8): p.line([(-44, y), (-4, y)], (80, 80, 84), 1)
    p.rect(8, 40, 46, 62, fill=esc(c, 0.8)); p.ell(26, 26, 8, 8, fill=(30, 30, 30))
    if o.get("ligado"): p.ell(40, 66, 2.5, 2.5, fill=(80, 255, 90)); p.luz(40, 66, 10, (80, 255, 90), 120)


@movel("tambor", "piso", 60, 90, ("tambor", "barril", "galão", "tonel"))
def _tambor(p, o):
    c = o.get("cor", (40, 80, 150))
    p.rect(-30, 0, 30, 88, fill=c); p.ell(0, 88, 30, 5, fill=esc(c, 0.7))
    for y in (24, 62): p.rect(-30, y, 30, y + 3, fill=esc(c, 0.75))


@movel("botijao", "piso", 36, 50, ("botijão", "botijao", "gás"))
def _botijao(p, o):
    p.rrect(-17, 0, 17, 40, 10, fill=(200, 50, 40)); p.rect(-8, 40, 8, 50, fill=(170, 40, 30)); p.rect(-3, 50, 3, 54, fill=(160, 160, 170))


@movel("carrinho", "piso", 80, 100, ("carrinho de compras", "carrinho"))
def _carrinho(p, o):
    m = (170, 176, 186)
    for x in (-30, 26): p.ell(x, 4, 5, 5, fill=(30, 30, 34))
    p.line([(-36, 10), (34, 10)], m, 1.5); p.poly([(-38, 30), (36, 30), (40, 90), (-42, 90)], outline=m)
    for x in range(-36, 40, 8): p.line([(x, 30), (x * 1.08, 90)], m, 0.6)
    for y in range(36, 90, 10): p.line([(-40, y), (38, y)], m, 0.6)
    p.line([(36, 90), (48, 104)], m, 2); p.line([(-36, 10), (-38, 30)], m, 1.2); p.line([(34, 10), (36, 30)], m, 1.2)
    if o.get("conteudo"): encher(p, o["conteudo"], -34, 30, 60, 30, seed=3)


@movel("maca", "piso", 190, 90, ("maca", "leito"))
def _maca(p, o):
    m = (180, 186, 196)
    p.rect(-90, 54, 90, 64, fill=m); p.rrect(-88, 62, 88, 76, 4, fill=(230, 236, 236))
    p.rrect(54, 74, 84, 84, 4, fill=(244, 244, 244))
    for x in (-80, 76): p.rect(x, 6, x + 4, 54, fill=esc(m, 0.7)); p.ell(x + 2, 4, 5, 5, fill=(40, 40, 44))
    if o.get("lencol"): p.rrect(-88, 70, 60, 90, 8, fill=(160, 200, 210))
    if o.get("ocupada"): p.rrect(-80, 72, 50, 92, 10, fill=(170, 200, 210)); p.ell(66, 88, 12, 10, fill=(200, 160, 130))


@movel("cadeira_rodas", "piso", 70, 95, ("cadeira de rodas",))
def _cadeira_rodas(p, o):
    p.ell(-12, 30, 30, 30, outline=(60, 60, 66), w=2.5); p.ell(22, 8, 8, 8, fill=(40, 40, 44))
    p.rect(-24, 44, 24, 52, fill=(50, 70, 120)); p.rect(-24, 52, -18, 94, fill=(50, 70, 120)); p.line([(-22, 94), (-30, 98)], (60, 60, 66), 2)


@movel("suporte_soro", "piso", 40, 180, ("soro", "suporte de soro"))
def _soro(p, o):
    p.line([(-16, 2), (16, 2)], (150, 150, 160), 1.5); p.rect(-1.2, 2, 1.2, 175, fill=(170, 170, 180))
    p.line([(-12, 175), (12, 175)], (170, 170, 180), 1.2); p.rrect(-10, 140, 4, 172, 3, fill=(210, 230, 240)); p.line([(-3, 140), (-3, 100), (8, 60)], (200, 220, 230), 0.5)


@movel("mesa_escritorio", "piso", 140, 76, ("mesa de escritório", "computador", "monitor", "teclado"))
def _mesa_esc(p, o):
    c = o.get("cor", (180, 170, 150))
    p.rect(-70, 70, 70, 76, fill=c); p.rect(-66, 0, -26, 70, fill=esc(c, 0.85)); p.rect(66, 0, 62, 70, fill=esc(c, 0.85))
    for y in (10, 30, 50): p.rect(-62, y, -30, y + 16, outline=esc(c, 0.6), w=0.6)
    p.rect(-4, 76, 4, 86, fill=(30, 30, 34)); p.rect(-30, 84, 30, 120, fill=(24, 24, 28))
    est = o.get("tela", "ligada")
    p.rect(-27, 87, 27, 117, fill=(70, 130, 200) if est == "ligada" else ((200, 40, 40) if est == "alerta" else (20, 24, 30)))
    if est != "desligada": p.luz(0, 102, 50, (90, 140, 230) if est == "ligada" else (230, 50, 50), 90)
    p.rect(-24, 76, 24, 79, fill=(40, 40, 44))
    itens(p, o.get("itens", ["papel", "copo"]), 32, 66, 76)


@movel("arquivo", "piso", 50, 130, ("arquivo", "pasta", "fichário", "arquivos"))
def _arquivo(p, o):
    c = o.get("cor", (130, 140, 150))
    p.rect(-25, 0, 25, 130, fill=c)
    for i in range(4):
        y = 4 + i * 31; p.rect(-22, y, 22, y + 28, fill=esc(c, 1.08)); p.rect(-8, y + 18, 8, y + 21, fill=(70, 70, 76)); p.rect(-6, y + 8, 6, y + 14, fill=(240, 240, 230))
    if o.get("aberto"): p.rect(-22, 66, 22, 94, fill=(30, 30, 34)); encher(p, "papel", -20, 20, 70, 20, seed=1)


@movel("privada", "piso", 45, 80, ("privada", "vaso sanitário", "banheiro"))
def _privada(p, o):
    c = (240, 240, 240)
    p.rect(-18, 46, 18, 80, fill=c, outline=(200, 200, 206), w=0.5); p.poly([(-10, 0), (10, 0), (14, 30), (-14, 30)], fill=c)
    p.ell(0, 36, 22, 8, fill=c, outline=(200, 200, 206), w=0.5); p.ell(0, 37, 14, 4, fill=(190, 210, 220))


@movel("banheira", "piso", 170, 60, ("banheira",))
def _banheira(p, o):
    c = (240, 240, 244)
    p.rrect(-85, 6, 85, 60, 18, fill=c, outline=(200, 200, 210), w=0.6); p.rect(-80, 52, 80, 58, fill=o.get("agua", (150, 190, 210)))
    for x in (-70, 66): p.ell(x, 4, 6, 4, fill=(190, 170, 110))
    p.line([(70, 60), (70, 76), (60, 76)], (180, 180, 190), 2)


@movel("pia_banheiro", "piso", 60, 90, ("pia do banheiro", "lavabo"))
def _pia_b(p, o):
    c = (240, 240, 244)
    p.rect(-6, 0, 6, 70, fill=c); p.rrect(-30, 70, 30, 86, 6, fill=c); p.ell(0, 84, 22, 3, fill=(200, 210, 220))
    p.line([(0, 86), (0, 94), (8, 94)], (180, 180, 190), 1.5)


@movel("chuveiro", "parede", 60, 60, ("chuveiro", "box"))
def _chuveiro(p, o):
    p.line([(0, 0), (0, 30), (16, 34)], (180, 180, 190), 1.8); p.ell(20, 32, 10, 4, fill=(200, 200, 210))
    if o.get("ligado"):
        for k in range(10): p.line([(14 + k, 28), (10 + k * 1.8, -120)], (170, 200, 230), 0.4)


@movel("maquina_lavar", "piso", 60, 88, ("máquina de lavar", "lavadora", "lavanderia"))
def _maq(p, o):
    c = (236, 236, 240)
    p.rrect(-30, 0, 30, 86, 4, fill=c); p.rect(-28, 74, 28, 86, fill=esc(c, 0.9)); p.ell(0, 40, 20, 20, fill=(150, 150, 160)); p.ell(0, 40, 15, 15, fill=(80, 110, 150))
    p.ell(18, 80, 3, 3, fill=(60, 60, 60))


@movel("escada_mao", "piso", 50, 180, ("escada de mão", "escadinha"))
def _escada_mao(p, o):
    c = o.get("cor", (190, 190, 196))
    p.line([(-22, 0), (-12, 180)], c, 2.5); p.line([(22, 0), (12, 180)], c, 2.5)
    for k in range(6): y = 20 + k * 28; p.line([(-21 + y * 0.055, y), (21 - y * 0.055, y)], c, 2)


@movel("bicicleta", "piso", 170, 100, ("bicicleta", "bike"))
def _bike(p, o):
    c = o.get("cor", (200, 50, 40)); pn = (30, 30, 34)
    for x in (-55, 55): p.ell(x, 34, 33, 33, outline=pn, w=2.5)
    p.line([(-55, 34), (-10, 34), (30, 74), (-20, 74), (-55, 34)], c, 2.5); p.line([(-10, 34), (-24, 84)], c, 2.5); p.line([(30, 74), (55, 34)], c, 2.5)
    p.line([(30, 74), (26, 92), (40, 92)], c, 2); p.rect(-34, 84, -14, 89, fill=pn)


@movel("lareira", "piso", 150, 130, ("lareira", "chaminé"))
def _lareira(p, o):
    c = o.get("cor", (150, 90, 70))
    p.rect(-75, 0, 75, 130, fill=c)
    for y in range(8, 130, 14):
        for x in range(-75 + (y // 14 % 2) * 12, 75, 24): p.rect(x, y, x + 22, y + 12, outline=esc(c, 0.75), w=0.5)
    p.rect(-80, 100, 80, 110, fill=(80, 60, 50)); p.rrect(-44, 0, 44, 76, 20, fill=(20, 14, 12))
    if o.get("acesa", True):
        for k in range(5): p.poly([(-26 + k * 12, 6), (-18 + k * 12, 6), (-22 + k * 12, 34 + (k % 2) * 14)], fill=(250, 150 + k * 15, 40))
        p.luz(0, 30, 120, (255, 130, 40), 150)


@movel("caixao", "piso", 200, 70, ("caixão", "caixao", "velório", "funeral"))
def _caixao(p, o):
    c = o.get("cor", (70, 40, 30))
    p.rect(-80, 0, 80, 20, fill=(60, 50, 50)); p.poly([(-100, 30), (-70, 66), (90, 60), (100, 30), (90, 22), (-70, 22)], fill=c)
    p.line([(-70, 44), (90, 42)], esc(c, 1.4), 1)
    if o.get("aberto"): p.poly([(-70, 66), (-60, 104), (80, 98), (90, 60)], fill=esc(c, 0.8)); p.poly([(-66, 64), (86, 58), (80, 50), (-60, 54)], fill=(220, 210, 200))


@movel("cadeira_balanco", "piso", 70, 100, ("cadeira de balanço",))
def _cad_bal(p, o):
    c = o.get("cor", (110, 76, 50))
    p.arc(0, 30, 44, 30, 20, 160, c, 2.5); p.rect(-24, 6, -20, 96, fill=c); p.rect(20, 6, 24, 96, fill=c)
    p.rect(-26, 44, 26, 50, fill=c)
    for x in range(-18, 20, 8): p.rect(x, 60, x + 3, 94, fill=esc(c, 0.9))


@movel("piano", "piso", 150, 130, ("piano",))
def _piano(p, o):
    c = (30, 26, 26)
    p.rect(-75, 0, 75, 130, fill=c); p.rect(-75, 68, 75, 76, fill=(240, 236, 226))
    for x in range(-74, 75, 6): p.line([(x, 68), (x, 76)], (90, 90, 90), 0.4)
    for x in range(-71, 72, 12): p.rect(x, 72, x + 3, 76, fill=(20, 20, 20))
    p.rect(-70, 0, -64, 66, fill=esc(c, 1.5)); p.rect(64, 0, 70, 66, fill=esc(c, 1.5))


# ============================== EM CIMA DOS MÓVEIS ==============================
ITENS = {}


def item(nome, larg, sinonimos=()):
    def dec(f):
        ITENS[nome] = (f, larg); MOVEIS.setdefault(nome, Movel(lambda p, o, _f=f: _f(p, 0, 0, o), "cima", larg, larg, tuple(sinonimos), "objeto de cima de mesa"))
        return f
    return dec


def itens(p, lista, x0, x1, y):
    """Coloca objetos de cima (telefone, rádio, copo...) distribuídos sobre um tampo de x0 a x1 cm na altura y."""
    lista = [i if isinstance(i, dict) else {"m": i} for i in lista]
    if not lista: return
    for k, it in enumerate(lista):
        nome = it.get("m")
        if nome not in ITENS: continue
        x = it.get("x", x0 + (x1 - x0) * (k + 0.5) / len(lista))
        ITENS[nome][0](p, x, y, it)


@item("caixa_registradora", 40, ("caixa registradora", "registradora", "gaveta do caixa"))
def _registradora(p, x, y, o):
    p.rect(x - 20, y, x + 20, y + 12, fill=(60, 62, 70)); p.poly([(x - 18, y + 12), (x + 14, y + 12), (x + 10, y + 26), (x - 14, y + 26)], fill=(80, 84, 92))
    p.rect(x - 4, y + 26, x + 4, y + 30, fill=(50, 50, 56)); p.rect(x - 12, y + 30, x + 12, y + 40, fill=(30, 40, 30)); p.text(x, y + 35, o.get("visor", "0,00"), 5, (120, 255, 140), "mono")
    if o.get("aberta"): p.rect(x - 20, y - 4, x + 20, y + 2, fill=(40, 40, 44)); p.rect(x - 16, y - 2, x + 16, y + 1, fill=(90, 160, 90))


@item("telefone", 22, ("telefone", "telefone fixo", "chamada perdida", "secretária eletrônica"))
def _telefone(p, x, y, o):
    c = o.get("cor", (40, 40, 46))
    p.rrect(x - 11, y, x + 11, y + 8, 2, fill=c); p.rrect(x - 13, y + 7, x + 13, y + 12, 3, fill=esc(c, 1.3))
    p.rect(x - 7, y + 2, x + 7, y + 6, fill=(120, 200, 140) if o.get("visor") else (60, 70, 70))
    if o.get("visor"): p.text(x, y + 4, o["visor"], 2.2, (20, 40, 20), "mono")
    if o.get("pisca"): p.ell(x + 9, y + 3, 1.2, 1.2, fill=(255, 60, 40)); p.luz(x + 9, y + 3, 6, (255, 60, 40), 140)


@item("radinho", 26, ("radinho", "rádio", "radio", "música", "alerta no rádio"))
def _radinho(p, x, y, o):
    c = o.get("cor", (170, 50, 40))
    p.rrect(x - 13, y, x + 13, y + 16, 3, fill=c); p.ell(x - 5, y + 8, 5, 5, fill=(40, 30, 30))
    p.rect(x + 3, y + 10, x + 11, y + 13, fill=(240, 220, 120)); p.line([(x + 10, y + 16), (x + 18, y + 34)], (180, 180, 190), 0.6)


@item("copo", 6, ("copo", "xícara", "caneca", "café"))
def _copo(p, x, y, o):
    c = o.get("cor", (236, 236, 240))
    p.rect(x - 3, y, x + 3, y + 8, fill=c); p.arc(x + 4, y + 4, 2, 2.5, 270, 90, c, 0.6)


@item("papel", 20, ("papel", "papéis", "bilhete", "carta", "prancheta", "folha", "documento"))
def _papel(p, x, y, o):
    p.poly([(x - 10, y), (x + 10, y), (x + 8, y + 2), (x - 12, y + 2)], fill=(240, 240, 232))


@item("prancheta", 22, ("prancheta",))
def _prancheta(p, x, y, o):
    p.poly([(x - 11, y), (x + 11, y), (x + 9, y + 3), (x - 13, y + 3)], fill=(160, 120, 70)); p.poly([(x - 9, y + 3), (x + 9, y + 3), (x + 8, y + 4), (x - 10, y + 4)], fill=(240, 240, 232))


@item("abajur_mesa", 18, ("luminária", "abajur"))
def _abajur_mesa(p, x, y, o):
    p.ell(x, y + 1, 6, 1.5, fill=(40, 34, 30)); p.rect(x - 0.8, y, x + 0.8, y + 22, fill=(50, 44, 40))
    p.poly([(x - 9, y + 20), (x + 9, y + 20), (x + 6, y + 32), (x - 6, y + 32)], fill=(236, 214, 170))
    if o.get("aceso", True): p.luz(x, y + 24, 50, (255, 200, 120), 120)


@item("vela", 4, ("vela", "velas", "castiçal"))
def _vela(p, x, y, o):
    p.rect(x - 1.5, y, x + 1.5, y + 12, fill=(240, 234, 210)); p.ell(x, y + 14, 1.2, 2.4, fill=(255, 200, 80)); p.luz(x, y + 14, 30, (255, 170, 70), 130)


@item("prato", 22, ("prato", "comida", "jantar"))
def _prato(p, x, y, o):
    p.ell(x, y + 1, 11, 2, fill=(240, 240, 240)); p.ell(x, y + 2, 6, 1.4, fill=o.get("cor", (190, 120, 60)))


@item("garrafa", 7, ("garrafa",))
def _garrafa_i(p, x, y, o):
    produto(p, "garrafa", x, y, 7, 28, o.get("cor", (70, 150, 80)))


@item("lata", 9, ("lata", "lata de milho"))
def _lata_i(p, x, y, o):
    produto(p, "lata", x, y, 8, 11, o.get("cor", (232, 200, 60)), o.get("rot", "MILHO"))


@item("notebook", 34, ("notebook", "laptop"))
def _notebook(p, x, y, o):
    p.rect(x - 17, y, x + 17, y + 2, fill=(160, 160, 170)); p.poly([(x - 15, y + 2), (x + 15, y + 2), (x + 13, y + 22), (x - 13, y + 22)], fill=(40, 40, 46))
    p.poly([(x - 13, y + 4), (x + 13, y + 4), (x + 11.5, y + 20), (x - 11.5, y + 20)], fill=(80, 140, 210)); p.luz(x, y + 12, 34, (90, 150, 230), 80)


@item("celular_mesa", 8, ())
def _cel_mesa(p, x, y, o):
    p.rect(x - 4, y, x + 4, y + 1.2, fill=(20, 20, 24))
    if o.get("aceso"): p.rect(x - 3.5, y + 1, x + 3.5, y + 1.6, fill=(160, 210, 255)); p.luz(x, y + 2, 14, (150, 200, 255), 120)


@item("caixa_remedio", 10, ("remédio", "remedio", "comprimido", "pílula"))
def _remedio(p, x, y, o):
    produto(p, "caixinha", x, y, 10, 6, (240, 240, 240))


@item("vaso_flor", 12, ("flores", "vaso de flor", "flor"))
def _flor(p, x, y, o):
    p.poly([(x - 4, y), (x + 4, y), (x + 5, y + 12), (x - 5, y + 12)], fill=(120, 150, 190))
    for k in range(5): p.ell(x - 6 + k * 3, y + 18 + (k % 2) * 3, 2.4, 2.4, fill=[(230, 80, 90), (250, 200, 70), (240, 240, 240)][k % 3])


# ============================== PAREDE ==============================
@movel("janela", "parede", 120, 110, ("janela", "vidro da janela", "lá fora", "persiana", "cortina"), "opts vista: noite/dia/cidade/arvores/tempestade, grade, cortina, aberta")
def _janela(p, o):
    w = o.get("larg", 120) / 2; h = o.get("alt", 110); vista = o.get("vista", "noite")
    cores = {"noite": ((22, 30, 56), (40, 46, 80)), "dia": ((150, 196, 236), (210, 228, 240)), "cidade": ((24, 32, 60), (60, 50, 70)),
             "arvores": ((40, 60, 80), (70, 90, 90)), "tempestade": ((30, 34, 44), (60, 64, 76)), "amanhecer": ((120, 120, 160), (230, 170, 150))}[vista if vista in ("noite", "dia", "cidade", "arvores", "tempestade", "amanhecer") else "noite"]
    for i in range(12):
        y0 = i * h / 12; p.rect(-w, y0, w, y0 + h / 12 + 0.5, fill=tuple(int(cores[1][c] + (cores[0][c] - cores[1][c]) * i / 11) for c in range(3)))
    r = random.Random(o.get("seed", 5))
    if vista in ("cidade", "noite"):
        x = -w
        while x < w:
            bw = r.uniform(10, 22); bh = r.uniform(h * 0.2, h * 0.7)
            p.rect(x, 0, min(w, x + bw), bh, fill=(16, 20, 36))
            for yy in range(4, int(bh) - 4, 7):
                for xx in range(int(x) + 2, int(min(w, x + bw)) - 3, 5):
                    if r.random() < 0.3: p.rect(xx, yy, xx + 2.5, yy + 3, fill=(250, 210, 130))
            x += bw + 1
    elif vista == "arvores":
        for k in range(7): xx = r.uniform(-w, w); p.ell(xx, r.uniform(20, 50), r.uniform(14, 26), r.uniform(20, 40), fill=(30, 50, 40))
    if vista == "noite": p.ell(w * 0.5, h * 0.78, 6, 6, fill=(230, 226, 210))
    luzcor = {"dia": (200, 220, 240), "amanhecer": (230, 180, 150)}.get(vista)
    if luzcor: p.luz(0, h / 2, w * 2.2, luzcor, 70)
    mc = o.get("moldura", (230, 230, 226))
    p.rect(-w - 4, -4, w + 4, 0, fill=mc); p.rect(-w - 4, h, w + 4, h + 4, fill=mc); p.rect(-w - 4, -4, -w, h + 4, fill=mc); p.rect(w, -4, w + 4, h + 4, fill=mc)
    p.rect(-1.5, 0, 1.5, h, fill=mc); p.rect(-w, h / 2 - 1.5, w, h / 2 + 1.5, fill=mc)
    p.rect(-w - 8, -10, w + 8, -4, fill=esc(mc, 0.9))
    if o.get("grade"):
        for x in range(int(-w) + 8, int(w), 12): p.rect(x, 0, x + 1.6, h, fill=(30, 30, 34))
    if o.get("quebrada"):
        cx, cy = r.uniform(-w / 2, w / 2), r.uniform(h * 0.3, h * 0.7)
        for k in range(9): a = k * 0.7 + r.random() * 0.4; p.line([(cx, cy), (cx + math.cos(a) * w * 0.8, cy + math.sin(a) * h * 0.6)], (230, 236, 240), 0.5)
    if o.get("persiana"):
        for y in range(int(h * 0.4), int(h), 5): p.rect(-w, y, w, y + 3.5, fill=(214, 210, 200))
    if o.get("cortina", True):
        cc = o.get("cor_cortina", (150, 60, 60))
        p.poly([(-w - 14, h + 8), (-w + w * 0.28, h + 8), (-w + w * 0.18, -10), (-w - 14, -12)], fill=cc)
        p.poly([(w + 14, h + 8), (w - w * 0.28, h + 8), (w - w * 0.18, -10), (w + 14, -12)], fill=cc)
        p.rect(-w - 18, h + 8, w + 18, h + 11, fill=(60, 50, 40))


@movel("porta", "parede", 90, 210, ("porta", "porta dos fundos", "maçaneta", "fechadura"), "opts tipo: madeira, metal, vidro, vaivem, aco, emergencia; aberta 0–1")
def _porta(p, o):
    tipo = o.get("tipo", "madeira"); w = o.get("larg", 90 if tipo not in ("aco", "vidro") else 200) / 2; h = o.get("alt", 210)
    ab = float(o.get("aberta", 0) or 0)
    p.rect(-w - 6, 0, w + 6, h + 6, fill=o.get("batente", (60, 50, 44)))
    p.rect(-w, 0, w, h, fill=o.get("fundo", (14, 14, 18)))
    if tipo == "aco":                                  # porta de aço de enrolar
        c = o.get("cor", (150, 156, 164)); hb = h * (1 - ab)
        p.rect(-w - 10, h, w + 10, h + 18, fill=esc(c, 0.7))
        if hb > 1:
            p.rect(-w, h - hb, w, h, fill=c)
            for y in range(int(h - hb), int(h), 7): p.line([(-w, y), (w, y)], esc(c, 0.72), 0.8)
            p.rect(-8, h - hb, 8, h - hb + 6, fill=esc(c, 0.6))
        if o.get("cadeado"): p.rrect(-5, h - hb - 2, 5, h - hb + 8, 2, fill=(200, 170, 60)); p.arc(0, h - hb + 9, 4, 5, 180, 360, (170, 170, 180), 1.2)
        return
    if tipo == "vidro":
        p.rect(-w, 0, w, h, fill=o.get("vista_cor", (34, 44, 70)))
        if o.get("rua", True):
            p.rect(-w, 0, w, h * 0.18, fill=(40, 40, 48)); p.rect(-w, h * 0.18, w, h * 0.2, fill=(80, 80, 90))
            p.rect(w * 0.2, h * 0.2, w * 0.3, h * 0.75, fill=(30, 30, 36)); p.ell(w * 0.25, h * 0.78, 6, 3, fill=(250, 220, 150))
        p.line([(-w + 10, 20), (-w + 40, h - 30)], (190, 210, 230), 0.8); p.line([(-w + 20, 20), (-w + 50, h - 40)], (160, 180, 210), 0.5)
        p.rect(-2, 0, 2, h, fill=(120, 126, 136)); p.rect(-w, 0, w, 6, fill=(120, 126, 136)); p.rect(-w, h - 6, w, h, fill=(120, 126, 136))
        for x in (-8, 4): p.rect(x, h * 0.4, x + 4, h * 0.6, fill=(200, 200, 210))
        if o.get("texto"): p.text(-w / 2, h * 0.65, o["texto"], 7, (240, 240, 240))
        return
    c = o.get("cor", {"madeira": (120, 80, 50), "metal": (100, 110, 120), "vaivem": (180, 186, 192), "emergencia": (60, 120, 70)}.get(tipo, (120, 80, 50)))
    if tipo == "vaivem":
        for s in (-1, 1):
            p.rect(min(0, s * w), 0, max(0, s * w), h * 0.9, fill=c, outline=esc(c, 0.7), w=1)
            p.ell(s * w / 2, h * 0.62, w * 0.25, h * 0.08, fill=(30, 34, 40))
        return
    dw = w * 2 * (1 - ab * 0.82)
    p.rect(-w, 0, -w + dw, h, fill=c, outline=esc(c, 0.6), w=1)
    if dw > w:
        if tipo == "madeira":
            p.rect(-w + 10, h * 0.55, -w + dw - 10, h * 0.92, outline=esc(c, 0.75), w=1); p.rect(-w + 10, h * 0.08, -w + dw - 10, h * 0.48, outline=esc(c, 0.75), w=1)
        if tipo == "metal": p.rect(-w + 20, h * 0.62, -w + dw - 20, h * 0.8, fill=(160, 180, 200))
        if tipo == "emergencia": p.rect(-w + 6, h * 0.5, -w + dw - 6, h * 0.55, fill=(200, 200, 60)); p.text(0, h * 0.85, "SAÍDA", 9, (240, 240, 240))
        p.ell(-w + dw - 12, h * 0.48, 3.5, 3.5, fill=(210, 190, 120))
        if o.get("olho_magico"): p.ell(0, h * 0.75, 1.5, 1.5, fill=(10, 10, 10))
    if o.get("luz_baixo"): p.rect(-w, 0, w, 2, fill=(240, 210, 150)); p.luz(0, 0, 50, (240, 200, 140), 120)
    if o.get("placa"): p.rect(-18, h + 10, 18, h + 22, fill=(40, 40, 44)); p.text(0, h + 16, o["placa"], 6, (240, 240, 240))


@movel("quadro", "parede", 60, 45, ("quadro", "pintura", "retrato", "foto na parede", "porta-retrato"))
def _quadro(p, o):
    c = o.get("cor", (150, 110, 60)); w = o.get("larg", 60) / 2; h = o.get("alt", 45)
    p.rect(-w, 0, w, h, fill=c); p.rect(-w + 4, 4, w - 4, h - 4, fill=o.get("tela", (90, 120, 110)))
    if o.get("retrato"): p.ell(0, h * 0.45, w * 0.25, h * 0.25, fill=(200, 170, 140)); p.ell(0, h * 0.1, w * 0.45, h * 0.18, fill=(60, 60, 80))
    else: p.poly([(-w + 4, 4), (-w * 0.2, h * 0.6), (w * 0.2, h * 0.3), (w - 4, h * 0.7), (w - 4, 4)], fill=(70, 100, 80))


@movel("espelho", "parede", 50, 80, ("espelho", "reflexo"))
def _espelho(p, o):
    w = 25; h = o.get("alt", 80)
    p.rrect(-w - 3, -3, w + 3, h + 3, 6, fill=o.get("moldura", (180, 150, 90))); p.rrect(-w, 0, w, h, 5, fill=(160, 180, 196))
    p.line([(-w + 6, h - 10), (-w + 22, 12)], (220, 230, 240), 1.2)
    if o.get("vulto"): p.ell(6, h * 0.6, 8, 10, fill=(30, 34, 40)); p.rect(-4, 0, 16, h * 0.5, fill=(30, 34, 40))


@movel("relogio_parede", "parede", 36, 36, ("relógio de parede", "relógio na parede", "ponteiro"))
def _relogio_p(p, o):
    p.ell(0, 18, 18, 18, fill=(40, 40, 44)); p.ell(0, 18, 15.5, 15.5, fill=(244, 242, 234))
    for k in range(12): a = k / 12 * math.tau; p.line([(math.sin(a) * 12, 18 + math.cos(a) * 12), (math.sin(a) * 14, 18 + math.cos(a) * 14)], (40, 40, 44), 0.8)
    try: hh, mm = (int(v) for v in str(o.get("hora", "10:10")).split(":"))
    except ValueError: hh, mm = 10, 10
    am = mm / 60 * math.tau; ah = ((hh % 12) + mm / 60) / 12 * math.tau
    p.line([(0, 18), (math.sin(ah) * 8, 18 + math.cos(ah) * 8)], (20, 20, 24), 1.6); p.line([(0, 18), (math.sin(am) * 12, 18 + math.cos(am) * 12)], (20, 20, 24), 1.0)
    p.ell(0, 18, 1.2, 1.2, fill=(200, 40, 34))


@movel("placa", "parede", 120, 30, ("placa", "letreiro", "aviso", "cartaz", "faixa"), "opts texto, cor, cor_texto")
def _placa(p, o):
    txt = str(o.get("texto", "AVISO")); w = o.get("larg", max(40, len(txt) * 7 + 16)) / 2; h = o.get("alt", 26)
    p.rect(-w, 0, w, h, fill=o.get("cor", (200, 40, 40))); p.text(0, h / 2, txt, h * 0.5, o.get("cor_texto", (255, 245, 230)), "title")
    if o.get("acesa"): p.luz(0, h / 2, w * 2, o.get("cor", (200, 40, 40)), 90)


@movel("prateleira_parede", "parede", 90, 30, ("prateleira de parede", "nicho"))
def _prat_parede(p, o):
    w = o.get("larg", 90) / 2
    p.rect(-w, 0, w, 3, fill=o.get("cor", (130, 92, 60))); p.rect(-w + 6, -8, -w + 9, 0, fill=(80, 80, 80)); p.rect(w - 9, -8, w - 6, 0, fill=(80, 80, 80))
    encher(p, o.get("conteudo", "potes"), -w + 2, w - 2, 3, 24, seed=o.get("seed", 2))


@movel("armario_alto", "parede", 120, 60, ("armário de cozinha",))
def _armario_alto(p, o):
    c = o.get("cor", (190, 170, 140)); w = o.get("larg", 120) / 2
    p.rect(-w, 0, w, 60, fill=c)
    for x in range(int(-w), int(w), 40): p.rect(x + 2, 3, x + 38, 57, outline=esc(c, 0.75), w=0.6); p.rect(x + 32, 8, x + 34, 20, fill=esc(c, 0.5))


@movel("ar_condicionado", "parede", 80, 28, ("ar-condicionado", "ar condicionado"))
def _ar(p, o):
    p.rrect(-40, 0, 40, 28, 6, fill=(236, 236, 240)); p.rect(-34, 3, 34, 7, fill=(200, 200, 206)); p.ell(30, 20, 1.5, 1.5, fill=(80, 220, 120))


@movel("quadro_avisos", "parede", 90, 60, ("mural", "quadro de avisos", "quadro de cortiça"))
def _mural(p, o):
    p.rect(-45, 0, 45, 60, fill=(170, 130, 80)); p.rect(-41, 4, 41, 56, fill=(200, 160, 110)); r = random.Random(3)
    for k in range(7):
        x = r.uniform(-36, 26); y = r.uniform(8, 40); c = r.choice([(250, 250, 240), (250, 230, 120), (180, 220, 250)])
        p.rect(x, y, x + 12, y + 14, fill=c); p.ell(x + 6, y + 13, 1.2, 1.2, fill=(200, 40, 40))


@movel("quadro_energia", "parede", 40, 55, ("quadro de luz", "disjuntor", "quadro de energia", "relógio de luz", "fusível"))
def _qenergia(p, o):
    p.rect(-20, 0, 20, 55, fill=(150, 156, 160)); p.rect(-16, 4, 16, 51, fill=(70, 74, 80))
    for k in range(6):
        y = 8 + k * 7; on = (o.get("desligado") is None) or k not in o.get("desligado", [])
        p.rect(-12, y, -2, y + 5, fill=(230, 230, 230)); p.rect(-12 if on else -7, y + 1, -7 if on else -2, y + 4, fill=(40, 40, 40))
    p.poly([(8, 46), (4, 38), (8, 38), (6, 30), (12, 40), (8, 40)], fill=(240, 200, 60))


@movel("camera_seguranca", "parede", 30, 20, ("câmera de segurança", "câmera", "cftv"))
def _cam(p, o):
    p.rect(-2, 0, 2, 10, fill=(60, 60, 66)); p.poly([(-14, 10), (14, 6), (16, 18), (-12, 22)], fill=(220, 222, 226)); p.ell(-12, 16, 3, 3, fill=(30, 30, 40))
    if o.get("ligada", True): p.ell(10, 16, 1.2, 1.2, fill=(255, 40, 40)); p.luz(10, 16, 8, (255, 40, 40), 140)


@movel("cruz", "parede", 30, 50, ("crucifixo", "cruz na parede"))
def _cruz(p, o):
    c = o.get("cor", (90, 60, 40)); p.rect(-2.5, 0, 2.5, 50, fill=c); p.rect(-14, 32, 14, 37, fill=c)


@movel("tv_parede", "parede", 110, 64, ("tv na parede", "televisão na parede"))
def _tvp(p, o):
    tela(p, -55, 0, 55, 62, o.get("tv", "desligada"))


@movel("calendario", "parede", 30, 40, ("calendário", "calendario", "data"))
def _cal(p, o):
    p.rect(-15, 0, 15, 40, fill=(244, 244, 240)); p.rect(-15, 30, 15, 40, fill=(200, 40, 40)); p.text(0, 35, o.get("mes", "NOV"), 5, (255, 255, 255))
    for r_ in range(4):
        for c_ in range(5): p.rect(-13 + c_ * 5.4, 4 + r_ * 6, -9.5 + c_ * 5.4, 8 + r_ * 6, fill=(200, 200, 200))
    if o.get("marcado"): p.ell(-2, 18, 4, 3.4, outline=(220, 30, 30), w=0.7)


@movel("cabideiro", "piso", 50, 175, ("cabideiro", "casaco pendurado", "chapéu"))
def _cabideiro(p, o):
    c = (60, 44, 34); p.line([(-16, 0), (0, 10), (16, 0)], c, 2); p.rect(-1.5, 0, 1.5, 172, fill=c)
    for s in (-1, 1): p.line([(0, 162), (s * 12, 170)], c, 1.5)
    if o.get("casaco", True): p.poly([(-4, 166), (-18, 150), (-20, 80), (6, 80), (4, 160)], fill=o.get("cor", (120, 60, 50)))


# ============================== TETO ==============================
@movel("lampada", "teto", 30, 60, ("lâmpada", "lampada", "luz do teto"), "lâmpada pendurada no fio; aceso True/False")
def _lampada(p, o):
    L = o.get("fio", 50)
    p.line([(0, 0), (0, -L)], (20, 20, 22), 0.8); p.rect(-2.5, -L - 4, 2.5, -L, fill=(60, 60, 60))
    aceso = o.get("aceso", True)
    p.ell(0, -L - 9, 6, 7, fill=(255, 236, 170) if aceso else (90, 90, 96))
    if aceso: p.luz(0, -L - 9, 90, o.get("cor_luz", (255, 200, 120)), 110)


@movel("fluorescente", "teto", 120, 10, ("luz fluorescente", "fluorescente", "lâmpada que pisca", "lâmpadas"))
def _fluor(p, o):
    w = o.get("larg", 120) / 2; aceso = o.get("aceso", True)
    p.rect(-w, -8, w, 0, fill=(200, 204, 210)); p.rect(-w + 4, -6, w - 4, -2, fill=(250, 252, 255) if aceso else (120, 124, 130))
    if aceso: p.luz(0, -5, w * 1.4, o.get("cor_luz", (210, 240, 230)), 50)


@movel("ventilador_teto", "teto", 140, 40, ("ventilador", "ventilador de teto"))
def _vent(p, o):
    p.rect(-1.5, -30, 1.5, 0, fill=(30, 30, 34)); p.ell(0, -32, 8, 4, fill=(40, 40, 44))
    p.poly([(-70, -32), (-6, -30), (-6, -34)], fill=(60, 50, 44)); p.poly([(70, -32), (6, -30), (6, -34)], fill=(60, 50, 44))


@movel("lustre", "teto", 80, 60, ("lustre", "candelabro"))
def _lustre(p, o):
    p.line([(0, 0), (0, -30)], (60, 50, 30), 0.8); p.arc(0, -38, 32, 10, 0, 180, (170, 140, 70), 1.5)
    for x in (-30, -15, 0, 15, 30):
        p.rect(x - 1, -38, x + 1, -30, fill=(240, 236, 220)); p.ell(x, -27, 1.4, 2.6, fill=(255, 210, 120))
    p.luz(0, -30, 150, (255, 200, 120), 120)


# ============================== CHÃO (objetos pequenos) ==============================
@movel("cracha", "chao", 10, 2, ("crachá", "cracha"))
def _cracha(p, o):
    p.poly([(-6, 0), (6, 0), (7, 2.4), (-5, 2.4)], fill=(240, 240, 236)); p.rect(-4, 0.6, -1, 1.8, fill=(180, 150, 130)); p.line([(-1, 2.4), (6, 8), (14, 4)], (30, 80, 160), 0.6)
    if o.get("nome"): p.text(3, 1.4, o["nome"], 1.0, (40, 40, 40))


@movel("cadeado", "chao", 8, 10, ("cadeado",))
def _cadeado(p, o):
    p.rrect(-4, 0, 4, 6, 1, fill=(200, 170, 60)); p.arc(0 if not o.get("aberto") else 2, 6, 3, 4, 180, 360, (170, 170, 180), 0.9)


@movel("chave", "chao", 8, 2, ("chave", "chaves", "molho de chaves"))
def _chave(p, o):
    p.ell(-3, 1, 2, 1, fill=(210, 180, 80)); p.rect(-1, 0.6, 5, 1.3, fill=(210, 180, 80)); p.rect(3, 0, 4, 0.7, fill=(210, 180, 80))


@movel("celular", "chao", 10, 2, ("celular", "telefone celular", "tela do celular"))
def _celular(p, o):
    p.poly([(-4, 0), (4, 0), (5, 1.6), (-3, 1.6)], fill=(20, 20, 24))
    if o.get("aceso", True): p.poly([(-3.4, 0.2), (3.4, 0.2), (4.3, 1.4), (-2.5, 1.4)], fill=(150, 200, 255)); p.luz(0, 1, 18, (150, 200, 255), 110)


@movel("lata_caida", "chao", 12, 6, ("lata rolando", "lata caída", "lata no chão"))
def _lata_c(p, o):
    c = o.get("cor", (232, 200, 60)); p.rrect(-6, 0, 6, 8, 2, fill=c); p.ell(6, 4, 1.6, 4, fill=(190, 190, 196)); p.rect(-6, 2, 6, 6, fill=esc(c, 0.8))


@movel("poca", "chao", 80, 4, ("poça", "poca", "água no chão", "gota", "goteira", "vazamento"))
def _poca(p, o):
    c = o.get("cor", (60, 80, 110)); p.ell(0, 1, o.get("larg", 80) / 2, 4, fill=c); p.ell(-8, 2, 10, 1.2, fill=esc(c, 1.5))


@movel("mancha", "chao", 70, 4, ("mancha", "rastro", "marca no chão", "água preta"))
def _mancha(p, o):
    c = o.get("cor", (30, 24, 26)); r = random.Random(4)
    for k in range(6): p.ell(r.uniform(-25, 25), 1.5, r.uniform(8, 20), r.uniform(1.6, 3), fill=c)


@movel("pegadas", "chao", 100, 4, ("pegadas", "pegada", "marcas de pé", "rastro de pés"))
def _pegadas(p, o):
    c = o.get("cor", (40, 34, 30))
    for k in range(5): x = -40 + k * 20; p.ell(x, 1 + (k % 2) * 3, 4, 1.6, fill=c)


@movel("mochila", "chao", 36, 44, ("mochila", "bolsa"))
def _mochila(p, o):
    c = o.get("cor", (60, 90, 140))
    p.rrect(-16, 0, 16, 40, 8, fill=c); p.rrect(-12, 4, 12, 20, 4, fill=esc(c, 0.8)); p.arc(0, 40, 8, 6, 180, 360, esc(c, 0.7), 1.5)


@movel("lanterna", "chao", 20, 5, ("lanterna",))
def _lanterna(p, o):
    p.rect(-10, 0, 6, 4, fill=(40, 40, 44)); p.poly([(6, -1), (10, -2), (10, 6), (6, 5)], fill=(60, 60, 64))
    if o.get("acesa"): p.ell(10, 2, 1.4, 3, fill=(255, 250, 220)); p.luz(30, 2, 40, (255, 240, 200), 100)


@movel("garrafa_caida", "chao", 30, 7, ("garrafa quebrada", "caco", "cacos", "vidro quebrado"))
def _cacos(p, o):
    r = random.Random(7)
    for k in range(9):
        x = r.uniform(-14, 14); p.poly([(x, 0), (x + r.uniform(2, 5), 0.5), (x + r.uniform(0, 3), r.uniform(1.5, 3))], fill=(180, 210, 220))


@movel("sapato", "chao", 28, 10, ("sapato", "tênis", "tenis", "chinelo"))
def _sapato(p, o):
    c = o.get("cor", (220, 220, 224)); p.rrect(-14, 0, 14, 6, 3, fill=c); p.rrect(-14, 0, -2, 10, 3, fill=c); p.rect(-14, 0, 14, 1.5, fill=(60, 60, 64))


@movel("livro_chao", "chao", 22, 4, ("caderno", "diário", "livro no chão"))
def _livro_c(p, o):
    c = o.get("cor", (120, 50, 50)); p.poly([(-11, 0), (11, 0), (13, 3), (-9, 3)], fill=c); p.poly([(-10, 3), (12, 3), (12, 4), (-10, 4)], fill=(240, 236, 220))


@movel("brinquedo", "chao", 20, 26, ("boneca", "brinquedo", "ursinho", "urso de pelúcia"))
def _brinquedo(p, o):
    c = o.get("cor", (170, 120, 80)); p.ell(0, 8, 8, 9, fill=c); p.ell(0, 21, 6, 6, fill=c); p.ell(-5, 26, 2.4, 2.4, fill=c); p.ell(5, 26, 2.4, 2.4, fill=c)
    p.ell(-2, 22, 0.8, 0.8, fill=(20, 20, 20)); p.ell(2, 22, 0.8, 0.8, fill=(20, 20, 20))


# ============================== EXTERNOS ==============================
@movel("arvore", "fora", 160, 380, ("árvore", "arvore", "árvores", "galho", "tronco"), "opts tipo: frondosa, pinheiro, seca, palmeira")
def _arvore(p, o):
    tipo = o.get("tipo", "frondosa"); g = o.get("cor", (44, 82, 54)); tr = (70, 52, 40); h = o.get("alt", 380); r = random.Random(o.get("seed", 3))
    if tipo == "pinheiro":
        p.rect(-8, 0, 8, h * 0.25, fill=tr)
        for k in range(4): y = h * (0.15 + k * 0.2); wd = 80 - k * 16; p.poly([(-wd, y), (wd, y), (0, y + h * 0.32)], fill=esc(g, 0.85 + k * 0.06))
    elif tipo == "seca":
        p.poly([(-10, 0), (10, 0), (5, h * 0.7), (-5, h * 0.7)], fill=tr)
        for k in range(7):
            y = h * (0.35 + k * 0.08); s = 1 if k % 2 else -1; L = r.uniform(40, 90)
            p.line([(0, y), (s * L, y + L * 0.7), (s * L * 1.3, y + L * 1.1)], tr, 3 - k * 0.3)
    elif tipo == "palmeira":
        p.line([(0, 0), (10, h * 0.5), (0, h * 0.9)], tr, 7)
        for k in range(7): a = -2.6 + k * 0.85; p.line([(0, h * 0.9), (math.cos(a) * 60, h * 0.9 + math.sin(a) * 30 - 20), (math.cos(a) * 90, h * 0.8)], g, 5)
    else:
        p.poly([(-12, 0), (12, 0), (7, h * 0.55), (-7, h * 0.55)], fill=tr)
        for k in range(9):
            x = r.uniform(-60, 60); y = r.uniform(h * 0.5, h * 0.92); rr = r.uniform(34, 60)
            p.ell(x, y, rr, rr * 0.85, fill=esc(g, r.uniform(0.75, 1.1)))


@movel("arbusto", "fora", 90, 60, ("arbusto", "moita", "mato", "cerca viva"))
def _arbusto(p, o):
    g = o.get("cor", (50, 90, 56)); r = random.Random(o.get("seed", 2))
    for k in range(6): p.ell(r.uniform(-34, 34), r.uniform(18, 40), r.uniform(18, 28), r.uniform(16, 24), fill=esc(g, r.uniform(0.8, 1.1)))


@movel("poste", "fora", 60, 520, ("poste", "luz do poste", "iluminação da rua"))
def _poste(p, o):
    c = (60, 62, 70)
    p.rect(-5, 0, 5, 500, fill=c); p.line([(0, 498), (60, 510)], c, 3); p.rect(48, 500, 74, 508, fill=(40, 40, 44))
    if o.get("aceso", True):
        p.rect(52, 496, 70, 500, fill=(255, 230, 170)); p.luz(61, 480, 160, (255, 200, 120), 120)


@movel("carro", "fora", 420, 140, ("carro", "automóvel", "carro batido", "pisca-alerta", "farol"), "opts cor, batido, farol, pisca")
def _carro(p, o):
    c = o.get("cor", (150, 40, 40)); vidro = (60, 80, 110)
    p.rrect(-210, 18, 210, 80, 18, fill=c); p.poly([(-130, 78), (100, 78), (60, 136), (-100, 136)], fill=c)
    p.poly([(-118, 80), (-12, 80), (-12, 128), (-92, 128)], fill=vidro); p.poly([(0, 80), (88, 80), (54, 128), (0, 128)], fill=vidro)
    for x in (-130, 130): p.ell(x, 20, 34, 34, fill=(24, 24, 26)); p.ell(x, 20, 15, 15, fill=(140, 140, 150))
    p.rect(196, 52, 210, 66, fill=(255, 240, 200)); p.rect(-210, 52, -196, 66, fill=(200, 30, 30))
    if o.get("farol"): p.luz(260, 58, 140, (255, 240, 200), 120)
    if o.get("batido"):
        p.poly([(150, 80), (210, 70), (214, 30), (170, 40)], fill=esc(c, 0.6)); p.line([(10, 128), (30, 90), (0, 100)], (230, 236, 240), 0.8)
        p.ell(200, 100, 30, 14, fill=(180, 180, 186))
    if o.get("pisca"): p.rect(196, 70, 208, 76, fill=(255, 170, 40)); p.luz(202, 73, 30, (255, 160, 40), 140)


@movel("moto", "fora", 200, 110, ("moto", "motocicleta"))
def _moto(p, o):
    c = o.get("cor", (30, 30, 34))
    for x in (-70, 70): p.ell(x, 30, 30, 30, outline=(20, 20, 22), w=6)
    p.poly([(-60, 40), (60, 40), (40, 80), (-40, 80)], fill=c); p.rect(-50, 78, 10, 88, fill=(20, 20, 22)); p.line([(50, 80), (70, 108)], (150, 150, 160), 3)


@movel("casa", "fora", 600, 520, ("casa", "fachada", "sobrado", "vizinho"), "opts cor, janelas_acesas, porta_aberta")
def _casa(p, o):
    c = o.get("cor", (200, 186, 160)); tel = o.get("telhado", (130, 60, 50)); w = o.get("larg", 600) / 2; h = o.get("alt", 360)
    p.rect(-w, 0, w, h, fill=c); p.poly([(-w - 30, h), (w + 30, h), (0, h + 160)], fill=tel)
    p.rect(-50, 0, 50, 210, fill=(110, 76, 50) if not o.get("porta_aberta") else (16, 14, 14)); p.ell(34, 100, 4, 4, fill=(210, 190, 120))
    acesa = o.get("janelas_acesas", [True, False])
    for k, x in enumerate((-w * 0.62, w * 0.62)):
        on = acesa[k % len(acesa)] if isinstance(acesa, list) else bool(acesa)
        p.rect(x - 60, 120, x + 60, 240, fill=(250, 210, 130) if on else (40, 48, 66)); p.rect(x - 2, 120, x + 2, 240, fill=c); p.rect(x - 60, 178, x + 60, 182, fill=c)
        if on: p.luz(x, 180, 140, (255, 200, 120), 90)
    p.rect(-w, 0, w, 14, fill=esc(c, 0.75))


@movel("predio", "fora", 500, 900, ("prédio", "predio", "edifício", "condomínio"))
def _predio(p, o):
    c = o.get("cor", (120, 126, 140)); w = o.get("larg", 500) / 2; h = o.get("alt", 900); r = random.Random(o.get("seed", 4))
    p.rect(-w, 0, w, h, fill=c)
    for y in range(40, int(h) - 40, 90):
        for x in range(int(-w) + 30, int(w) - 60, 90):
            on = r.random() < o.get("acesas", 0.3); p.rect(x, y, x + 50, y + 56, fill=(250, 210, 130) if on else esc(c, 0.55))
    p.rect(-60, 0, 60, 150, fill=(40, 46, 60))


@movel("muro", "fora", 600, 200, ("muro", "parede de tijolo"))
def _muro(p, o):
    c = o.get("cor", (170, 160, 150)); w = o.get("larg", 600) / 2; h = o.get("alt", 200)
    p.rect(-w, 0, w, h, fill=c); p.rect(-w, h - 12, w, h, fill=esc(c, 0.8))
    if o.get("tijolo"):
        for y in range(0, int(h) - 12, 16):
            for x in range(int(-w) + (y // 16 % 2) * 18, int(w), 36): p.rect(x, y, x + 34, y + 14, outline=esc(c, 0.75), w=0.6)
    if o.get("pichacao"): p.text(0, h * 0.5, o["pichacao"], h * 0.3, (60, 60, 70), "title")
    if o.get("caco"):
        for x in range(int(-w), int(w), 14): p.poly([(x, h), (x + 6, h + 12), (x + 10, h)], fill=(160, 200, 190))


@movel("cerca", "fora", 500, 130, ("cerca", "grade", "alambrado", "arame"), "opts tipo: madeira, arame, grade")
def _cerca(p, o):
    w = o.get("larg", 500) / 2; tipo = o.get("tipo", "madeira"); h = o.get("alt", 130)
    if tipo == "arame":
        for x in range(int(-w), int(w) + 1, 80): p.rect(x - 3, 0, x + 3, h, fill=(110, 110, 116))
        for y in range(12, int(h), 14): p.line([(-w, y), (w, y)], (150, 150, 158), 0.6)
        for x in range(int(-w), int(w), 14): p.line([(x, 0), (x + 14, h)], (140, 140, 150), 0.5); p.line([(x + 14, 0), (x, h)], (140, 140, 150), 0.5)
    elif tipo == "grade":
        c = o.get("cor", (40, 44, 50)); p.rect(-w, h - 8, w, h, fill=c); p.rect(-w, 10, w, 16, fill=c)
        for x in range(int(-w), int(w) + 1, 14): p.rect(x - 2, 0, x + 2, h + 10, fill=c); p.poly([(x - 4, h + 10), (x + 4, h + 10), (x, h + 18)], fill=c)
    else:
        c = o.get("cor", (150, 110, 70)); p.rect(-w, 30, w, 40, fill=esc(c, 0.85)); p.rect(-w, 90, w, 100, fill=esc(c, 0.85))
        for x in range(int(-w), int(w), 26): p.poly([(x, 0), (x + 20, 0), (x + 20, h - 10), (x + 10, h), (x, h - 10)], fill=c)


@movel("portao", "fora", 300, 220, ("portão", "portao"))
def _portao(p, o):
    c = o.get("cor", (60, 64, 72)); w = o.get("larg", 300) / 2; ab = float(o.get("aberto", 0) or 0)
    for s in (-1, 1): p.rect(s * w - 14, 0, s * w + 14, 240, fill=(150, 146, 140))
    ww = w * 2 * (1 - ab * 0.8)
    p.rect(-w, 6, -w + ww, 12, fill=c); p.rect(-w, 200, -w + ww, 208, fill=c)
    for x in range(int(-w), int(-w + ww), 12): p.rect(x, 6, x + 3, 214, fill=c)
    if o.get("cadeado"): p.rrect(-w + ww - 10, 100, -w + ww, 112, 2, fill=(200, 170, 60))


@movel("banco_praca", "fora", 180, 90, ("banco da praça", "banco de praça"))
def _banco_praca(p, o):
    c = o.get("cor", (130, 92, 60)); m = (40, 44, 50)
    for x in (-80, 72): p.rect(x, 0, x + 8, 44, fill=m)
    for y in (40, 46): p.rect(-90, y, 90, y + 5, fill=c)
    for y in (60, 72, 84): p.rect(-90, y, 90, y + 8, fill=c)
    p.rect(-80, 44, -72, 90, fill=m); p.rect(72, 44, 80, 90, fill=m)


@movel("hidrante", "fora", 30, 70, ("hidrante",))
def _hidrante(p, o):
    c = (200, 40, 30); p.rect(-12, 0, 12, 50, fill=c); p.ell(0, 52, 13, 10, fill=c); p.rect(-20, 30, 20, 38, fill=esc(c, 0.8)); p.rect(-14, 0, 14, 5, fill=esc(c, 0.7))


@movel("placa_rua", "fora", 80, 260, ("placa de rua", "placa de trânsito", "pare", "nome da rua"), "opts texto")
def _placa_rua(p, o):
    p.rect(-3, 0, 3, 230, fill=(150, 150, 160))
    txt = o.get("texto", "PARE")
    if txt == "PARE":
        pts = [(math.cos(a) * 32, 230 + math.sin(a) * 32) for a in [math.pi / 8 + k * math.pi / 4 for k in range(8)]]
        p.poly(pts, fill=(200, 30, 30)); p.text(0, 230, "PARE", 14, (255, 255, 255), "title")
    else:
        w = max(40, len(str(txt)) * 6); p.rect(-w, 220, w, 250, fill=(30, 90, 150)); p.text(0, 235, txt, 12, (255, 255, 255))


@movel("lixeira_rua", "fora", 120, 130, ("caçamba", "lixeira de rua", "contêiner de lixo", "sacos de lixo"))
def _cacamba(p, o):
    c = o.get("cor", (40, 100, 70))
    p.poly([(-60, 0), (60, 0), (66, 110), (-66, 110)], fill=c); p.rect(-68, 106, 68, 118, fill=esc(c, 0.75))
    for x in (-40, 40): p.ell(x, 0, 8, 8, fill=(20, 20, 22))
    for k in range(4): p.ell(-40 + k * 26, 122, 16, 12, fill=(30, 30, 36))


@movel("lapide", "fora", 60, 90, ("lápide", "lapide", "túmulo", "cemitério", "cova"))
def _lapide(p, o):
    c = o.get("cor", (150, 150, 156))
    p.rect(-26, 0, 26, 64, fill=c); p.ell(0, 64, 26, 24, fill=c); p.rect(-30, 0, 30, 8, fill=esc(c, 0.75))
    p.rect(-3, 34, 3, 70, fill=esc(c, 0.7)); p.rect(-12, 56, 12, 62, fill=esc(c, 0.7))
    if o.get("nome"): p.text(0, 20, o["nome"], 7, esc(c, 0.5))
    if o.get("terra"): p.poly([(-50, 0), (50, 0), (40, -4), (-40, -4)], fill=(90, 66, 44))


@movel("fogueira", "fora", 80, 60, ("fogueira", "fogo", "chamas", "brasa"))
def _fogueira(p, o):
    for a in (-0.5, 0.5): p.line([(-40 * math.cos(a), 0), (40 * math.cos(a), 12)], (90, 60, 40), 5)
    for k in range(6):
        x = -24 + k * 10; p.poly([(x - 6, 6), (x + 6, 6), (x, 40 + (k % 3) * 12)], fill=(255, 120 + k * 20, 30))
    p.luz(0, 30, 260, (255, 140, 50), 160)


@movel("barraca", "fora", 240, 160, ("barraca", "acampamento", "tenda"))
def _barraca(p, o):
    c = o.get("cor", (220, 140, 50))
    p.poly([(-120, 0), (120, 0), (0, 160)], fill=c); p.poly([(-30, 0), (30, 0), (0, 90)], fill=(30, 24, 20)); p.line([(0, 160), (0, 0)], esc(c, 0.7), 1)
    if o.get("acesa"): p.poly([(-30, 0), (30, 0), (0, 90)], fill=(250, 200, 110)); p.luz(0, 50, 120, (255, 190, 100), 110)


@movel("ponto_onibus", "fora", 260, 250, ("ponto de ônibus", "parada de ônibus"))
def _ponto(p, o):
    c = (60, 66, 76); p.rect(-130, 236, 130, 250, fill=c)
    for x in (-124, 118): p.rect(x, 0, x + 6, 240, fill=c)
    p.rect(-118, 80, 112, 236, fill=(130, 170, 190)); p.rect(-90, 40, 90, 48, fill=(140, 100, 70)); p.rect(60, 120, 108, 220, fill=(240, 220, 120))


@movel("orelhao", "fora", 90, 230, ("orelhão", "orelhao", "telefone público"))
def _orelhao(p, o):
    c = o.get("cor", (250, 170, 40)); p.rect(-4, 0, 4, 150, fill=(100, 100, 106))
    p.ell(0, 190, 45, 50, fill=c); p.ell(0, 175, 30, 32, fill=esc(c, 0.6)); p.rect(-10, 160, 10, 186, fill=(50, 50, 54))


@movel("balanco", "fora", 220, 220, ("balanço", "parquinho", "playground"))
def _balanco(p, o):
    c = (180, 60, 50); p.line([(-110, 0), (-90, 220), (90, 220), (110, 0)], c, 4); p.line([(-70, 0), (-90, 220)], c, 4); p.line([(70, 0), (90, 220)], c, 4)
    for x in (-30, 30): p.line([(x - 14, 220), (x - 14, 60)], (150, 150, 150), 0.8); p.line([(x + 14, 220), (x + 14, 60)], (150, 150, 150), 0.8); p.rect(x - 18, 56, x + 18, 62, fill=(60, 40, 30))


@movel("escorregador", "fora", 260, 200, ("escorregador",))
def _escorregador(p, o):
    p.line([(-110, 0), (-90, 180)], (60, 60, 70), 4); p.line([(-60, 0), (-70, 180)], (60, 60, 70), 4)
    p.rect(-100, 170, -60, 180, fill=(40, 100, 180)); p.poly([(-62, 180), (-50, 180), (130, 6), (110, 0)], fill=(220, 60, 50))


@movel("pedra", "fora", 120, 60, ("pedra", "rocha", "pedras"))
def _pedra(p, o):
    c = o.get("cor", (120, 116, 110)); p.poly([(-60, 0), (60, 0), (50, 34), (14, 60), (-30, 52), (-56, 26)], fill=c); p.poly([(14, 60), (50, 34), (40, 20), (10, 40)], fill=esc(c, 1.2))


@movel("poco", "fora", 140, 120, ("poço", "poco"))
def _poco(p, o):
    c = (140, 136, 130); p.rect(-60, 0, 60, 60, fill=c)
    for y in range(0, 60, 14):
        for x in range(-60 + (y // 14 % 2) * 12, 60, 24): p.rect(x, y, x + 22, y + 12, outline=esc(c, 0.7), w=0.5)
    p.rect(-56, 120, -48, 60, fill=(90, 66, 44)); p.rect(48, 120, 56, 60, fill=(90, 66, 44)); p.poly([(-74, 120), (74, 120), (0, 160)], fill=(110, 60, 50))
    p.line([(0, 120), (0, 80)], (160, 140, 110), 0.6); p.rect(-8, 70, 8, 82, fill=(110, 80, 50))


@movel("caixa_dagua", "fora", 160, 420, ("caixa d'água", "caixa dágua", "torre"))
def _caixa_dagua(p, o):
    m = (110, 110, 116)
    for x in (-60, 52): p.line([(x, 0), (x * 0.8, 300)], m, 3)
    p.line([(-60, 0), (42, 300)], m, 1.2); p.line([(52, 0), (-48, 300)], m, 1.2)
    p.rect(-70, 300, 70, 400, fill=(60, 110, 160)); p.ell(0, 400, 70, 16, fill=(50, 90, 140))


@movel("guarda_sol", "fora", 200, 220, ("guarda-sol", "guarda sol", "praia"))
def _guarda_sol(p, o):
    p.line([(0, 0), (0, 200)], (220, 220, 220), 2)
    for k in range(6):
        a0 = math.pi * k / 6; a1 = math.pi * (k + 1) / 6
        p.poly([(0, 230), (-math.cos(a0) * 100, 190 + math.sin(a0) * 10), (-math.cos(a1) * 100, 190 + math.sin(a1) * 10)], fill=[(230, 60, 60), (250, 250, 250)][k % 2])


@movel("barco", "fora", 300, 120, ("barco", "canoa", "bote"))
def _barco(p, o):
    c = o.get("cor", (200, 200, 210)); p.poly([(-150, 40), (150, 40), (110, 0), (-120, 0)], fill=c); p.rect(-150, 36, 150, 42, fill=(170, 60, 50))
    if o.get("vela"): p.line([(0, 40), (0, 220)], (110, 80, 50), 2); p.poly([(4, 210), (4, 60), (110, 60)], fill=(240, 240, 236))


@movel("cruz_estrada", "fora", 40, 90, ("cruz da estrada", "cruz de madeira"))
def _cruz_e(p, o):
    c = (110, 80, 54); p.rect(-3, 0, 3, 90, fill=c); p.rect(-18, 62, 18, 68, fill=c)


@movel("viatura", "fora", 420, 150, ("viatura", "carro de polícia", "polícia", "sirene"))
def _viatura(p, o):
    _carro(p, {"cor": (236, 236, 240)}); p.rect(-200, 46, 200, 56, fill=(30, 50, 110))
    p.rect(-24, 136, 0, 146, fill=(220, 30, 30)); p.rect(0, 136, 24, 146, fill=(30, 80, 230))
    if o.get("sirene", True): p.luz(-12, 141, 80, (230, 40, 40), 140); p.luz(12, 141, 80, (40, 90, 240), 140)


@movel("ambulancia", "fora", 460, 220, ("ambulância", "ambulancia"))
def _ambulancia(p, o):
    c = (240, 240, 244)
    p.rect(-230, 20, 120, 210, fill=c); p.poly([(120, 20), (230, 20), (230, 110), (190, 160), (120, 160)], fill=c)
    p.poly([(130, 110), (190, 110), (220, 100), (220, 60), (130, 60)], fill=(70, 90, 120)); p.rect(-230, 90, 230, 104, fill=(200, 40, 40))
    p.rect(-60, 130, -30, 180, fill=(200, 40, 40)); p.rect(-80, 150, -10, 160, fill=(200, 40, 40))
    for x in (-150, 150): p.ell(x, 20, 34, 34, fill=(24, 24, 26))
    p.rect(-10, 210, 20, 220, fill=(220, 40, 40)); p.luz(5, 215, 80, (230, 40, 40), 120)


# ============================== MAIS (hortifrúti, fazenda, laboratório) ==============================
@movel("banca_frutas", "piso", 160, 95, ("banca", "hortifrúti", "hortifruti", "frutas", "legumes", "verduras", "maçã", "laranja", "tomate", "banana"))
def _banca(p, o):
    c = o.get("cor", (150, 110, 70)); r = random.Random(o.get("seed", 6))
    p.rect(-80, 0, 80, 60, fill=c); p.poly([(-84, 60), (84, 60), (80, 92), (-80, 92)], fill=esc(c, 0.8))
    frutas = o.get("frutas", [(220, 50, 40), (240, 150, 40), (90, 170, 60), (240, 210, 60)])
    for k in range(4):
        x0 = -78 + k * 39; cor = frutas[k % len(frutas)]
        p.poly([(x0, 62), (x0 + 37, 62), (x0 + 35, 90), (x0 + 2, 90)], fill=esc(c, 0.65))
        for j in range(14): p.ell(x0 + r.uniform(5, 32), r.uniform(68, 92), 4.5, 4.2, fill=esc(cor, r.uniform(0.85, 1.1)))
    if o.get("placa", True): p.rect(-22, 96, 22, 110, fill=(250, 240, 200)); p.text(0, 103, o.get("preco", "R$ 4,99"), 6, (200, 40, 40))


@movel("feno", "piso", 120, 60, ("feno", "palha", "fardo"))
def _feno(p, o):
    c = (214, 180, 96); p.rect(-60, 0, 60, 56, fill=c)
    for y in range(6, 56, 8): p.line([(-60, y), (60, y + 2)], esc(c, 0.85), 0.6)
    for x in (-30, 30): p.rect(x - 1.5, 0, x + 1.5, 56, fill=(120, 80, 40))


@movel("varal", "fora", 300, 180, ("varal", "roupa no varal", "lençol no varal"))
def _varal(p, o):
    for x in (-150, 146): p.rect(x, 0, x + 4, 180, fill=(120, 90, 60))
    p.line([(-148, 176), (0, 168), (148, 176)], (200, 200, 200), 0.5)
    for k, cor in enumerate([(230, 230, 236), (180, 60, 60), (60, 100, 160), (240, 220, 120)]):
        x = -110 + k * 62; p.rect(x, 110 - (k % 2) * 16, x + 44, 170 - abs(k - 1.5) * 1.5, fill=cor)


@movel("caixa_correio", "fora", 40, 120, ("caixa de correio", "correspondência", "carta na caixa"))
def _correio(p, o):
    p.rect(-3, 0, 3, 90, fill=(80, 70, 60)); p.rrect(-18, 88, 18, 116, 8, fill=o.get("cor", (60, 80, 140)))
    if o.get("bandeira", True): p.rect(18, 100, 21, 124, fill=(200, 40, 40)); p.rect(21, 116, 30, 124, fill=(200, 40, 40))


@movel("bancada", "piso", 180, 92, ("bancada", "laboratório", "tubo de ensaio", "microscópio", "frasco"))
def _bancada(p, o):
    c = o.get("cor", (220, 224, 228))
    p.rect(-90, 0, 90, 86, fill=esc(c, 0.85)); p.rect(-92, 86, 92, 92, fill=(40, 44, 50))
    for x in (-88, -28, 32): p.rect(x, 6, x + 56, 80, outline=esc(c, 0.65), w=0.8)
    r = random.Random(o.get("seed", 4))
    for k in range(7):
        x = -80 + k * 24; cor = r.choice([(120, 220, 160), (240, 120, 120), (140, 180, 250), (250, 220, 120)])
        p.rect(x, 92, x + 6, 112, fill=(220, 236, 240)); p.rect(x, 92, x + 6, 92 + r.uniform(6, 16), fill=cor)
    p.rect(50, 92, 76, 96, fill=(40, 40, 46)); p.rect(60, 96, 66, 126, fill=(40, 40, 46)); p.rect(56, 120, 76, 128, fill=(40, 40, 46))


MOVEL_LUGARES = ("piso", "parede", "teto", "chao", "fora", "cima")


def sinonimos():
    """{palavra: nome do objeto} para a leitura literal da narração (as mais longas primeiro)."""
    out = {}
    for nome, m in MOVEIS.items():
        for s in (nome.replace("_", " "),) + m.sinonimos: out.setdefault(s.lower(), nome)
    return dict(sorted(out.items(), key=lambda kv: -len(kv[0])))
