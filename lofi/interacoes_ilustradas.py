"""Contatos por marcos de desenhos completos, piso e oclusão por profundidade."""
import math


def projetar(ponto,size,fundo_info):
    W,H=size
    if fundo_info:
        (w,h),x,y,s=fundo_info
        return (x+ponto[0]*w*s)/W,(y+ponto[1]*h*s)/H
    return ponto[0],ponto[1]


def alvo(nome,cfg,size,fundo_info):
    pontos=dict(cfg.get('mapa_composicao',{}).get('interacoes',{}),**cfg.get('pontos_interacao',{}))
    if nome not in pontos:raise ValueError(f'Ponto de interação ausente: {nome}')
    p=pontos[nome]
    if len(p)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in p):raise ValueError('Ponto de interação inválido')
    return projetar(p,size,fundo_info)


def aplicar(p,cfg,t,size,fundo_info,ciclo=None,frame=None,espelhado=False):
    """Só translada a raiz de um desenho, conservando escala e membros unidos.

    modo posicionar: bloqueia no marco final do ciclo durante toda a ação,
    para a mão chegar ao alvo sem arrastar os pés na fase final.
    modo contato: trava o marco atual; exige posição já compatível com o piso.
    """
    W,H=size;out=dict(p)
    piso=p.get('seguir_piso')
    if piso:
        linhas=cfg.get('mapa_composicao',{}).get('pisos',{})
        if piso not in linhas:raise ValueError(f'Linha de piso ausente: {piso}')
        pts=sorted(projetar(v,size,fundo_info) for v in linhas[piso])
        if len(pts)<2:raise ValueError('Piso precisa de ao menos dois pontos')
        if any(a[0]>=b[0] for a,b in zip(pts,pts[1:])):raise ValueError('Piso tem coordenadas horizontais repetidas')
        x=out.get('pos',.5);out['chao']=pts[0][1] if x<=pts[0][0] else pts[-1][1]
        for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
            if x0<=x<=x1:out['chao']=y0+(y1-y0)*(x-x0)/(x1-x0);break
    for contato in p.get('interacoes',[]):
        if not contato['inicio']<=t<contato['fim']:continue
        if ciclo is None or frame is None:raise ValueError('Interação exige ciclo completo com marcos calibrados')
        marco=contato.get('marco','mao_d');modo=contato.get('modo','posicionar')
        f=ciclo['frames'][-1] if modo=='posicionar' else frame
        if marco not in f.get('marcos',{}):raise ValueError(f'Marco não calibrado: {marco}')
        mx,my=f['marcos'][marco];ax,ay=f['ancora']
        if espelhado:mx=1-mx;ax=1-ax
        aspecto=contato.get('aspecto_celula',ciclo.get('aspecto_celula'))
        if not aspecto:raise ValueError('Ciclo de interação precisa de aspecto_celula')
        fator=ciclo['referencia'].get('altura_referencia',.98)/ciclo['referencia']['altura_corpo']
        altura=out.get('altura',.5)*fator
        tx,ty=alvo(contato['alvo'],cfg,size,fundo_info)
        pos=tx-(mx-ax)*altura*H/W*aspecto
        chao=ty-(my-ay)*altura
        if modo=='contato':
            if abs(chao-out.get('chao',.94))*H>contato.get('tolerancia_px',5):
                raise ValueError('Mão e chão incompatíveis; ajuste o bloqueio ou a pose antes do contato')
            chao=out.get('chao',.94)
        elif modo!='posicionar':raise ValueError('Modo de interação inválido')
        out.update(pos=pos,chao=chao,orientacao='manual',espelhar=espelhado,respirar=0,balanco_corpo=0)
        out.pop('andar',None)
    return out
