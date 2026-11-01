
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
            hair=None, hair_color=(56, 36, 28), scarf=None, backpack=None, glasses=False, infected=False, scale=1.0, body="normal",
            eye=(14, 14, 18), bottom="pants", skirt=None, tights=None, sleeves="long", inner=(235, 235, 235), facial=None,
            facial_color=None, acc=(), ghost=False, cape=None, tie=(170, 40, 40))
SKINS = {"palido": (236, 236, 230), "claro": (244, 216, 192), "medio": (220, 176, 138), "moreno": (176, 122, 86),
         "escuro": (112, 74, 52), "oliva": (198, 164, 116), "verde": (150, 190, 130), "azul": (150, 170, 230)}
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
    "zombie_corredor": dict(skin=(150, 150, 146), top=(110, 70, 66), top_style="torn", legs=(60, 60, 70), shoes=(30, 30, 30), infected=True),
    "zombie_rastejante": dict(skin=(140, 148, 144), top=(80, 86, 80), top_style="torn", legs=(56, 58, 62), shoes=(30, 30, 30), infected=True, body="thin"),
    "zombie_enfermeiro": dict(skin=(148, 156, 152), top=(120, 150, 150), top_style="scrubs", legs=(120, 150, 150), shoes=(200, 200, 200),
                              hair="bun", hair_color=(90, 80, 70), infected=True),
    "zombie_policial": dict(skin=(146, 152, 150), top=(50, 60, 92), top_style="uniform", legs=(40, 46, 70), shoes=(20, 20, 24),
                            hat="cap", hat_color=(40, 48, 74), infected=True),
    # ---------- presets para outros gêneros ----------
    "detetive": dict(top=(150, 120, 80), top_style="trench", inner=(220, 220, 210), legs=(60, 60, 70), hat="fedora", hat_color=(70, 60, 50),
                     hair="short", hair_color=(60, 44, 34), facial="stubble", skin="claro"),
    "cientista": dict(top=(240, 242, 245), top_style="labcoat", inner=(90, 130, 170), legs=(70, 70, 80), hair="curly", hair_color=(80, 60, 50),
                      glasses=True, skin="medio"),
    "estudante": dict(top=(240, 240, 240), top_style="tshirt", sleeves="short", legs=(40, 60, 110), backpack=(200, 60, 60), hair="spiky",
                      hair_color=(30, 26, 24), skin="moreno", scale=0.9),
    "estudante2": dict(top=(60, 90, 160), top_style="sweater", bottom="skirt", skirt=(70, 70, 90), tights=(30, 30, 40), hair="pigtails",
                       hair_color=(140, 80, 50), acc=("bow",), skin="claro", scale=0.88),
    "executiva": dict(top=(50, 54, 70), top_style="suit", bottom="skirt", skirt=(50, 54, 70), tights=(60, 50, 50), hair="bob",
                      hair_color=(30, 24, 22), acc=("earrings", "necklace"), skin="escuro"),
    "executivo": dict(top=(44, 48, 60), top_style="suit", legs=(44, 48, 60), hair="short", hair_color=(40, 30, 26), facial="beard", skin="oliva"),
    "medica": dict(top=(240, 242, 245), top_style="labcoat", inner=(96, 168, 178), legs=(96, 168, 178), hair="long", hair_color=(90, 50, 30),
                   acc=("stethoscope",), skin="medio"),
    "policial": dict(top=(50, 60, 92), top_style="uniform", legs=(40, 46, 70), hat="cap", hat_color=(40, 48, 74), acc=("badge",), skin="moreno"),
    "roqueiro": dict(top=(30, 30, 34), top_style="leather", legs=(40, 40, 60), hair="mohawk", hair_color=(200, 40, 60), acc=("sunglasses", "earrings"),
                     skin="claro"),
    "vovo": dict(top=(170, 110, 130), top_style="sweater", bottom="skirt", skirt=(90, 70, 80), tights=(200, 180, 170), hair="bun",
                 hair_color=(220, 220, 225), glasses=True, body="old", skin="claro"),
    "vovo2": dict(top=(120, 100, 70), top_style="sweater", legs=(80, 70, 60), hair="bald", facial="mustache", facial_color=(220, 220, 225),
                  body="old", hat="tophat", hat_color=(40, 34, 30), skin="medio"),
    "crianca": dict(top=(240, 190, 60), top_style="tshirt", sleeves="short", bottom="shorts", legs=(60, 90, 150), hair="afro", hair_color=(30, 22, 18),
                    body="child", skin="escuro"),
    "bruxa": dict(top=(60, 40, 80), top_style="dress", hat="witch", hat_color=(40, 26, 56), hair="long", hair_color=(30, 30, 30),
                  cape=(30, 20, 40), skin="verde"),
    "rainha": dict(top=(170, 40, 60), top_style="dress", hat="crown", hat_color=(230, 190, 60), hair="braids", hair_color=(60, 36, 26),
                   cape=(120, 20, 40), acc=("necklace",), skin="moreno"),
    "chef": dict(top=(245, 245, 245), top_style="chef", legs=(40, 40, 46), hat="chef", hat_color=(245, 245, 245), facial="mustache", skin="claro"),
    "cowboy": dict(top=(170, 80, 60), top_style="shirt", legs=(60, 80, 130), hat="cowboy", hat_color=(130, 90, 50), facial="beard",
                   facial_color=(90, 60, 40), acc=("bandana",), skin="claro"),
    "fantasma": dict(top=(220, 230, 250), top_style="dress", skin=(230, 238, 255), ghost=True, eye=(40, 60, 120)),
    "dj": dict(top=(120, 60, 200), top_style="hoodie", legs=(30, 30, 40), hair="braids", hair_color=(20, 18, 16), acc=("headphones",), skin="escuro"),
    "pirata": dict(top=(240, 230, 210), top_style="shirt", legs=(60, 40, 30), hat="bandana_hat", hat_color=(180, 30, 30), facial="beard",
                   facial_color=(40, 30, 20), acc=("eyepatch", "earrings"), skin="oliva"),
    "soldado": dict(top=(84, 98, 64), top_style="uniform", legs=(74, 86, 56), shoes=(30, 28, 24), hat="helmet",
                    hat_color=(70, 82, 52)),
}
def _col(v, default=None):
    if v is None: return default
    if isinstance(v, str): return SKINS.get(v, default)
    return tuple(int(x) for x in v)
