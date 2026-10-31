
"""Monta o episódio a partir de um roteiro JSON (ver SPEC.md).

    python3 -m lofi.render episodio.json                  # vídeo completo
    python3 -m lofi.render episodio.json --jobs 2         # vídeo completo em paralelo
    python3 -m lofi.render episodio.json --test 5 12.5    # só alguns quadros (PNG)
"""
import sys, os, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
from .core import W, H, RED, CREAM, font, text_center, ease, ease_out, c01, lerp, keyframe
from . import fx, scenes, text, audio, particles, detail
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

def rotate_about(spr, anc, deg):
    """Gira o sprite em torno do ponto de apoio (pés)."""
    if not deg: return spr, anc
    R = int(math.hypot(spr.width, spr.height)) + 4
    big = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0))
    big.paste(spr, (int(R - anc[0]), int(R - anc[1])), spr)
    big = big.rotate(-deg, center=(R, R), resample=Image.BICUBIC)
    bb = big.getbbox() or (0, 0, 2, 2)
    return big.crop(bb), (R - bb[0], R - bb[1])

class Episode:
    def __init__(self, spec_path):
        self.spec_path = os.path.abspath(spec_path)
        self.base = os.path.dirname(self.spec_path)
        self.spec = json.load(open(spec_path))
        sp = self.spec
        self.fps = sp.get("fps", 30)
        self.shots = sorted(sp["shots"], key=lambda s: s["start"])
        self.total = sp.get("total", max(s["end"] for s in self.shots))
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
        self.mix_path = os.path.join(self.base, "_mix.wav")
        self.env = audio.mix(self.total, self.clips, self.voices, sfx, self.spec.get("music", []), amb, self.mix_path, self.fps) or {}

    def level(self, voice, t, smooth=0):
        e = self.env.get(voice)
        if e is None or len(e) == 0: return 0.0
        i = int(t * self.fps)
        if smooth:
            a, b = max(0, i - smooth), min(len(e), i + smooth + 1)
            return float(np.mean(e[a:b])) if b > a else 0.0
        return float(e[min(len(e) - 1, i)])

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
            if sc.name in ("corredor", "hospital", "mercado", "escola", "delegacia") and not props.get("_lamp_on", True): name = "dark"
            if val(shot.get("dark"), 0, 0, 0) and val(shot.get("dark"), 0, 0, 0) > 0.5: name = "dark"
        if fx.flash_amount(t, self.flashes) > 0.5: name = "flash"
        return name, LIGHTS.get(name, LIGHTS["night"])

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
                               pk=c01(pose_dt / 0.32) if pose_prev else 1.0, blink_force=emo_dt < 0.1,
                               sniff=bool(val(a.get("sniff", False), rel, norm)), prop=val(a.get("prop"), rel, norm))
        rot = val(a.get("rot"), rel, norm)
        if rot is None: rot = {"fallen": 86, "crawl": 72}.get(pose, 0) * (1 if facing >= 0 else -1)
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

    # ---------------- câmera ----------------
    def camera(self, shot, sc, t, rel, norm):
        cam = shot.get("camera", {})
        camx = val(cam.get("x", 0), rel, norm, 0)
        z = val(cam.get("zoom", 1.0), rel, norm, 1.0)
        cx = val(cam.get("cx", 0.5), rel, norm, 0.5); cy = val(cam.get("cy", 0.5), rel, norm, 0.5)
        actors = shot.get("actors", [])
        close = val(cam.get("close"), rel, norm); follow = val(cam.get("follow"), rel, norm)
        if close is not None and close != "none" and int(close) < len(actors):
            a = actors[int(close)]; x, y, s = self.actor_state(a, sc, rel, norm)
            z = val(cam.get("close_zoom", 2.9), rel, norm, 2.9)
            sh = 760 * s * 0.5 * 0.95
            hx, hy = x - camx * sc.depths[1], y - sh * (1 - HEAD_FRAC) * 0.97
            x0, y0 = hx - W / 2 / z, hy - 820 / z
            k = ease(c01(rel / cam.get("close_in", 0.0001)))
            z = lerp(1.0, z, k); x0 = lerp(0, x0, k); y0 = lerp(0, y0, k)
        elif follow is not None and int(follow) < len(actors):
            a = actors[int(follow)]; x, y, s = self.actor_state(a, sc, rel, norm)
            z = val(cam.get("zoom", 1.3), rel, norm, 1.3)
            camx = val(cam.get("x", (x - 540) * 0.25), rel, norm)
            x0 = (x - camx * sc.depths[1]) - W / 2 / z
            y0 = (H - H / z) * cy
        else:
            x0 = (W - W / z) * cx; y0 = (H - H / z) * cy
        dx, dy = fx.shake_offset(t, shot.get("shake", []) + shot.get("scare", []), amp=cam.get("shake_amp", 16))
        rot = 0.0
        hh = val(cam.get("handheld"), rel, norm)
        if hh:
            hx_, hy_, hr_ = fx.handheld(t, hh if not isinstance(hh, bool) else 10)
            dx += hx_; dy += hy_; rot += hr_
        x0 -= dx / z; y0 -= dy / z
        x0 = max(-30, min(W - W / z + 30, x0)); y0 = max(-30, min(H - H / z + 30, y0))
        return camx, (z, x0, y0), rot

    # ---------------- planos ----------------
    def scene_frame(self, shot, t, t_anim=None):
        t_anim = t if t_anim is None else t_anim
        sc = scenes.get(shot["scene"])
        rel = t - shot["start"]; norm = c01(rel / max(1e-6, shot["end"] - shot["start"]))
        props = {k: val(v, rel, norm) for k, v in shot.get("props", {}).items()}
        if props.get("level") == "auto": props["level"] = min(1.0, self.level(props.get("level_voice", "_all"), t) * 0.9)
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
            img = img.transform((W, H), Image.EXTENT, ((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2), Image.BILINEAR)
        focus_on = val(shot.get("camera", {}).get("focus"), rel, norm)
        if z != 1.0 or x0 or y0:
            img = img.transform((W, H), Image.EXTENT, (x0, y0, x0 + W / z, y0 + H / z), Image.BILINEAR)
            dof = shot.get("camera", {}).get("dof", 1.0) * max(0.0, (z - 1.15) * 2.2)
            if focus_on is not None: dof = max(dof, 2.5)
            if dof > 0.3: img = img.filter(ImageFilter.GaussianBlur(dof))
        light_name, light = self.resolve_light(shot, sc, t_anim)
        actors = list(shot.get("actors", []))
        crowd = shot.get("crowd")
        if crowd:
            for cs in (crowd if isinstance(crowd, list) else [crowd]): actors += particles.crowd_actors(cs, rel * (t_anim - shot["start"]) / max(1e-6, rel) if rel else 0)
        self._beams = []; self._lit = []; self._lit_soft = []
        order = sorted([(i, a) for i, a in enumerate(actors) if not a.get("fg")], key=lambda ia: self.actor_state(ia[1], sc, rel, norm)[1])
        prepared = []
        for i, a in order:
            if rel < a.get("enter", -1e9) or rel > a.get("exit", 1e9): continue
            prepared.append(self.prepare_actor(a, sc, shot, t_anim, rel, norm, camx, cam, light, focus_on, i))
        self.wall_shadows(img, prepared, shot)
        for P in prepared: self.paint_actor(img, P, sc, shot, t_anim, light)
        for (o, ang, ln, sp) in self._beams: particles.flashlight(img, t_anim, o, ang, ln, spread=sp)
        if shot.get("dust"): particles.dust(img, t_anim, n=shot["dust"] if isinstance(shot["dust"], int) else 60)
        img = sc.render_front(img, t_anim, camx, props, self.flashes)
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
        if rot: img = img.rotate(rot, resample=Image.BILINEAR, fillcolor=(0, 0, 0)).transform((W, H), Image.EXTENT, (W * 0.012, H * 0.012, W * 0.988, H * 0.988))
        sc.rain_strength, sc.rain_full, sc.fog_cfg = saved
        return img

    def detail_frame(self, shot, t, t_anim):
        rel = t - shot["start"]; norm = c01(rel / max(1e-6, shot["end"] - shot["start"]))
        params = {}
        for k, v in shot.get("params", {}).items():
            params[k] = v
            params[k + "_now"] = val(v, rel, norm)
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
        path = os.path.join(self.base, shot["from"])
        if path not in self._recap_cache: self._recap_cache[path] = Episode(path)
        other = self._recap_cache[path]
        times = shot.get("times", [5.0]); seg = dur / len(times); i = min(len(times) - 1, int(rel / seg))
        to = times[i] + (rel - i * seg) * 0.7
        oshot = next((s for s in other.shots if s["start"] <= to < s["end"] and s.get("type", "scene") == "scene"), None)
        if oshot is None: img = Image.new("RGB", (W, H), (10, 10, 14))
        else:
            other._heads = []; other._beams = []; other._treal = to
            img = other.scene_frame(oshot, to)
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
            f = self.scene_frame(dict(opt, start=shot["start"], end=shot["end"]), t)
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

    def pick_sub_y(self, shot):
        if shot.get("sub_y"): return shot["sub_y"]
        y = text.SUB_Y; band = (y - 170, y + 70)
        hits = [h for h in self._heads if h[1] > 120 and h[0] < W - 120 and h[2] < band[1] and h[3] > band[0]]
        if not hits: return y
        top = min(h[2] for h in hits); bot = max(h[3] for h in hits)
        if top - 70 >= 760: return top - 70
        return min(1640, bot + 150)

    def frame(self, t):
        self._heads = []; self._beams = []; self._treal = t
        shot = next((s for s in self.shots if s["start"] <= t < s["end"]), self.shots[-1])
        typ = shot.get("type", "scene")
        slow = shot.get("slowmo")
        t_anim = shot["start"] + (t - shot["start"]) * slow if slow else t
        if typ == "title": img = self.title_frame(shot, t)
        elif typ == "choice": img = self.choice_frame(shot, t)
        elif typ == "detail": img = self.detail_frame(shot, t, t_anim)
        elif typ == "recap": img = self.recap_frame(shot, t)
        else: img = self.scene_frame(shot, t, t_anim)
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
        hs = self.hud_state(t)
        if hs and shot.get("hud", typ not in ("title", "recap", "detail") and not shot.get("hook")): text.hud(img, t, hs[0], hs[1], hs[2], hs[3])
        if not shot.get("hook") and typ != "recap":
            sy = self.pick_sub_y(shot) if typ == "scene" else shot.get("sub_y", 1590 if typ == "choice" else None)
            text.subtitle(img, t, self.subs, self.speakers, sy, words=self.word_subs)
        if t > self.total - 0.6: img = Image.blend(img, fx.BLACK, c01((t - (self.total - 0.6)) / 0.6))
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
    if "--jobs" in sys.argv:
        ep.render_parallel(int(sys.argv[sys.argv.index("--jobs") + 1])); sys.exit()
    if "--test" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--test") + 1:]]
        if ep.voices:
            try: ep.build_audio()
            except Exception as e: print("áudio:", e)
        for t in ts:
            path = os.path.join(ep.base, f"_teste_{t:05.1f}.png"); ep.frame(t).save(path); print(path)
    else:
        ep.render()
