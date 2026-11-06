"""Sombras no plano do chão: contato e silhueta projetada por luzes calibradas.

Não detecta iluminação em pixels. As posições pertencem ao cenário; os atores
e a câmera usam a mesma geometria do compositor de imagens.
"""
import copy
import json
import math
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops
from .core import keyframe

PADRAO={'ambiente':.35,'luzes':[{'tipo':'pontual','posicao':[.28,.60],'altura_m':3.2,
                              'intensidade':.8,'suavidade':.65,'espaco':'tela'}]}


@lru_cache(maxsize=16)
def _catalogo(path,stamp):
    c=json.loads(Path(path).read_text(encoding='utf-8'))
    return {v['img']:v.get('iluminacao') for v in c.get('cenarios',{}).values()}


@lru_cache(maxsize=64)
def _altura_ficha(path,stamp):
    return json.loads(Path(path).read_text(encoding='utf-8'))['altura_m']


def altura_fisica(p,base=None):
    valor=p.get('altura_m')
    if valor is None and base:
        raiz=(Path(base)/'imagens').resolve();id=p.get('id') or p.get('img','').split('/')[0]
        path=(raiz/id/'personagem.json').resolve()
        if path.is_relative_to(raiz) and path.is_file():valor=_altura_ficha(str(path),path.stat().st_mtime_ns)
    valor=1.7 if valor is None else valor
    if not isinstance(valor,(int,float)) or not math.isfinite(valor) or not .2<=valor<=5:raise ValueError('Altura física inválida para sombra')
    return float(valor)


def iluminacao(cfg,base):
    if 'iluminacao' in cfg:return copy.deepcopy(cfg['iluminacao'])
    path=Path(base)/'catalogo.json'
    if path.is_file():
        nome=cfg.get('fundo','');nome=nome if '/' in nome or nome.startswith(('fundo_','ref_')) else 'fundo_'+nome
        c=_catalogo(str(path),path.stat().st_mtime_ns).get(nome)
        if c is not None:return copy.deepcopy(c)
    return copy.deepcopy(PADRAO)


def numero(config,nome,t,padrao):
    v=keyframe(config.get('trajeto',{}).get(nome,config.get(nome,padrao)),t)
    if not isinstance(v,(int,float)) or not math.isfinite(v):raise ValueError(f'Luz/sombra inválida: {nome}')
    return float(v)


def projetar(pos,config,size,fundo_info):
    W,H=size
    if config.get('espaco','cenario')=='cenario' and fundo_info:
        (w,h),x,y,s=fundo_info
        return x+pos[0]*w*s,y+pos[1]*h*s
    return pos[0]*W,pos[1]*H


def fontes(config,size,fundo_info,t):
    ambiente=numero(config,'ambiente',t,.35)
    if not 0<=ambiente<=1:raise ValueError('Luz ambiente fora de 0..1')
    out=[]
    for original in config.get('luzes',[]):
        luz=copy.deepcopy(original);tipo=luz.get('tipo','pontual')
        if tipo not in ('pontual','direcional'):raise ValueError('Tipo de luz inválido')
        intensidade=numero(luz,'intensidade',t,1);soft=numero(luz,'suavidade',t,.6)
        if not 0<=intensidade<=2 or not 0<=soft<=1:raise ValueError('Intensidade/suavidade de luz inválida')
        luz.update(tipo=tipo,intensidade=intensidade,suavidade=soft)
        if tipo=='pontual':
            xy=luz.get('posicao',[.5,.6])
            if len(xy)!=2:raise ValueError('Posição da luz inválida')
            xy=[numero(luz,'x',t,xy[0]),numero(luz,'y',t,xy[1])]
            luz['xy']=projetar(xy,luz,size,fundo_info)
            luz['altura_m']=numero(luz,'altura_m',t,3.2)
            if luz['altura_m']<=0:raise ValueError('Altura da luz precisa ser positiva')
        else:
            direcao=luz.get('direcao',[.7,.4])
            if len(direcao)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in direcao) or math.hypot(*direcao)<1e-6:
                raise ValueError('Direção da luz inválida')
            luz['direcao']=direcao
            luz['comprimento']=numero(luz,'comprimento',t,.55)
            if luz['comprimento']<0:raise ValueError('Comprimento da sombra negativo')
        out.append(luz)
    return ambiente,out