def char_def(name, custom=None):
    d = dict(BASE); d.update(CHARS.get(name, {}))
    if custom: d.update(custom)
    d["skin"] = _col(d["skin"], (236, 236, 230))
    for k in ("top", "legs", "shoes", "hat_color", "hair_color", "scarf", "backpack", "skirt", "tights", "inner", "facial_color", "cape", "tie", "eye"):
        if d.get(k) is not None and not isinstance(d[k], str): d[k] = tuple(int(x) for x in d[k])
    d["acc"] = tuple(d.get("acc") or ())
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
    "jump":    ((-150, 10), (150, -10)),
    "hide":    ((-150, -95), (150, 95)),
    "open_door": ((-8, 6), (80, -8)),
    "remove_bag": ((-8, 6), (24, -30)),
    "fallen":  ((-20, 10), (20, -10)),
    "crawl":   ((-60, 0), (60, 0)),
    "chest":   ((-8, 6), (-35, -75)),       # mão no peito
    "hand_r":  ((-8, 6), (45, -5)),         # mão dada com quem está à direita
    "hand_l":  ((-45, 5), (8, -6)),         # mão dada com quem está à esquerda
    "reach_l": ((-72, -14), (8, -6)),
    "hug":     ((80, -10), (100, -20)),     # abraço (use vista 3q de frente um para o outro)
    "carry":   ((70, -40), (85, -45)),      # carregando alguém no colo
    "push":    ((85, 0), (95, 0)),          # empurrando
}
EMOTIONS = ("neutral", "fear", "shock", "angry", "sad", "determined", "happy", "suspicious", "cry", "panting")

CW, CH = 480, 760          # tela 2x
HIP_Y, FEET_Y = 480, 690

def _seg(p, ang, L):
    a = math.radians(ang); return (p[0] + L * math.sin(a), p[1] + L * math.cos(a))

