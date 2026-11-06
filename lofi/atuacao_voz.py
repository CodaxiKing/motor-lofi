"""Congela a voz de referência antes da atuação e deriva pausas do áudio real."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

import numpy as np


def janelas(audio, sr, passo=.02):
    n = max(1, round(sr*passo))
    rms = np.array([np.sqrt(np.mean(audio[i:i+n]**2)) for i in range(0,len(audio),n)])
    if not len(rms): raise ValueError('Áudio vazio')
    limiar = max(.004, float(np.percentile(rms,90))*.12)
    ativos = rms >= limiar
    # Pausas menores que 120 ms pertencem à mesma unidade de atuação.
    for i in range(1,len(ativos)-1):
        if ativos[i]: continue
        fim=i
        while fim<len(ativos) and not ativos[fim]: fim+=1
        if ativos[i-1] and fim<len(ativos) and (fim-i)*passo<.12: ativos[i:fim]=True
    fala=[];pausas=[];inicio=0
    for i in range(1,len(ativos)+1):
        if i<len(ativos) and ativos[i]==ativos[inicio]: continue
        a=inicio*n/sr;b=min(len(audio),i*n)/sr
        (fala if ativos[inicio] else pausas).append({'inicio':round(a,4),'fim':round(b,4)})
        inicio=i
    return fala,[p for p in pausas if p['fim']-p['inicio']>=.12]


def preparar(historia, base, previa=False):
    from .sincronia import ler_audio
    from .audio import visemes
    out=copy.deepcopy(historia)
    falas=[f for c in out['cenas'] for f in c.get('falas',[])]
    if not falas: raise ValueError('Informe falas com arquivos de voz antes de preparar atuação')
    for f in falas:
        if not f.get('audio'): raise ValueError('Fala sem áudio: '+f['texto'])
        if not previa and f.get('audio_final') is not True:
            raise ValueError('Voz final ainda não definida; marque audio_final ou use --previa para vozes de teste')
        path=(Path(base)/f['audio']).resolve()
        audio,sr=ler_audio(path)
        src=f.get('src',[0,len(audio)/sr])
        if len(src)!=2 or not 0<=src[0]<src[1]<=len(audio)/sr+.001: raise ValueError('Recorte de voz inválido')
        audio=audio[round(src[0]*sr):round(src[1]*sr)]
        fala,pausas=janelas(audio,sr)
        f['atuacao_voz']={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                          'src':src,'duracao':len(audio)/sr,'janelas_fala':fala,'pausas':pausas,
                          'audio_final':bool(f.get('audio_final')), 'metodo':'RMS com pausas; visemas acústicos aproximados'}
        f['duracao']=len(audio)/sr
        if not f.get('mouth_cues') and not f.get('mouth_cues_file'):
            step=max(1,sr//24);nomes={0:'rest',1:'M',2:'A',3:'E',4:'O',5:'U'}
            cues=[]
            for i,v in enumerate(visemes(audio,step)):
                a=i*step/sr;b=min(len(audio)/sr,(i+1)*step/sr)
                if b<=a:continue
                shape=nomes[int(v)]
                if any(p['inicio']<=a<p['fim'] for p in pausas):shape='rest'
                if cues and cues[-1]['shape']==shape:cues[-1]['end']=b
                else:cues.append({'start':a,'end':b,'shape':shape})
            f.update(mouth_cues=cues,cue_format='viseme')
    out.setdefault('producao',{}).update(etapa='previa_audio' if previa else 'animacao',vozes_congeladas=True)
    return out


def validar_snapshot(historia, base):
    producao=historia.get('producao',{})
    if producao.get('etapa') not in ('previa_audio','animacao','final'):return
    final=producao['etapa']!='previa_audio'
    for c in historia['cenas']:
        for f in c.get('falas',[]):
            snapshot=f.get('atuacao_voz')
            if not snapshot or not f.get('audio'):raise ValueError('Prepare a atuação com a voz antes de animar')
            if final and (not snapshot.get('audio_final') or f.get('audio_final') is not True):
                raise ValueError('Etapa final exige voz final definida')
            path=(Path(base)/f['audio']).resolve()
            if hashlib.sha256(path.read_bytes()).hexdigest()!=snapshot['sha256']:
                raise ValueError('Voz alterada depois da atuação; prepare novamente pausas e sincronização')
            if f.get('src',snapshot['src'])!=snapshot['src']:
                raise ValueError('Recorte de voz mudou depois da atuação')


def gestos(evento):
    if not evento.get('audio_pronto'):return []
    j=evento.get('atuacao_voz',{}).get('janelas_fala')
    if j is None:return [dict(evento)]
    return [dict(evento,start=evento['start']+v['inicio'],end=evento['start']+v['fim']) for v in j if v['fim']-v['inicio']>=.12]


def validar_eventos(spec, base):
    for evento in spec.get('dialogue_events',[]):
        snapshot=evento.get('atuacao_voz')
        if not snapshot:continue
        nome=spec.get('voices',{}).get(evento['voice'])
        if not nome or hashlib.sha256((Path(base)/nome).read_bytes()).hexdigest()!=snapshot['sha256']:
            raise ValueError('Voz alterada depois da atuação; recompile antes de renderizar')
        clips=[c for c in spec.get('clips',[]) if c['voice']==evento['voice']]
        if len(clips)!=1 or clips[0]['src']!=snapshot['src']:
            raise ValueError('Recorte de voz mudou depois da atuação')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('historia',type=Path);p.add_argument('--saida',required=True,type=Path)
    p.add_argument('--previa',action='store_true')
    args=p.parse_args()
    doc=preparar(json.loads(args.historia.read_text(encoding='utf-8')),args.historia.resolve().parent,args.previa)
    for cena in doc['cenas']:
        for fala in cena.get('falas',[]):
            for campo in ('audio','mouth_cues_file'):
                if fala.get(campo):fala[campo]=os.path.relpath((args.historia.resolve().parent/fala[campo]).resolve(),args.saida.resolve().parent)
    args.saida.parent.mkdir(parents=True,exist_ok=True)
    with args.saida.open('x',encoding='utf-8') as f:f.write(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print(args.saida)


if __name__=='__main__':main()
