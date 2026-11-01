"""Camadas PNG transparentes por plano; suportam cenários ilustrados externamente.

Uso no shot: "layers": [{"path":"assets/fundo.png", "x":0,"y":0,
"scale":1,"opacity":0.9,"depth":0.2,"motion_x":20,"motion_y":0}]
Os caminhos são relativos à pasta do JSON. Limites impedem leituras fora do projeto.
"""
from functools import lru_cache
from pathlib import Path
from PIL import Image
from .core import W,H

@lru_cache(maxsize=64)
def _read(path):
    with Image.open(path) as source:
        return source.convert('RGBA').copy()

def _asset(base, rel):
    if not isinstance(rel,str) or not rel or Path(rel).is_absolute():
        raise ValueError('Caminho de asset deve ser relativo')
    base=Path(base).resolve(); path=(base/rel).resolve()
    if not path.is_relative_to(base):
        raise ValueError('Asset fora da pasta do episódio')
    if path.suffix.lower() not in ('.png','.webp'):
        raise ValueError('Asset precisa ser PNG ou WEBP')
    return str(path)

def composite_layers(frame, layers, base, progress=0.0, camera_x=0.0, camera_y=0.0):
    if not layers: return frame
    out=frame.convert('RGBA')
    for layer in sorted(layers,key=lambda x:float(x.get('depth',0))):
        img=_read(_asset(base,layer['path']))
        scale=float(layer.get('scale',1))
        if not 0.05<=scale<=8: raise ValueError('scale deve estar entre 0.05 e 8')
        w,h=max(1,round(img.width*scale)),max(1,round(img.height*scale))
        if w*h>W*H*32: raise ValueError('Camada grande demais')
        if (w,h)!=img.size: img=img.resize((w,h),Image.Resampling.BILINEAR)
        opacity=float(layer.get('opacity',1))
        if not 0<=opacity<=1: raise ValueError('opacity deve estar entre 0 e 1')
        if opacity<1: img.putalpha(img.getchannel('A').point(lambda a:int(a*opacity)))
        depth=float(layer.get('depth',0))
        x=round(float(layer.get('x',0))+float(layer.get('motion_x',0))*progress-camera_x*depth)
        y=round(float(layer.get('y',0))+float(layer.get('motion_y',0))*progress-camera_y*depth)
        out.alpha_composite(img,(x,y))
    return out.convert(frame.mode)