def piso(config,size,fundo_info):
    pontos=config.get('piso')
    if not pontos:return None
    if len(pontos)<3 or any(len(p)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) and 0<=v<=1 for v in p) for p in pontos):
        raise ValueError('Polígono do chão inválido')
    return [projetar(p,config,size,fundo_info) for p in pontos]


def geometria(luz,pe,altura_px,altura_m,elevacao_px):
    """Raio projetado no chão; elevação desloca e dispersa a sombra."""
    altura_m=max(.2,altura_m);mpp=altura_m/max(1,altura_px);elev=max(0,elevacao_px)*mpp
    if luz['tipo']=='pontual':
        vx,vy=pe[0]-luz['xy'][0],pe[1]-luz['xy'][1]
        distancia=math.hypot(vx,vy)
        dx,dy=(vx/distancia,vy/distancia) if distancia>1 else (0,1)
        L=luz['altura_m'];ratio=altura_m/max(.35,L-altura_m-elev)
        comprimento=min(altura_px*.75,distancia*ratio)
        desloc=min(altura_px*.5,distancia*elev/max(.35,L-elev))
    else:
        vx,vy=luz['direcao'];n=math.hypot(vx,vy);dx,dy=vx/n,vy/n
        comprimento=altura_px*luz['comprimento'];desloc=elevacao_px*luz['comprimento']
    return {'vetor':(dx*comprimento,dy*comprimento),'deslocamento':(dx*desloc,dy*desloc),
            'blur':max(.6,altura_px*(.004+.025*luz['suavidade'])+elevacao_px*.15)}


def _projetada(alpha,dx,dy,blur,opacidade):
    w,h=alpha.size;B=dy-h*.055
    if abs(B)<2:B=2 if dy>=0 else -2
    x0=min(0,dx);y0=min(0,B);ow=max(2,math.ceil(w+abs(dx)));oh=max(2,math.ceil(abs(B)))
    matrix=(1,-dx/B,x0-dx/B*y0,0,-h/B,h-h/B*y0)
    mask=alpha.transform((ow,oh),Image.Transform.AFFINE,matrix,resample=Image.Resampling.BILINEAR)
    pad=math.ceil(blur*3);expanded=Image.new('L',(ow+2*pad,oh+2*pad));expanded.paste(mask,(pad,pad))
    expanded=expanded.filter(ImageFilter.GaussianBlur(blur)).point(lambda a:round(a*opacidade))
    im=Image.new('RGBA',expanded.size,(5,7,13,0));im.putalpha(expanded)
    return im,x0-pad,y0-pad


