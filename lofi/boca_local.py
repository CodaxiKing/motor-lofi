"""Bocas locais por visema: mantém o recorte, âncora e corpo originais."""
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

CODIGOS={0:'rest',1:'M',2:'A',3:'E',4:'O',5:'U',6:'M',7:'E',8:'A'}
RHUBARB={'X':'rest','A':'M','B':'E','C':'A','D':'A','E':'O','F':'U','G':'M','H':'E'}


def estado(p,t,nivel=None,visema=None,permitir=True):
    if not permitir:return 'rest',None
    eventos=p.get('eventos_fala',[])
    e=next((e for e in eventos if e['start']<=t<e['end']),None)
    if eventos and e is None:return 'rest',None
    voz=e['voice'] if e else p.get('fala')
    if not voz:return 'rest',None
    if e and e.get('mouth_cues'):
        rel=t-e['start']
        cue=next((c for c in e['mouth_cues'] if c['start']<=rel<c['end']),None)
        shape=cue.get('shape','rest') if cue else 'rest'
        if e.get('cue_format')=='rhubarb':shape=RHUBARB.get(shape,'rest')
        return shape,e
    if not nivel or nivel(voz,t)<.10:return 'rest',e
    return CODIGOS.get(visema(voz,t),'A') if visema else 'A',e


def compor(base,atlas,config,shape):
    if shape=='rest':return base
    celula=config.get('formas',{}).get(shape)
    if celula is None:raise ValueError(f'Visema sem asset: {shape}')
    def rect(r,size):
        if len(r)!=4 or not 0<=r[0]<r[2]<=1 or not 0<=r[1]<r[3]<=1:raise ValueError('Região de boca inválida')
        return tuple(round(v*size[i%2]) for i,v in enumerate(r))
    dst=rect(config['regiao'],base.size);src=rect(celula,atlas.size)
    patch=atlas.convert('RGBA').crop(src).resize((dst[2]-dst[0],dst[3]-dst[1]),Image.Resampling.BICUBIC)
    # Compensa a cor da pele na borda da placa; o desenho preto da boca é preservado.
    if config.get('igualar_pele',True):
        original=np.array(base.convert('RGBA').crop(dst),dtype=float);a=np.array(patch,dtype=float)
        borda=np.zeros(a.shape[:2],bool);m=max(1,min(a.shape[:2])//5)
        borda[:m]=True;borda[-m:]=True;borda[:,:m]=True;borda[:,-m:]=True
        valid=borda&(a[:,:,3]>200)
        if np.any(valid):
            offset=np.median(original[:,:,:3][valid],axis=0)-np.median(a[:,:,:3][valid],axis=0)
            peso=np.clip(np.mean(a[:,:,:3],axis=2)/100,0,1)[:,:,None]
            a[:,:,:3]=np.clip(a[:,:,:3]+offset*peso,0,255)
            patch=Image.fromarray(a.astype('uint8'),'RGBA')
    mask=Image.new('L',patch.size,0);d=ImageDraw.Draw(mask);m=max(1,min(patch.size)//9)
    d.rectangle((m,m,patch.width-1-m,patch.height-1-m),fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(max(.5,m/2)))
    from PIL import ImageChops
    mask=ImageChops.multiply(mask,patch.getchannel('A'))
    out=base.convert('RGBA').copy();out.paste(patch,dst[:2],mask)
    return out
