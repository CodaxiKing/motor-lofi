
"""Monta o episódio a partir de um roteiro JSON (ver SPEC.md).

    python3 -m lofi.render episodio.json                  # vídeo completo
    python3 -m lofi.render episodio.json --jobs 2         # vídeo completo em paralelo
    python3 -m lofi.render episodio.json --test 5 12.5    # só alguns quadros (PNG)
"""
import sys, os, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
from .core import W, H, RED, CREAM, font, text_center, ease, ease_out, c01, lerp, keyframe, fast_blur, crop_zoom
from . import fx, scenes, text, audio, particles, detail, partes
from .visual_profiles import resolve_profile, apply_profile
from .layers import composite_layers
from .rig import render_char, paste_char, shadow, reflection, LIGHTS

HEAD_FRAC = 0.215
RAIN_LEVELS = {"forte": 1.7, "normal": 1.0, "fraca": 0.45, "nenhuma": 0.0}

def val(v, rel, norm, default=None):
    if v is None: return default
    if isinstance(v, (list, tuple)) and v and isinstance(v[0], (list, tuple)): return keyframe(v, rel)
    if isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(k, (int, float)) for k in v) and not isinstance(v[0], bool):
        return lerp(v[0], v[1], ease(norm))
    return v

def change(v, rel):
    """Keyframes de texto: (atual, anterior, segundos desde a troca)."""
    if not (isinstance(v, (list, tuple)) and v and isinstance(v[0], (list, tuple))): return v, None, 99.0
    pts = sorted(v); cur, prev, ts = pts[0][1], None, -99.0
    for tk, val_ in pts:
        if rel >= tk and val_ != cur: prev, cur, ts = cur, val_, tk
        elif rel >= tk: cur = val_
    return cur, prev, rel - ts

_ROT = {}
def rotate_about(spr, anc, deg):
    """Gira o sprite em torno do ponto de apoio (pés)."""
    if not deg: return spr, anc
    key = (id(spr), round(deg))
    if key in _ROT and _ROT[key][0] is spr: return _ROT[key][1]
    res = _rotate_about(spr, anc, round(deg))
    if len(_ROT) > 600: _ROT.clear()
    _ROT[key] = (spr, res)
    return res

def _rotate_about(spr, anc, deg):
    R = int(math.hypot(spr.width, spr.height)) + 4
    big = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0))
    big.paste(spr, (int(R - anc[0]), int(R - anc[1])), spr)
    big = big.rotate(-deg, center=(R, R), resample=Image.BILINEAR)
    bb = big.getbbox() or (0, 0, 2, 2)
    return big.crop(bb), (R - bb[0], R - bb[1])

GEST_POINT = {"ali", "lá", "la", "olha", "olhe", "aquele", "aquela", "aquilo", "ali!", "acolá", "veja"}
GEST_CHEST = {"eu", "meu", "minha", "mim", "comigo", "juro"}
GEST_YES = {"sim", "isso", "claro", "certo", "beleza"}
GEST_NO = {"não", "nao", "nunca", "jamais", "nada"}
GEST_DOWN = {"desculpa", "desculpe", "perdão", "perdi", "morreu", "sinto", "triste", "sozinha", "sozinho"}