def gerar(im,x,y,s,p,cfg,light_config,size,fundo_info,t,espelhado=False,ciclo=None,frame=None,base=None):
    """Lista de (sprite, x, y) no mundo; compositor aplica câmera uma só vez."""
    if cfg.get('sombras',True) is False or p.get('sombra',True) is False:return []
    opt=p.get('sombra') if isinstance(p.get('sombra'),dict) else {}
    foco=(frame or {}).get('marcos',{}).get('foco')=='rosto'
    if ciclo and (ciclo.get('tipo')=='retrato' or foco) and 'chao' not in opt:return []
    alpha=im.getchannel('A')
    if espelhado:alpha=alpha.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    box=alpha.point(lambda a:255 if a>40 else 0).getbbox()
    if not box:return []
    W,H=size;ground=numero(opt,'chao',t,p.get('chao',.94))*H
    bottom=y+box[3]*s;physical=p.get('altura',.6)*H*.98
    # Static cutouts may have transparent pixels below the sole. Calibrate
    # that fixed offset without following breathing or a lifted body. Cycles
    # retain their virtual ground, including the flight phase of a run.
    anchor=p.get('_ancora_sombra',p.get('ancora'))
    if not ciclo and 'chao' not in opt and anchor:
        ground+=(box[3]-anchor[1]*im.height)*s
    gap=max(0,ground-bottom)
    if 'elevacao' in opt:gap=max(gap,numero(opt,'elevacao',t,0)*H)
    physique=altura_fisica(p,base)
    ambient,lights=fontes(light_config,size,fundo_info,t)
    intensity=numero(opt,'intensidade',t,1)
    if not 0<=intensity<=2:raise ValueError('Intensidade da sombra inválida')
    # Use the sole band to locate both feet; the coat/head cannot move the base.
    band=max(box[1],min(im.height-1,round((ground-y)/max(s,1e-6)-physical/max(s,1e-6)*.035)))
    foot=np.asarray(alpha.crop((0,band,im.width,min(im.height,band+max(2,round(physical/max(s,1e-6)*.05))))))
    cols=np.flatnonzero(np.max(foot,axis=0)>40) if foot.size else np.array([])
    center=(float(cols.mean()) if len(cols) else (box[0]+box[2])/2)
    foot_x=x+center*s
    shadow_alpha=alpha.crop(box)
    sw=max(2,round((box[2]-box[0])*s));sh=max(2,round((box[3]-box[1])*s))
    shadow_alpha=shadow_alpha.resize((sw,sh),Image.Resampling.BILINEAR)
    out=[];total=max(1,sum(l['intensidade'] for l in lights))
    for luz in lights:
        if luz['intensidade']<=0:continue
        g=geometria(luz,(foot_x,ground),physical,physique,gap)
        # Crouching lowers the silhouette's effective height without changing
        # physical reference scale, while the ground and sole stay anchored.
        fraction=min(1.15,sh/max(1,physical));dx,dy=(v*fraction for v in g['vetor'])
        opacity=.34*(1-.65*ambient)*luz['intensidade']/total*intensity/(1+gap/max(1,physical)*3)
        sprite,ox,oy=_projetada(shadow_alpha,dx,dy,g['blur'],opacity)
        offsetx,offsety=g['deslocamento']
        out.append((sprite,x+box[0]*s+ox+offsetx,ground+oy+offsety))
    contact=max(0,1-gap/max(1,physical*.045))
    if contact>0 and len(cols):
        breaks=np.flatnonzero(np.diff(cols)>max(2,im.width*.015))+1
        groups=np.split(cols,breaks)
        for group in groups:
            if len(group)<2:continue
            fw=max(physical*.045,(group[-1]-group[0]+1)*s*1.12)
            fh=max(2,physical*.012);blur=max(.45,physical*.0015)
            pad=math.ceil(blur*3);w=math.ceil(fw)+2*pad;h=math.ceil(fh)+2*pad
            mask=Image.new('L',(w,h));ImageDraw.Draw(mask).ellipse((pad,pad,w-pad-1,h-pad-1),fill=min(255,round(155*contact*(1-.4*ambient)*intensity)))
            # Dense contact core touches the actual sole, independently for
            # each foot. A single global baseline left a gap under higher soles.
            ImageDraw.Draw(mask).ellipse((pad+fw*.12,pad+fh*.18,w-pad-fw*.12-1,h-pad-fh*.18-1),fill=min(255,round(210*contact*(1-.3*ambient)*intensity)))
            mask=mask.filter(ImageFilter.GaussianBlur(blur));sprite=Image.new('RGBA',mask.size,(4,6,11,0));sprite.putalpha(mask)
            sole=ground
            if gap<=physical*.018:
                strip=np.asarray(alpha)[:,int(group[0]):int(group[-1])+1]
                rows=np.flatnonzero(np.max(strip,axis=1)>40)
                if len(rows):sole=y+(float(rows[-1])+1)*s
            out.append((sprite,x+(float(group[0])+float(group[-1]))/2*s-w/2,sole-h/2))
    return out


def recortar_piso(sprite,origem,pontos,camera):
    if not pontos:return sprite
    z,ox,oy=camera;x,y=origem
    mask=Image.new('L',sprite.size);ImageDraw.Draw(mask).polygon([(px*z+ox-x,py*z+oy-y) for px,py in pontos],fill=255)
    out=sprite.copy();out.putalpha(ImageChops.multiply(out.getchannel('A'),mask));return out
