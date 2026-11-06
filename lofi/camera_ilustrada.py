"""Planos do Motor Lo-Fi adaptados a recortes com alturas físicas e alfa.

O bloqueio pertence ao mapa; a câmera transforma o mundo já composto.
Referências anatômicas estáveis evitam zoom oscilando a cada desenho do ciclo.
"""
import copy
import math
from .core import keyframe, ease

ALIASES={'corpo_inteiro':'inteiro','corpo_todo':'inteiro','cintura':'medio',
         'cintura_acima':'medio','cintura_para_cima':'medio','rosto':'close'}
PLANOS=('auto','aberto','conjunto','inteiro','americano','medio','close','detalhe')
MARCOS={'cintura':.56,'joelhos':.79,'ombros':.32,'centro_rosto':.12,'largura_rosto':.32}


def configurar(camera,pessoas):
    if isinstance(camera,str):camera={'plano':camera}
    if not isinstance(camera,dict):raise ValueError('Câmera ilustrada precisa de um plano ou objeto')
    out=copy.deepcopy(camera);p=ALIASES.get(out.get('plano','auto'),out.get('plano','auto'))
    if out.get('close') not in (None,'none'):
        p='close';out.setdefault('alvo',out['close']);out.setdefault('entrada_s',out.get('close_in',0))
    elif out.get('follow') is not None:
        out.setdefault('alvo',out['follow']);out['seguir']=True
    if p not in PLANOS:raise ValueError(f'Plano ilustrado inválido: {p}')
    out['plano']=p
    al=out.get('alvo')
    if al is not None:
        al=al if isinstance(al,list) else [al];ids=[]
        for a in al:
            if isinstance(a,int) and not isinstance(a,bool):
                if not 0<=a<len(pessoas):raise ValueError('Índice do alvo de câmera inválido')
                a=pessoas[a].get('id',pessoas[a].get('img'))
            if not isinstance(a,str) or a not in [p.get('id',p.get('img')) for p in pessoas]:
                raise ValueError(f'Alvo de câmera ausente: {a}')
            ids.append(a)
        if not ids:raise ValueError('Lista de alvos vazia')
        out['alvo']=ids
    for nome,padrao in [('push',0),('entrada_s',0),('zoom_max',9)]:
        v=out.get(nome,padrao)
        if not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 or (nome=='zoom_max' and v<1):
            raise ValueError(f'Parâmetro de câmera inválido: {nome}')
    if 'cortes' in out:
        base={k:v for k,v in out.items() if k!='cortes'};cortes=[];fim=0
        for corte in out['cortes']:
            a=corte['inicio'];b=corte['fim']
            if not all(isinstance(v,(float,int)) and math.isfinite(v) for v in (a,b)) or a<fim or b<=a:
                raise ValueError('Cortes de câmera precisam ser ordenados e sem sobreposição')
            c=configurar(dict(base,**corte),pessoas);c.update(inicio=a,fim=b);cortes.append(c);fim=b
        out['cortes']=cortes
    return out


def caixas(pessoas,base,size,rel,seguir=True):
    from .composicao import animar,medida,envelope
    W,H=size;out=[]
    for p in pessoas:
        q=animar(p if seguir else p.get('_origem_camera',p),rel if seguir else 0)
        (w,h),b=medida(base,q.get('referencia_escala',q['img']))
        ax,ay=q.get('ancora',[.5,1]);s=q.get('altura',.6)*H/h
        x=q.get('pos',.5)*W
        if not isinstance(x,(int,float)):continue
        floor=q.get('chao',.94)*H
        if q.get('animacoes_quadros'):
            # Whole-body cycles normalize their physical height to .98.
            bot=floor;top=bot-q.get('altura',.6)*H*.98
        else:
            top=floor+(b[1]-ay*h)*s;bot=floor+(b[3]-ay*h)*s
        _,l,r=envelope(q,base);bh=bot-top
        marcos=dict(MARCOS,**q.get('marcos_camera',{}))
        face_x=x;face_top=top;face_y=top+bh*marcos['centro_rosto'];face_width=bh*marcos['largura_rosto']
        frame=q.get('_frame_camera');ciclo=q.get('_ciclo_camera')
        if frame and ciclo and 'centro_rosto' in frame.get('marcos',{}):
            fm=frame['marcos'];mx,my=fm['centro_rosto'];ax,ay=frame['ancora']
            if q.get('_flip_camera'):mx=1-mx;ax=1-ax
            fator=ciclo['referencia'].get('altura_referencia',.98)/ciclo['referencia']['altura_corpo']
            altura=q.get('altura',.6)*H*fator;aspecto=ciclo.get('aspecto_celula',1)
            face_x=x+(mx-ax)*altura*aspecto;face_top=floor+(fm['topo_cabeca']-ay)*altura
            face_y=floor+(my-ay)*altura;face_width=fm['largura_rosto']*altura*aspecto
            # Keep physical body height stable across gait frames. Face
            # landmarks guide close-ups without pumping whole-body zoom.
        for k,v in marcos.items():
            if not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<v<1:
                raise ValueError(f'Marco anatômico inválido: {k}')
        amplas=('andar','correr','agachar','abaixar','levantar','esconder','espreitar','avancar','caminhar')
        movimento=q.get('portal') or q.get('andar') or any(
            a['inicio']<=rel<a['fim'] and any(nome in (a.get('acao','')+' '+a.get('ciclo','')) for nome in amplas)
            for a in q.get('animacoes_quadros',[]))
        out.append({'id':q.get('id',q['img']),'x':x,'top':top,'bot':bot,'h':bh,'acao_ampla':bool(movimento),
                    'left':x-l*bh,'right':x+r*bh,
                    'torso_left':x+(b[0]-ax*w)*s,'torso_right':x+(b[2]-ax*w)*s,'marcos':marcos,
                    'face_x':face_x,'face_y':face_y,'face_top':face_top,'face_width':face_width})
    return out


