
"""Rig de personagem lo-fi: emoções, poses, piscar, respiração, caminhada, cabelo/cachecol, sombra e luz de borda.

Uso:
    spr, anchor = render_char("roberta", view="front", emotion="fear", pose="idle", t=1.2, scale=1.0, light=LIGHTS["night"])
    paste_char(frame, spr, anchor, x, y)
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from .core import OUT

# ---------------- fichas de personagem ----------------
BASE = dict(skin=(236, 236, 230), top=(200, 200, 205), top_style="shirt", legs=(50, 60, 90), shoes=(30, 30, 36),
            hat=None, hat_color=(30, 42, 72), hat_band=(44, 60, 98), hat_stripe=(220, 220, 226),
            hair=None, hair_color=(56, 36, 28), scarf=None, backpack=None, glasses=False, infected=False, scale=1.0,
            eye=(14, 14, 18))
CHARS = {
    "roberta": dict(top=(232, 233, 238), top_style="puffer", legs=(52, 70, 110), hat="beanie", scarf=(214, 120, 52),
                    hair="ponytail", hair_color=(56, 36, 28)),
    "rafa": dict(top=(70, 140, 92), top_style="hoodie", hat="hood", legs=(40, 50, 80), shoes=(200, 50, 44),
                 backpack=(236, 196, 50), scale=0.84),
    "lia": dict(top=(96, 168, 178), top_style="scrubs", legs=(96, 168, 178), shoes=(230, 230, 230), hair="bun",
                hair_color=(40, 28, 24)),
    "valter": dict(skin=(150, 158, 154), top=(112, 86, 66), top_style="torn", legs=(80, 84, 90), shoes=(40, 36, 34),
                   hair="short", hair_color=(170, 170, 170), infected=True),
    "zombie": dict(skin=(146, 154, 150), top=(90, 96, 92), top_style="torn", legs=(64, 66, 72), shoes=(36, 34, 34),
                   infected=True, scale=0.95),
    "soldado": dict(top=(84, 98, 64), top_style="uniform", legs=(74, 86, 56), shoes=(30, 28, 24), hat="helmet",
                    hat_color=(70, 82, 52)),
}
def char_def(name, custom=None):
    d = dict(BASE); d.update(CHARS.get(name, {}))
    if custom: d.update(custom)
    return d

# ---------------- luz por ambiente ----------------
LIGHTS = {
    "night":   dict(key=(0.70, 0.76, 0.98), dir=-0.6, rim=(90, 130, 230), rim_side=1, rim_k=0.9),
    "warm":    dict(key=(1.00, 0.88, 0.74), dir=0.7, rim=(255, 190, 110), rim_side=-1, rim_k=0.8),
    "tv":      dict(key=(0.66, 0.74, 1.00), dir=-1.0, rim=(80, 150, 255), rim_side=-1, rim_k=1.0),
    "dawn":    dict(key=(0.80, 0.82, 0.88), dir=0.3, rim=(220, 200, 190), rim_side=1, rim_k=0.5),
    "red":     dict(key=(0.95, 0.55, 0.55), dir=0.8, rim=(255, 50, 40), rim_side=1, rim_k=1.0),
    "dark":    dict(key=(0.40, 0.42, 0.52), dir=0.0, rim=(70, 90, 160), rim_side=1, rim_k=0.7),
    "flash":   dict(key=(1.00, 1.00, 1.05), dir=0.0, rim=(220, 230, 255), rim_side=1, rim_k=1.0),
    "silhouette": dict(key=(0.18, 0.2, 0.26), dir=0.0, rim=(120, 140, 200), rim_side=1, rim_k=0.6),
}

# ---------------- poses (graus; 0 = para baixo, + = para a direita da tela) ----------------
# braço: (ombro, cotovelo) para esquerdo e direito da tela
POSES = {
    "idle":    ((-8, 6), (8, -6)),
    "point":   ((-8, 6), (92, 0)),
    "reach":   ((-8, 6), (72, 14)),
    "pull":    ((-90, 0), (8, -6)),
    "knock":   ((-8, 6), (150, -70)),
    "knock2":  ((-8, 6), (120, -40)),
    "phone":   ((-8, 6), (28, 132)),
    "hold":    ((-8, 6), (40, 70)),
    "scared":  ((-40, -125), (40, 125)),
    "hands_up": ((-150, 10), (150, -10)),
    "wave":    ((-8, 6), (160, 20)),
    "cross":   ((-8, 6), (8, -6)),     # desenhado à parte
    "forward": ((-8, 6), (8, -6)),     # desenhado à parte (braços para a câmera)
    "sit":     ((-14, 40), (14, -40)),
    "crouch":  ((-30, 60), (30, -60)),
    "run":     ((-8, 6), (8, -6)),
}
EMOTIONS = ("neutral", "fear", "shock", "angry", "sad", "determined", "happy", "suspicious")

CW, CH = 480, 760          # tela 2x
HIP_Y, FEET_Y = 480, 690

def _seg(p, ang, L):
    a = math.radians(ang); return (p[0] + L * math.sin(a), p[1] + L * math.cos(a))

def _limb(d, pts, col, w):
    """Membro grosso com contorno e juntas arredondadas."""
    for c, ww in ((OUT, w + 9), (col + (255,), w)):
        d.line(pts, fill=c, width=ww, joint="curve")
        for p in (pts[0], pts[-1]):
            d.ellipse([p[0] - ww / 2, p[1] - ww / 2, p[0] + ww / 2, p[1] + ww / 2], fill=c)

def _hand(d, p, skin, r=19):
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=skin + (255,), outline=OUT, width=4)

def _blink(t, seed):
    r = random.Random(seed)
    period = r.uniform(3.0, 4.6); off = r.uniform(0, period)
    ph = (t + off) % period
    return ph < 0.11

def _backout(x, c=1.6):
    x = max(0.0, min(1.0, x)); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def _draw(cd, view, facing, emotion, pose, t, walk, run, look, seed, sway_k, breath_k, mouth=0.0, talk=0.0,
          pose_prev=None, pk=1.0, blink_force=False):
    if pose_prev and pk < 1.0 and pk < 0.5: draw_pose = pose_prev
    else: draw_pose = pose

    im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    skin, top = cd["skin"], cd["top"]
    inf = cd["infected"]
    cx = CW / 2
    # --- ciclo de caminhada / corrida / respiração ---
    amp = 1.0 if not walk else (1.0 if not run else 1.6)
    ph = (t * (1.9 if run else 1.25) + seed * 0.13) % 1.0 if walk else 0.0
    s = math.sin(2 * math.pi * ph)
    bob = -abs(math.cos(2 * math.pi * ph)) * (14 if run else 8) if walk else 0
    breath = math.sin(t * 2 * math.pi / (3.2 if not inf else 2.4) + seed) * breath_k
    hunch = 14 if inf else 0
    sit = draw_pose == "sit"; crouch = draw_pose == "crouch"
    hip_y = HIP_Y + bob + (110 if sit else 0) + (70 if crouch else 0)
    torso_top = hip_y - 238 + hunch - breath * 4
    sh_y = torso_top + 52
    neck = (cx + (hunch * 0.8 if view == "side" else 0), torso_top + 6)
    head_c = (neck[0] + (6 * math.sin(t * 1.3 + seed) if inf else 0), neck[1] - 74 + bob * 0.2 - breath * 2)
    if view == "side": head_c = (head_c[0] + 18 + hunch * 0.6, head_c[1])
    if talk > 0: head_c = (head_c[0] + math.sin(t * 6.3 + seed) * 6 * talk, head_c[1] - abs(math.sin(t * 8.1)) * 6 * talk)
    # --- pernas ---
    if view == "side":
        hips = [(cx, hip_y), (cx, hip_y)]
        legA = [s * 30 * amp, -s * 30 * amp]
        kneeB = [max(0, -s) * 45 * amp, max(0, s) * 45 * amp]
    else:
        hips = [(cx - 30, hip_y), (cx + 30, hip_y)]
        legA = [-4 + (s * 5 if walk else 0), 4 - (s * 5 if walk else 0)]
        kneeB = [0, 0]
    leg_pts = []
    for i in range(2):
        hp = hips[i]
        if sit:
            kn = (hp[0] + (-46 if i == 0 else 46) * (0.3 if view != "side" else 0) + (60 if view == "side" else 0), hp[1] + 24)
            ft = (kn[0] + (0 if view != "side" else 10), kn[1] + 96)
        elif crouch:
            kn = (hp[0] + (-50 if i == 0 else 50), hp[1] + 60); ft = (hp[0] + (-28 if i == 0 else 28), hp[1] + 140)
        else:
            if view == "side":
                kn = _seg(hp, legA[i], 102); ft = _seg(kn, legA[i] - kneeB[i], 100)
            else:
                lift = (max(0, s if i == 0 else -s) * 22) if walk else 0
                kn = _seg(hp, legA[i], 102 - lift * 0.4); ft = _seg(kn, legA[i], 100 - lift)
        leg_pts.append((hp, kn, ft))
    # --- braços ---
    pa = POSES.get(pose, POSES["idle"])
    if pose_prev and pk < 1.0:
        pb = POSES.get(pose_prev, POSES["idle"]); bk = _backout(pk)
        pa = tuple((pb[i][0] + (pa[i][0] - pb[i][0]) * bk, pb[i][1] + (pa[i][1] - pb[i][1]) * bk) for i in range(2))
    sh = [(cx - 76, sh_y), (cx + 76, sh_y)] if view != "side" else [(cx + hunch * 0.6, sh_y), (cx + hunch * 0.6, sh_y)]
    arms = []
    for i in range(2):
        a_sh, a_el = pa[i]
        if talk > 0 and draw_pose in ("idle", "cross") and i == 1 and not walk:
            a_el += math.sin(t * 5.2 + seed) * 22 * talk; a_sh += math.sin(t * 3.1 + seed) * 10 * talk
        if walk and pose in ("idle", "run"):
            sw = (-s if i == 0 else s) * (24 if view == "side" else 10) * amp
            a_sh = a_sh + sw if view == "side" else a_sh + sw * 0.3
            a_el = a_el + (abs(sw) * 0.8 if view == "side" else 0)
        if inf and pose in ("idle", "forward") and view == "side":
            a_sh, a_el = 80, 10
        if draw_pose == "knock" and int(t * 6) % 2 == 1 and i == 1: a_sh, a_el = POSES["knock2"][1]
        if view == "side":
            a_sh = a_sh if i == 1 else -a_sh * 0.6 + (s * 24 if walk else 0)
            a_sh = abs(a_sh) if pose in ("point", "reach", "hold", "phone", "forward") and i == 1 else a_sh
        el = _seg(sh[i], a_sh, 86); hd = _seg(el, a_sh + a_el, 80)
        arms.append((sh[i], el, hd))
    legc, shoe, topc = cd["legs"], cd["shoes"], top
    back = view == "back"; side = view == "side"
    dark = lambda c, k=0.75: tuple(int(v * k) for v in c)

    # --- itens atrás do corpo ---
    hr = 84
    if cd["hat"] == "hood" and not back:
        d.ellipse([head_c[0] - 100, head_c[1] - 100, head_c[0] + 100, head_c[1] + 100], fill=dark(topc, 0.88) + (255,), outline=OUT, width=6)
    if cd["hair"] == "ponytail" and not back:
        sw = math.sin(t * 2.6 + seed) * 10 * sway_k + (s * 10 if walk else 0)
        px = head_c[0] + (66 if not side else -70)
        d.ellipse([px - 24 + sw * 0.3, head_c[1] - 10, px + 26 + sw, head_c[1] + 110], fill=cd["hair_color"] + (255,), outline=OUT, width=5)
    if cd["hair"] == "long" and not back:
        d.rounded_rectangle([head_c[0] - 96, head_c[1] - 40, head_c[0] + 96, head_c[1] + 130], 50, fill=cd["hair_color"] + (255,), outline=OUT, width=5)
    if cd["backpack"] and side:
        d.rounded_rectangle([cx - 110, torso_top + 30, cx - 30, torso_top + 200], 26, fill=cd["backpack"] + (255,), outline=OUT, width=6)
    # braço de trás (lado)
    if side:
        a = arms[0]; _limb(d, [a[0], a[1], a[2]], dark(topc), 42); _hand(d, a[2], dark(skin, 0.85))
    if back or (not side and pose not in ("cross", "forward")):
        pass
    # --- pernas ---
    order = [0, 1] if not side else [0, 1]
    for i in order:
        hp, kn, ft = leg_pts[i]
        col = legc if not (side and i == 0) else dark(legc)
        _limb(d, [hp, kn, ft], col, 50)
        fx = 26 if side else 0
        d.rounded_rectangle([ft[0] - 36 + fx * 0.3, ft[1] - 16, ft[0] + 36 + fx, ft[1] + 22], 18,
                            fill=(shoe if not (side and i == 0) else dark(shoe)) + (255,), outline=OUT, width=6)
    # --- tronco ---
    tw = 164 if not side else 124
    tx0 = cx - tw / 2 + (hunch * 0.5 if side else 0)
    sq = breath * 3
    d.rounded_rectangle([tx0, torso_top - sq, tx0 + tw, hip_y + 12], 62, fill=topc + (255,), outline=OUT, width=6)
    st = cd["top_style"]
    if st == "puffer":
        for k in range(3):
            y = torso_top + 62 + k * 52
            d.arc([tx0 + 8, y - 34, tx0 + tw - 8, y + 16], 20, 160, fill=dark(topc, 0.8) + (255,), width=5)
    elif st == "hoodie" and not back and not side:
        d.rounded_rectangle([cx - 46, hip_y - 86, cx + 46, hip_y - 30], 16, outline=dark(topc, 0.75) + (255,), width=5)
        d.line([(cx - 14, torso_top + 20), (cx - 18, torso_top + 70)], fill=(230, 230, 230, 255), width=5)
        d.line([(cx + 14, torso_top + 20), (cx + 18, torso_top + 70)], fill=(230, 230, 230, 255), width=5)
    elif st == "torn":
        r = random.Random(seed + 3)
        for _ in range(5):
            x0 = r.uniform(tx0 + 20, tx0 + tw - 30); y0 = r.uniform(torso_top + 40, hip_y - 30)
            d.polygon([(x0, y0), (x0 + 24, y0 + 8), (x0 + 8, y0 + 32), (x0 + 16, y0 + 14)], fill=dark(topc, 0.45) + (255,))
    elif st == "scrubs" and not back:
        d.polygon([(cx - 40, torso_top + 4), (cx, torso_top + 60), (cx + 40, torso_top + 4)], fill=dark(topc, 0.8) + (255,))
    elif st == "uniform":
        d.rectangle([tx0 + 20, torso_top + 80, tx0 + tw - 20, torso_top + 96], fill=dark(topc, 0.7) + (255,))
    if cd["backpack"]:
        if back:
            d.rounded_rectangle([cx - 70, torso_top + 22, cx + 70, torso_top + 214], 34, fill=cd["backpack"] + (255,), outline=OUT, width=6)
            d.rounded_rectangle([cx - 40, torso_top + 100, cx + 40, torso_top + 170], 16, fill=dark(cd["backpack"], 0.88) + (255,), outline=OUT, width=4)
        elif not side:
            for xx in (cx - 50, cx + 50): d.line([(xx, torso_top + 10), (xx, torso_top + 190)], fill=cd["backpack"] + (255,), width=16)
    # --- braços da frente ---
    if draw_pose == "cross" and not back and not side:
        d.rounded_rectangle([cx - 104, sh_y + 40, cx + 104, sh_y + 100], 28, fill=topc + (255,), outline=OUT, width=6)
        _hand(d, (cx - 92, sh_y + 70), skin); _hand(d, (cx + 92, sh_y + 70), skin)
    elif (draw_pose == "forward" or (inf and draw_pose == "idle")) and not back and not side:
        for sx, ex in ((cx - 76, cx - 66), (cx + 76, cx + 66)):
            _limb(d, [(sx, sh_y), (ex, sh_y + 46)], topc, 46)
            _hand(d, (ex + (8 if ex > cx else -8), sh_y + 60), skin, 25)
    else:
        rng_arms = [1] if side else [0, 1]
        for i in rng_arms:
            a = arms[i]; _limb(d, [a[0], a[1], a[2]], topc, 44); _hand(d, a[2], skin)
            if draw_pose == "phone" and i == 1:
                d.rounded_rectangle([a[2][0] - 18, a[2][1] - 40, a[2][0] + 18, a[2][1] + 20], 6, fill=(20, 20, 26, 255), outline=OUT, width=3)
            if draw_pose == "hold" and i == 1:
                d.rounded_rectangle([a[2][0] - 12, a[2][1] - 10, a[2][0] + 46, a[2][1] + 12], 6, fill=(60, 60, 66, 255), outline=OUT, width=3)
    # --- cachecol ---
    if cd["scarf"]:
        sc = cd["scarf"]
        d.rounded_rectangle([cx - 82 + (hunch * 0.5 if side else 0), torso_top - 22, cx + 82, torso_top + 32], 24, fill=sc + (255,), outline=OUT, width=6)
        sw = math.sin(t * 3.1 + seed) * 8 * sway_k + (s * 14 if walk else 0)
        if not back:
            tx = cx - 50 if not side else cx - 70
            d.polygon([(tx, torso_top + 20), (tx + 40, torso_top + 20), (tx + 44 + sw, torso_top + 110), (tx + 4 + sw, torso_top + 112)],
                      fill=dark(sc, 0.92) + (255,), outline=OUT)
            for k in range(3):
                yy = torso_top + 48 + k * 20
                d.line([(tx + 4 + sw * (yy - torso_top) / 110, yy), (tx + 40 + sw * (yy - torso_top) / 110, yy)], fill=dark(sc, 0.75) + (255,), width=3)
    # --- cabeça ---
    hx, hy = head_c
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=skin + (255,), outline=OUT, width=7)
    # sombra suave no rosto (lado de baixo)
    sh_l = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(sh_l).ellipse([hx - hr + 6, hy - hr * 0.1, hx + hr - 6, hy + hr - 6], fill=40)
    face = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); face.putalpha(sh_l.filter(ImageFilter.GaussianBlur(14)))
    head_mask = Image.new("L", (CW, CH), 0); ImageDraw.Draw(head_mask).ellipse([hx - hr + 7, hy - hr + 7, hx + hr - 7, hy + hr - 7], fill=255)
    face.putalpha(ImageChops.multiply(face.split()[3], head_mask)); im.alpha_composite(face); d = ImageDraw.Draw(im)
    # cabelo
    if cd["hair"] == "short":
        d.chord([hx - hr, hy - hr, hx + hr, hy + hr * 0.5], 190, 350, fill=cd["hair_color"] + (255,))
    if cd["hair"] == "bun":
        d.chord([hx - hr, hy - hr, hx + hr, hy + hr * 0.4], 180, 360, fill=cd["hair_color"] + (255,), outline=OUT, width=5)
        d.ellipse([hx - 34, hy - hr - 46, hx + 34, hy - hr + 18], fill=cd["hair_color"] + (255,), outline=OUT, width=5)
    if back and cd["hair"] in ("ponytail", "long", "bun", "short"):
        d.ellipse([hx - hr + 8, hy - hr + 8, hx + hr - 8, hy + hr - 8], fill=cd["hair_color"] + (255,))
    # chapéus
    if cd["hat"] == "beanie":
        d.chord([hx - 92, hy - 120, hx + 92, hy + 44], 180, 360, fill=cd["hat_color"] + (255,), outline=OUT, width=6)
        d.rounded_rectangle([hx - 95, hy - 52, hx + 95, hy - 18], 16, fill=cd["hat_band"] + (255,), outline=OUT, width=5)
        for yy in (hy - 98, hy - 78): d.line([(hx - 66, yy), (hx + 66, yy)], fill=cd["hat_stripe"] + (255,), width=8)
        pb = math.sin(t * 2.2 + seed) * 4 * sway_k + (s * 6 if walk else 0)
        d.ellipse([hx - 25 + pb, hy - 148, hx + 25 + pb, hy - 100], fill=cd["hat_stripe"] + (255,), outline=OUT, width=5)
    elif cd["hat"] == "cap":
        d.chord([hx - 88, hy - 96, hx + 88, hy + 40], 180, 360, fill=cd["hat_color"] + (255,), outline=OUT, width=6)
        if not back: d.rounded_rectangle([hx - 20 if not side else hx, hy - 40, hx + 110, hy - 20], 10, fill=cd["hat_color"] + (255,), outline=OUT, width=5)
    elif cd["hat"] == "helmet":
        d.chord([hx - 96, hy - 116, hx + 96, hy + 28], 180, 360, fill=cd["hat_color"] + (255,), outline=OUT, width=6)
        d.rectangle([hx - 100, hy - 48, hx + 100, hy - 34], fill=tuple(int(v * 0.7) for v in cd["hat_color"]) + (255,))
    elif cd["hat"] == "hood":
        if back: d.ellipse([hx - 92, hy - 92, hx + 92, hy + 92], fill=topc + (255,), outline=OUT, width=6)
        else: d.arc([hx - 98, hy - 98, hx + 98, hy + 98], 160, 380, fill=dark(topc, 0.88) + (255,), width=24)
    if cd["hair"] == "ponytail" and back:
        sw = math.sin(t * 2.6 + seed) * 12 * sway_k + (s * 12 if walk else 0)
        d.ellipse([hx - 28 + sw * 0.4, hy + 24, hx + 28 + sw, hy + 150], fill=cd["hair_color"] + (255,), outline=OUT, width=5)
    # --- rosto ---
    if not back:
        fx = hx + look + (34 if side else 0)
        eyes = [(fx - 30, hy + 16), (fx + 30, hy + 16)] if not side else [(fx + 6, hy + 16)]
        blink = (_blink(t, seed) or blink_force) and not inf
        if inf:
            glow = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
            for (x, y) in eyes: gd.ellipse([x - 30, y - 26, x + 30, y + 26], fill=(255, 255, 235, 120))
            im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10))); d = ImageDraw.Draw(im)
            for (x, y) in eyes: d.ellipse([x - 14, y - 12, x + 14, y + 12], fill=(252, 252, 240, 255))
            d.line([(hx - 40, hy + 50), (hx - 10, hy + 46), (hx + 10, hy + 54), (hx + 36, hy + 48)], fill=(80, 86, 84, 255), width=5)
        else:
            ew, eh = {"neutral": (10, 13), "fear": (12, 16), "shock": (14, 17), "angry": (10, 8), "sad": (9, 11),
                      "determined": (10, 10), "happy": (10, 10), "suspicious": (10, 7)}.get(emotion, (10, 13))
            ec = cd["eye"]
            for i, (x, y) in enumerate(eyes):
                if blink:
                    d.line([(x - ew, y), (x + ew, y)], fill=ec + (255,), width=5)
                elif emotion == "happy":
                    d.arc([x - 12, y - 8, x + 12, y + 14], 200, 340, fill=ec + (255,), width=6)
                else:
                    d.ellipse([x - ew, y - eh, x + ew, y + eh], fill=ec + (255,))
                    if emotion in ("fear", "shock"):
                        d.ellipse([x - ew + 4, y - eh + 3, x - ew + 9, y - eh + 8], fill=(255, 255, 255, 255))
                # sobrancelhas
                side_k = -1 if (i == 0 and not side) else 1
                by = y - 27
                if emotion == "fear" or emotion == "sad":
                    p0, p1 = (x - 16 * side_k * -1, by + 6), (x + 16 * side_k * -1, by - 6)
                    p0, p1 = ((x - 16, by + (6 if side_k > 0 else -6)), (x + 16, by + (-6 if side_k > 0 else 6)))
                    p0, p1 = ((x - 16, by - 6), (x + 16, by + 6)) if side_k < 0 else ((x - 16, by + 6), (x + 16, by - 6))
                    p0, p1 = (p1, p0) if False else (p0, p1)
                    # interno sobe
                    if side_k < 0: p0, p1 = (x - 16, by + 6), (x + 14, by - 8)
                    else: p0, p1 = (x - 14, by - 8), (x + 16, by + 6)
                elif emotion == "angry" or emotion == "determined":
                    k = 10 if emotion == "angry" else 4
                    if side_k < 0: p0, p1 = (x - 16, by - k), (x + 14, by + k)
                    else: p0, p1 = (x - 14, by + k), (x + 16, by - k)
                elif emotion == "shock":
                    p0, p1 = (x - 15, by - 10), (x + 15, by - 12)
                elif emotion == "suspicious":
                    p0, p1 = ((x - 15, by + 4), (x + 15, by + 4)) if side_k < 0 else ((x - 15, by - 8), (x + 15, by - 2))
                else:
                    p0, p1 = (x - 14, by - 2), (x + 14, by - 2)
                if emotion != "neutral" or True:
                    d.line([p0, p1], fill=ec + (255,), width=6)
            # boca só em emoções fortes
            mx, my = fx + (8 if side else 0), hy + 56
            if emotion == "shock":
                d.ellipse([mx - 10, my - 12, mx + 10, my + 12], fill=ec + (255,))
            elif emotion == "fear":
                d.line([(mx - 16, my), (mx - 8, my - 5), (mx, my), (mx + 8, my - 5), (mx + 16, my)], fill=ec + (255,), width=4)
                # gota de suor
                d.polygon([(hx + 62, hy - 40), (hx + 54, hy - 18), (hx + 70, hy - 18)], fill=(170, 210, 250, 255))
                d.ellipse([hx + 53, hy - 26, hx + 71, hy - 8], fill=(170, 210, 250, 255))
            elif emotion == "happy":
                d.arc([mx - 16, my - 14, mx + 16, my + 10], 20, 160, fill=ec + (255,), width=5)
            elif emotion == "angry":
                d.line([(mx - 12, my + 2), (mx + 12, my + 2)], fill=ec + (255,), width=5)
            if mouth > 0.06:
                mh = 5 + 22 * mouth; mw = 13 + 7 * mouth
                d.ellipse([mx - mw, my - mh * 0.45, mx + mw, my + mh * 0.55], fill=(40, 18, 22, 255), outline=ec + (255,), width=4)
                if mouth > 0.45: d.chord([mx - mw + 5, my + mh * 0.05, mx + mw - 5, my + mh * 0.5], 0, 180, fill=(190, 80, 90, 255))
            if cd["glasses"]:
                for (x, y) in eyes: d.ellipse([x - 22, y - 20, x + 22, y + 20], outline=OUT, width=5)
                if len(eyes) == 2: d.line([(eyes[0][0] + 22, eyes[0][1]), (eyes[1][0] - 22, eyes[1][1])], fill=OUT, width=5)
    return im, (CW / 2, FEET_Y + 22 + (0 if not sit else 0))

def _shade(im, light):
    """Sombra suave no corpo (lado oposto à luz), tingimento ambiente e luz de borda."""
    arr = np.asarray(im).astype(np.float32)
    h, w = arr.shape[:2]
    A = arr[..., 3] / 255.0
    xs = np.linspace(-1, 1, w)[None, :]
    ys = np.linspace(0, 1, h)[:, None]
    lx = light.get("dir", 0.0)
    shade = 1 - 0.30 * np.clip(-lx * xs, 0, 1) - 0.12 * ys
    key = np.array(light.get("key", (1, 1, 1)))
    arr[..., :3] *= shade[..., None] * key
    # borda
    a_img = Image.fromarray((A * 255).astype("uint8"))
    er = np.asarray(a_img.filter(ImageFilter.MinFilter(7))).astype(np.float32) / 255.0
    edge = np.clip(A - er, 0, 1)
    edge = np.asarray(Image.fromarray((edge * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0
    side = np.clip(light.get("rim_side", 1) * xs * 1.4 + 0.2, 0, 1)
    rim = edge * side * light.get("rim_k", 0.0)
    arr[..., :3] += rim[..., None] * np.array(light.get("rim", (255, 255, 255))) * 0.9
    arr[..., :3] = np.clip(arr[..., :3], 0, 255)
    return Image.fromarray(arr.astype("uint8"), "RGBA")

_CACHE = {}
def render_char(name, view="front", emotion="neutral", pose="idle", t=0.0, scale=1.0, light=None, walk=False, run=False,
                look=0, facing=1, custom=None, seed=None, sway=1.0, breath=1.0, mouth=0.0, talk=0.0, pose_prev=None, pk=1.0,
                blink_force=False):
    """Devolve (sprite RGBA, (ax, ay)) — ancorado nos pés."""
    cd = char_def(name, custom)
    seed = seed if seed is not None else (sum(map(ord, name)) % 97)
    light = light or LIGHTS["night"]
    qt = round(t * 15) / 15 if (walk or sway or breath) else 0
    key = (name, view, emotion, pose, qt, round(scale * cd["scale"], 3), id(light) if not isinstance(light, dict) else tuple(sorted((k, str(v)) for k, v in light.items())),
           walk, run, int(look), facing, seed, str(custom), round(mouth * 6), round(talk * 4), pose_prev if pk < 1 else None, round(pk * 10), blink_force)
    if key in _CACHE: return _CACHE[key]
    im, anc = _draw(cd, view, facing, emotion, pose, qt, walk, run, look, seed, sway, breath, round(mouth * 6) / 6, round(talk * 4) / 4,
                    pose_prev, round(pk * 10) / 10, blink_force)
    k = 0.5 * scale * cd["scale"]
    nw, nh = max(2, int(CW * k)), max(2, int(CH * k))
    im = im.resize((nw, nh), Image.LANCZOS)
    im = _shade(im, light)
    if facing < 0: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    res = (im, (nw / 2, anc[1] * k))
    if len(_CACHE) > 4000: _CACHE.clear()
    _CACHE[key] = res
    return res

def shadow(frame, x, y, width, alpha=110, dx=0, stretch=1.0):
    """Sombra projetada no chão (elipse desfocada)."""
    w = width * stretch; h = width * 0.18
    m = Image.new("L", (int(w * 2 + 60), int(h * 2 + 60)), 0)
    ImageDraw.Draw(m).ellipse([30, 30, 30 + w * 2, 30 + h * 2], fill=alpha)
    m = m.filter(ImageFilter.GaussianBlur(max(2, width * 0.08)))
    frame.paste((0, 0, 0), (int(x - w - 30 + dx), int(y - h - 30)), m)

def reflection(frame, spr, anchor, x, y, alpha=0.28, blur=3):
    """Reflexo no chão molhado."""
    r = spr.transpose(Image.FLIP_TOP_BOTTOM)
    a = r.split()[3].point(lambda v: int(v * alpha))
    grad = Image.linear_gradient("L").resize(r.size).point(lambda v: 255 - v)
    a = ImageChops.multiply(a, grad); r.putalpha(a)
    r = r.filter(ImageFilter.GaussianBlur(blur))
    frame.paste(r, (int(x - anchor[0]), int(y + (spr.height - anchor[1]))), r)

def paste_char(frame, spr, anchor, x, y):
    frame.paste(spr, (int(x - anchor[0]), int(y - anchor[1])), spr)
