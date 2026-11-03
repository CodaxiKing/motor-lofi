"""Contraplano do perigo: a câmera no chão, por baixo da porta, só os pés de quem está do outro lado.

PES  {"type": "pes", "x": [[0, -160], [2.2, 470]], "pes": "sapato" | "descalco" | "garra", "facing": 1,
      "luz": [210, 176, 120], "piscar": false, "handheld": 4}
    O quadro é a fresta: a porta escura em cima, o chão do corredor aceso no meio e o chão do quarto embaixo, com a luz
    vazando pela fresta e as sombras das pernas vindo na direção da câmera. "x" (animável, em px da tela) move os pés:
    quando muda, eles andam com passo alternado e o som "step" sai sozinho; parado, o peso muda de um pé para o outro.
    "pes": sapato (gente), descalco (dedos) ou garra (dedos longos com unhas: a criatura). "luz" = cor do corredor;
    "piscar": true faz a lâmpada do corredor falhar. Use alternando com o close de reação de quem está escondido (1–2 s cada).
"""
import math
from PIL import Image, ImageDraw, ImageFilter
from .core import W, H, ease, c01, lerp, keyframe, crop_zoom, fast_blur

Y0, Y1 = 760, 1060          # a fresta (chão do corredor) na tela em pé
PASSO = 260                 # px de tela por passada
_BASE = {}


def _x(shot, rel, dur):
    v = shot.get("x", W / 2)
    if isinstance(v, (list, tuple)) and v and isinstance(v[0], (list, tuple)): return keyframe(v, rel)
    if isinstance(v, (list, tuple)) and len(v) == 2: return lerp(v[0], v[1], ease(c01(rel / max(0.001, dur))))
    return float(v)


def _fundo(luz):
    key = tuple(luz)
    if key in _BASE: return _BASE[key]
    img = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
    for y in range(0, Y0):                                   # a porta, quase preta, um pouco mais clara perto da fresta
        k = (y / Y0) ** 3
        d.line([(0, y), (W, y)], fill=(int(8 + 22 * k), int(7 + 17 * k), int(8 + 14 * k)))
    for y in range(Y0, Y1):                                  # chão do corredor: claro no fundo, mais escuro na frente
        k = (y - Y0) / (Y1 - Y0)
        f = 0.95 - 0.45 * k
        d.line([(0, y), (W, y)], fill=tuple(int(c * f) for c in luz))
    d.rectangle([0, Y0, W, Y0 + 38], fill=tuple(int(c * 0.42) for c in luz))     # rodapé da parede do outro lado
    for y in range(Y1, H):                                   # chão do quarto, escuro, com a luz que vaza pela fresta
        k = (y - Y1) / (H - Y1)
        f = 0.34 * (1 - k) ** 1.6
        d.line([(0, y), (W, y)], fill=tuple(int(14 + c * f) for c in luz))
    d.rectangle([0, Y1 - 6, W, Y1 + 4], fill=(4, 4, 5))     # a soleira
    _BASE[key] = img
    return img


def _pe(d, x, y, facing, tipo, lift, cor, k=1.9):
    """Perna (sobe até sumir atrás da porta) e pé de perfil, apontando para facing. k = tamanho (1.9 enche a fresta)."""
    y = y - lift
    X = lambda dx: x + facing * dx * k           # para a frente do pé
    Y = lambda dy: y + dy * k
    if tipo == "garra":
        d.polygon([(x - 12 * k, Y0 - 10), (x + 12 * k, Y0 - 10), (x + 9 * k, Y(-24)), (x - 9 * k, Y(-24))], fill=cor)
        d.ellipse([x - 16 * k, Y(-34), x + 16 * k, Y(-6)], fill=cor)
        for n, (dx, dy) in enumerate(((120, 2), (100, -10), (70, -20))):   # dedos longos com unha
            tx, ty = X(dx), Y(dy)
            d.line([(x, Y(-16)), (tx, ty)], fill=cor, width=int((9 - n * 2) * k))
            d.polygon([(tx, ty - 5 * k), (X(dx + 22), ty + 6 * k), (tx, ty + 4 * k)], fill=cor)
        d.polygon([(X(-24), Y(-16)), (X(-44), Y(2)), (X(-16), Y(-4))], fill=cor)   # esporão
        return
    if tipo == "descalco":
        d.rectangle([x - 15 * k, Y0 - 10, x + 15 * k, Y(-30)], fill=cor)
        d.polygon([(X(-26), y), (X(-26), Y(-34)), (X(14), Y(-40)), (X(92), Y(-12)), (X(96), y)], fill=cor)
        for n in range(4):
            cx = X(80 + n * 8); d.ellipse([cx - 7 * k, Y(-14 + n * 2), cx + 7 * k, y], fill=cor)
        return
    d.rectangle([x - 22 * k, Y0 - 10, x + 22 * k, Y(-44)], fill=cor)                 # calça
    d.rectangle([x - 26 * k, Y(-70), x + 26 * k, Y(-40)], fill=cor)                  # barra
    a, b = sorted((X(-34), X(108)))
    d.rounded_rectangle([a, Y(-50), b, y], int(18 * k), fill=cor)
    a, b = sorted((X(-34), X(112)))
    d.rectangle([a, Y(-8), b, y], fill=cor)                                          # sola


