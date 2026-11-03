"""Opt-in illustrated shot bridge for motor-lofi Episode.scene_frame.

The procedural renderer is untouched unless episode visual_mode == 'DESENHO'
and the shot explicitly provides 'image_scene'.
"""
from __future__ import annotations
import json
from pathlib import Path
from .image_scene_animator import render_frame
from .character_motion import render_character


def _safe(base, value):
    base = Path(base).resolve()
    target = (base / value).resolve()
    if not target.is_relative_to(base):
        raise ValueError(f'Asset path outside episode directory: {value}')
    return target


def draw_shot(shot, t, episode_dir, size, asset_root=None):
    """Render a shot with optional layered facial cutouts and environment effects.

    image_scene is either an inline object or a JSON filename relative to episode_dir.
    All scene images are resolved relative to the scene file's directory.
    """
    base = Path(episode_dir).resolve()
    spec = shot['image_scene']
    if isinstance(spec, str):
        path = _safe(base, spec)
        scene = json.loads(path.read_text(encoding='utf-8'))
        base = path.parent
    elif isinstance(spec, dict):
        scene = json.loads(json.dumps(spec))
    else:
        raise TypeError('image_scene must be JSON path or object')
    scene['size'] = list(size)
    scene['duration'] = shot['end'] - shot['start']
    if scene['duration'] <= 0:
        raise ValueError('Shot duration must be positive')
    rel = max(0.0, t - shot['start'])
    # Generate character sprites in memory rather than writing temporary images.
    sprites = {}
    for layer in scene.get('layers', []):
        if 'character' not in layer:
            continue
        config = layer['character']
        if not isinstance(config, dict) or 'parts' not in config or 'state' not in config:
            raise ValueError('character requires parts and state')
        sprite = render_character(config['parts'], config['state'], rel, base)
        key = f'__character_{len(sprites)}'
        sprites[key] = sprite
        layer['path'] = key
        del layer['character']
    def load(path):
        if str(path) in sprites:
            return sprites[str(path)].copy()
        from PIL import Image
        with Image.open(_safe(base, path)) as source:
            return source.convert('RGBA')
    return render_frame(scene, rel, base, image_loader=load)
