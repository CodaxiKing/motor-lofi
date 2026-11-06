"""Contratos de fala no módulo ilustrado; narração não aciona a boca em cena."""
import math
import os
import json
from pathlib import Path


def texto_cena(cena):
    return ' '.join([cena.get('narracao','')]+[f.get('texto','') for f in cena.get('falas',[])])


def minimo_cena(cena,base):
    cursor=.15;fim=0
    for f in cena.get('falas',[]):
        dur=f.get('duracao',max(.4,len(f['texto'].split())/3))
        if f.get('audio'):
            from .sincronia import ler_audio
            x,sr=ler_audio(Path(base)/f['audio']);src=f.get('src',[0,len(x)/sr]);dur=src[1]-src[0]
        start=f.get('inicio',cursor);fim=max(fim,start+dur+.15);cursor=start+dur+.2
    return fim


def validar(cenas):
    for cena in cenas:
        ids={p['id'] for p in cena['personagens']}
        for f in cena.get('falas',[]):
            if f.get('personagem') not in ids|{'narrador'}:raise ValueError('Fala de personagem ausente da cena')
            if not f.get('texto','').strip():raise ValueError('Fala sem texto')
            for campo in ('inicio','duracao'):
                v=f.get(campo,0 if campo=='inicio' else 1)
                if not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 or campo=='duracao' and v==0:
                    raise ValueError('Tempo de fala inválido')


def compilar(cenas,shots,pasta_saida,pasta_audio=None):
    validar(cenas);eventos=[];voices={};clips=[];subs=[]
    base=Path(pasta_audio or pasta_saida).resolve()
    for cena,shot in zip(cenas,shots):
        cursor=.15
        for f in cena.get('falas',[]):
            f=dict(f)
            if f.get('mouth_cues_file'):
                path=(base/f['mouth_cues_file']).resolve();doc=json.loads(path.read_text(encoding='utf-8'))
                f['mouth_cues']=doc.get('cues',doc.get('mouthCues',[]))
                f['mouth_cues']=[dict(c,shape=c.get('shape',c.get('value','rest'))) for c in f['mouth_cues']]
                f['cue_format']=doc.get('cue_format','rhubarb' if 'mouthCues' in doc else 'viseme')
            local=f.get('inicio',cursor);src=f.get('src');dur=f.get('duracao',max(.4,len(f['texto'].split())/3))
            for cue in f.get('mouth_cues',[]):
                if not 0<=cue['start']<cue['end']: raise ValueError('Cue de boca inválida')
            audio=f.get('audio');voice=f'{f["personagem"]}_fala_{len(eventos):03d}'
            if audio:
                from .sincronia import ler_audio
                path=(base/audio).resolve();x,sr=ler_audio(path);total=len(x)/sr
                src=src or [0,total]
                if len(src)!=2 or not 0<=src[0]<src[1]<=total+.001:raise ValueError('Recorte de fala inválido')
                dur=src[1]-src[0]
                voices[voice]=os.path.relpath(path,Path(pasta_saida).resolve())
            start=round(shot['start']+local,4);end=round(start+dur,4)
            if f.get('cue_format','viseme') not in ('viseme','rhubarb'):raise ValueError('Formato de cues inválido')
            if any(c['end']>dur+.001 for c in f.get('mouth_cues',[])):raise ValueError('Cues ultrapassam a duração da fala')
            if start<shot['start'] or end>shot['end']+.001:raise ValueError('Fala não cabe na cena; aumente duração ou ajuste o áudio')
            e={'speaker':f['personagem'],'voice':voice,'start':start,'end':end,'text':f['texto'],
               'intencao':f.get('intencao','afirmar'),'audio_pronto':bool(audio),'mouth_cues':f.get('mouth_cues',[]),'cue_format':f.get('cue_format','viseme')}
            if f.get('atuacao_voz'):e['atuacao_voz']=f['atuacao_voz']
            for anterior in eventos:
                if anterior['speaker']==e['speaker'] and max(anterior['start'],start)<min(anterior['end'],end):
                    raise ValueError('Falas simultâneas do mesmo personagem')
            eventos.append(e)
            if audio: subs.append({'voice':voice,'src':src,'text':[f['texto']]})
            if audio:clips.append({'voice':voice,'src':src,'at':start,'acoustic':None})
            cursor=local+dur+.2
        for p in shot['imagens']['personagens']:
            p['eventos_fala']=[e for e in eventos if e['speaker']==p.get('id') and e['start']>=shot['start'] and e['end']<=shot['end']+.001]
    return eventos,voices,clips,subs
