"""Renderiza uma prévia GIF de um ciclo de caminhada com recortes reais."""
import argparse
import json
import sys
import subprocess
import tempfile
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lofi.imagens import quadro, faltam


def renderizar(spec_path, output):
    spec_path = Path(spec_path).resolve()
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    missing = faltam(spec_path)
    if missing:
        raise ValueError(f'Recortes ausentes: {missing}')
    fps = spec.get('fps', 20)
    size = tuple(spec.get('preview_size', spec.get('size', [360, 640])))
    nivel=visema=None;buffers={}
    if spec.get('voices') and spec.get('clips'):
        from lofi.sincronia import canais
        nivel,visema,buffers=canais(spec,spec_path.parent)
    frames = []
    for i in range(round(spec['total'] * fps)):
        t = i / fps
        shot = next(s for s in spec['shots'] if s['start'] <= t < s['end'])
        frames.append(quadro(shot, t, str(spec_path.parent), size,nivel,visema,not spec.get('narrado',False)))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower()=='.mp4':
        from lofi.sincronia import ffmpeg
        from lofi import wavio
        import numpy as np
        with tempfile.TemporaryDirectory(dir=output.parent) as temp:
            wav=Path(temp)/'mix.wav';sr=44100
            mix=sum(buffers.values(),np.zeros(round(spec['total']*sr)))
            wavio.write(wav,np.clip(mix,-1,1),sr)
            cmd=[ffmpeg(),'-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{size[0]}x{size[1]}',
                 '-r',str(fps),'-i','-','-i',str(wav),'-c:v','libx264','-preset','fast','-crf','20',
                 '-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart',str(output)]
            proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                for frame in frames:proc.stdin.write(frame.convert('RGB').tobytes())
                proc.stdin.close();error=proc.stderr.read();ret=proc.wait()
                if ret:raise RuntimeError(error.decode(errors='replace'))
            finally:
                if proc.poll() is None:proc.kill();proc.wait()
        return output
    # Paleta compartilhada mantém o fundo estável e reduz o peso das prévias.
    amostras=Image.new('RGB',(6*72,4*128))
    for k in range(24):
        index=min(len(frames)-1,round(k*(len(frames)-1)/23))
        amostras.paste(frames[index].resize((72,128)),((k%6)*72,(k//6)*128))
    paleta=amostras.quantize(colors=256)
    frames=[im.quantize(palette=paleta,dither=Image.Dither.NONE) for im in frames]
    frames[0].save(output, save_all=True, append_images=frames[1:],
                   duration=[round((i+1)*100/fps)*10-round(i*100/fps)*10 for i in range(len(frames))], loop=0, optimize=True)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec')
    parser.add_argument('output')
    args = parser.parse_args()
    print(renderizar(args.spec, args.output))