def resolver(camera,pessoas,base,size,rel=0,duracao=1):
    W,H=size;cam=configurar(camera,pessoas)
    for corte in cam.get('cortes',[]):
        if corte['inicio']<=rel<corte['fim']:
            cam=dict(corte,_inicio_plano=corte['inicio'],_duracao_plano=corte['fim']-corte['inicio']);break
    tempo_camera=max(0,rel-cam.get('_inicio_plano',0))
    u=min(1,max(0,tempo_camera/max(.001,cam.get('_duracao_plano',duracao))))
    def valor(nome,padrao):
        v=cam.get(nome,padrao)
        tempo=u if isinstance(v,list) and len(v)==2 and all(isinstance(x,(float,int)) for x in v) else tempo_camera
        n=keyframe(v,tempo)
        if not isinstance(n,(int,float)) or not math.isfinite(n):raise ValueError(f'Parâmetro de câmera inválido: {nome}')
        return n
    zoom_k=valor('zoom_k',1)
    if zoom_k<=0:raise ValueError('zoom_k precisa ser positivo')
    if 'zoom' in cam:
        z=valor('zoom',1)*zoom_k
        if z<1:raise ValueError('Zoom menor que 1 revela bordas fora do cenário')
        z=min(z,cam.get('zoom_max',9));cx=valor('cx',.5);cy=valor('cy',.5)
        if not 0<=cx<=1 or not 0<=cy<=1:raise ValueError('Centro de câmera fora do cenário')
        return {'z':z,'ox':(W-W*z)*cx,'oy':(H-H*z)*cy,'plano':'manual','alvos':cam.get('alvo',[]),'corte_inferior_intencional':True}
    acts=caixas(pessoas,base,size,rel,cam.get('seguir',True))
    alvo=cam.get('alvo')
    if alvo:acts=[a for a in acts if a['id'] in alvo]
    plano=cam['plano']
    if plano=='auto':
        # Keep one composition for the shot, including every scheduled broad
        # action; no mid-shot camera jump when a walk/gesture starts or stops.
        amplos=any(a.get('acao_ampla') for a in acts)
        if len(acts)==1:
            selected=next((p for p in pessoas if p.get('id',p['img'])==acts[0]['id']),{})
            amplos=amplos or bool(selected.get('animacoes_quadros'))
        plano=('inteiro' if amplos else 'medio') if len(acts)==1 else 'conjunto'
    if not acts or plano=='aberto':return {'z':1.,'ox':0.,'oy':0.,'plano':'aberto','alvos':[]}
    if plano not in ('inteiro','conjunto') and not alvo:acts=acts[:1]
    top=min(a['face_top'] if plano in ('close','detalhe') else a['top'] for a in acts)
    if plano in ('inteiro','conjunto'):
        bot=max(a['bot'] for a in acts);left=min(a['left'] for a in acts);right=max(a['right'] for a in acts)
        headroom=.06;footroom=.06
    else:
        frac={'americano':'joelhos','medio':'cintura','close':'ombros','detalhe':'centro_rosto'}[plano]
        bot=max(a['top']+a['h']*a['marcos'][frac] for a in acts)
        if plano=='close':bot=max(a['face_top']+a['h']*a['marcos']['ombros'] for a in acts)
        if plano=='detalhe':
            top=min(a['top']+a['h']*max(0,a['marcos']['centro_rosto']-.11) for a in acts)
            bot=max(a['top']+a['h']*(a['marcos']['centro_rosto']+.14) for a in acts)
        headroom=.055;footroom=0
        if plano in ('medio','americano'):
            # Upper-body poses still reserve hands/shoulders horizontally.
            left=min(a['torso_left'] for a in acts);right=max(a['torso_right'] for a in acts)
        else:
            left=min(a['face_x']-a['face_width']*.56 for a in acts)
            right=max(a['face_x']+a['face_width']*.56 for a in acts)
    height=max(1,bot-top);width=max(1,right-left)
    z=max(1,min((1-headroom-footroom)*H/height,.92*W/width,cam.get('zoom_max',9)))
    push=1+.035*u*cam.get('push',0)
    # Full bodies must retain feet and head even at the end of a push-in.
    if plano in ('inteiro','conjunto'):
        z=min(z*push,(1-headroom-.015)*H/height,.98*W/width,cam.get('zoom_max',9))
    else:z=min(cam.get('zoom_max',9),z*push)
    z=max(1,min(cam.get('zoom_max',9),z*zoom_k))
    ox=W/2-(left+right)/2*z;oy=headroom*H-top*z
    if cam.get('entrada_s',0):
        k=ease(min(1,max(0,tempo_camera/cam['entrada_s'])));z=1+(z-1)*k;ox*=k;oy*=k
    ox=min(0,max(W-W*z,ox));oy=min(0,max(H-H*z,oy))
    return {'z':z,'ox':ox,'oy':oy,'plano':plano,'alvos':[a['id'] for a in acts],
            'corte_inferior_intencional':plano not in ('inteiro','conjunto')}
