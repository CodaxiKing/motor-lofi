
"""Biblioteca de efeitos sonoros sintetizados + mixagem de vozes, efeitos, ambiente e trilha."""
import subprocess
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt

SR = 44100
_r = np.random.default_rng(8)
def t_(x): return np.arange(int(x * SR)) / SR
def bp(x, lo, hi, o=4): return sosfilt(butter(o, [lo, hi], btype="band", fs=SR, output="sos"), x)
def lp(x, f, o=4): return sosfilt(butter(o, f, btype="low", fs=SR, output="sos"), x)
def hp(x, f, o=4): return sosfilt(butter(o, f, btype="high", fs=SR, output="sos"), x)
def env(n, a=0.005, r=0.1):
    t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)
def noise(d): return _r.standard_normal(int(d * SR))
def fadeio(s, a=0.03, b=0.03):
    s = s.copy(); na, nb = min(len(s) // 2, int(a * SR)), min(len(s) // 2, int(b * SR))
    if na: s[:na] *= np.linspace(0, 1, na)
    if nb: s[-nb:] *= np.linspace(1, 0, nb)
    return s

# ------------------- efeitos (nome -> função que devolve o sinal) -------------------
def beep():
    out = []
    for _ in range(2):
        t = t_(0.28); s = (np.sin(2*np.pi*853*t) + np.sin(2*np.pi*960*t)) * 0.5
        s *= np.minimum(1, t/0.01) * np.minimum(1, (0.28-t)/0.02); out += [s, np.zeros(int(0.09*SR))]
    return np.concatenate(out) * 0.3
def stamp():
    d = 0.8; t = t_(d)
    s = np.sin(2*np.pi*(80*np.exp(-t*6)+40)*t) * env(len(t), 0.001, 0.25) + bp(noise(d), 300, 4000) * env(len(t), 0.0005, 0.04) * 0.8
    return np.tanh(s * 2) * 0.6
def whoosh():
    d = 0.5; t = t_(d); n = noise(d)
    s = bp(n, 300, 3000) * np.sin(np.pi * t / d) ** 2
    return s * 0.25
def step():
    t = t_(0.25)
    return (np.sin(2*np.pi*(90-120*t)*t) * env(len(t), 0.002, 0.04) + lp(noise(0.25), 800) * env(len(t), 0.001, 0.02) * 0.3) * 0.35
def shuffle():
    d = 0.45; t = t_(d)
    return (lp(noise(d), 900) * env(len(t), 0.03, 0.12) * 0.5 + np.sin(2*np.pi*(80-60*t)*t) * env(len(t), 0.003, 0.05) * 0.4) * 0.45
def echo_step():
    s = np.zeros(int(1.2*SR)); st = step()
    for k, g in enumerate([1, 0.5, 0.28, 0.15]):
        i = int(k*0.21*SR); s[i:i+len(st)] += st * g
    return s
def door_open():
    d = 0.7; t = t_(d); f = 380 + 260*np.sin(np.pi*t/d)
    s = np.sin(2*np.pi*np.cumsum(f)/SR) * (0.5+0.5*np.sin(2*np.pi*23*t)) * np.sin(np.pi*t/d)**2
    return bp(s + noise(d)*0.1, 250, 2500) * 0.12
def door_close():
    d = 0.5; t = t_(d)
    return (np.sin(2*np.pi*95*t) * env(len(t), 0.001, 0.07) + lp(noise(d), 700) * env(len(t), 0.001, 0.03) * 0.6) * 0.35
def lock():
    t = t_(0.25); s = bp(noise(0.25), 2000, 7000) * env(len(t), 0.0005, 0.008) * 0.8 + np.sin(2*np.pi*2600*t) * env(len(t), 0.001, 0.05) * 0.25
    s2 = np.zeros_like(s); i = int(0.06*SR); s2[i:] = s[:-i]*0.6
    return (s + s2) * 0.5
def bang():
    d = 0.6; t = t_(d)
    s = np.sin(2*np.pi*70*t) * env(len(t), 0.002, 0.12) + np.sin(2*np.pi*140*t) * env(len(t), 0.001, 0.05) * 0.7 + bp(noise(d), 100, 1800) * env(len(t), 0.0005, 0.03)
    return np.tanh(s * 2.5) * 0.38
def knock():
    d = 0.4; t = t_(d)
    s = np.sin(2*np.pi*170*t) * env(len(t), 0.001, 0.05) + np.sin(2*np.pi*95*t) * env(len(t), 0.001, 0.08) * 0.8 + bp(noise(d), 200, 2500) * env(len(t), 0.0005, 0.015) * 0.9
    return np.tanh(s*2.2) * 0.6
def glass():
    d = 1.2; t = t_(d); s = hp(noise(d), 2500) * env(len(t), 0.001, 0.12) * 0.6
    for _ in range(14):
        f = _r.uniform(2500, 7000); off = _r.uniform(0, 0.25); tt = np.clip(t - off, 0, None)
        s += np.sin(2*np.pi*f*tt) * (t > off) * np.exp(-tt/_r.uniform(0.05, 0.25)) * 0.12
    return s * 0.6
def impact():
    d = 2.0; t = t_(d); f = 60*np.exp(-t*1.2) + 28
    s = np.sin(2*np.pi*np.cumsum(f)/SR) * env(len(t), 0.002, 0.7) + lp(noise(d), 300) * env(len(t), 0.001, 0.15) * 0.8
    return np.tanh(s*1.5) * 0.6
def thunder():
    d = 4.0; t = t_(d)
    s = lp(noise(d), 120) * np.exp(-t*0.9) * 2.2 + lp(noise(d), 600) * env(len(t), 0.02, 0.35) * 1.2
    s *= 0.6 + 0.4 * np.abs(np.sin(2*np.pi*1.7*t))
    return np.tanh(s) * 0.45
def no_service():
    out = []
    for f in [988, 784, 659]:
        t = t_(0.18); out += [np.sin(2*np.pi*f*t) * env(len(t), 0.005, 0.1), np.zeros(int(0.05*SR))]
    return np.concatenate(out) * 0.18
def notif():
    t = t_(0.5); return (np.sin(2*np.pi*1320*t) + 0.5*np.sin(2*np.pi*1980*t)) * env(len(t), 0.003, 0.12) * 0.12
def vibe():
    t = t_(0.38); s = np.sign(np.sin(2*np.pi*150*t)) * 0.6 + np.sin(2*np.pi*300*t) * 0.3
    return lp(s, 600) * np.minimum(1, t/0.02) * np.minimum(1, (0.38-t)/0.03) * 0.35
def click():
    return bp(noise(0.03), 1000, 5000) * env(int(0.03*SR), 0.0005, 0.006) * 0.6
def growl():
    d = 1.2; t = t_(d); f0 = _r.uniform(70, 110)
    s = np.sign(np.sin(2*np.pi*(f0 + 15*np.sin(2*np.pi*3*t))*t)) * np.sin(np.pi*t/d)**2
    return lp(s, 600) * 0.2
def car_alarm():
    d = 3.0; t = t_(d); f = 900 + 500 * (np.sin(2*np.pi*2*t) > 0)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * 0.15
def siren():
    d = 4.0; t = t_(d); f = 700 + 400 * np.sin(2*np.pi*0.5*t)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * np.minimum(1, t/1) * np.minimum(1, (d-t)/1) * 0.12
def heartbeat(d=6.0, b0=80, b1=118):
    out = np.zeros(int(d*SR)); k = 0.0
    while k < d - 0.4:
        for o, g in [(0, 1.0), (0.17, 0.7)]:
            t = t_(0.22); s = np.sin(2*np.pi*(55-40*t)*t) * env(len(t), 0.004, 0.05) * g
            i = int((k+o)*SR); j = min(len(out), i+len(s)); out[i:j] += s[:j-i]
        k += 60/(b0 + (b1-b0)*k/d)
    return out * 0.55
def breath(d=2.0):
    out = np.zeros(int(d*SR)); k = 0.0
    while k < d - 0.6:
        ln = _r.uniform(0.35, 0.55); n = bp(noise(ln), 300, 2500); tt = np.arange(len(n))/SR
        n *= np.sin(np.pi*tt/ln)**2; i = int(k*SR); out[i:i+len(n)] += n[:len(out)-i]; k += ln + _r.uniform(0.1, 0.2)
    return out * 0.09
def static(d=2.0):
    return (bp(noise(d), 600, 6000) + (_r.random(int(d*SR)) > 0.9995) * _r.standard_normal(int(d*SR)) * 3) * 0.05
def crowd(d=4.0):
    n = lp(noise(d), 350) * 1.2; t = np.arange(len(n))/SR
    m = 0.6 + 0.4*np.sin(2*np.pi*0.3*t) * np.sin(2*np.pi*0.13*t + 1)
    g = np.zeros_like(t)
    for _ in range(int(d*1.5)):
        st = _r.uniform(0, max(0.01, d-1.2)); gs = growl(); i = int(st*SR); g[i:i+len(gs)] += gs[:len(g)-i]
    return (n * m + g) * np.minimum(1, t/0.8) * np.minimum(1, (d-t)/0.8) * 0.12

SFX = {k: v for k, v in globals().items() if callable(v) and k in (
    "beep stamp whoosh step shuffle echo_step door_open door_close lock bang knock glass impact thunder no_service notif vibe "
    "click growl car_alarm siren heartbeat breath static crowd").split()}
DURATION_SFX = {"heartbeat", "breath", "static", "crowd"}   # aceitam "dur"

# ------------------- ambientes -------------------
def amb(kind, d):
    t = t_(d); f = np.minimum(1, t/0.5) * np.minimum(1, (d-t)/0.5)
    if kind == "chuva_dentro": s = lp(bp(noise(d), 600, 9000) * 0.5 + lp(noise(d), 400) * 0.6, 1800) * 0.05
    elif kind == "chuva_fora":
        s = (bp(noise(d), 600, 9000) * 0.5 + lp(noise(d), 400) * 0.6) * 0.07
        s += hp((_r.random(len(t)) > 0.9992) * _r.standard_normal(len(t)) * 2, 2000) * 0.05
    elif kind == "zumbido": s = (np.sin(2*np.pi*120*t)*0.5 + np.sin(2*np.pi*240*t)*0.3) * 0.035
    elif kind == "eco": s = lp(noise(d), 200) * 0.05
    elif kind == "vento":
        s = lp(noise(d), 500) * (0.6 + 0.4*np.sin(2*np.pi*0.18*t)) * 0.08
    else: s = np.zeros(len(t))
    return s * f

def drone(d, base=55.0, tense=0.0):
    t = t_(d)
    s = np.sin(2*np.pi*base*t) + 0.6*np.sin(2*np.pi*base*1.5*t + .4) + 0.35*np.sin(2*np.pi*base*2.02*t)
    s += tense * 0.45 * np.sin(2*np.pi*base*1.06*t) + lp(noise(d), 180) * 0.5
    return s * (0.7 + 0.3*np.sin(2*np.pi*0.12*t))

# ------------------- mixagem -------------------
def load_voice(path):
    tmp = path + ".44.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-ar", str(SR), "-ac", "1", tmp], check=True)
    x, _ = sf.read(tmp); return x

