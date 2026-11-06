"""Esqueleto hierárquico de peças reais com pivôs, interpolação e IK de dois ossos."""
import json
import math
from functools import lru_cache
from pathlib import Path
from PIL import Image


def rot(v,graus):
    a=math.radians(graus);c,s=math.cos(a),math.sin(a)
    return (v[0]*c-v[1]*s,v[0]*s+v[1]*c)


def ik(dx,dy,l1,l2,lado=1):
    d=max(.0001,min(math.hypot(dx,dy),l1+l2-.0001))
    a=math.atan2(dy,dx)+lado*math.acos(max(-1,min(1,(l1*l1+d*d-l2*l2)/(2*l1*d))))
    kx,ky=l1*math.cos(a),l1*math.sin(a)
    b=math.atan2(dy-ky,dx-kx)
    return math.degrees(a)-90,math.degrees(b-a)


@lru_cache(maxsize=32)
def _ler(path,stamp):
    rig=json.loads(Path(path).read_text(encoding='utf-8'));ids=[]
    for p in rig['partes']:
        if p['id'] in ids or p.get('pai') and p['pai'] not in ids:raise ValueError('Ordem/pais inválidos no rig articulado')
        if len(p['regiao'])!=4 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in p['regiao']) or not 0<=p['regiao'][0]<p['regiao'][2]<=1 or not 0<=p['regiao'][1]<p['regiao'][3]<=1 or not math.isfinite(p['altura']) or p['altura']<=0:raise ValueError('Peça inválida')
        ids.append(p['id'])
    return rig


def carregar(base,nome):
    raiz=(Path(base)/'imagens').resolve();path=(raiz/nome).resolve()
    if not path.is_relative_to(raiz):raise ValueError('Rig fora da biblioteca')
    return _ler(str(path),path.stat().st_mtime_ns)


def raiz_movimento(rig,t,acoes):
    from .atuacao import envoltoria
    dy=lean=weight=0.
    for ac in acoes or []:
        if ac['tipo'] not in ('caminhar','correr'):continue
        w=envoltoria(t,ac['start'],ac['end'])
        if not w:continue
        ciclo=ac.get('ciclo',.62 if ac['tipo']=='correr' else 1.2)
        if ciclo<=0:raise ValueError('Ciclo inválido')
        phase=(t-ac['start'])/ciclo+ac.get('fase_inicial',0)
        if ac['tipo']=='correr':
            u=phase%.5
            value=.005*math.sin(math.pi*u/.32)**2 if u<.32 else -.012*math.sin(math.pi*(u-.32)/.18)**2
            dy+=value*w
        lean+=(9 if ac['tipo']=='correr' else 1.5)*w if rig.get('vista')=='perfil' else 0
        weight+=w
    return dy/max(1,weight),lean/max(1,weight)


