"""Composição de imagens para planos FULL_SCENE/LAYERED_SCENE/HYBRID_SCENE."""
from pathlib import Path
from PIL import Image


def compose_shot(size, layers, output):
    """layers: [{path, x, y, scale, opacity, rotation}] em ordem de profundidade."""
    canvas = Image.new('RGBA', tuple(size), (0, 0, 0, 0))
    for layer in layers:
        with Image.open(layer['path']) as source:
            sprite = source.convert('RGBA')
        scale = float(layer.get('scale', 1))
        if scale <= 0:
            raise ValueError('scale deve ser positivo')
        sprite = sprite.resize((max(1, round(sprite.width * scale)),
                                max(1, round(sprite.height * scale))), Image.Resampling.LANCZOS)
        if layer.get('rotation'):
            sprite = sprite.rotate(float(layer['rotation']), expand=True,
                                   resample=Image.Resampling.BICUBIC)
        opacity = float(layer.get('opacity', 1))
        if not 0 <= opacity <= 1:
            raise ValueError('opacity deve estar entre 0 e 1')
        if opacity < 1:
            sprite.putalpha(sprite.getchannel('A').point(lambda a: round(a * opacity)))
        canvas.alpha_composite(sprite, (int(layer.get('x', 0)), int(layer.get('y', 0))))
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination)
    return destination
