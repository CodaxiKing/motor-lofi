"""Pins normalizados com deformação suave por malha; não é o motor da Adobe."""
import copy
import json
import math
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw


def validar(rig):
    pins=rig.get('pins',{})
    if len(pins)<3: raise ValueError('Puppet requer pelo menos três pins')
    vistos=set()
    for nome,p in pins.items():
        xy=p.get('pos',[])
        if len(xy)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) and 0<=v<=1 for v in xy):
            raise ValueError(f'Pin inválido: {nome}')
        if tuple(xy) in vistos: raise ValueError('Pins coincidentes')
        vistos.add(tuple(xy))
        for campo in ('amplitude',):
            if campo in p and (len(p[campo])!=2 or any(not math.isfinite(v) or abs(v)>.08 for v in p[campo])):
                raise ValueError('Amplitude deve ficar entre -0.08 e 0.08')
        for t,delta in p.get('keys',[]):
            if not math.isfinite(t) or len(delta)!=2 or any(not math.isfinite(v) or abs(v)>.08 for v in delta):
                raise ValueError('Keyframe de pin inválido')
        if p.get('periodo',1)<=0: raise ValueError('Período inválido')
    for g in rig.get('grupos_rigidos',[]):
        if len(g.get('centro',[]))!=2 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in g['centro']):
            raise ValueError('Centro do grupo inválido')
        if any(n not in pins for n in g['pins']): raise ValueError('Grupo referencia pin inexistente')
        if not math.isfinite(g.get('graus',0)) or abs(g.get('graus',0))>12: raise ValueError('Rotação máxima: 12 graus')
        if g.get('periodo',1)<=0: raise ValueError('Período inválido')
    if not isinstance(rig.get('aspecto',1),(int,float)) or not math.isfinite(rig.get('aspecto',1)) or rig.get('aspecto',1)<=0:
        raise ValueError('Aspecto do rig inválido')
    return rig


@lru_cache(maxsize=64)
def _ler(path, stamp):
    return validar(json.loads(Path(path).read_text(encoding='utf-8')))


def carregar(base, arquivo):
    if isinstance(arquivo,dict): return validar(arquivo)
    raiz=(Path(base)/'imagens').resolve()
    p=(raiz/arquivo).resolve()
    if not p.is_relative_to(raiz): raise ValueError('Rig fora da biblioteca')
    return _ler(str(p),p.stat().st_mtime_ns)


def alvos(rig,t):
    validar(rig);pins=rig['pins'];nomes=list(pins)
    src=np.array([pins[n]['pos'] for n in nomes],dtype=float);dst=src.copy()
    for i,n in enumerate(nomes):
        p=pins[n]
        if p.get('fixo'): continue
        amp=p.get('amplitude',[0,0]);onda=math.sin(2*math.pi*t/p.get('periodo',4)+p.get('fase',0))
        delta=np.array(amp,dtype=float)*onda
        keys=p.get('keys',[])
        if keys:
            local=t%p['loop_s'] if p.get('loop_s') else t
            for eixo in range(2):
                from .core import keyframe
                delta[eixo]+=keyframe([[k,v[eixo]] for k,v in keys],local)
        dst[i]+=delta+np.array(p.get('offset',[0,0]),dtype=float)
    for g in rig.get('grupos_rigidos',[]):
        indices=[nomes.index(n) for n in g['pins']]
        centro=np.array(g['centro']);a=math.radians(g.get('graus',0))*math.sin(2*math.pi*t/g.get('periodo',4))+math.radians(g.get('offset_graus',0))
        # Correção de aspecto evita deformar círculos ao girar em coordenadas normalizadas.
        aspecto=rig.get('aspecto',1)
        rot=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
        for i in indices:
            if pins[nomes[i]].get('fixo'): continue
            v=(src[i]-centro)*[aspecto,1]
            dst[i]=centro+(rot@v)/[aspecto,1]+(dst[i]-src[i])
    return src,dst


def _kernel(a,b):
    r2=np.sum((a[:,None,:]-b[None,:,:])**2,axis=2)
    return .5*r2*np.log(np.maximum(r2,1e-15))


def deformar(image,rig,t):
    """Inversa TPS amostrada em malha quad; movimentos pequenos, alfa preservado."""
    src,dst=alvos(rig,t)
    if np.max(np.abs(src-dst))<1e-9:return image.copy()
    # Bordas fixas impedem que pixels sejam puxados para fora da tela do recorte.
    borda=np.array([[0,0],[.5,0],[1,0],[0,.5],[1,.5],[0,1],[.5,1],[1,1]],dtype=float)
    keep=[v for v in borda if np.min(np.linalg.norm(src-v,axis=1))>1e-6]
    if keep:src=np.vstack([src,keep]);dst=np.vstack([dst,keep])
    n=len(src);P=np.column_stack([np.ones(n),dst])
    K=_kernel(dst,dst)+np.eye(n)*1e-9
    system=np.block([[K,P],[P.T,np.zeros((3,3))]])
    try:coeff=np.linalg.solve(system,np.vstack([src-dst,np.zeros((3,2))]))
    except np.linalg.LinAlgError as exc:raise ValueError('Malha degenerada; reveja os pins') from exc
    W,H=image.size;nx=int(rig.get('colunas',12));ny=max(4,round(nx*H/W))
    if not 4<=nx<=32: raise ValueError('Malha requer 4 a 32 colunas')
    xs=np.unique(np.round(np.linspace(0,W,nx+1)).astype(int));ys=np.unique(np.round(np.linspace(0,H,ny+1)).astype(int))
    grid=np.array([(x/W,y/H) for y in ys for x in xs])
    mapped=grid+np.column_stack([_kernel(grid,dst),np.ones(len(grid)),grid])@coeff
    mapped*=np.array([W,H]);cols=len(xs);mesh=[]
    for j in range(len(ys)-1):
        for i in range(len(xs)-1):
            ids=[j*cols+i,(j+1)*cols+i,(j+1)*cols+i+1,j*cols+i+1]
            quad=tuple(float(v) for k in ids for v in mapped[k])
            mesh.append(((int(xs[i]),int(ys[j]),int(xs[i+1]),int(ys[j+1])),quad))
    return image.convert('RGBA').transform(image.size,Image.Transform.MESH,mesh,
                                          resample=Image.Resampling.BICUBIC)


def diagnostico(image,rig,output):
    im=image.convert('RGBA').copy();d=ImageDraw.Draw(im);w,h=im.size
    for nome,p in rig['pins'].items():
        x,y=p['pos'][0]*w,p['pos'][1]*h
        cor='#44eeaa' if p.get('fixo') else '#ffcc44'
        d.ellipse((x-4,y-4,x+4,y+4),fill=cor);d.text((x+6,y),nome,fill=cor)
    im.save(output)
