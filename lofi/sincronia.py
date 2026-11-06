"""Análise local de voz e montagem de canais secos por falante, sem downloads."""
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
import numpy as np
from scipy.signal import resample_poly
from . import wavio


def ffmpeg():
    path=shutil.which('ffmpeg')
    if path:return path
    try:
        import imageio_ffmpeg
        path=imageio_ffmpeg.get_ffmpeg_exe()
        if Path(path).is_file():return path
    except ImportError:pass
    raise RuntimeError('FFmpeg não disponível')


def ler_audio(path,sr=44100):
    path=Path(path)
    if not path.is_file():raise FileNotFoundError(path)
    if path.suffix.lower()=='.wav':x,taxa=wavio.read(path)
    else:
        result=subprocess.run([ffmpeg(),'-v','error','-i',str(path),'-ac','1','-ar',str(sr),
                               '-f','f32le','-acodec','pcm_f32le','pipe:1'],check=True,capture_output=True)
        x=np.frombuffer(result.stdout,dtype='<f4').astype(float);taxa=sr
    if x.ndim>1:x=x.mean(axis=1)
    if taxa!=sr:
        divisor=math.gcd(int(taxa),sr);x=resample_poly(x,sr//divisor,int(taxa)//divisor)
    return np.asarray(x,dtype=float),sr


def analisar(path,fps=24,backend='espectro',dialogo=None):
    if backend not in ('espectro','rhubarb'):raise ValueError('Backend de sincronia inválido')
    x,sr=ler_audio(path);dur=len(x)/sr
    if backend=='rhubarb':
        from .lipsync_pipeline import generate_cues
        with tempfile.TemporaryDirectory() as temp:
            wav=Path(temp)/'voz.wav';wavio.write(wav,x,sr)
            cues=generate_cues(wav,Path(temp)/'cues.json',dialog_file=dialogo)
        return {'metodo':'rhubarb','cue_format':'rhubarb','aproximado':True,'duracao':dur,'cues':cues}
    from .audio import visemes
    step=max(1,sr//fps);codes=visemes(x,step)
    nomes={0:'rest',1:'M',2:'A',3:'E',4:'O',5:'U'};cues=[]
    for i,code in enumerate(codes):
        a=i*step/sr;b=min(dur,(i+1)*step/sr);shape=nomes[int(code)]
        if cues and cues[-1]['shape']==shape:cues[-1]['end']=b
        else:cues.append({'start':a,'end':b,'shape':shape})
    return {'metodo':'espectro','cue_format':'viseme','aproximado':True,'duracao':dur,'cues':cues,
            'nota':'Estimativa acústica; não é alinhamento fonético exato.'}


def canais(spec,base,fps=None):
    """Retorna callbacks no tempo do episódio; música/efeitos não comandam boca."""
    fps=fps or spec.get('fps',24);sr=44100;n=round(spec['total']*sr)
    buffers={};cache={}
    for clip in spec.get('clips',[]):
        voz=clip['voice'];path=Path(base)/spec['voices'][voz]
        if str(path) not in cache:cache[str(path)]=ler_audio(path)[0]
        x=cache[str(path)];a,b=clip['src'];seg=x[round(a*sr):round(b*sr)]
        at=round(clip['at']*sr);end=min(n,at+len(seg))
        if at<0 or end<at:raise ValueError('Clip fora da timeline')
        buf=buffers.setdefault(voz,np.zeros(n));buf[at:end]+=seg[:end-at]
    from .audio import visemes
    levels={};shapes={};step=max(1,sr//fps)
    for voz,x in buffers.items():
        env=np.array([np.sqrt(np.mean(x[i:i+step]**2)) for i in range(0,len(x),step)])
        mx=np.percentile(env[env>1e-4],90) if np.any(env>1e-4) else 1
        levels[voz]=np.clip(env/max(mx,1e-8),0,1);shapes[voz]=visemes(x,step)
    def valor(data,v,t):
        vals=data.get(v,[]);i=int(t*fps)
        return vals[i] if 0<=i<len(vals) else 0
    return lambda v,t:float(valor(levels,v,t)),lambda v,t:int(valor(shapes,v,t)),buffers


if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('audio');p.add_argument('output')
    p.add_argument('--backend',choices=['espectro','rhubarb'],default='espectro');p.add_argument('--dialogo')
    args=p.parse_args();out=Path(args.output)
    if out.exists():raise FileExistsError(out)
    out.write_text(json.dumps(analisar(args.audio,backend=args.backend,dialogo=args.dialogo),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
