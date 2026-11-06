"""Composição local de pálpebras, sem substituir corpo, âncora ou rig."""
from PIL import Image,ImageDraw,ImageFilter


def compor(base, variante, regioes):
    out=base.convert('RGBA').copy()
    for regiao in regioes:
        origem=regiao.get('origem',regiao['destino']);destino=regiao['destino']
        if any(len(r)!=4 or not 0<=r[0]<r[2]<=1 or not 0<=r[1]<r[3]<=1 for r in (origem,destino)):
            raise ValueError('Região de piscada inválida')
        def pixels(r,size):
            w,h=size;return tuple(round(v*(w if i%2==0 else h)) for i,v in enumerate(r))
        src=pixels(origem,variante.size);dst=pixels(destino,out.size)
        size=(dst[2]-dst[0],dst[3]-dst[1])
        patch=variante.convert('RGBA').crop(src).resize(size,Image.Resampling.BICUBIC)
        mask=Image.new('L',size,0);d=ImageDraw.Draw(mask)
        margem=max(1,round(min(size)*.12))
        d.rectangle((margem,margem,size[0]-1-margem,size[1]-1-margem),fill=255)
        mask=mask.filter(ImageFilter.GaussianBlur(max(.5,margem/2)))
        out.paste(patch,dst[:2],mask)
    return out
