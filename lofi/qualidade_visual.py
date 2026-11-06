"""Arte por enquadramento, orçamento de pixels e reamostragem com alfa correto."""
import json,math
from functools import lru_cache
from pathlib import Path
from PIL import Image
from .core import keyframe


@lru_cache(maxsize=32)
def _perfil(path,stamp):return json.loads(Path(path).read_text(encoding='utf-8'))


def perfil(base,p):
    if p.get('arte_por_plano'):return p['arte_por_plano']
    root=(Path(base)/'imagens').resolve();id=p.get('id') or p['img'].split('/')[0]
    path=(root/id/'personagem.json').resolve()
    if not path.is_relative_to(root):raise ValueError('Ficha de arte fora da biblioteca')
    return _perfil(str(path),path.stat().st_mtime_ns).get('arte_por_plano',{}) if path.is_file() else {}


def redimensionar(im,size):
    # Premultiplication prevents transparent black pixels tinting the outline.
    if im.mode=='RGBA':return im.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA')
    return im.resize(size,Image.Resampling.LANCZOS)


def escolher(base,p,plano,t,ciclo=None,frame=None,tempo_global=None):
    familia='close' if plano in ('close','detalhe') else 'medio' if plano=='medio' else None
    if familia is None:return None,'plano_sem_variante'
    if p.get('usar_variantes',True) is False:return None,'variante_desativada'
    if ciclo and ciclo.get('tipo')=='retrato':return None,'retrato_existente'
    acao=(ciclo or {}).get('acao','neutro')
    if ciclo and acao not in ('parado','neutro','reacao'):return None,'acao_exige_arte_compativel'
    # Do not erase calibrated phonemes or replace a reaching hand with a
    # portrait that does not depict the same action.
    if p.get('interacoes'):return None,'contato_exige_arte_compativel'
    agora=t if tempo_global is None else tempo_global
    ativo=any(e['start']<=agora<e['end'] for e in p.get('eventos_fala',[]))
    if ativo or p.get('fala'):return None,'fala_exige_boca_hd_calibrada'
    estado=keyframe(p.get('expressao','neutro'),t)
    banco=perfil(base,p).get(familia,{})
    if estado=='neutro' and 'piscando' in banco and p.get('piscar_hd',True) and t%p.get('periodo_piscar_hd',3.6)<.12:
        estado='piscando'
    if estado not in banco:return None,'expressao_hd_ausente'
    arte=banco[estado]
    if ciclo is None and arte.get('poses_compativeis') and p['img'] not in arte['poses_compativeis']:
        return None,'pose_exige_arte_compativel'
    return arte,None


def substituir(layer,arte,rosto,base,camera,size,exigir_cobertura=True):
    from .imagens import carregar
    im,x,y,s,prof,portal,mov=layer
    if arte['img']==mov.get('fonte'):
        return (im,x,y,s,prof,portal,dict(mov,arte_hd=arte['img']))
    nova=carregar(base,arte['img']);r=arte['rosto'];w,h=nova.size
    if len(r)!=4 or not 0<=r[0]<r[2]<=1 or not 0<=r[1]<r[3]<=1:raise ValueError('Referência do rosto inválida')
    flip=mov.get('espelhado',False)
    cx=(r[0]+r[2])/2
    if flip:cx=1-cx
    scale=rosto['face_width']/((r[2]-r[0])*w)
    nx=rosto['face_x']-cx*w*scale;ny=rosto['face_y']-(r[1]+r[3])/2*h*scale
    z,ox,oy=(camera[k] for k in ('z','ox','oy'))
    # A waist-short portrait cannot replace a full-body drawing when the
    # viewport reveals its bottom edge. Keep the original in that case.
    if exigir_cobertura and arte.get('cobertura','retrato')=='retrato' and (ny+h*scale)*z+oy<size[1]-2:return None
    newmov=dict(mov,rig=None,arte_hd=arte['img'])
    return (nova,nx,ny,scale,prof,portal,newmov)


def acomodar_retratos(camera,layers,variantes,size):
    """Pan within the existing world so a complete bust reaches the bottom.

    This changes the camera composition, never stretches or extends artwork.
    """
    H=size[1];z=camera['z'];oy=camera['oy'];necessario=0.;permitido=min(H*.24,-oy)
    for i,(_,arte,_) in variantes.items():
        if arte.get('cobertura','retrato')!='retrato':continue
        im,x,y,s,*_=layers[i]
        necessario=max(necessario,H+1-((y+im.height*s)*z+oy))
        face_bottom=(y+arte['rosto'][3]*im.height*s)*z+oy
        permitido=min(permitido,H*.82-face_bottom)
    if 0<necessario<=permitido:return dict(camera,oy=oy+necessario)
    return camera


def ajustar_camera(camera,layers,cfg,size):
    config=cfg.get('qualidade_visual',{})
    if config is False:return camera,[]
    maximo=config.get('max_ampliacao',1.25)
    if not isinstance(maximo,(int,float)) or not math.isfinite(maximo) or maximo<1:raise ValueError('Limite de ampliação inválido')
    focos=set(camera.get('alvos',[]));ator_layers=[l for l in layers if l[-1] and l[-1].get('ator')]
    selecionados=[l for l in ator_layers if not focos or l[-1].get('id') in focos]
    desejado=camera['z'];limite=min([maximo/max(l[3],1e-9) for l in selecionados]+[desejado])
    z=max(1,min(desejado,limite)) if config.get('limitar_zoom',True) else desejado
    out=dict(camera)
    if z<desejado:
        # Preserve the camera's focus point while pulling back.
        W,H=size;cx=(W/2-camera['ox'])/desejado;cy=(H/2-camera['oy'])/desejado
        out.update(z=z,ox=min(0,max(W-W*z,W/2-cx*z)),oy=min(0,max(H-H*z,H/2-cy*z)))
    relatorio=[]
    for im,x,y,s,prof,portal,mov in selecionados:
        relatorio.append({'personagem':mov.get('id'),'fonte':mov.get('arte_hd',mov.get('fonte')),
                          'pixels_origem':list(im.size),'ampliacao':round(s*z,3),'limite':maximo,
                          'zoom_pedido':round(desejado,3),'zoom_aplicado':round(z,3),
                          'insuficiente_na_origem':s>maximo,'variante_hd':bool(mov.get('arte_hd')),
                          'motivo_variante':mov.get('motivo_variante')})
    return out,relatorio


def analisar(spec,base,size=None):
    from .imagens import quadro
    size=tuple(size or spec.get('preview_size',spec.get('size',[1080,1920])))
    rows=[]
    for shot in spec.get('shots',[]):
        if not shot.get('imagens'):continue
        a,b=shot['start'],shot['end'];times={a,(a+b)/2,max(a,b-1/spec.get('fps',24))}
        for c in shot['imagens'].get('camera_ilustrada',{}).get('cortes',[]):times.add(a+(c['inicio']+c['fim'])/2)
        for t in sorted(times):
            diag=[];quadro(shot,t,str(base),size,diagnostico=diag)
            rows.extend(dict(r,tempo=round(t,3)) for r in diag)
    return {'tamanho':list(size),'amostras':rows,'metodo':'pixels de origem versus projeção; não cria detalhe ausente'}


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('spec');p.add_argument('--out',required=True);args=p.parse_args()
    path=Path(args.spec);out=analisar(json.loads(path.read_text(encoding='utf-8')),path.resolve().parent)
    Path(args.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
