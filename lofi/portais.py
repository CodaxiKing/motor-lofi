"""Máscaras geométricas da abertura de portas, projetadas junto com o fundo."""
from PIL import Image, ImageDraw, ImageChops


def validar(portal):
    poligono=portal.get('poligono',[])
    if len(poligono)<3 or any(len(p)!=2 or not all(isinstance(v,(int,float)) and 0<=v<=1 for v in p) for p in poligono):
        raise ValueError('Portal precisa de polígono normalizado válido')
    return portal


def recortar(sprite, origem, portal, fundo_size, tela_size, fundo_y=.5, camera=(1,0,0)):
    """Recorta só o sprite. O cenário mantém os pixels originais da porta/batente."""
    validar(portal)
    W,H=tela_size; w,h=fundo_size; z,ox,oy=camera
    s=max(W/w,H/h)*1.03
    bx=(W-w*s)/2; by=(H-h*s)*fundo_y
    x,y=origem
    pontos=[((bx+px*w*s)*z+ox-x,(by+py*h*s)*z+oy-y) for px,py in portal['poligono']]
    mask=Image.new('L',sprite.size,0);ImageDraw.Draw(mask).polygon(pontos,fill=255)
    out=sprite.copy();out.putalpha(ImageChops.multiply(out.getchannel('A'),mask))
    return out