def angulos(rig,t,acoes):
    from .core import keyframe
    from .atuacao import envoltoria
    out={p['id']:float(p.get('angulo',0)) for p in rig['partes']}
    raiz_y,lean=raiz_movimento(rig,t,acoes);out['torso']=out.get('torso',0)+lean
    movimentos={};total=0.
    for acao in acoes or []:
        start,end=acao['start'],acao['end'];tipo=acao['tipo']
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (start,end)) or end<=start:raise ValueError('Tempo de ação inválido')
        if tipo not in ('caminhar','correr','apontar','negar','ouvir','alertar','perguntar','afirmar','esconder','provocar'):raise ValueError('Ação desconhecida')
        peso=envoltoria(t,start,end)
        if not peso:continue
        if tipo in ('caminhar','correr'):
            run=tipo=='correr';ciclo=acao.get('ciclo',.62 if run else 1.2)
            if ciclo<=0:raise ValueError('Ciclo inválido')
            phase=(t-start)/ciclo+acao.get('fase_inicial',0);pose={};duty=.32 if run else .5
            for lado,off in [('e',0),('d',.5)]:
                u=(phase+off)%1;speed=acao.get('velocidade_x',0);stride=speed*ciclo*duty
                next_stride=stride;spent=speed*u*ciclo
                if acao.get('trilho'):
                    from .travelling import estado as estado_trilho
                    contact=start+(math.floor(phase+off)-acao.get('fase_inicial',0)-off)*ciclo
                    def distance(at):
                        return estado_trilho(acao['trilho'],at)[0]*acao['fator_trilho']+speed*at
                    stride=distance(contact+duty*ciclo)-distance(contact)
                    next_stride=distance(contact+ciclo+duty*ciclo)-distance(contact+ciclo)
                    spent=distance(t)-distance(contact)
                if u<duty:x=stride/2-spent;y=.935
                else:
                    q=(u-duty)/(1-duty);blend=.5-.5*math.cos(math.pi*q);x=-stride/2*(1-blend)+next_stride/2*blend
                    y=.935-(.085 if run else .03)*math.sin(math.pi*q)**2
                hip=rig.get('quadril',[.5,.57]);W,H=rig['canvas']
                offset=next(p.get('offset',[0,0]) for p in rig['partes'] if p['id']=='coxa_'+lado)
                ox,oy=rot((offset[0]*W,offset[1]*H),lean)
                branch=-1 if rig.get('vista')=='perfil' else (1 if lado=='e' else -1)
                a,b=ik((x+offset[0])*W-ox,(y-hip[1]-raiz_y)*H-oy,.19*H,.18*H,branch)
                pose['coxa_'+lado]=a-lean;pose['canela_'+lado]=b
                if 'pe_'+lado in out:pose['pe_'+lado]=-(a+b)
                pose['braco_'+lado]=math.cos(2*math.pi*(phase+off))*(38 if run else 17)
                pose['antebraco_'+lado]=(-58 if run else -4)+math.cos(2*math.pi*(phase+off))*(-12 if run else -5)
            for nome,v in pose.items():movimentos[nome]=movimentos.get(nome,0)+v*peso
            total+=peso
        else:
            targets={'apontar':{'braco_d':-65,'antebraco_d':-18},'negar':{'cabeca':-5},
                     'ouvir':{'cabeca':4},'alertar':{'braco_d':-40,'antebraco_d':-35},
                     'perguntar':{'cabeca':4,'antebraco_d':-15},'afirmar':{'cabeca':2},
                     'esconder':{'cabeca':-3,'antebraco_e':-8},'provocar':{'cabeca':5,'braco_d':-10}}
            for nome,v in targets[tipo].items():out[nome]=out.get(nome,0)+v*peso
        for nome,keys in acao.get('angulos',{}).items():out[nome]=keyframe(keys,t-start)*peso
    for nome,v in movimentos.items():out[nome]=out.get(nome,0)+v/max(1,total)
    return out


def juntas(rig,size,t,acoes=None):
    W,H=size;joints={};angles=angulos(rig,t,acoes)
    for p in rig['partes']:
        if p.get('pai'):
            par=joints[p['pai']];delta=rot((p.get('offset',[0,0])[0]*W,p.get('offset',[0,0])[1]*H),par[2])
            x,y=par[0]+delta[0],par[1]+delta[1];angle=par[2]+angles[p['id']]
        else:
            dy,_=raiz_movimento(rig,t,acoes)
            x,y=p['pos'][0]*W,(p['pos'][1]+dy)*H;angle=angles[p['id']]
        joints[p['id']]=(x,y,angle)
    return joints


def renderizar(rig,atlas,size,t,acoes=None,boca=None):
    """Peças são lidas do atlas sem modificar a arte original."""
    W,H=size;canvas=Image.new('RGBA',size);joints={};layers=[]
    angles=angulos(rig,t,acoes)
    joints=juntas(rig,size,t,acoes)
    for p in rig['partes']:
        x,y,angle=joints[p['id']]
        r=p['regiao'];crop=atlas.crop(tuple(round(v*atlas.size[i%2]) for i,v in enumerate(r)))
        h=max(1,round(p['altura']*H));w=max(1,round(h*crop.width/crop.height));im=crop.resize((w,h),Image.Resampling.BICUBIC)
        if boca and p['id']==rig.get('boca',{}).get('parte'):
            from .boca_local import compor
            im=compor(im,boca['atlas'],rig['boca']['config'],boca['shape'])
        pivot=p.get('pivot',[.5,.05]);px,py=pivot[0]*w,pivot[1]*h
        turned=im.rotate(-angle,expand=True,resample=Image.Resampling.BICUBIC)
        shift=rot((px-w/2,py-h/2),angle)
        at=(round(x-turned.width/2-shift[0]),round(y-turned.height/2-shift[1]))
        layers.append((p.get('z',0),turned,at))
    for _,im,at in sorted(layers,key=lambda l:l[0]):canvas.alpha_composite(im,at)
    return canvas
