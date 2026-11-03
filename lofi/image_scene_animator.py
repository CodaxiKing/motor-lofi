"""Image-based cinematic scene renderer; Pillow-only, deterministic frame sampling."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


def sample(value, t, default=0.0):
    """Sample scalar, [start,end] or [[time,value],...] keyframes at normalized time."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, list) and len(value) == 2 and all(isinstance(x, (int, float)) for x in value):
        return float(value[0]) + (float(value[1]) - float(value[0])) * t
    if isinstance(value, list) and value and all(isinstance(x, list) and len(x) == 2 for x in value):
        keys = sorted((float(k), float(v)) for k, v in value)
        if t <= keys[0][0]: return keys[0][1]
        if t >= keys[-1][0]: return keys[-1][1]
        for (a, va), (b, vb) in zip(keys, keys[1:]):
            if a <= t <= b:
                u = (t - a) / max(b-a, 1e-9)
                return va + (vb-va) * u
    raise ValueError(f'Invalid keyframe: {value!r}')


def _rgba(path):
    with Image.open(path) as im:
        return im.convert('RGBA')


def _place(canvas, layer, x, y, scale=1.0, opacity=1.0, rotation=0.0, pivot=None):
    if scale <= 0: return
    w, h = layer.size
    layer = layer.resize((max(1, round(w*scale)), max(1, round(h*scale))), Image.Resampling.LANCZOS)
    if opacity < 1:
        a = layer.getchannel('A').point(lambda p: round(p * max(0, min(1, opacity))))
        layer.putalpha(a)
    if rotation:
        if pivot is None: pivot = (.5, .5)
        px, py = float(pivot[0])*layer.width, float(pivot[1])*layer.height
        # Pillow rotates about center; adjust destination to keep pivot anchored.
        original_pivot_x, original_pivot_y = px, py
        layer = layer.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC, center=(px, py))
        # Rotation expand coordinates are not exact for off-center pivots; center-pivot recommended.
        if pivot != (.5, .5):
            x -= (layer.width - w*scale)/2
            y -= (layer.height - h*scale)/2
    canvas.alpha_composite(layer, (round(x), round(y)))


def render_frame(scene, time_seconds, base_dir='.', image_loader=None):
    """Render scene JSON at absolute time. Images remain external and are never modified."""
    base_dir = Path(base_dir)
    width, height = map(int, scene.get('size', [1080, 1920]))
    if width < 1 or height < 1: raise ValueError('Invalid scene size')
    duration = max(float(scene.get('duration', 1)), .001)
    t = min(1., max(0., float(time_seconds)/duration))
    canvas = Image.new('RGBA', (width, height), tuple(scene.get('background', [0,0,0,255])))
    camera = scene.get('camera', {})
    zoom = sample(camera.get('zoom', 1), t, 1)
    if zoom <= 0: raise ValueError('Camera zoom must be positive')
    cx = sample(camera.get('x', 0), t)
    cy = sample(camera.get('y', 0), t)
    for item in sorted(scene.get('layers', []), key=lambda l: l.get('z', 0)):
        path = base_dir / item['path']
        layer = image_loader(item['path']) if image_loader else _rgba(path)
        motion = item.get('motion', {})
        parallax = float(item.get('parallax', 1))
        scale = sample(item.get('scale', 1), t, 1) * zoom
        x = sample(item.get('x', 0), t) - cx*parallax
        y = sample(item.get('y', 0), t) - cy*parallax
        x += sample(motion.get('x', 0), t)
        y += sample(motion.get('y', 0), t)
        if motion.get('float'):
            y += math.sin(time_seconds*float(motion.get('frequency',1.5)))*float(motion.get('float_amplitude',4))
        if motion.get('sway'):
            x += math.sin(time_seconds*float(motion.get('frequency',1.5)))*float(motion.get('sway_amplitude',3))
        if motion.get('breathing'):
            y += math.sin(2*math.pi*float(motion.get('breaths_per_minute', 12))*time_seconds/60) * float(motion.get('amplitude', 2))
        # Zoom about frame center.
        x = (x-width/2)*zoom+width/2
        y = (y-height/2)*zoom+height/2
        rotation = sample(motion.get('rotation', 0), t)
        if motion.get('sway_rotation'):
            rotation += math.sin(time_seconds*float(motion.get('frequency',1.5)))*float(motion['sway_rotation'])
        opacity = sample(item.get('opacity', 1), t, 1)
        _place(canvas, layer, x, y, scale, opacity, rotation)
    for effect in scene.get('effects', []):
        kind = effect.get('type')
        if kind == 'flicker':
            rate = float(effect.get('rate', 3))
            strength = max(0, min(1, float(effect.get('strength', .3))))
            # Deterministic, non-random flicker.
            brightness = 1-strength*(.5+.5*math.sin(time_seconds*rate*2*math.pi))**8
            canvas = ImageEnhance.Brightness(canvas).enhance(brightness)
        elif kind == 'light_pulse':
            strength=max(0,min(1,float(effect.get('strength',.25))))
            rate=float(effect.get('rate',.6))
            canvas=ImageEnhance.Brightness(canvas).enhance(1+strength*math.sin(2*math.pi*rate*time_seconds))
        elif kind == 'fog':
            fog = Image.new('RGBA', (width, height), (0,0,0,0))
            d = ImageDraw.Draw(fog)
            speed = float(effect.get('speed', 12))
            alpha = max(0, min(255, int(effect.get('alpha', 24))))
            for i in range(4):
                x = (i*width/3 + time_seconds*speed) % (width+width/2)-width/4
                d.ellipse((int(x-width/4), height//3, int(x+width/3), height), fill=(210,220,230,alpha))
            fog = fog.filter(ImageFilter.GaussianBlur(max(1,width//18)))
            canvas = Image.alpha_composite(canvas, fog)
        elif kind == 'vignette':
            strength = max(0, min(1, float(effect.get('strength', .4))))
            # quarter-resolution radial mask for efficient rendering
            small = Image.new('L', (max(1,width//4), max(1,height//4)))
            p = small.load(); sw,sh = small.size
            for yy in range(sh):
                for xx in range(sw):
                    r = math.sqrt(((xx-sw/2)/(sw/2))**2 + ((yy-sh/2)/(sh/2))**2)
                    p[xx,yy] = round(255*strength*min(1,max(0,(r-.25)/1.1)))
            mask = small.resize((width,height), Image.Resampling.BILINEAR)
            canvas.paste((0,0,0,255), (0,0,width,height), mask)
        else:
            raise ValueError(f'Unknown effect: {kind}')
    return canvas.convert('RGB')


def render_frames(scene, output_dir, base_dir='.', fps=12):
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    duration = float(scene.get('duration', 1))
    if duration <= 0 or fps <= 0: raise ValueError('duration and fps must be positive')
    count = max(1, math.ceil(duration*fps))
    for i in range(count):
        render_frame(scene, i/fps, base_dir).save(output_dir/f'frame_{i:06d}.png')
    return count


def main():
    parser=argparse.ArgumentParser(description='Render cinematic image frames')
    parser.add_argument('scene'); parser.add_argument('output'); parser.add_argument('--fps',type=int,default=12)
    args=parser.parse_args()
    path=Path(args.scene)
    scene=json.loads(path.read_text(encoding='utf8'))
    print(f'{render_frames(scene,args.output,path.parent,args.fps)} frames rendered')

if __name__ == '__main__': main()
