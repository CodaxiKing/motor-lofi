"""Auditoria amostrada de animação: saltos, escala, apoio, fala e fechamento de loop."""
import json
from pathlib import Path
import numpy as np


def analisar(spec,base,amostras_s=8):
    from .composicao import planejar,animar,identidade
    from .boca_local import estado
    achados=[];prev={};size=tuple(spec.get('preview_size',[432,768]));nivel=visema=None
    def add(code,text,t,severity='warning'):
        chave=(code,text)
        if not any((a['code'],a['message'])==chave for a in achados):achados.append({'code':code,'message':text,'t':round(t,3),'severity':severity})
    if spec.get('voices') and spec.get('clips'):
        try:
            from .sincronia import canais
            nivel,visema,_=canais(spec,base)
        except (FileNotFoundError,RuntimeError,ValueError) as exc:add('audio_indisponivel',str(exc),0)
    for s in spec.get('shots',[]):
        cfg=s.get('imagens')
        if not cfg:continue
        pasta=(Path(base)/cfg.get('pasta_biblioteca','.')).resolve()
        if cfg.get('mapa_composicao'):cfg,_=planejar(cfg,pasta,size,auditoria=False)
        times=np.linspace(s['start'],max(s['start'],s['end']-1e-5),max(2,round((s['end']-s['start'])*amostras_s)))
        extras=[]
        for p in cfg.get('personagens',[]):
            for e in p.get('eventos_fala',[]):
                extras.extend(e['start']+(c['start']+c['end'])/2 for c in e.get('mouth_cues',[]))
        times=sorted(set(float(t) for t in times)|{t for t in extras if s['start']<=t<s['end']})
        for t in times:
            for original in cfg.get('personagens',[]):
                p=animar(original,t-s['start']);id=identidade(p)
                pos=p.get('pos',.5)
                if not isinstance(pos,(int,float)):continue
                if p.get('andar'):
                    u=(t-s['start'])/max(.001,s['end']-s['start']);pos=p['andar'][0]+(p['andar'][1]-p['andar'][0])*u
                now=(pos,p.get('chao',.94),p.get('altura',.6),t,s.get('scene'))
                old=prev.get(id)
                if old and t-old[3]<.3 and old[4]==now[4] and not s.get('corte_intencional'):
                    if max(abs(now[i]-old[i]) for i in (0,1))>.06:add('salto_posicao',f'{id}: salto brusco de posição',t)
                    if abs(now[2]/max(.001,old[2])-1)>.10:add('salto_escala',f'{id}: escala muda bruscamente',t)
                prev[id]=now
                if p.get('rig_camadas'):
                    from .articulado import carregar,juntas
                    rig=carregar(pasta,p['rig_camadas']);cw,ch=rig['canvas'];acoes=[dict(a) for a in p.get('acoes',[])]
                    if p.get('andar'):
                        speed=(p['andar'][1]-p['andar'][0])*size[0]/(p['altura']*size[1])*ch/cw/(s['end']-s['start'])
                        for a in acoes:
                            if a['tipo'] in ('caminhar','correr'):a['velocidade_x']=speed
                    rel=t-s['start']
                    if cfg.get('travelling') and p.get('seguir_travelling'):
                        for a in acoes:
                            if a['tipo'] in ('caminhar','correr'):
                                a['trilho']=cfg['travelling'];a['fator_trilho']=ch/cw/p['altura']
                    js=juntas(rig,(cw,ch),rel,acoes)
                    from .composicao import espelhamento
                    for a in acoes:
                        if a['tipo'] not in ('caminhar','correr') or not a['start']+.2<rel<a['end']-.2:continue
                        for lado,off in [('e',0),('d',.5)]:
                            u=((rel-a['start'])/a.get('ciclo',.62 if a['tipo']=='correr' else 1.2)+a.get('fase_inicial',0)+off)%1
                            key='pe:'+id+lado+':'+a['tipo']+':'+str(a['start'])
                            if u>=(.32 if a['tipo']=='correr' else .5):prev.pop(key,None);continue
                            bone='pe_'+lado
                            if bone not in js:continue
                            x,y,_=js[bone];ax,ay=p.get('ancora',[.5,1])
                            if espelhamento(p,pos):x=cw-x;ax=1-ax
                            world=(pos+(x-ax*cw)*p['altura']*size[1]/ch/size[0],p['chao']+(y-ay*ch)*p['altura']/ch)
                            if cfg.get('travelling'):
                                from .travelling import estado as estado_trilho
                                dist,_=estado_trilho(cfg['travelling'],rel);world=(world[0]+dist*size[1]/size[0],world[1])
                            antes=prev.get(key)
                            if antes and max(abs(world[i]-antes[i]) for i in (0,1))>.006:
                                add('pe_deslizando',f'{id}: apoio {bone} desliza durante contato',t)
                            prev[key]=world
                shape,e=estado(p,t,nivel,visema,not spec.get('narrado',False))
                if e and e.get('audio_pronto') and p.get('img') and not p.get('bocas_locais',{}).get(p['img']) and not p.get('boca') and not p.get('bocas'):
                    add('boca_sem_asset',f'{id}: pose falante não tem boca local calibrada',t)
                if shape!='rest' and e and nivel and nivel(e['voice'],t)<.05:
                    add('boca_no_silencio',f'{id}: boca aberta em silêncio',t)
                if p.get('apoios'):
                    for apoio in p['apoios']:
                        if apoio['start']<=t-s['start']<apoio['end']:
                            key='apoio:'+id+':'+apoio['id'];v=(pos,p.get('chao',.94))
                            anterior=prev.get(key)
                            if anterior and max(abs(v[i]-anterior[i]) for i in (0,1))>.006:
                                add('pe_deslizando',f'{id}: posição do corpo mudou durante apoio fixo {apoio["id"]}',t)
                            prev[key]=v
    for e in spec.get('dialogue_events',[]):
        if not e.get('audio_pronto'):add('fala_sem_audio',f'{e["speaker"]}: fala aguarda gravação',e['start'])
    if spec.get('seamless_loop'):
        from .imagens import quadro
        shots=[s for s in spec['shots'] if s.get('imagens')]
        if shots:
            try:
                a=quadro(shots[0],shots[0]['start'],str(base),(108,192),nivel,visema,not spec.get('narrado',False))
                b=quadro(shots[-1],shots[-1]['end'],str(base),(108,192),nivel,visema,not spec.get('narrado',False))
                if np.abs(np.asarray(a,dtype=float)-np.asarray(b,dtype=float)).mean()>1:
                    add('loop_descontinuo','Fim do loop difere do início',spec['total'])
            except (FileNotFoundError,ValueError) as exc:add('loop_nao_verificado',str(exc),spec['total'])
    return {'ok':not any(a['severity']=='error' for a in achados),'achados':achados,
            'amostras_s':amostras_s,'nota':'Auditoria geométrica e acústica amostrada; não substitui revisão visual.'}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('episode');parser.add_argument('--out')
    args=parser.parse_args();p=Path(args.episode).resolve();r=analisar(json.loads(p.read_text(encoding='utf-8')),p.parent)
    text=json.dumps(r,ensure_ascii=False,indent=2)
    if args.out:Path(args.out).write_text(text+'\n',encoding='utf-8')
    print(text)