def _limb(d, pts, col, w):
    """Membro grosso com contorno e juntas arredondadas."""
    w = int(round(w))
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
          pose_prev=None, pk=1.0, blink_force=False, sniff=False, prop=None, viseme=0, gesture=None):
    if pose_prev and pk < 1.0 and pk < 0.5: draw_pose = pose_prev
    else: draw_pose = pose

    im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    skin, top = cd["skin"], cd["top"]
    inf = cd["infected"]
    cx = CW / 2
    bt = cd.get("body", "normal")
    TWK = {"fat": 1.36, "thin": 0.8, "child": 0.92, "tall": 0.96}.get(bt, 1.0)
    LEGK = {"tall": 1.2, "child": 0.7, "old": 0.94}.get(bt, 1.0)
    HEADK = {"child": 1.16}.get(bt, 1.0)
    LIMBK = {"thin": 0.8, "fat": 1.18, "child": 0.92}.get(bt, 1.0)
    HUNCH_ADD = {"old": 26}.get(bt, 0)
    q3 = view == "3q"
    if q3: view = "front"
    if sniff: look = math.sin(t * 2.3 + seed) * 22
    # --- ciclo de caminhada / corrida / respiração ---
    amp = 1.0 if not walk else (1.0 if not run else 1.6)
    ph = (t * (1.9 if run else 1.25) + seed * 0.13) % 1.0 if walk else 0.0
    s = math.sin(2 * math.pi * ph)
    bob = -abs(math.cos(2 * math.pi * ph)) * (14 if run else 8) if walk else 0
    pant = emotion == "panting"
    breath = math.sin(t * 2 * math.pi / ((3.2 if not inf else 2.4) if not pant else 0.8) + seed) * breath_k * (3.2 if pant else 1)
    hunch = (14 if inf else 0) + HUNCH_ADD
    sit = draw_pose == "sit"; crouch = draw_pose in ("crouch", "hide"); jump = draw_pose == "jump"
    hip_y = HIP_Y + bob + (1 - LEGK) * 202 + (110 if sit else 0) + (70 if crouch else 0) + (50 if jump else 0)
    torso_top = hip_y - 238 + hunch - breath * 4
    sh_y = torso_top + 52
    neck = (cx + (hunch * 0.8 if view == "side" else 0), torso_top + 6)
    head_c = (neck[0] + (6 * math.sin(t * 1.3 + seed) if inf else 0), neck[1] - 74 + bob * 0.2 - breath * 2)
    if view == "side": head_c = (head_c[0] + 18 + hunch * 0.6, head_c[1])
    if q3: head_c = (head_c[0] + 14, head_c[1])
    if sniff: head_c = (head_c[0] + math.sin(t * 2.3 + seed) * 16, head_c[1] - 8 - abs(math.sin(t * 4.6)) * 6)
    if gesture == "nod": head_c = (head_c[0], head_c[1] + abs(math.sin(t * 9)) * 12)
    elif gesture == "shake": head_c = (head_c[0] + math.sin(t * 13) * 14, head_c[1]); look = math.sin(t * 13) * 18
    elif gesture == "down": head_c = (head_c[0], head_c[1] + 14)
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
            kn = (hp[0] + (-50 if i == 0 else 50), hp[1] + 60 * LEGK); ft = (hp[0] + (-28 if i == 0 else 28), hp[1] + 140 * LEGK)
        elif jump:
            kn = (hp[0] + (-44 if i == 0 else 44), hp[1] + 66 * LEGK); ft = (hp[0] + (-18 if i == 0 else 18), hp[1] + 118 * LEGK)
        else:
            if view == "side":
                kn = _seg(hp, legA[i], 102 * LEGK); ft = _seg(kn, legA[i] - kneeB[i], 100 * LEGK)
            else:
                lift = (max(0, s if i == 0 else -s) * 22) if walk else 0
                kn = _seg(hp, legA[i], 102 * LEGK - lift * 0.4); ft = _seg(kn, legA[i], 100 * LEGK - lift)
        leg_pts.append((hp, kn, ft))
    # --- braços ---
    pa = POSES.get(pose, POSES["idle"])
    if pose_prev and pk < 1.0:
        pb = POSES.get(pose_prev, POSES["idle"]); bk = _backout(pk)
        pa = tuple((pb[i][0] + (pa[i][0] - pb[i][0]) * bk, pb[i][1] + (pa[i][1] - pb[i][1]) * bk) for i in range(2))
    sh = ([(cx - 76 * TWK, sh_y), (cx + 76 * TWK, sh_y)] if not q3 else [(cx - 58 * TWK, sh_y), (cx + 70 * TWK, sh_y)]) if view != "side" else [(cx + hunch * 0.6, sh_y), (cx + hunch * 0.6, sh_y)]
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
    hr = 84 * HEADK
    if cd["hat"] == "hood" and not back:
        d.ellipse([head_c[0] - 100, head_c[1] - 100, head_c[0] + 100, head_c[1] + 100], fill=dark(topc, 0.88) + (255,), outline=OUT, width=6)
    if cd["hair"] == "ponytail" and not back:
        sw = math.sin(t * 2.6 + seed) * 10 * sway_k + (s * 10 if walk else 0)
        px = head_c[0] + ((66 if not side else -70) if not q3 else -64)
        d.ellipse([px - 24 + sw * 0.3, head_c[1] - 10, px + 26 + sw, head_c[1] + 110], fill=cd["hair_color"] + (255,), outline=OUT, width=5)
    if cd["cape"] and draw_pose not in ("fallen", "crawl"):
        cw_ = math.sin(t * 2.2 + seed) * 16 * sway_k + (s * 22 if walk else 0)
        d.polygon([(cx - 80, torso_top + 4), (cx + 80, torso_top + 4), (cx + 120 + cw_, FEET_Y - 30), (cx - 120 + cw_ * 0.6, FEET_Y - 30)],
                  fill=cd["cape"] + (255,), outline=OUT)
    if cd["hair"] == "afro":
        d.ellipse([head_c[0] - 122, head_c[1] - 132, head_c[0] + 122, head_c[1] + 70], fill=cd["hair_color"] + (255,), outline=OUT, width=6)
    if cd["hair"] in ("long", "braids") and back:
        d.rounded_rectangle([head_c[0] - 90, head_c[1] - 20, head_c[0] + 90, head_c[1] + 170], 50, fill=cd["hair_color"] + (255,), outline=OUT, width=5)
    if cd["hair"] == "long" and not back:
        d.rounded_rectangle([head_c[0] - 96, head_c[1] - 40, head_c[0] + 96, head_c[1] + 130], 50, fill=cd["hair_color"] + (255,), outline=OUT, width=5)
    if cd["backpack"] and side:
        d.rounded_rectangle([cx - 110, torso_top + 30, cx - 30, torso_top + 200], 26, fill=cd["backpack"] + (255,), outline=OUT, width=6)
    # braço de trás (lado)
    def arm(a, col, w, sk):
        if cd["sleeves"] == "short":
            _limb(d, [a[0], a[1], a[2]], sk, w * 0.9)
            mid = (a[0][0] + (a[1][0] - a[0][0]) * 0.55, a[0][1] + (a[1][1] - a[0][1]) * 0.55)
            _limb(d, [a[0], mid], col, w)
        else:
            _limb(d, [a[0], a[1], a[2]], col, w)
        _hand(d, a[2], sk)
    if side or (q3 and draw_pose not in ("cross", "forward")):
        arm(arms[0], dark(topc), 42 * LIMBK, dark(skin, 0.85))
    if back or (not side and pose not in ("cross", "forward")):
        pass
    # --- pernas ---
    order = [0, 1] if not side else [0, 1]
    for i in order:
        hp, kn, ft = leg_pts[i]
        bot = cd["bottom"] if cd["top_style"] != "dress" else "dress"
        base_leg = legc if bot == "pants" else (cd["tights"] or skin)
        col = base_leg if not (side and i == 0) else dark(base_leg)
        _limb(d, [hp, kn, ft], col, (50 if bot == "pants" else 40) * LIMBK)
        if bot == "shorts":
            mid = (hp[0] + (kn[0] - hp[0]) * 0.75, hp[1] + (kn[1] - hp[1]) * 0.75)
            _limb(d, [hp, mid], legc if not (side and i == 0) else dark(legc), 54 * LIMBK)
        fx = 26 if side else 0
        d.rounded_rectangle([ft[0] - 36 + fx * 0.3, ft[1] - 16, ft[0] + 36 + fx, ft[1] + 22], 18,
                            fill=(shoe if not (side and i == 0) else dark(shoe)) + (255,), outline=OUT, width=6)
    # --- tronco ---
    tw = (164 if not side else 124) * TWK * (0.9 if q3 else 1.0)
    tx0 = cx - tw / 2 + (hunch * 0.5 if side else 0) - (6 if q3 else 0)
    sq = breath * 3
    st = cd["top_style"]
    coat = st in ("trench", "labcoat")
    d.rounded_rectangle([tx0, torso_top - sq, tx0 + tw, hip_y + 12], 62, fill=(cd["inner"] if coat and not back else topc) + (255,), outline=OUT, width=6)
    bot = cd["bottom"] if st != "dress" else "dress"
    if bot in ("skirt", "dress") and draw_pose not in ("sit", "fallen", "crawl"):
        sc_ = cd["skirt"] or (topc if bot == "dress" else legc); ln_ = 86 if bot == "skirt" else 150
        fl = 26 + (s * 8 if walk else 0)
        d.polygon([(tx0 + 4, hip_y - 14), (tx0 + tw - 4, hip_y - 14), (tx0 + tw + fl, hip_y + ln_), (tx0 - fl, hip_y + ln_)], fill=sc_ + (255,), outline=OUT)
        for k in (1, 2, 3): d.line([(tx0 + tw * k / 4, hip_y - 6), (tx0 + tw * k / 4 + (k - 2) * 18, hip_y + ln_ - 4)], fill=dark(sc_, 0.82) + (255,), width=3)
    if coat:
        ln_ = 170 if st == "trench" else 150
        for sgn in (-1, 1):
            xa = cx + sgn * 16; xb = cx + sgn * (tw / 2 + 4)
            d.polygon([(xa, torso_top + 30), (xb, torso_top + 10), (xb + sgn * 22, hip_y + ln_), (xa + sgn * 6, hip_y + ln_)], fill=topc + (255,), outline=OUT)
        if not back:
            d.polygon([(cx - 16, torso_top + 30), (cx - 50, torso_top), (cx - 40, torso_top + 90)], fill=dark(topc, 0.85) + (255,), outline=OUT)
            d.polygon([(cx + 16, torso_top + 30), (cx + 50, torso_top), (cx + 40, torso_top + 90)], fill=dark(topc, 0.85) + (255,), outline=OUT)
        if st == "trench": d.rectangle([tx0 - 10, hip_y - 30, tx0 + tw + 10, hip_y - 14], fill=dark(topc, 0.7) + (255,))
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
    elif st == "suit" and not back:
        d.polygon([(cx - 30, torso_top + 4), (cx, torso_top + 110), (cx + 30, torso_top + 4)], fill=(235, 235, 235, 255))
        d.polygon([(cx - 8, torso_top + 20), (cx + 8, torso_top + 20), (cx + 12, torso_top + 104), (cx, torso_top + 120), (cx - 12, torso_top + 104)], fill=cd["tie"] + (255,))
        for sgn in (-1, 1): d.polygon([(cx + sgn * 30, torso_top + 2), (cx + sgn * 6, torso_top + 116), (cx + sgn * 56, torso_top + 50)], fill=dark(topc, 0.8) + (255,), outline=OUT)
        for k in range(2): d.ellipse([cx - 6, hip_y - 70 + k * 30, cx + 6, hip_y - 58 + k * 30], fill=(20, 20, 20, 255))
    elif st == "tshirt" and not back:
        d.arc([cx - 34, torso_top - 20, cx + 34, torso_top + 28], 20, 160, fill=dark(topc, 0.75) + (255,), width=5)
        d.ellipse([cx - 30, torso_top + 70, cx + 30, torso_top + 130], fill=dark(topc, 0.78) + (255,))
    elif st == "leather":
        for sgn in (-1, 1): d.polygon([(cx + sgn * 20, torso_top + 4), (cx + sgn * 70, torso_top - 6), (cx + sgn * 40, torso_top + 70)], fill=dark(topc, 1.5) + (255,), outline=OUT)
        d.line([(cx + 12, torso_top + 30), (cx + 12, hip_y + 8)], fill=(180, 180, 190, 255), width=4)
    elif st == "sweater":
        d.rectangle([tx0 + 4, hip_y - 22, tx0 + tw - 4, hip_y + 8], fill=dark(topc, 0.82) + (255,))
        for xx in range(int(tx0) + 14, int(tx0 + tw) - 8, 14): d.line([(xx, hip_y - 20), (xx, hip_y + 6)], fill=dark(topc, 0.65) + (255,), width=2)
        d.arc([cx - 40, torso_top - 24, cx + 40, torso_top + 30], 20, 160, fill=dark(topc, 0.75) + (255,), width=8)
    elif st == "chef" and not back:
        for k in range(3):
            for sgn in (-1, 1): d.ellipse([cx + sgn * 26 - 6, torso_top + 40 + k * 44, cx + sgn * 26 + 6, torso_top + 52 + k * 44], fill=(60, 60, 60, 255))
    elif st == "dress" and not back:
        d.arc([cx - 40, torso_top - 24, cx + 40, torso_top + 34], 20, 160, fill=dark(topc, 0.75) + (255,), width=6)
        d.line([(tx0 + 6, hip_y - 16), (tx0 + tw - 6, hip_y - 16)], fill=dark(topc, 0.7) + (255,), width=8)
    # acessórios no peito
    if not back:
        acc = cd["acc"]
        if "necklace" in acc:
            d.arc([cx - 46, torso_top - 30, cx + 46, torso_top + 50], 30, 150, fill=(230, 200, 80, 255), width=4)
            d.ellipse([cx - 9, torso_top + 40, cx + 9, torso_top + 58], fill=(230, 200, 80, 255))
        if "badge" in acc:
            bx, by = cx - 46, torso_top + 70
            d.polygon([(bx + 16 * math.cos(math.radians(a_ * 72 - 90)) * (1 if k_ % 2 == 0 else 0.45), by + 16 * math.sin(math.radians(a_ * 72 - 90)) * (1 if k_ % 2 == 0 else 0.45))
                       for k_, a_ in enumerate([i * 0.5 for i in range(10)])], fill=(230, 190, 60, 255), outline=OUT)
        if "stethoscope" in acc:
            d.arc([cx - 50, torso_top - 20, cx + 50, torso_top + 120], 10, 170, fill=(40, 40, 50, 255), width=6)
            d.ellipse([cx + 34, torso_top + 104, cx + 56, torso_top + 126], fill=(180, 180, 190, 255), outline=OUT, width=3)
        if "bowtie" in acc:
            d.polygon([(cx, torso_top + 14), (cx - 24, torso_top + 2), (cx - 24, torso_top + 26)], fill=cd["tie"] + (255,), outline=OUT)
            d.polygon([(cx, torso_top + 14), (cx + 24, torso_top + 2), (cx + 24, torso_top + 26)], fill=cd["tie"] + (255,), outline=OUT)
        if "tie" in acc and st != "suit":
            d.polygon([(cx - 8, torso_top + 10), (cx + 8, torso_top + 10), (cx + 12, torso_top + 110), (cx, torso_top + 126), (cx - 12, torso_top + 110)], fill=cd["tie"] + (255,), outline=OUT)
        if "bandana" in acc:
            d.polygon([(cx - 60, torso_top - 10), (cx + 60, torso_top - 10), (cx, torso_top + 50)], fill=(180, 40, 40, 255), outline=OUT)
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
        rng_arms = [1] if (side or q3) else [0, 1]
        for i in rng_arms:
            arm(arms[i], topc, 44 * LIMBK, skin)
    # --- objeto na mão ---
    pr = prop or ("phone" if draw_pose == "phone" else ("flashlight" if draw_pose == "hold" else ("bag" if draw_pose == "remove_bag" else None)))
    if pr and not back and draw_pose not in ("cross", "forward"):
        hx_, hy_ = arms[1][2]
        if pr == "phone":
            d.rounded_rectangle([hx_ - 19, hy_ - 44, hx_ + 19, hy_ + 22], 7, fill=(20, 20, 26, 255), outline=OUT, width=3)
            d.rounded_rectangle([hx_ - 13, hy_ - 38, hx_ + 13, hy_ + 14], 4, fill=(170, 200, 255, 255))
        elif pr == "handset":   # fone de gancho do telefone fixo, encostado na orelha
            d.line([(hx_ - 4, hy_ - 58), (hx_ + 6, hy_ + 26)], fill=OUT, width=22)
            d.line([(hx_ - 4, hy_ - 58), (hx_ + 6, hy_ + 26)], fill=(214, 206, 180, 255), width=14)
            for (ex, ey) in ((hx_ - 6, hy_ - 64), (hx_ + 8, hy_ + 32)):
                d.ellipse([ex - 16, ey - 12, ex + 16, ey + 12], fill=(214, 206, 180, 255), outline=OUT, width=3)
        elif pr == "flashlight":
            d.rounded_rectangle([hx_ - 10, hy_ - 13, hx_ + 54, hy_ + 13], 7, fill=(70, 72, 80, 255), outline=OUT, width=3)
            d.ellipse([hx_ + 46, hy_ - 16, hx_ + 62, hy_ + 16], fill=(255, 240, 180, 255), outline=OUT, width=3)
        elif pr == "radio":
            d.line([(hx_ + 30, hy_ - 30), (hx_ + 48, hy_ - 86)], fill=(160, 160, 165, 255), width=5)
            d.rounded_rectangle([hx_ - 34, hy_ - 32, hx_ + 40, hy_ + 22], 9, fill=(120, 80, 54, 255), outline=OUT, width=4)
            for k in range(3): d.line([(hx_ - 24, hy_ - 20 + k * 12), (hx_ + 4, hy_ - 20 + k * 12)], fill=(60, 40, 28, 255), width=4)
            d.ellipse([hx_ + 14, hy_ - 14, hx_ + 30, hy_ + 2], fill=(230, 210, 160, 255))
        elif pr == "key":
            d.ellipse([hx_ - 6, hy_ - 30, hx_ + 18, hy_ - 6], outline=(230, 190, 70, 255), width=6)
            d.line([(hx_ + 6, hy_ - 8), (hx_ + 6, hy_ + 26)], fill=(230, 190, 70, 255), width=6)
            d.line([(hx_ + 6, hy_ + 18), (hx_ + 16, hy_ + 18)], fill=(230, 190, 70, 255), width=5)
        elif pr == "bag":
            bc = cd["backpack"] or (236, 196, 50)
            d.rounded_rectangle([hx_ - 34, hy_ + 2, hx_ + 40, hy_ + 104], 22, fill=bc + (255,), outline=OUT, width=5)
            d.line([(hx_, hy_ + 4), (hx_ - 4, hy_ - 14)], fill=bc + (255,), width=10)
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
    hc_ = cd["hair_color"] + (255,)
    hs = cd["hair"]
    if hs in ("curly", "afro") and not back:
        for k in range(9):
            a_ = math.pi + k * math.pi / 8
            bx_, by_ = hx + math.cos(a_) * hr * 0.92, hy + math.sin(a_) * hr * 0.92
            d.ellipse([bx_ - 26, by_ - 26, bx_ + 26, by_ + 26], fill=hc_, outline=OUT, width=4)
    elif hs == "bob":
        d.chord([hx - hr - 8, hy - hr - 6, hx + hr + 8, hy + hr * 0.9], 160, 380, fill=hc_, outline=OUT, width=5)
        if not back: d.chord([hx - hr * 0.8, hy - hr * 0.2, hx + hr * 0.8, hy + hr * 1.6], 180, 360, fill=skin + (255,))
    elif hs == "spiky":
        for k in range(6):
            x_ = hx - hr + k * hr * 0.4
            d.polygon([(x_ - 16, hy - hr * 0.55), (x_ + 4, hy - hr - 34 - (k % 2) * 12), (x_ + 24, hy - hr * 0.55)], fill=hc_, outline=OUT)
        d.chord([hx - hr, hy - hr, hx + hr, hy + hr * 0.3], 180, 360, fill=hc_)
    elif hs == "mohawk":
        for k in range(5):
            y_ = hy - hr + 10 + k * 8
            d.polygon([(hx - 16, y_ + 20), (hx - 4 + k * 3, y_ - 56), (hx + 16, y_ + 20)], fill=hc_, outline=OUT)
    elif hs in ("braids", "pigtails"):
        d.chord([hx - hr, hy - hr, hx + hr, hy + hr * 0.35], 180, 360, fill=hc_, outline=OUT, width=5)
        if not back:
            for sgn in (-1, 1):
                sw_ = math.sin(t * 2.4 + seed + sgn) * 6 * sway_k
                if hs == "pigtails":
                    d.ellipse([hx + sgn * hr - 26 + sw_, hy - 30, hx + sgn * hr + 26 + sw_, hy + 70], fill=hc_, outline=OUT, width=4)
                else:
                    for k in range(5):
                        d.ellipse([hx + sgn * (hr - 10) - 14 + sw_, hy + k * 28 - 6, hx + sgn * (hr - 10) + 14 + sw_, hy + k * 28 + 26], fill=hc_, outline=OUT, width=3)
    elif hs == "long" and not back:
        d.chord([hx - hr, hy - hr, hx + hr, hy + hr * 0.35], 180, 360, fill=hc_, outline=OUT, width=5)
    if back and hs in ("ponytail", "long", "bun", "short", "curly", "bob", "spiky", "braids", "pigtails"):
        d.ellipse([hx - hr + 8, hy - hr + 8, hx + hr - 8, hy + hr - 8], fill=hc_)
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
    elif cd["hat"] == "fedora":
        hcol = cd["hat_color"] + (255,)
        d.ellipse([hx - 130, hy - 70, hx + 130, hy - 34], fill=hcol, outline=OUT, width=5)
        d.rounded_rectangle([hx - 76, hy - 146, hx + 76, hy - 50], 30, fill=hcol, outline=OUT, width=5)
        d.rectangle([hx - 76, hy - 80, hx + 76, hy - 62], fill=(30, 26, 22, 255))
    elif cd["hat"] == "cowboy":
        hcol = cd["hat_color"] + (255,)
        d.chord([hx - 150, hy - 110, hx + 150, hy - 20], 0, 180, fill=hcol, outline=OUT, width=5)
        d.ellipse([hx - 150, hy - 76, hx + 150, hy - 40], fill=hcol, outline=OUT, width=5)
        d.rounded_rectangle([hx - 70, hy - 160, hx + 70, hy - 56], 34, fill=hcol, outline=OUT, width=5)
    elif cd["hat"] == "tophat":
        hcol = cd["hat_color"] + (255,)
        d.ellipse([hx - 110, hy - 74, hx + 110, hy - 44], fill=hcol, outline=OUT, width=5)
        d.rectangle([hx - 64, hy - 220, hx + 64, hy - 58], fill=hcol, outline=OUT, width=5)
        d.rectangle([hx - 64, hy - 90, hx + 64, hy - 70], fill=(150, 30, 30, 255))
    elif cd["hat"] == "crown":
        hcol = cd["hat_color"] + (255,)
        pts_ = [(hx - 70, hy - 60)]
        for k in range(5): pts_ += [(hx - 70 + k * 35 + 17, hy - 130), (hx - 70 + (k + 1) * 35, hy - 84)]
        pts_ += [(hx + 70, hy - 60)]
        d.polygon(pts_, fill=hcol, outline=OUT)
        for k in range(3): d.ellipse([hx - 44 + k * 38, hy - 84, hx - 32 + k * 38, hy - 72], fill=(200, 40, 60, 255))
    elif cd["hat"] == "witch":
        hcol = cd["hat_color"] + (255,)
        d.ellipse([hx - 150, hy - 76, hx + 150, hy - 36], fill=hcol, outline=OUT, width=5)
        tip = math.sin(t * 1.5 + seed) * 12
        d.polygon([(hx - 76, hy - 60), (hx + 76, hy - 60), (hx + 40 + tip, hy - 260)], fill=hcol, outline=OUT)
        d.rectangle([hx - 72, hy - 88, hx + 72, hy - 70], fill=(140, 90, 200, 255))
    elif cd["hat"] == "chef":
        hcol = cd["hat_color"] + (255,)
        d.rectangle([hx - 76, hy - 110, hx + 76, hy - 50], fill=hcol, outline=OUT, width=5)
        for k in range(3): d.ellipse([hx - 96 + k * 64, hy - 200, hx - 96 + k * 64 + 66, hy - 100], fill=hcol, outline=OUT, width=5)
    elif cd["hat"] in ("headband", "bandana_hat"):
        hcol = cd["hat_color"] + (255,)
        if cd["hat"] == "bandana_hat": d.chord([hx - hr, hy - hr - 4, hx + hr, hy + hr * 0.2], 180, 360, fill=hcol, outline=OUT, width=5)
        d.rounded_rectangle([hx - hr - 2, hy - 54, hx + hr + 2, hy - 34], 8, fill=hcol, outline=OUT, width=4)
        if not back: d.polygon([(hx + hr - 6, hy - 46), (hx + hr + 40, hy - 20), (hx + hr + 20, hy - 6)], fill=hcol, outline=OUT)
    elif cd["hat"] == "hood":
        if back: d.ellipse([hx - 92, hy - 92, hx + 92, hy + 92], fill=topc + (255,), outline=OUT, width=6)
        else: d.arc([hx - 98, hy - 98, hx + 98, hy + 98], 160, 380, fill=dark(topc, 0.88) + (255,), width=24)
    if "headphones" in cd["acc"]:
        d.arc([hx - hr - 6, hy - hr - 10, hx + hr + 6, hy + hr - 20], 180, 360, fill=(30, 30, 36, 255), width=12)
        for sgn in (-1, 1): d.rounded_rectangle([hx + sgn * hr - 18, hy - 20, hx + sgn * hr + 18, hy + 34], 12, fill=(200, 40, 60, 255), outline=OUT, width=4)
    if cd["hair"] == "ponytail" and back:
        sw = math.sin(t * 2.6 + seed) * 12 * sway_k + (s * 12 if walk else 0)
        d.ellipse([hx - 28 + sw * 0.4, hy + 24, hx + 28 + sw, hy + 150], fill=cd["hair_color"] + (255,), outline=OUT, width=5)
    # --- rosto ---
    if not back:
        fx = hx + look + (34 if side else 0)
        if q3: fx += 18
        if gesture == "down": hy += 6
        eyes = ([(fx - 30, hy + 16), (fx + 30, hy + 16)] if not q3 else [(fx - 22, hy + 16), (fx + 26, hy + 16)]) if not side else [(fx + 6, hy + 16)]
        blink = (_blink(t, seed) or blink_force) and not inf
        if inf:
            glow = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
            for (x, y) in eyes: gd.ellipse([x - 30, y - 26, x + 30, y + 26], fill=(255, 255, 235, 120))
            im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10))); d = ImageDraw.Draw(im)
            for (x, y) in eyes: d.ellipse([x - 14, y - 12, x + 14, y + 12], fill=(252, 252, 240, 255))
            d.line([(hx - 40, hy + 50), (hx - 10, hy + 46), (hx + 10, hy + 54), (hx + 36, hy + 48)], fill=(80, 86, 84, 255), width=5)
        else:
            ew, eh = {"neutral": (10, 13), "fear": (12, 16), "shock": (14, 17), "angry": (10, 8), "sad": (9, 11),
                      "determined": (10, 10), "happy": (10, 10), "suspicious": (10, 7), "cry": (10, 5), "panting": (10, 12)}.get(emotion, (10, 13))
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
                if emotion in ("fear", "sad", "cry"):
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
            elif emotion == "cry":
                d.arc([mx - 16, my - 2, mx + 16, my + 18], 200, 340, fill=ec + (255,), width=5)
                for (x, y) in eyes:
                    d.line([(x - 2, y + 6), (x - 6, y + 46)], fill=(140, 190, 245, 255), width=6)
                    dy = (t * 70 + x) % 60
                    d.ellipse([x - 12, y + 30 + dy, x - 2, y + 42 + dy], fill=(140, 190, 245, 255))
            if pant: mouth = max(mouth, 0.35 + 0.25 * math.sin(t * 2 * math.pi / 0.8))
            vis = viseme if mouth > 0.04 or viseme == 1 else 0
            if vis == 1:      # M/B/P: lábios fechados apertados
                d.line([(mx - 16, my + 2), (mx + 16, my + 2)], fill=ec + (255,), width=7)
            elif vis == 3:    # E/I: boca larga e baixa, dentes
                mw = 20 + 6 * mouth; mh = 6 + 10 * mouth
                d.rounded_rectangle([mx - mw, my - mh * 0.5, mx + mw, my + mh * 0.6], 8, fill=(40, 18, 22, 255), outline=ec + (255,), width=4)
                d.rectangle([mx - mw + 5, my - mh * 0.5 + 3, mx + mw - 5, my - mh * 0.5 + 3 + mh * 0.35], fill=(245, 245, 240, 255))
            elif vis == 4:    # O: redonda
                r_ = 9 + 12 * mouth
                d.ellipse([mx - r_ * 0.85, my - r_, mx + r_ * 0.85, my + r_], fill=(40, 18, 22, 255), outline=ec + (255,), width=4)
            elif vis == 5:    # U: biquinho
                r_ = 6 + 5 * mouth
                d.ellipse([mx - r_, my - r_, mx + r_, my + r_], fill=(40, 18, 22, 255), outline=ec + (255,), width=6)
            elif mouth > 0.06:  # A (padrão)
                mh = 5 + 24 * mouth; mw = 13 + 7 * mouth
                d.ellipse([mx - mw, my - mh * 0.45, mx + mw, my + mh * 0.55], fill=(40, 18, 22, 255), outline=ec + (255,), width=4)
                if mouth > 0.45: d.chord([mx - mw + 5, my + mh * 0.05, mx + mw - 5, my + mh * 0.5], 0, 180, fill=(190, 80, 90, 255))
            fcol = (cd["facial_color"] or cd["hair_color"]) + (255,)
            if cd["facial"] == "beard":
                d.chord([hx - hr + 6, hy - 10, hx + hr - 6, hy + hr + 10], 0, 180, fill=fcol, outline=OUT, width=4)
                if mouth > 0.06 or emotion in ("shock", "happy"): d.ellipse([mx - 14, my - 6, mx + 14, my + 10 + 12 * mouth], fill=(40, 18, 22, 255))
            elif cd["facial"] == "mustache":
                d.chord([mx - 34, my - 22, mx + 2, my + 6], 180, 360, fill=fcol, outline=OUT, width=3)
                d.chord([mx - 2, my - 22, mx + 34, my + 6], 180, 360, fill=fcol, outline=OUT, width=3)
            elif cd["facial"] == "stubble":
                r_ = random.Random(seed)
                for _ in range(40):
                    a_ = r_.uniform(0.15, 2.99); rr_ = r_.uniform(hr * 0.55, hr * 0.92)
                    px_, py_ = hx + math.cos(a_) * rr_, hy + 6 + math.sin(a_) * rr_ * 0.95
                    d.ellipse([px_ - 2, py_ - 2, px_ + 2, py_ + 2], fill=dark(fcol[:3], 0.8) + (255,))
            acc = cd["acc"]
            if "sunglasses" in acc:
                for (x, y) in eyes: d.rounded_rectangle([x - 26, y - 18, x + 26, y + 16], 10, fill=(14, 14, 20, 255), outline=OUT, width=4)
                if len(eyes) == 2: d.line([(eyes[0][0] + 26, eyes[0][1] - 6), (eyes[1][0] - 26, eyes[1][1] - 6)], fill=OUT, width=5)
                for (x, y) in eyes: d.line([(x - 14, y - 8), (x - 4, y - 12)], fill=(200, 200, 220, 255), width=3)
            if "eyepatch" in acc:
                x, y = eyes[-1]
                d.line([(hx - hr + 10, hy - 40), (hx + hr - 10, hy - 20)], fill=OUT, width=6)
                d.ellipse([x - 22, y - 20, x + 22, y + 20], fill=(14, 14, 18, 255))
            if "mask" in acc:
                d.rounded_rectangle([hx - 52 + (fx - hx), hy + 34, hx + 52 + (fx - hx), hy + 84], 18, fill=(150, 200, 220, 255), outline=OUT, width=4)
                d.line([(hx - 52 + (fx - hx), hy + 46), (hx - hr + 4, hy + 20)], fill=(150, 200, 220, 255), width=4)
            if "earrings" in acc:
                for sgn in ((-1, 1) if not side else (-1,)): d.ellipse([hx + sgn * (hr - 4) - 7, hy + 30, hx + sgn * (hr - 4) + 7, hy + 44], fill=(230, 200, 80, 255))
            if "bow" in acc:
                bx_, by_ = hx + hr * 0.6, hy - hr * 0.75
                d.polygon([(bx_, by_), (bx_ - 34, by_ - 22), (bx_ - 34, by_ + 22)], fill=(220, 70, 110, 255), outline=OUT)
                d.polygon([(bx_, by_), (bx_ + 34, by_ - 22), (bx_ + 34, by_ + 22)], fill=(220, 70, 110, 255), outline=OUT)
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
    er = A.copy()
    for dx_, dy_ in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        er = np.minimum(er, np.roll(np.roll(A, dx_, axis=1), dy_, axis=0))
    edge = np.clip(A - er, 0, 1)
    edge = np.asarray(Image.fromarray((edge * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0
    side = np.clip(light.get("rim_side", 1) * xs * 1.4 + 0.2, 0, 1)
    rim = edge * side * light.get("rim_k", 0.0)
    arr[..., :3] += rim[..., None] * np.array(light.get("rim", (255, 255, 255))) * 0.9
    arr[..., :3] = np.clip(arr[..., :3], 0, 255)
    return Image.fromarray(arr.astype("uint8"), "RGBA")

_CACHE = {}
_CACHE_PX = 0
def render_char(name, view="front", emotion="neutral", pose="idle", t=0.0, scale=1.0, light=None, walk=False, run=False,
                look=0, facing=1, custom=None, seed=None, sway=1.0, breath=1.0, mouth=0.0, talk=0.0, pose_prev=None, pk=1.0,
                blink_force=False, sniff=False, prop=None, viseme=0, gesture=None):
    """Devolve (sprite RGBA, (ax, ay)) — ancorado nos pés."""
    cd = char_def(name, custom)
    seed = seed if seed is not None else (sum(map(ord, name)) % 97)
    light = light or LIGHTS["night"]
    qt = round(t * 15) / 15 if (walk or sway or breath) else 0
    key = (name, view, emotion, pose, qt, round(scale * cd["scale"], 3), id(light) if not isinstance(light, dict) else tuple(sorted((k, str(v)) for k, v in light.items())),
           walk, run, int(look), facing, seed, str(custom), round(mouth * 6), round(talk * 4), pose_prev if pk < 1 else None, round(pk * 10), blink_force, sniff, prop, int(viseme), gesture)
    if key in _CACHE: return _CACHE[key]
    im, anc = _draw(cd, view, facing, emotion, pose, qt, walk, run, look, seed, sway, breath, round(mouth * 6) / 6, round(talk * 4) / 4,
                    pose_prev, round(pk * 10) / 10, blink_force, sniff, prop, int(viseme), gesture)
    k = 0.5 * scale * cd["scale"]
    nw, nh = max(2, int(CW * k)), max(2, int(CH * k))
    im = im.resize((nw, nh), Image.LANCZOS)
    im = _shade(im, light)
    if cd.get("ghost"):
        r_, g_, b_, a_ = im.split()
        a_ = a_.point(lambda v: int(v * 0.58))
        im = Image.merge("RGBA", (r_.point(lambda v: min(255, int(v * 0.9 + 30))), g_.point(lambda v: min(255, int(v * 0.95 + 30))), b_.point(lambda v: min(255, v + 50)), a_))
    if facing < 0: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    res = (im, (nw / 2, anc[1] * k))
    global _CACHE_PX
    px = im.width * im.height
    if px > 3_000_000: return res                       # sprite gigante (close/médio perto): não guarda, cabe na memória
    if len(_CACHE) > 1500 or _CACHE_PX + px > 120_000_000: _CACHE.clear(); _CACHE_PX = 0   # ~500 MB no máximo
    _CACHE[key] = res; _CACHE_PX += px
    return res

_SHADOWS = {}
def shadow(frame, x, y, width, alpha=110, dx=0, stretch=1.0):
    """Sombra projetada no chão (elipse desfocada)."""
    w = width * stretch; h = width * 0.18
    key = (int(w / 3), int(alpha / 10))
    if key not in _SHADOWS:
        m = Image.new("L", (int(w * 2 + 60), int(h * 2 + 60)), 0)
        ImageDraw.Draw(m).ellipse([30, 30, 30 + w * 2, 30 + h * 2], fill=alpha)
        _SHADOWS[key] = m.filter(ImageFilter.GaussianBlur(max(2, width * 0.08)))
    m = _SHADOWS[key]
    frame.paste((0, 0, 0), (int(x - m.width / 2 + dx), int(y - m.height / 2)), m)

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