class Episode:
    def __init__(self, spec_path):
        self.spec_path = os.path.abspath(spec_path)
        self.base = os.path.dirname(self.spec_path)
        self.spec = json.load(open(spec_path, encoding="utf-8"))
        self.visual_profile = resolve_profile(self.spec.get("visual_profile", "lofi_classic"), self.spec.get("visual_overrides"))
        sp = self.spec
        self.fps = sp.get("fps", 30)
        from .mapa import resolver_plano
        self._avoid = []; self._heads = []
        self.shots = sorted((resolver_plano(s) for s in sp["shots"]), key=lambda s: s["start"])
        self.total = sp.get("total", max(s["end"] for s in self.shots))
        # modo redes (TikTok/Instagram): padrão nos episódios novos; os antigos ("plano_padrao": "aberto") ficam como eram
        self.redes = sp.get("modo_redes", sp.get("plano_padrao", "auto") != "aberto")
        text.set_redes(self.redes)
        self._hook_end = max([s["end"] for s in self.shots if s.get("hook")] or [0.0])
        if self.redes and sp.get("loop", True) and self._hook_end and not any(s.get("type") == "loop" for s in self.shots):
            t0 = round(max(self.total, max(s["end"] for s in self.shots)), 3)   # último meio segundo = primeiro: o vídeo emenda
            ls = {"start": t0, "end": round(t0 + 0.5, 3), "type": "loop"}
            self.shots.append(ls); sp["shots"] = list(sp["shots"]) + [ls]; self.total = ls["end"]
        self._cortes_cache = {}
        self.voices = {k: os.path.join(self.base, v) for k, v in sp.get("voices", {}).items()}
        self.speakers = {k: {"label": v.get("label"), "color": tuple(v.get("color", (250, 250, 248)))} for k, v in sp.get("speakers", {}).items()}
        # personagens travados da série: personagens.json na pasta do roteiro (ou na pasta acima) sempre vence
        self.locked = {}
        for cand in (os.path.join(self.base, "personagens.json"), os.path.join(os.path.dirname(self.base), "personagens.json")):
            if os.path.exists(cand):
                self.locked = {k: v for k, v in json.load(open(cand, encoding="utf-8")).items() if not k.startswith("_")}; break
        self.custom = {**sp.get("characters", {}), **self.locked}
        self.clips = sp.get("clips", [])
        self.subs = text.split_subs([(s["voice"], s["src"][0], s["src"][1], s["text"]) for s in sp.get("subs", [])], self.to_video)
        self.flashes = sp.get("lightning", [])
        self.word_subs = sp.get("word_captions", True)
        self.env = {}
        self._recap_cache = {}

    def to_video(self, voice, t):
        for c in self.clips:
            a, b = c["src"]
            if c["voice"] == voice and a - 0.25 <= t <= b + 0.25: return c["at"] + (t - a)
        raise ValueError(f"fala fora dos clipes: {voice} {t}")

    # ---------------- áudio ----------------
    def build_audio(self):
        amb = []
        for s in self.shots:
            sc = s.get("scene")
            if sc and sc in scenes.REGISTRY and s.get("type", "scene") == "scene":
                kind = scenes.REGISTRY[sc].amb
                if s.get("rain") == "nenhuma" and kind == "chuva_fora": kind = "vento"
                amb.append((s["start"], s["end"], kind))
        if self.spec.get("ambience") is not None: amb = [tuple(a) for a in self.spec["ambience"]]
        sfx = list(self.spec.get("sfx", []))
        for th in self.flashes: sfx.append({"t": th + 0.3, "name": "thunder"})
        for s in self.shots:
            if s.get("transition") == "whip": sfx.append({"t": s["start"] - 0.1, "name": "whoosh"})
            if s.get("transition") == "glitch": sfx.append({"t": s["start"], "name": "static", "dur": 0.3, "gain": 1.5})
            if s.get("type") == "title" and s.get("stamp"): sfx.append({"t": s["stamp"]["t"], "name": "stamp"})
            if s.get("type") == "recap": sfx.append({"t": s["start"], "name": "static", "dur": 0.5, "gain": 1.2})
            for sc_t in s.get("scare", []): sfx.append({"t": sc_t, "name": "impact", "gain": 0.9})
        if self.redes:
            for s in self.shots:
                if s.get("hook") and not any(abs(x.get("t", -9) - s["start"]) < 0.2 and x.get("name") == "impact" for x in sfx):
                    sfx += [{"t": s["start"], "name": "impact", "gain": 1.2}, {"t": s["start"], "name": "whoosh"}]
            cs = next((s for s in self.shots if s.get("type") == "choice"), None)
            if cs: sfx += [{"t": cs["start"] - k, "name": "beep", "gain": 0.8} for k in (3, 2, 1)]
            if self.spec.get("voto"): sfx.append({"t": self._hook_end + 0.3, "name": "stamp"})
            pq = self.pergunta()
            if pq: sfx.append({"t": pq[0], "name": "notif", "gain": 0.8})
        self.mix_path = os.path.join(self.base, "_mix.wav")
        clips = []
        for c in self.clips:
            c = dict(c)
            if "acoustic" not in c and self.spec.get("acoustics", True):
                sh = next((s for s in self.shots if s["start"] <= c["at"] + 0.3 < s["end"]), None)
                if sh and sh.get("type", "scene") == "scene" and sh.get("scene") in scenes.REGISTRY:
                    c["acoustic"] = sh.get("acoustic", scenes.REGISTRY[sh["scene"]].acoustic)
                elif sh and sh.get("type") == "choice": c["acoustic"] = None
            clips.append(c)
        self.env = audio.mix(self.total, clips, self.voices, sfx, self.spec.get("music", []), amb, self.mix_path, self.fps) or {}

    def level(self, voice, t, smooth=0):
        e = self.env.get(voice)
        if e is None or len(e) == 0: return 0.0
        i = int(t * self.fps)
        if smooth:
            a, b = max(0, i - smooth), min(len(e), i + smooth + 1)
            return float(np.mean(e[a:b])) if b > a else 0.0
        return float(e[min(len(e) - 1, i)])

    def viseme(self, voice, t):
        e = self.env.get("_vis_" + voice)
        if e is None or len(e) == 0: return 0
        return int(e[min(len(e) - 1, int(t * self.fps))])

    def speech_gesture(self, voice, t):
        """Gesto automático pela palavra que está sendo dita: (pose, gesto de cabeça, emoção) ou None."""
        for a, b, txt, v in self.subs:
            if v != voice or not (a <= t < b): continue
            for w, wa, wb in text._word_times(txt, a, b):
                if not (wa - 0.15 <= t < wb + 0.55): continue
                k = w.lower().strip(".,!?…:;\"'()—-")
                if k in GEST_POINT: return ("point", None, None)
                if k in GEST_CHEST: return ("chest", None, None)
                if k in GEST_YES: return (None, "nod", None)
                if k in GEST_NO: return (None, "shake", None)
                if k in GEST_DOWN: return (None, "down", "sad")
        return None

    # ---------------- HUD ----------------
    def hud_state(self, t):
        h = self.spec.get("hud")
        if not h: return None
        days = sorted(h.get("days", [[0, "DIA 1", "00:00"]])); cur = days[0]
        for d in days:
            if t >= d[0]: cur = d
        hh, mm = map(int, cur[2].split(":"))
        mins = hh * 60 + mm + int((t - cur[0]) / h.get("sec_per_min", 8))
        flash = max(0.0, 1 - (t - cur[0]) / 0.5) if cur[0] > 0 and t - cur[0] < 0.5 else 0.0
        return cur[1], f"{(mins // 60) % 24:02d}:{mins % 60:02d}", h.get("place", ""), flash

    # ---------------- personagens ----------------
    def actor_state(self, a, sc, rel, norm):
        x = val(a.get("x", 540), rel, norm)
        y = val(a.get("y", sc.ground[0] + (sc.ground[1] - sc.ground[0]) * 0.6), rel, norm)
        scale = val(a.get("scale"), rel, norm) or sc.scale_at(y) * a.get("scale_k", 1.0)
        return x, y, scale

    def resolve_light(self, shot, sc, t):
        name = shot.get("light")
        props = shot.get("_props", {})
        if not name:
            name = sc.light
            if sc.name == "escada": name = "red" if props.get("_light_on", True) else "dark"
            if sc.name in ("corredor", "hospital", "mercado", "escola", "delegacia", "loja", "deposito", "camara_fria") and not props.get("_lamp_on", True): name = "dark"
            if val(shot.get("dark"), 0, 0, 0) and val(shot.get("dark"), 0, 0, 0) > 0.5: name = "dark"
        if fx.flash_amount(t, self.flashes) > 0.5: name = "flash"
        return name, LIGHTS.get(name, LIGHTS["night"])

    def link_actors(self, actors, sc, rel, norm):
        """Interações: 'hold' (mãos dadas) e 'carried_by' (no colo de alguém). Referência por nome do personagem."""
        by = {a["char"]: a for a in actors}
        out = []
        for a in actors:
            a = dict(a)
            cb = val(a.get("carried_by"), rel, norm) if a.get("carried_by") else None
            if cb and cb in by:
                c = by[cb]; cx, cy, cs = self.actor_state(c, sc, rel, norm)
                f = val(c.get("facing", 1), rel, norm) or 1
                a["x"] = cx + 34 * cs * f; a["y"] = cy + 1; a["scale"] = cs * 0.92
                a["_carried"] = 80 * f; a["walk"] = False; a["shadow"] = False
                a["_zbias"] = 1; a.setdefault("pose", "idle")
            h = val(a.get("hold"), rel, norm) if a.get("hold") else None
            if h and h in by:
                ox = val(by[h].get("x", 540), rel, norm); mx = val(a.get("x", 540), rel, norm)
                a["_hold_pose"] = "hand_r" if ox > mx else "hand_l"; a["_hold_with"] = h
            out.append(a)
        held = {a["_hold_with"]: a["char"] for a in out if a.get("_hold_with")}
        for a in out:
            if a["char"] in held and not a.get("_hold_pose"):
                o = by[held[a["char"]]]
                a["_hold_pose"] = "hand_r" if val(o.get("x", 540), rel, norm) > val(a.get("x", 540), rel, norm) else "hand_l"
                a["_hold_with"] = held[a["char"]]
        return out

    def paint_holds(self, img, prepared):
        d = None; done = set()
        P_by = {P["a"]["char"]: P for P in prepared}
        for P in prepared:
            o = P_by.get(P["a"].get("_hold_with"))
            if not o or frozenset((P["a"]["char"], o["a"]["char"])) in done: continue
            done.add(frozenset((P["a"]["char"], o["a"]["char"])))
            l, r = (P, o) if P["sx"] < o["sx"] else (o, P)
            y = (l["sy"] + r["sy"]) / 2 - l["spr"].height * 0.42
            x0 = l["sx"] + l["spr"].width * 0.18; x1 = r["sx"] - r["spr"].width * 0.18
            if x1 - x0 > 8:
                d = d or ImageDraw.Draw(img)
                d.line([(x0, y), (x1, y)], fill=(30, 30, 40), width=max(6, int(14 * l["scale"])))
            mx = (l["sx"] + r["sx"]) / 2; rr = max(6, 11 * l["scale"])
            d = d or ImageDraw.Draw(img)
            d.ellipse([mx - rr, y - rr, mx + rr, y + rr], fill=(222, 200, 180), outline=(30, 30, 40), width=3)

    def prepare_actor(self, a, sc, shot, t, rel, norm, camx, cam, light, focus_on, idx):
        x, y, base_scale = self.actor_state(a, sc, rel, norm)
        z, x0, y0 = cam
        wx = x - camx * a.get("depth", sc.depths[1])
        lift = val(a.get("lift", 0), rel, norm, 0)
        trem = val(a.get("tremble", 0), rel, norm, 0)
        sx = (wx - x0) * z + (math.sin(t * 61) * 4 * trem if trem else 0)
        sy = (y - y0) * z
        pop = 1.0
        emo, emo_prev, emo_dt = change(a.get("emotion", "neutral"), rel)
        pose, pose_prev, pose_dt = change(a.get("pose", "idle"), rel)
        if emo_dt < 0.25: pop = 1 + 0.07 * (1 - emo_dt / 0.25)
        scale = base_scale * z * pop
        voice = a.get("voice", a["char"])
        lips = a.get("lipsync", True)
        gesture = val(a.get("gesture"), rel, norm)
        if lips and a.get("gestures", self.spec.get("gestures", True)) and pose == "idle" and not a.get("_crowd"):
            g = self.speech_gesture(voice, self._treal)
            if g:
                if g[0]: pose = g[0]
                gesture = gesture or g[1]
                if g[2] and emo == "neutral": emo = g[2]
        if a.get("_hold_pose") and pose in ("idle", "walk"): pose = a["_hold_pose"]
        talk = min(1.0, self.level(voice, self._treal, smooth=4) * 1.3) if lips else 0.0
        mouth = min(1.0, self.level(voice, self._treal) * 1.25) if lips else 0.0
        walk = val(a.get("walk", False), rel, norm)
        view = val(a.get("view", "front"), rel, norm)
        facing = val(a.get("facing", 1), rel, norm)
        spr, anc = render_char(a["char"], view=view, emotion=emo, pose=pose, t=t * a.get("_limp", 1.0), scale=scale, light=light,
                               walk=bool(walk), run=bool(val(a.get("run", False), rel, norm)), look=val(a.get("look", 0), rel, norm),
                               facing=facing, custom=({**(a.get("custom") or {}), **self.locked[a["char"]]} if a["char"] in self.locked
                                                      else (a.get("custom") or self.custom.get(a["char"]))), seed=a.get("seed"),
                               mouth=mouth if view != "back" else 0, talk=talk, pose_prev=pose_prev,
                               viseme=self.viseme(voice, self._treal) if lips and view != "back" else 0, gesture=gesture,
                               pk=c01(pose_dt / 0.32) if pose_prev else 1.0, blink_force=emo_dt < 0.1,
                               sniff=bool(val(a.get("sniff", False), rel, norm)), prop=val(a.get("prop"), rel, norm))
        rot = val(a.get("rot"), rel, norm)
        if rot is None: rot = {"fallen": 86, "crawl": 72}.get(pose, 0) * (1 if facing >= 0 else -1)
        if a.get("_carried"): rot = a["_carried"]
        if rot: spr, anc = rotate_about(spr, anc, rot)
        blur = a.get("blur", 0)
        if focus_on is not None and focus_on != idx and not a.get("_crowd"): blur = max(blur, 4)
        if blur: spr = spr.filter(ImageFilter.GaussianBlur(blur))
        return dict(a=a, spr=spr, anc=anc, sx=sx, sy=sy - lift * z, floor_y=sy, scale=scale, view=view, facing=facing, idx=idx, rot=rot)

    def paint_actor(self, img, P, sc, shot, t, light):
        a, spr, anc, sx, sy, scale = P["a"], P["spr"], P["anc"], P["sx"], P["sy"], P["scale"]
        if a.get("shadow", True):
            lift = P["floor_y"] - sy
            shadow(img, sx, P["floor_y"], 64 * scale * (1 - min(0.5, lift / 600)), alpha=110, dx=-18 * light.get("dir", 0) * scale)
        if sc.wet and a.get("reflection", True) and not a.get("_crowd") and not P["rot"]: reflection(img, spr, anc, sx, P["floor_y"])
        paste_char(img, spr, anc, sx, sy)
        top = sy - anc[1]; hcy = top + spr.height * HEAD_FRAC; hr = spr.height * 0.11
        if not a.get("_crowd") and not P["rot"]: self._heads.append((sx - spr.width / 2, sx + spr.width / 2, top, top + spr.height * 0.34))
        rain_on = sc.rain_full and shot.get("rain", "normal") != "nenhuma"
        if rain_on and not a.get("_crowd") and a.get("splash", True) and not P["rot"]:
            particles.splash_on(img, t, (sx - hr, hcy - hr * 1.15, sx + hr, hcy - hr * 0.6), n=3, seed=P["idx"])
        if a.get("breath", shot.get("cold", bool(shot.get("snow")))) and P["view"] != "back" and not a.get("_crowd") and not P["rot"]:
            particles.breath_fog(img, t, (sx + (P["facing"] * hr * 0.6 if P["view"] in ("side", "3q") else 0), hcy + hr * 0.55),
                                 P["facing"], seed=P["idx"], strength=min(1, scale))
        fl = a.get("flashlight")
        if fl:
            ang = fl if isinstance(fl, (int, float)) and not isinstance(fl, bool) else (12 if P["facing"] >= 0 else 168)
            o = (sx + P["facing"] * spr.width * 0.42, top + spr.height * 0.47)
            self._beams.append((o, ang, 900 * min(1.4, scale), 22))
            self._lit.append((sx, top + spr.height * 0.4, spr.height * 0.5))
        elif not a.get("_crowd"):
            self._lit_soft.append((sx, top + spr.height * 0.4, spr.height * 0.42))

    def wall_shadows(self, img, prepared, shot):
        ws = shot.get("wall_shadow")
        if not ws: return
        cfg = ws if isinstance(ws, dict) else {}
        lx, ly = cfg.get("light", [540, 600]); alpha = cfg.get("alpha", 0.5); k = cfg.get("scale", 1.35)
        for P in prepared:
            if P["a"].get("_crowd"): continue
            spr = P["spr"]; m = spr.split()[3].point(lambda v: int(v * alpha))
            m = m.resize((int(spr.width * k), int(spr.height * k))).filter(ImageFilter.GaussianBlur(cfg.get("blur", 7)))
            dx = (P["sx"] - lx) * cfg.get("spread", 0.55)
            x = P["sx"] + dx - m.width / 2; y = P["sy"] - P["anc"][1] * k - cfg.get("raise", 140) + (P["sy"] - ly) * 0.0
            img.paste((0, 0, 0), (int(x), int(y)), m)

    # ---------------- enquadramento (planos de cinema) ----------------
    # aberto   = o cenário inteiro (zoom 1), para situar o lugar
    # conjunto = todos os personagens do plano de corpo inteiro, grandes (ocupam ~44% da altura), fundo levemente desfocado
    # medio    = um personagem da cabeça até os joelhos, enchendo o quadro, fundo desfocado (padrão com 1 personagem)
    # close    = só o rosto (camera.close, já existente)
    # Padrão (spec "plano_padrao", "auto" se ausente): plano com personagens e sem zoom/close/follow escolhe sozinho:
    # 1 personagem -> medio, 2 ou mais -> conjunto. "plano_padrao": "aberto" mantém o comportamento antigo.
    PLANOS = ("aberto", "conjunto", "medio", "close")

    def _visiveis(self, shot, rel):
        acts = []
        for i, a in enumerate(shot.get("actors", [])):
            if a.get("fg") or a.get("_crowd") or a.get("carried_by"): continue
            if rel < a.get("enter", -1e9) or rel > a.get("exit", 1e9): continue
            acts.append((i, a))
        return acts

    def plano_de(self, shot, sc, rel=None):
        cam = shot.get("camera", {})
        p = cam.get("plano")
        if p: return p
        if shot.get("type", "scene") != "scene" or any(k in cam for k in ("zoom", "close", "follow", "vertigo")): return "aberto"
        padrao = self.spec.get("plano_padrao", "auto")
        if padrao in ("conjunto", "medio"): return padrao
        if padrao != "auto": return "aberto"
        from .mapa import MAPA
        if MAPA.get(sc.name, {}).get("chao") is None: return "aberto"      # closes de objeto (rádio, cftv...)
        acts = [a for a in shot.get("actors", []) if not a.get("fg") and not a.get("_crowd") and not a.get("carried_by")]
        if not acts or any(a.get("fg") for a in shot.get("actors", [])): return "aberto"
        return "medio" if len(acts) == 1 else "conjunto"

    def enquadrar(self, plano, shot, sc, camx, rel, norm):
        from .rig import char_def, CH
        cam = shot.get("camera", {})
        acts = self._visiveis(shot, rel)
        alvo = cam.get("alvo")
        if alvo is not None:
            alvo = alvo if isinstance(alvo, list) else [alvo]
            acts = [ia for ia in acts if ia[0] in alvo] or acts
        if not acts: return 1.0, 0.0, 0.0
        if plano == "medio": acts = acts[:1]      # o primeiro da lista (ou o "alvo")
        caixas = []
        for i, a in acts:
            x, y, s = self.actor_state(a, sc, rel, norm)
            cd = char_def(a["char"], self.custom.get(a["char"]))
            h = CH * 0.5 * s * cd.get("scale", 1.0) * 0.93
            wx = x - camx * a.get("depth", sc.depths[1])
            caixas.append((wx, y, h))
        push = 1 + 0.035 * norm * cam.get("push", 1.0)                 # aproximação lenta: o plano nunca fica parado
        if plano == "medio":
            wx, y, h = caixas[0]
            z = min(6.0, max(1.0, 1.22 * H / h)) * push
            x0 = wx - W / 2 / z; y0 = (y - h * 0.88) - 0.27 * H / z
        else:
            hmax = max(c[2] for c in caixas)
            xa = min(c[0] for c in caixas) - 0.3 * hmax; xb = max(c[0] for c in caixas) + 0.3 * hmax
            top = min(c[1] - c[2] * 0.88 for c in caixas); bot = max(c[1] for c in caixas)
            z = min(0.52 * H / max(1, bot - top), 0.98 * W / max(1, xb - xa), 3.0)
            z = max(1.0, z) * push
            x0 = (xa + xb) / 2 - W / 2 / z; y0 = bot - 0.76 * H / z
        z *= val(cam.get("zoom_k", 1.0), rel, norm, 1.0)
        return z, x0, y0

    # ---------------- câmera ----------------
    def camera(self, shot, sc, t, rel, norm):
        cam = shot.get("camera", {})
        base_plano = self.plano_de(shot, sc)
        if self.redes and base_plano in ("conjunto", "medio") and not any(k in cam for k in ("zoom", "close", "follow", "vertigo")):
            for (s0, s1, var, quem) in self.cortes(shot):
                if s0 <= shot["start"] + rel < s1 or s1 == shot["end"]:
                    if var == 1:      # close em quem fala
                        cam = dict(cam, plano="close", alvo=quem)
                    elif var == 2:    # o outro enquadramento: conjunto vira médio em quem fala; médio vira corpo inteiro
                        cam = dict(cam, plano="medio", alvo=quem) if base_plano == "conjunto" else dict(cam, plano="conjunto", alvo=quem)
                    shot = dict(shot, camera=cam); norm = c01((shot["start"] + rel - s0) / max(1e-6, s1 - s0))
                    break
        camx = val(cam.get("x", 0), rel, norm, 0)
        z = val(cam.get("zoom", 1.0), rel, norm, 1.0)
        cx = val(cam.get("cx", 0.5), rel, norm, 0.5); cy = val(cam.get("cy", 0.5), rel, norm, 0.5)
        actors = shot.get("actors", [])
        close = val(cam.get("close"), rel, norm); follow = val(cam.get("follow"), rel, norm)
        if close is None and cam.get("plano") == "close":
            al = cam.get("alvo", 0); close = al[0] if isinstance(al, list) else al
        if close is not None and close != "none" and int(close) < len(actors):
            a = actors[int(close)]; x, y, s = self.actor_state(a, sc, rel, norm)
            sh = 760 * s * 0.5 * 0.95
            if "close_zoom" in cam or self.spec.get("plano_padrao", "auto") == "aberto":
                z = val(cam.get("close_zoom", 2.9), rel, norm, 2.9)
            else:                                    # close de verdade: cabeça e ombros enchendo o quadro, em qualquer distância
                z = min(9.0, max(2.0, 2.3 * H / sh))
            hx, hy = x - camx * sc.depths[1], y - sh * (1 - HEAD_FRAC) * 0.97
            x0, y0 = hx - W / 2 / z, hy - (820 if "close_zoom" in cam or self.spec.get("plano_padrao", "auto") == "aberto" else (880 if self.redes else 960)) / z
            k = ease(c01(rel / cam.get("close_in", 0.0001)))
            z = lerp(1.0, z, k); x0 = lerp(0, x0, k); y0 = lerp(0, y0, k)
        elif follow is not None and int(follow) < len(actors):
            a = actors[int(follow)]; x, y, s = self.actor_state(a, sc, rel, norm)
            z = val(cam.get("zoom", 1.3), rel, norm, 1.3)
            camx = val(cam.get("x", (x - 540) * 0.25), rel, norm)
            x0 = (x - camx * sc.depths[1]) - W / 2 / z
            y0 = (H - H / z) * cy
        elif self.plano_de(shot, sc) in ("conjunto", "medio"):
            z, x0, y0 = self.enquadrar(self.plano_de(shot, sc), shot, sc, camx, rel, norm)
        else:
            x0 = (W - W / z) * cx; y0 = (H - H / z) * cy
        if self.redes and shot.get("hook"):   # gancho: entra num "soco" de zoom que assenta em 0,4 s
            cxw, cyw = x0 + W / 2 / z, y0 + H / 2 / z
            z = z * (1 + 0.18 * (1 - ease_out(c01(rel / 0.4)))); x0, y0 = cxw - W / 2 / z, cyw - H / 2 / z
        dx, dy = fx.shake_offset(t, shot.get("shake", []) + shot.get("scare", []), amp=cam.get("shake_amp", 16))
        rot = 0.0
        hh = val(cam.get("handheld"), rel, norm)
        if hh:
            hx_, hy_, hr_ = fx.handheld(t, hh if not isinstance(hh, bool) else 10)
            dx += hx_; dy += hy_
        x0 -= dx / z; y0 -= dy / z
        x0 = max(-30, min(W - W / z + 30, x0)); y0 = max(-30, min(H - H / z + 30, y0))
        return camx, (z, x0, y0), rot

    # ---------------- planos ----------------
    def scene_frame(self, shot, t, t_anim=None):
        t_anim = t if t_anim is None else t_anim
        trav = shot.get("travelling")
        tdir = trav.get("dir") if isinstance(trav, dict) else None
        sc = scenes.get(shot["scene"], "frente" if tdir in ("frente", "fundo") else bool(trav))
        rel = t - shot["start"]; norm = c01(rel / max(1e-6, shot["end"] - shot["start"]))
        props = {k: val(v, rel, norm) for k, v in shot.get("props", {}).items()}
        if trav:
            from .travelling import posicao
            tv = dict(trav) if isinstance(trav, dict) else {"speed": trav}
            if tv.get("speed", 300) is True: tv["speed"] = 300 * (shot.get("actors") or [{}])[0].get("facing", 1)
            dur = shot["end"] - shot["start"]
            props["_scroll"], props["_chegada"] = posicao(tv, rel, dur); props["_frente"] = bool(tv.get("frente"))
            if tdir == "frente": props["_scroll"] = -props["_scroll"]   # vêm para a câmera: o caminho fica para trás
            props["_parou"] = bool(tv.get("chegada")) and rel > dur - 0.12 - 0.0 and props["_chegada"] is not None and \
                abs(posicao(tv, rel, dur)[0] - posicao(tv, dur, dur)[0]) < 4
        if props.get("level") == "auto": props["level"] = min(1.0, self.level(props.get("level_voice", "_all"), t) * 0.9)
        props["_hand"] = partes.resolver(False if props.get("hand") is False else shot.get("hand"), sc.name, self.locked, self.custom)
        props["_avoid"] = self._avoid
        shot["_props"] = props
        # clima
        saved = (sc.rain_strength, sc.rain_full, sc.fog_cfg)
        rn = shot.get("rain")
        if rn is not None:
            lvl = RAIN_LEVELS.get(rn, 1.0)
            sc.rain_strength = lvl * (saved[0] if saved[0] else 1.0)
            if lvl == 0: sc.rain_full = False
        fogv = val(shot.get("fog"), rel, norm)
        if fogv is not None: sc.fog_cfg = dict(y=1100, height=1500, alpha=min(0.95, fogv), col=(120, 128, 148), speed=14) if fogv > 0 else None
        camx, cam, rot = self.camera(shot, sc, t_anim, rel, norm)
        z, x0, y0 = cam
        img = sc.render_back(t_anim, camx, props)
        vz = val(shot.get("camera", {}).get("vertigo"), rel, norm)
        if vz and vz != 1.0:
            cw, ch = W / vz, H / vz
            img = crop_zoom(img, (W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)
        focus_on = val(shot.get("camera", {}).get("focus"), rel, norm)
        if z != 1.0 or x0 or y0:
            img = crop_zoom(img, max(0, x0), max(0, y0), min(W, x0 + W / z), min(H, y0 + H / z))
            dof = shot.get("camera", {}).get("dof", 1.0) * max(0.0, (z - 1.15) * 2.2)
            if focus_on is not None: dof = max(dof, 2.5)
            if dof > 0.3: img = fast_blur(img, dof) if dof >= 6 else img.filter(ImageFilter.BoxBlur(dof * 0.8))
        light_name, light = self.resolve_light(shot, sc, t_anim)
        actors = list(shot.get("actors", []))
        crowd = shot.get("crowd")
        if crowd:
            for cs in (crowd if isinstance(crowd, list) else [crowd]): actors += particles.crowd_actors(cs, rel * (t_anim - shot["start"]) / max(1e-6, rel) if rel else 0)
        self._beams = []; self._lit = []; self._lit_soft = []
        if props.get("_parou"): actors = [a if a.get("_crowd") else dict(a, walk=False, run=False) for a in actors]   # chegou: param de andar
        actors = self.link_actors(actors, sc, rel, norm)
        order = sorted([(i, a) for i, a in enumerate(actors) if not a.get("fg")], key=lambda ia: self.actor_state(ia[1], sc, rel, norm)[1] + ia[1].get("_zbias", 0))
        prepared = []
        for i, a in order:
            if rel < a.get("enter", -1e9) or rel > a.get("exit", 1e9): continue
            prepared.append(self.prepare_actor(a, sc, shot, t_anim, rel, norm, camx, cam, light, focus_on, i))
        for P in prepared:   # quem está no colo: centro do corpo sobre os braços de quem carrega
            cb = P["a"].get("carried_by")
            C = next((Q for Q in prepared if Q["a"]["char"] == cb), None) if P["a"].get("_carried") else None
            if C:
                ch = C["spr"].height
                P["sx"] = C["sx"] + C["facing"] * ch * 0.12 - (P["spr"].width / 2 - P["anc"][0])
                P["sy"] = C["sy"] - ch * 0.5 + (P["anc"][1] - P["spr"].height / 2); P["floor_y"] = C["floor_y"]
        self.wall_shadows(img, prepared, shot)
        for P in prepared: self.paint_actor(img, P, sc, shot, t_anim, light)
        self.paint_holds(img, prepared)
        for (o, ang, ln, sp) in self._beams: particles.flashlight(img, t_anim, o, ang, ln, spread=sp)
        if shot.get("dust"): particles.dust(img, t_anim, n=shot["dust"] if isinstance(shot["dust"], int) else 60)
        sc._cam = (z, x0, y0)
        img = sc.render_front(img, t_anim, camx, props, self.flashes)
        sc._cam = None
        if shot.get("snow"): fx.snow(img, t_anim, shot["snow"] if not isinstance(shot["snow"], bool) else 1.0)
        dk = val(shot.get("dark"), rel, norm, 0) or 0
        if dk:
            dk *= (1 - fx.flash_amount(t_anim, self.flashes))
            circles = [tuple(c) for c in shot.get("lights", [])] + self._lit
            img = fx.darkness(img, dk, beams=self._beams, circles=circles, soft_circles=self._lit_soft)
        for i, a in enumerate(actors):
            if not a.get("fg") or rel < a.get("enter", -1e9) or rel > a.get("exit", 1e9): continue
            x, y = val(a.get("x", 200), rel, norm), val(a.get("y", 2350), rel, norm)
            spr, anc = render_char(a["char"], view=a.get("view", "back"), emotion="neutral", pose=val(a.get("pose", "idle"), rel, norm), t=t_anim,
                                   scale=val(a.get("scale", 3.0), rel, norm), light=LIGHTS[a.get("light", "silhouette")], facing=a.get("facing", 1),
                                   custom=self.custom.get(a["char"]), talk=min(1, self.level(a.get("voice", a["char"]), t, 4)))
            spr = spr.filter(ImageFilter.GaussianBlur(a.get("blur", 5)))
            paste_char(img, spr, anc, x, y)
        img = fx.grade(img, shot.get("grade", sc.grade))
        tm, tm_prev, tm_dt = change(shot.get("time"), rel)
        if tm:
            cur = fx.time_of_day(img, tm)
            if tm_prev and tm_dt < 1.5: cur = Image.blend(fx.time_of_day(img, tm_prev), cur, tm_dt / 1.5)
            img = cur
        if shot.get("effect") == "peephole": img = fx.peephole(img)
        rot += val(shot.get("camera", {}).get("rot", 0.0), rel, norm, 0.0)
        if abs(rot) > 0.25: img = crop_zoom(img.rotate(rot, resample=Image.NEAREST, fillcolor=(0, 0, 0)), W * 0.012, H * 0.012, W * 0.988, H * 0.988)
        sc.rain_strength, sc.rain_full, sc.fog_cfg = saved
        return img

    def detail_frame(self, shot, t, t_anim):
        rel = t - shot["start"]; norm = c01(rel / max(1e-6, shot["end"] - shot["start"]))
        params = {}
        for k, v in shot.get("params", {}).items():
            params[k] = v
            params[k + "_now"] = val(v, rel, norm)
        subj = {"maçaneta": "macaneta", "relógio": "relogio"}.get(shot["subject"], shot["subject"])
        hspec = shot.get("hand", False if params.get("hand") is False else None)
        params["_hand"] = partes.resolver(hspec, subj, self.locked, self.custom)
        if subj == "olho" and hspec: params["_hand"] = (partes.visual(hspec if isinstance(hspec, str) else hspec.get("of"), self.locked, self.custom), None)
        params["_avoid"] = self._avoid
        img = detail.render_detail(shot["subject"], t_anim - shot["start"], params)
        img = fx.grade(img, shot.get("grade", "noite"))
        cam = shot.get("camera", {})
        z = val(cam.get("zoom", [1.0, 1.08]), rel, norm, 1.0)
        dx, dy = fx.shake_offset(t, shot.get("shake", []) + shot.get("scare", []))
        if cam.get("handheld", True):
            hx, hy, _ = fx.handheld(t, cam.get("handheld", 8) if not isinstance(cam.get("handheld"), bool) else 8); dx += hx; dy += hy
        return fx.apply_camera(img, z, 0.5, 0.5, dx, dy)

    def recap_frame(self, shot, t):
        rel = t - shot["start"]; dur = shot["end"] - shot["start"]
        path = os.path.join(self.base, shot.get("from", ""))
        moments = shot.get("moments")  # alternativa sem o arquivo do episódio anterior: [{"scene": ..., "actors": [...]}, ...]
        n = len(moments) if moments and not os.path.isfile(path) else len(shot.get("times", [5.0]))
        seg = dur / n; i = min(n - 1, int(rel / seg))
        if moments and not os.path.isfile(path):
            m0 = shot["start"] + i * seg
            mshot = dict(moments[i], start=m0, end=m0 + seg)
            mshot.setdefault("camera", {"zoom": [1.0, 1.06]})
            img = self.scene_frame(mshot, t)
        elif os.path.isfile(path):
            if path not in self._recap_cache: self._recap_cache[path] = Episode(path)
            other = self._recap_cache[path]
            to = shot.get("times", [5.0])[i] + (rel - i * seg) * 0.7
            oshot = next((s for s in other.shots if s["start"] <= to < s["end"] and s.get("type", "scene") == "scene"), None)
            if oshot is None: img = Image.new("RGB", (W, H), (10, 10, 14))
            else:
                other._heads = []; other._beams = []; other._treal = to
                img = other.scene_frame(oshot, to)
        else:  # sem arquivo e sem momentos: fundo de TV com chiado e só as frases
            img = Image.fromarray(np.random.default_rng(int(t * 30)).integers(10, 60, (H // 4, W // 4, 1), dtype=np.uint8).repeat(3, 2)).resize((W, H))
        img = ImageEnhance.Color(img).enhance(0.3)
        img = fx.apply_camera(img, 1.04 + 0.04 * ((rel - i * seg) / seg))
        d = ImageDraw.Draw(img)
        for y in range(0, H, 6): d.line([(0, y), (W, y)], fill=(0, 0, 0), width=1)
        off = int((t * 300) % H); d.rectangle([0, off, W, off + 14], fill=(200, 200, 210))
        lab = shot.get("label", "ANTERIORMENTE...")
        d.rectangle([0, 470, W, 590], fill=(12, 12, 16))
        text_center(d, lab, W / 2, 530, font("title", 72), (255, 214, 60))
        lines = shot.get("lines", [])
        if i < len(lines):
            text_center(d, lines[i], W / 2, 1480, font("title", 78 if len(lines[i]) < 22 else 60), (250, 250, 248), 8)
        if rel - i * seg < 0.08: img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.6)
        return img

    def title_frame(self, shot, t):
        img = Image.new("RGB", (W, H), (8, 10, 16))
        if shot.get("scene"):
            bg = self.scene_frame(dict(shot), t).filter(ImageFilter.GaussianBlur(10))
            img = Image.blend(bg, img, 0.55)
        d = ImageDraw.Draw(img); a = c01((t - shot["start"] - 0.2) / 0.4)
        text_center(d, shot.get("title", ""), W / 2, 760, font("title", 140), tuple(int(v * a) for v in CREAM))
        text_center(d, shot.get("subtitle", ""), W / 2, 880, font("mono", 46), tuple(int(v * a) for v in RED))
        stp = shot.get("stamp")
        if stp: fx.stamp(img, t, stp["t"], stp.get("top", "A MAIORIA ESCOLHEU"), stp["word"], 1250)
        return img

    def choice_frame(self, shot, t):
        img = Image.new("RGB", (W, H), (10, 10, 14))
        for i, key in enumerate(("a", "b")):
            opt = shot[key]
            o = dict(opt, start=shot["start"], end=shot["end"])
            o.setdefault("camera", {}); o["camera"] = dict({"plano": "aberto"}, **o["camera"])   # o recorte já aproxima
            f = self.scene_frame(o, t)
            cx = opt.get("crop_x", 270)
            part = f.crop((cx, 300, cx + W // 2, 1450)).resize((W // 2 - 6, 1150))
            img.paste(part, (0 if i == 0 else W // 2 + 6, 300))
        d = ImageDraw.Draw(img)
        d.rectangle([W // 2 - 6, 300, W // 2 + 6, 1450], fill=(235, 232, 225))
        p = ease_out(c01((t - shot["start"]) / 0.4)); y = lerp(1560, 1395, p)
        d.rounded_rectangle([40, y - 64, W // 2 - 40, y + 64], 26, fill=(235, 232, 225))
        d.rounded_rectangle([W // 2 + 40, y - 64, W - 40, y + 64], 26, fill=RED)
        for k, (lab, x, col) in enumerate(((shot["a"]["label"], 320, (20, 20, 20)), (shot["b"]["label"], W // 2 + 320, (255, 255, 255)))):
            text_center(d, "AB"[k], x - 210, y, font("title", 84), col)
            text_center(d, lab, x, y, font("title", 70 if len(lab) < 9 else 54), col)
        ec = shot.get("end_card")
        if ec and t >= ec["t"]:
            k = c01((t - ec["t"]) / 0.4)
            d.rectangle([0, 1690, W, 1880], fill=(int(200 * k), int(40 * k), int(35 * k)))
            text_center(d, ec["text"], W / 2, 1785, font("title", 80), tuple(int(v * k) for v in CREAM))
        return img

    def draw_overlays(self, img, shot, t):
        d = ImageDraw.Draw(img)
        hk = shot.get("hook")
        if hk:
            rel = t - shot["start"]; p = ease_out(c01(rel / 0.2))
            txt = hk["text"] if isinstance(hk, dict) else str(hk)
            y = hk.get("y", 860) if isinstance(hk, dict) else 860
            lines = txt.split("\n")
            if self.redes:   # aparece palavra por palavra desde o 1º quadro (o 1º quadro vira a capa no feed)
                passo = hk.get("passo", 0.16) if isinstance(hk, dict) else 0.16; n = 0
                for k, line in enumerate(lines):
                    f = font("title", 112 if len(line) < 16 else 90)
                    bb = d.textbbox((0, 0), line, font=f); w = bb[2] - bb[0]; yy = y + k * 138
                    ws = line.split(); vis = [wd for j, wd in enumerate(ws) if rel >= (n + j) * passo]; n += len(ws)
                    if not vis: continue
                    d.rectangle([W / 2 - w / 2 - 28, yy - 66, W / 2 + w / 2 + 28, yy + 66], fill=RED if k == len(lines) - 1 else (12, 12, 16))
                    d.text((W / 2 - w / 2 - bb[0], yy), " ".join(vis), font=f, fill=(255, 255, 255), anchor="lm")
            else:
              for k, line in enumerate(lines):
                f = font("title", 104 if len(line) < 16 else 84)
                bb = d.textbbox((0, 0), line, font=f); w = bb[2] - bb[0]; yy = y + k * 130
                d.rectangle([W / 2 - w / 2 - 26, yy - 62, W / 2 - w / 2 - 26 + (w + 52) * p, yy + 62], fill=RED if k == len(lines) - 1 else (12, 12, 16))
                if p > 0.6: text_center(d, line, W / 2, yy, f, (255, 255, 255))
        for o in shot.get("overlay", []):
            a, b = o.get("t", [shot["start"], shot["end"]])
            if not (a <= t < b): continue
            p = ease_out(c01((t - a) / 0.3)) * (1 - ease(c01((t - (b - 0.25)) / 0.25)))
            if o["type"] == "phone":
                px, py = o.get("x", 560), int(lerp(2100, o.get("y", 980), p))
                d.rounded_rectangle([px - 125, py - 230, px + 125, py + 230], 30, fill=(16, 16, 20), outline=(70, 70, 80), width=6)
                d.rounded_rectangle([px - 108, py - 205, px + 108, py + 205], 20, fill=(36, 40, 52))
                for k, line in enumerate(o.get("text", [])):
                    text_center(d, line, px, py - 30 + k * 72, font("title", 62), tuple(o.get("color", (255, 110, 100))))
            elif o["type"] == "text":
                col = tuple(int(v * p) for v in o.get("color", CREAM))
                text_center(d, o["text"], W / 2, o.get("y", 900), font("title", o.get("size", 120)), col, 8)
            elif o["type"] == "stamp":
                fx.stamp(img, t, a, o.get("top", ""), o.get("word", ""), o.get("y", 1000))
            elif o["type"] == "comment":
                pass  # desenhado no fim do quadro, depois dos filtros (ver draw_comments)

    def draw_comments(self, img, shot, t):
        """Cartões de comentário ficam por cima de tudo (filtro de desenho, cor, grão), como num app."""
        for o in shot.get("overlay", []):
            if o.get("type") != "comment": continue
            a, b = o.get("t", [shot["start"], shot["end"]])
            if not (a <= t < b): continue
            p = ease_out(c01((t - a) / 0.35)) * (1 - ease(c01((t - (b - 0.3)) / 0.3)))
            text.comment_card(img, o, p)

    # ---------------- modo redes: selo, voto, pergunta no meio e contagem antes da escolha ----------------
    def pergunta(self):
        """(ini, fim, texto) da pergunta na tela no meio do episódio, ou None."""
        pq = self.spec.get("pergunta")
        if not self.redes or pq is False: return None
        pq = pq if isinstance(pq, dict) else ({"text": pq} if isinstance(pq, str) else {})
        if not pq and not any(s.get("type") == "choice" for s in self.shots): return None
        t0 = pq.get("t")
        if t0 is None:   # começo do 1º plano de cena depois da metade (fora do gancho e do final)
            cand = [s["start"] for s in self.shots if s.get("type", "scene") == "scene" and not s.get("hook")
                    and self.total * 0.48 <= s["start"] <= self.total * 0.75]
            if not cand: return None
            t0 = cand[0] + 0.4
        return (t0, t0 + pq.get("dur", 3.0), pq.get("text", "E VOCÊ, O QUE FARIA?"))

    def draw_redes(self, img, shot, t):
        typ = shot.get("type", "scene")
        if shot.get("hook") or typ in ("loop", "title", "recap"): return
        d = ImageDraw.Draw(img); sp = self.spec; h0 = self._hook_end
        # selo da série (no lugar da cartela de título): grande logo depois do gancho, depois discreto
        ep, tot = sp.get("episode"), sp.get("episodes_total")
        if ep and typ != "choice" and not any(s.get("type") == "title" for s in self.shots):
            rel = t - h0; big = rel < 3.5
            lab = f"EP {ep}/{tot}" if tot else f"EP {ep}"
            f = font("title", 64 if big else 42); bb = d.textbbox((0, 0), lab, font=f); w = bb[2] - bb[0]
            p = ease_out(c01(rel / 0.3)) if big else 1.0
            x1 = W - 56; x0 = x1 - w - 44; y0 = 236 - (1 - p) * 120; y1 = y0 + (92 if big else 66)
            d.rounded_rectangle([x0, y0, x1, y1], 18, fill=RED if big else (150, 30, 30))
            text_center(d, lab, (x0 + x1) / 2, (y0 + y1) / 2, f, (255, 255, 255))
            if big and sp.get("series_title"):
                text_center(d, sp["series_title"], (x0 + x1) / 2 - 10, y1 + 30, font("mono", 30), (235, 232, 225), 3)
            # carimbo do voto da maioria, rápido e no alto
            if sp.get("voto") and 0.2 <= rel < 3.4:
                q = ease_out(c01((rel - 0.2) / 0.25)) * (1 - ease_out(c01((rel - 3.1) / 0.3)))
                yy = 470 - (1 - q) * 60
                fw = font("title", 96); bw = d.textbbox((0, 0), sp["voto"], font=fw); ww = max(bw[2] - bw[0], 420)
                d.rounded_rectangle([W / 2 - ww / 2 - 34, yy - 92, W / 2 + ww / 2 + 34, yy + 70], 24, fill=(12, 12, 16), outline=RED, width=6)
                text_center(d, "A MAIORIA ESCOLHEU", W / 2, yy - 52, font("mono", 32), (235, 232, 225))
                text_center(d, sp["voto"], W / 2, yy + 14, fw, RED)
        # pergunta na tela no meio do episódio (puxa comentário)
        pq = self.pergunta()
        if pq and pq[0] <= t < pq[1] and typ != "choice":
            q = ease_out(c01((t - pq[0]) / 0.3)) * (1 - ease_out(c01((t - (pq[1] - 0.3)) / 0.3)))
            yy = 560 - (1 - q) * 80
            fq = font("title", 72); bq = d.textbbox((0, 0), pq[2], font=fq); ww = min(W - 220, bq[2] - bq[0])
            d.rounded_rectangle([W / 2 - 40 - ww / 2 - 36, yy - 70, W / 2 - 40 + ww / 2 + 36, yy + 96], 28, fill=(240, 236, 228))
            text_center(d, pq[2], W / 2 - 40, yy - 8, fq if bq[2] - bq[0] <= W - 220 else font("title", 56), (20, 20, 22))
            text_center(d, "COMENTA AQUI EMBAIXO", W / 2 - 40, yy + 60, font("mono", 30), RED)
        # contagem regressiva antes da tela A/B
        cs = next((s for s in self.shots if s.get("type") == "choice"), None)
        if cs and cs["start"] - 3 <= t < cs["start"] and typ != "choice":
            k = cs["start"] - t; n = int(k) + 1; fr = 1 - (k - int(k))
            pop = 1 + 0.35 * (1 - ease_out(c01(fr / 0.25)))
            r = 92 * pop; cx, cy = W - 190, 470            # canto direito, abaixo do selo: não cobre rostos nem legenda
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(12, 12, 16), outline=RED, width=10)
            d.arc([cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18], -90, -90 + 360 * (1 - fr), fill=(255, 255, 255), width=8)
            text_center(d, str(n), cx, cy, font("title", int(150 * pop)), (255, 255, 255))
            text_center(d, "O QUE VOCÊ", cx - 10, cy + 92 + 52, font("title", 54), (255, 255, 255), 7)
            text_center(d, "FARIA?", cx - 10, cy + 92 + 108, font("title", 54), (255, 214, 60), 7)

    # ---------------- cortes automáticos (modo redes) ----------------
    def cortes(self, shot):
        """Divide um plano longo em trechos de ~2,4–3,8 s nas pausas da fala: [(ini, fim, variante, alvo)]."""
        key = (shot["start"], shot["end"])
        if key in self._cortes_cache: return self._cortes_cache[key]
        a0, b0 = shot["start"], shot["end"]; res = [(a0, b0, 0, None)]
        acts = [i for i, a in enumerate(shot.get("actors", [])) if not a.get("fg") and not a.get("_crowd")]
        cam = shot.get("camera", {})
        ok = (self.redes and self.spec.get("cortes_auto", True) and cam.get("cortes", True) and shot.get("type", "scene") == "scene"
              and acts and b0 - a0 >= 4.8 and not shot.get("hook") and not shot.get("travelling"))
        if ok:
            cand = sorted({round(s0, 2) for s0, s1, _, _ in self.subs if a0 + 2.2 <= s0 <= b0 - 1.8})
            pts = [a0]
            for c in cand:
                if c - pts[-1] >= 2.4: pts.append(c)
            while b0 - pts[-1] > 4.6: pts.append(round(pts[-1] + 3.0, 2))   # sem fala por muito tempo: corta mesmo assim
            if b0 - pts[-1] < 1.8 and len(pts) > 1: pts.pop()
            pts.append(b0)
            res = []
            for k in range(len(pts) - 1):
                s0, s1 = pts[k], pts[k + 1]
                vozes = {}
                for x0, x1, _, v in self.subs:
                    ov = min(x1, s1) - max(x0, s0)
                    if ov > 0: vozes[v] = vozes.get(v, 0) + ov
                quem = None
                if vozes:
                    fala = max(vozes, key=vozes.get)
                    quem = next((i for i in acts if shot["actors"][i].get("voice", shot["actors"][i]["char"]) == fala), None)
                if quem is None: quem = acts[k % len(acts)]
                res.append((s0, s1, k % 3, quem))
        self._cortes_cache[key] = res
        return res

    def pick_sub_y(self, shot):
        if shot.get("sub_y"): return shot["sub_y"]
        av = getattr(self, "_avoid", [])
        if av:   # braço/mão em cena: legenda numa faixa livre (braço > objeto em destaque > cabeças)
            wd = text.sub_width(self._treal, self.subs) or 600
            sx0, sx1 = W / 2 - wd / 2 - 20, W / 2 + wd / 2 + 20
            foco = partes.FOCO.get(shot.get("scene") or {"maçaneta": "macaneta", "relógio": "relogio"}.get(shot.get("subject"), shot.get("subject")), [])
            def bate(y, itens):
                return any(partes.bate_retangulo(it, (sx0, y - 80, sx1, y + 60)) for it in itens)
            def cabeca(y):
                return any(h[1] > 120 and h[0] < W - 120 and h[2] < y + 160 and h[3] > y - 80 for h in self._heads)
            cands = tuple(c for c in (text.SUB_Y, 1600, 1440, 1700, 1380, 1250, 900, 780) if c <= text.SAFE_Y_MAX)
            for rects in (av + foco, foco, av):   # 1º livre de tudo; 2º só o objeto em destaque (pode passar sobre a manga)
                for y in cands:
                    if not bate(y, rects) and not cabeca(y): return y
        y = text.SUB_Y; band = (y - 170, y + 70)
        hits = [h for h in self._heads if h[1] > 120 and h[0] < W - 120 and h[2] < band[1] and h[3] > band[0]]
        if not hits: return y
        top = min(h[2] for h in hits); bot = max(h[3] for h in hits)
        if top - 70 >= 760: return top - 70
        return min(text.SAFE_Y_MAX, 1640, bot + 150)

    def frame(self, t):
        self._heads = []; self._beams = []; self._treal = t; self._avoid = []
        shot = next((s for s in self.shots if s["start"] <= t < s["end"]), self.shots[-1])
        typ = shot.get("type", "scene")
        if typ == "loop":   # o gancho de trás para frente: o último quadro é o primeiro, e o vídeo emenda sem pulo
            return self.frame(max(0.0, shot["end"] - t - 1.0 / self.fps))
        slow = shot.get("slowmo")
        t_anim = shot["start"] + (t - shot["start"]) * slow if slow else t
        if typ == "title": img = self.title_frame(shot, t)
        elif typ == "choice": img = self.choice_frame(shot, t)
        elif typ == "detail": img = self.detail_frame(shot, t, t_anim)
        elif typ == "recap": img = self.recap_frame(shot, t)
        else: img = self.scene_frame(shot, t, t_anim)
        if shot.get("layers"):
            progress = max(0.0, min(1.0, (t-shot["start"])/max(0.001, shot["end"]-shot["start"])))
            img = composite_layers(img, shot["layers"], self.base, progress)
        self.draw_overlays(img, shot, t)
        if shot.get("bloom", self.spec.get("bloom", True)) and typ in ("scene", "detail"): img = fx.bloom(img)
        if shot.get("lens_drops"): img = fx.lens_drops(img, t)
        sa = fx.scare_amount(t, shot.get("scare", []))
        if sa: img = Image.blend(fx.chromatic(img, 18 * sa), Image.new("RGB", (W, H), (255, 255, 255)), 0.25 * sa if sa > 0.85 else 0)
        tn = shot.get("tint", self.spec.get("tint"))
        if tn and typ != "title": img = fx.tint(img, tn[:3], tn[3] if len(tn) > 3 else 0.15)
        if self.spec.get("style") == "desenho" and typ in ("scene", "detail", "choice"): img = fx.hand_drawn(img)
        img = fx.vignette(img, shot.get("vignette", 1.0)); img = fx.grain(img)
        tr = shot.get("transition", "cut"); dur = shot.get("transition_dur", 0.28)
        rel = t - shot["start"]
        if tr != "cut" and rel < dur: img = fx.transition(img, None, tr, rel / dur)
        self.draw_comments(img, shot, t)
        if self.redes: self.draw_redes(img, shot, t)
        hs = self.hud_state(t)
        if hs and shot.get("hud", typ not in ("title", "recap", "detail") and not shot.get("hook")): text.hud(img, t, hs[0], hs[1], hs[2], hs[3])
        if not shot.get("hook") and typ != "recap":
            sy = self.pick_sub_y(shot) if typ in ("scene", "detail") else shot.get("sub_y", 1590 if typ == "choice" else None)
            text.subtitle(img, t, self.subs, self.speakers, sy, words=self.word_subs)
        if t > self.total - 0.6 and not self.redes: img = Image.blend(img, fx.BLACK, c01((t - (self.total - 0.6)) / 0.6))
        img = apply_profile(img, self.visual_profile)
        return img

    # ---------------- saída ----------------
    def _ffmpeg_video(self, out, with_audio):
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(self.fps), "-i", "-"]
        if with_audio: cmd += ["-i", self.mix_path, "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-shortest"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(self.spec.get("crf", 28)), "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
        return subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def render(self, out=None):
        out = out or os.path.join(self.base, self.spec.get("out", "episodio.mp4"))
        self.build_audio(); n = int(self.total * self.fps); p = self._ffmpeg_video(out, True)
        for i in range(n):
            p.stdin.write(self.frame(i / self.fps).tobytes())
            if i % 300 == 0: print(f"quadro {i}/{n}", flush=True)
        p.stdin.close(); p.wait(); print("pronto:", out, p.returncode); return out

    def render_segment(self, a, b, out):
        self.build_audio(); p = self._ffmpeg_video(out, False)
        for i in range(a, b):
            p.stdin.write(self.frame(i / self.fps).tobytes())
            if (i - a) % 300 == 0: print(f"[{a}-{b}] quadro {i}", flush=True)
        p.stdin.close(); p.wait()

    # ---------------- cache por plano ----------------
    def _chaves_planos(self):
        """Uma chave por plano: muda só se o plano, o que é global ao vídeo, as vozes,
        as fichas dos personagens ou o código do motor mudarem. Som/trilha não entram (não mudam a imagem)."""
        import hashlib, glob
        h = hashlib.sha1()
        for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "*.py"))):
            h.update(open(f, "rb").read())
        for f in [os.path.join(self.base, v) for v in (self.spec.get("voices") or {}).values()] + [os.path.join(self.base, "personagens.json")]:
            if os.path.exists(f): st = os.stat(f); h.update(f"{f}{st.st_size}{st.st_mtime}".encode())
        glob_spec = {k: v for k, v in self.spec.items() if k not in ("shots", "sfx", "music", "out")}
        h.update(json.dumps(glob_spec, sort_keys=True, ensure_ascii=False, default=str).encode())
        base = h.hexdigest(); shots = self.spec["shots"]; chaves = []
        for i, sh in enumerate(sorted(shots, key=lambda x: x["start"])):
            k = hashlib.sha1((base + json.dumps(sh, sort_keys=True, ensure_ascii=False, default=str)).encode()).hexdigest()[:20]
            a, b = int(round(sh["start"] * self.fps)), int(round(sh["end"] * self.fps))
            chaves.append((k, a, min(b, int(self.total * self.fps))))
        return chaves

    def render_cache(self, jobs=2, out=None):
        """Renderiza só os planos que mudaram desde a última vez (o resto vem de series/<serie>/_cache/)."""
        out = out or os.path.join(self.base, self.spec.get("out", "episodio.mp4"))
        self.build_audio()
        cache = os.path.join(self.base, "_cache"); os.makedirs(cache, exist_ok=True)
        chaves = [(k, a, b) for k, a, b in self._chaves_planos() if b > a]
        falta = [(k, a, b) for k, a, b in chaves if not os.path.exists(os.path.join(cache, k + ".mp4"))]
        print(f"cache: {len(chaves) - len(falta)} de {len(chaves)} planos prontos; renderizando {len(falta)}", flush=True)
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        lotes = [[] for _ in range(max(1, jobs))]; carga = [0] * len(lotes)
        for k, a, b in sorted(falta, key=lambda x: x[1] - x[2]):           # maiores primeiro, no lote mais leve
            i = carga.index(min(carga)); lotes[i] += [str(a), str(b), os.path.join(cache, k + ".tmp.mp4")]; carga[i] += b - a
        procs = [subprocess.Popen([sys.executable, "-m", "lofi.render", self.spec_path, "--segments"] + l, cwd=root) for l in lotes if l]
        for pr in procs: pr.wait()
        for k, a, b in falta:
            tmp = os.path.join(cache, k + ".tmp.mp4")
            got = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", tmp],
                                       capture_output=True, text=True).stdout.strip() or 0) if os.path.exists(tmp) else 0
            if abs(got - (b - a) / self.fps) > 0.2:
                print(f"plano {a}-{b} incompleto; refazendo", flush=True); self.render_segment(a, b, tmp)
            os.replace(tmp, os.path.join(cache, k + ".mp4"))
        lst = os.path.join(self.base, "_partes.txt")
        open(lst, "w").write("".join(f"file '{os.path.join(cache, k + '.mp4')}'\n" for k, a, b in chaves))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", self.mix_path,
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", "-movflags", "+faststart", out], check=True)
        os.remove(lst)
        usados = {k + ".mp4" for k, a, b in chaves}
        for f in os.listdir(cache):                                          # planos antigos que não servem mais
            if f not in usados: os.remove(os.path.join(cache, f))
        print("pronto:", out); return out

    def render_parallel(self, jobs=2, out=None):
        out = out or os.path.join(self.base, self.spec.get("out", "episodio.mp4"))
        self.build_audio()
        n = int(self.total * self.fps); cuts = [n * k // jobs for k in range(jobs + 1)]
        procs, parts = [], []
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for k in range(jobs):
            part = os.path.join(self.base, f"_parte{k}.mp4"); parts.append(part)
            procs.append(subprocess.Popen([sys.executable, "-m", "lofi.render", self.spec_path, "--segment", str(cuts[k]), str(cuts[k + 1]), part], cwd=root))
        for pr in procs: pr.wait()
        # confere cada bloco: um processo interrompido gera um bloco curto e o vídeo sairia cortado
        for k, (pr, part) in enumerate(zip(procs, parts)):
            want = (cuts[k + 1] - cuts[k]) / self.fps
            try:
                got = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", part],
                                           capture_output=True, text=True).stdout.strip() or 0)
            except ValueError: got = 0.0
            if pr.returncode != 0 or abs(got - want) > 0.5:
                print(f"bloco {k} incompleto ({got:.1f}s de {want:.1f}s, código {pr.returncode}); refazendo sozinho", flush=True)
                self.render_segment(cuts[k], cuts[k + 1], part)
                got = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", part],
                                           capture_output=True, text=True).stdout.strip() or 0)
                if abs(got - want) > 0.5: raise RuntimeError(f"bloco {k} continua incompleto ({got:.1f}s de {want:.1f}s)")
        lst = os.path.join(self.base, "_partes.txt")
        open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", self.mix_path,
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", "-movflags", "+faststart", out], check=True)
        for p in parts + [lst]:
            try: os.remove(p)
            except OSError: pass
        print("pronto:", out); return out

if __name__ == "__main__":
    ep = Episode(sys.argv[1])
    if "--segment" in sys.argv:
        i = sys.argv.index("--segment"); ep.render_segment(int(sys.argv[i + 1]), int(sys.argv[i + 2]), sys.argv[i + 3]); sys.exit()
    if "--segments" in sys.argv:        # vários planos num processo só (usado pelo cache)
        r = sys.argv[sys.argv.index("--segments") + 1:]
        for i in range(0, len(r) - 2, 3): ep.render_segment(int(r[i]), int(r[i + 1]), r[i + 2])
        sys.exit()
    if "--jobs" in sys.argv:
        j = int(sys.argv[sys.argv.index("--jobs") + 1])
        if "--sem-cache" in sys.argv: ep.render_parallel(j)
        else: ep.render_cache(j)
        sys.exit()
    if "--test" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--test") + 1:]]
        if ep.voices:
            try: ep.build_audio()
            except Exception as e: print("áudio:", e)
        for t in ts:
            path = os.path.join(ep.base, f"_teste_{t:05.1f}.png"); ep.frame(t).save(path); print(path)
    else:
        ep.render()
