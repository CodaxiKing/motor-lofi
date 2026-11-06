"""Gera clipes curtos com voz e relatórios por cena antes da exportação completa."""
import argparse
import html
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from . import imagens, wavio
from .sincronia import canais, ffmpeg


def _audio(spec, base):
    from .atuacao_voz import validar_eventos
    validar_eventos(spec,base)
    if not spec.get('clips'):return None,None,None
    nivel,visema,buffers=canais(spec,base)
    mix=np.sum(list(buffers.values()),axis=0) if buffers else None
    return nivel,visema,mix


def revisar(spec, base, saida, cenas=None, max_segundos=8, size=(432,768), fps=24):
    if max_segundos<=0 or not 1<=fps<=60 or min(size)<16 or any(v%2 for v in size):raise ValueError('Configuração de revisão inválida; use dimensões pares')
    from .continuidade_animacao import analisar
    from .ciclos_quadros import carregar as ler_ciclo
    base=Path(base).resolve();saida=Path(saida).resolve()
    saida.mkdir(parents=True,exist_ok=False)
    nivel,visema,mix=_audio(spec,base)
    continuidade=analisar(spec,base)
    relatorios=[]
    shots=[(i,s) for i,s in enumerate(spec['shots'],1) if s.get('imagens') and (not cenas or i in cenas)]
    if not shots:raise ValueError('Nenhuma cena ilustrada selecionada')
    for i,shot in shots:
        a=shot['start'];b=min(shot['end'],a+max_segundos);cfg=shot['imagens']
        pasta=(base/cfg.get('pasta_biblioteca','.')).resolve()
        erros=[];avisos=[];apoios=[]
        for p in cfg.get('personagens',[]):
            for ac in p.get('animacoes_quadros',[]):
                c=ler_ciclo(pasta,ac['ciclo'])
                if c.get('deslocamento_corpo_ciclo'):
                    calibrado=bool(c.get('contatos_solo'))
                    movel=p.get('trajeto') or p.get('andar') or cfg.get('travelling') and p.get('seguir_travelling')
                    apoios.append({'id':p.get('id'),'ciclo':ac['ciclo'],'passada':True,
                                   'contatos_calibrados':calibrado,'trava_ativa':bool(p.get('travar_apoios',calibrado and movel))})
                    if not calibrado:avisos.append(p.get('id','ator')+': contatos dos pés ainda não calibrados')
        eventos=[e for e in spec.get('dialogue_events',[]) if a<=e['start']<shot['end']]
        for e in eventos:
            if not e.get('audio_pronto'):erros.append('Fala sem arquivo de voz: '+e['speaker'])
            elif not e.get('atuacao_voz',{}).get('audio_final'):avisos.append('Voz de referência ainda não marcada como final: '+e['speaker'])
        if not eventos and mix is None and not spec.get('sem_audio_intencional'):
            avisos.append('Cena sem voz disponível para revisão acústica')
        if b<shot['end']:avisos.append('Clipe parcial; conferir o restante da cena antes do vídeo completo')
        wav=None;peak=0
        if mix is not None:
            trecho=mix[round(a*44100):round(b*44100)]
            peak=float(np.max(np.abs(trecho))) if len(trecho) else 0
            if peak>=1:avisos.append('Soma das vozes excede o nível digital; prévia atenuada para não distorcer')
            wav=saida/f'cena_{i:03d}_voz.wav'
            wavio.write(wav,trecho/max(1,peak/.95),44100)
        video=saida/f'cena_{i:03d}.mp4'
        cmd=[ffmpeg(),'-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{size[0]}x{size[1]}',
             '-framerate',str(fps),'-i','pipe:0']
        if wav:cmd+=['-i',str(wav),'-c:a','aac','-b:a','128k']
        cmd+=['-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-threads','2','-t',str(b-a),str(video)]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        diagnostico=[];amostras=[]
        alvos={0,round((b-a)*fps/2),math.ceil((b-a)*fps)-1}
        for evento in eventos:
            cue=next((c for c in evento.get('mouth_cues',[]) if c.get('shape') not in ('rest','X')),None)
            t=evento['start']+((cue['start']+cue['end'])/2 if cue else (evento['end']-evento['start'])/2)
            if a<=t<b:alvos.add(min(math.ceil((b-a)*fps)-1,round((t-a)*fps)))
        try:
            for n in range(math.ceil((b-a)*fps)):
                t=min(b-1e-6,a+n/fps)
                frame=imagens.quadro(shot,t,base,size,nivel,visema,not spec.get('narrado',False),diagnostico)
                proc.stdin.write(frame.convert('RGB').tobytes())
                if n in alvos:amostras.append((t,frame.copy()))
            proc.stdin.close();stderr=proc.stderr.read();code=proc.wait()
            if code:raise RuntimeError(stderr.decode('utf-8',errors='replace'))
        except Exception:
            proc.kill();proc.wait()
            raise
        folha=Image.new('RGB',(size[0]*len(amostras),size[1]+28),'#0b1018');d=ImageDraw.Draw(folha)
        for k,(t,im) in enumerate(amostras):
            folha.paste(im,(k*size[0],28));d.text((k*size[0]+8,7),f'{t:.2f} s',fill='white')
        folha.save(saida/f'cena_{i:03d}.png')
        achados=[v for v in continuidade['achados'] if a<=v['t']<shot['end']]
        r={'cena':i,'scene':shot.get('scene'),'intervalo':[a,b], 'cena_completa':b==shot['end'],
           'video':video.name,'apoios':apoios,'contatos':'renderizados com marcos' if any(p.get('interacoes') for p in cfg.get('personagens',[])) else 'não aplicável',
           'enquadramento':[json.loads(v) for v in sorted({json.dumps(v,sort_keys=True,ensure_ascii=False) for v in diagnostico})],
           'sombras':'habilitadas' if cfg.get('sombras') is not False else 'desligadas na cena',
           'audio':{'voz_presente':peak>.0001,'trilha_voz_exportada':wav is not None,'pico_antes_atenuacao':peak,'mix':'vozes secas; música e efeitos requerem revisão na mixagem completa'},
           'continuidade':achados,'erros':erros,'avisos':sorted(set(avisos)),
           'revisao_visual':'pendente de assistir ao clipe; verificações automáticas não aprovam atuação'}
        r['ok_tecnico']=not erros and not any(v.get('severity')=='error' for v in achados)
        relatorios.append(r)
    relatorio={'cenas':relatorios,'fps_previa':fps,'resolucao_previa':list(size),
               'ok_tecnico':all(r['ok_tecnico'] for r in relatorios),
               'metodo':'Compositor real; voz no tempo original do episódio; quadros e relatório por cena.'}
    (saida/'relatorio.json').write_text(json.dumps(relatorio,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    links='\n'.join(f'<article><h2>Cena {r["cena"]}</h2><video controls preload="metadata" width="360" src="{r["video"]}"></video><p>{html.escape("; ".join(r["avisos"]))}</p></article>' for r in relatorios)
    (saida/'index.html').write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Revisão por cena</title><style>body{background:#10151e;color:#eee;font:16px system-ui;margin:32px}article{display:inline-block;vertical-align:top;margin:16px;max-width:380px}video{max-width:100%}</style><h1>Revisão por cena</h1><p>Assistir aos apoios, contatos, câmera, sombras e voz. <a href="relatorio.json">Relatório</a></p>'+links+'</html>',encoding='utf-8')
    return relatorio


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('episode',type=Path)
    p.add_argument('--saida',required=True,type=Path);p.add_argument('--cenas',type=int,nargs='+')
    p.add_argument('--max-segundos',type=float,default=8);p.add_argument('--largura',type=int,default=432)
    args=p.parse_args();spec=json.loads(args.episode.read_text(encoding='utf-8'))
    h=round(args.largura*16/9/2)*2
    r=revisar(spec,args.episode.resolve().parent,args.saida,args.cenas,args.max_segundos,(args.largura,h))
    print(json.dumps({'saida':str(args.saida),'ok_tecnico':r['ok_tecnico']},ensure_ascii=False))


if __name__=='__main__':main()