def radio_filter(seg):
    seg = bp(seg, 350, 3200, 6); seg = np.tanh(seg * 4) / 2.0
    return seg + bp(noise(len(seg) / SR), 800, 5000) * 0.02

def mix(total, clips, voices, sfx, music, ambience, out_path, fps=30):
    """clips: [{voice, src:[a,b], at, radio?}], voices: {nome: caminho}, sfx: [{t, name, gain, dur}],
    music: [{start, end, gain:[a,b], tense, base}], ambience: [(ini, fim, tipo)]"""
    N = int(total * SR) + SR
    V = np.zeros(N); FX = np.zeros(N); MU = np.zeros(N); AM = np.zeros(N); PV = {}
    def add(buf, sig, at, g=1.0):
        i = int(at * SR); j = min(N, i + len(sig))
        if i < 0: sig = sig[-i:]; i = 0
        if j > i: buf[i:j] += sig[: j - i] * g
    src = {v: load_voice(p) for v, p in voices.items()}
    for c in clips:
        x = src[c["voice"]]; a, b = c["src"]
        seg = fadeio(x[int(a * SR): int(b * SR)])
        act = seg[np.abs(seg) > 0.005]
        if len(act): seg = seg * min(3.0, 0.09 / (np.sqrt(np.mean(act ** 2)) + 1e-9))
        if c.get("radio"): seg = radio_filter(seg) * 1.6
        add(V, seg * c.get("gain", 1.0), c["at"])
        PV.setdefault(c["voice"], np.zeros(N)); add(PV[c["voice"]], seg, c["at"])
    for e in sfx:
        fn = SFX[e["name"]]
        sig = fn(e["dur"]) if e["name"] in DURATION_SFX and "dur" in e else fn()
        add(FX, sig, e["t"], e.get("gain", 1.0))
    for a, b, kind in ambience:
        if b - a > 0.3: add(AM, amb(kind, b - a), a)
    for m in music:
        d = m["end"] - m["start"]; s = drone(d, m.get("base", 55.0), m.get("tense", 0.4)); t = np.arange(len(s)) / SR
        g0, g1 = m.get("gain", [0.05, 0.1]); fin, fout = m.get("fade_in", 0.8), m.get("fade_out", 0.05)
        add(MU, s * (g0 + (g1 - g0) * t / d) * np.minimum(1, t / fin) * np.minimum(1, (d - t) / fout), m["start"])
    venv = lp(np.abs(V), 8, 2); duck = 1 - np.clip(venv * 6, 0, 0.5)
    out = V + FX * 0.9 + (MU + AM * 0.8) * duck
    out = out[: int(total * SR)]
    vv = V[: len(out)]; act = vv[np.abs(vv) > 0.01]
    vr = np.sqrt(np.mean(act ** 2)) if len(act) else 0.1
    out = np.tanh(out / vr * 0.13 / 0.85) * 0.85
    sf.write(out_path, out, SR)
    step = SR // fps
    env_ = {"_all": lp(np.abs(V), 12, 2)[::step]}
    for v, buf in PV.items():
        e = lp(np.abs(buf), 14, 2)[::step]; mx = np.percentile(e[e > 1e-4], 95) if np.any(e > 1e-4) else 1
        env_[v] = np.clip(e / (mx + 1e-9), 0, 1.2)
    return env_