def frame(ep, shot, t):
    rel = t - shot["start"]; dur = max(0.001, shot["end"] - shot["start"])
    luz = list(shot.get("luz", [210, 176, 120]))
    flick = 1.0
    if shot.get("piscar"):
        s = math.sin(t * 23.0) + math.sin(t * 7.3 + 1.0)
        flick = 0.25 if s > 1.55 else (0.75 if s > 1.2 else 1.0)
    img = _fundo(tuple(int(c * flick) for c in luz)).copy()
    tipo = shot.get("pes", "sapato"); facing = shot.get("facing", 1); cor = tuple(shot.get("cor", (6, 6, 8)))
    x = _x(shot, rel, dur)
    vx = (_x(shot, rel + 0.05, dur) - _x(shot, max(0.0, rel - 0.05), dur)) / 0.1
    if abs(vx) > 15: facing = 1 if vx > 0 else -1
    fy = Y1 - 18
    andando = abs(vx) > 25
    fase = x / PASSO * math.pi
    pes = []
    for k, off in enumerate((-90, 90)):          # pé de trás e pé da frente
        if andando: lift = max(0.0, math.sin(fase + k * math.pi)) * 60
        else: lift = max(0.0, math.sin(t * 1.3 + k * math.pi) - 0.75) * 40   # muda o peso de um pé para o outro
        pes.append((x + off, lift))
    # sombras das pernas vindo na direção da câmera (a luz está atrás delas)
    som = Image.new("L", (W, H), 0); ds = ImageDraw.Draw(som)
    for px, lift in pes:
        if -300 < px < W + 300:
            cx = W / 2; ab = (px - cx) * 0.9
            ds.polygon([(px - 44, Y1), (px + 44, Y1), (px + 130 + ab, H), (px - 130 + ab, H)], fill=int(200 * (1 - lift / 140)))
    img.paste((4, 4, 6), (0, 0), fast_blur(som, 10))
    d = ImageDraw.Draw(img)
    for px, lift in pes: _pe(d, px, fy, facing, tipo, lift, cor)
    # a porta por cima da parte de cima das pernas
    img.paste(_fundo(tuple(int(c * flick) for c in luz)).crop((0, 0, W, Y0)), (0, 0))
    # câmera: aproximação lenta e tremida de leve
    z = 1.02 + 0.06 * ease(c01(rel / dur))
    hh = shot.get("handheld", 4)
    jx = math.sin(t * 1.7) * hh + math.sin(t * 3.1 + 1) * hh * 0.5; jy = math.sin(t * 1.3 + 2) * hh * 0.6
    cw, ch = W / z, H / z
    x0 = min(W - cw, max(0.0, (W - cw) / 2 + jx)); y0 = min(H - ch, max(0.0, (Y1 - ch * Y1 / H) + jy))
    return crop_zoom(img, x0, y0, x0 + cw, y0 + ch, size=(W, H))


def sons(ep, shot):
    """Um "step" a cada passada enquanto os pés andam."""
    out = []; dur = max(0.001, shot["end"] - shot["start"]); prev = None
    n = int(dur * 30)
    for i in range(n + 1):
        rel = i / 30; p = math.floor(_x(shot, rel, dur) / PASSO)
        if prev is not None and p != prev: out.append({"t": shot["start"] + rel, "name": "step", "gain": 0.7})
        prev = p
    return out
