"""Render an illustrated episode to MP4 via existing motor when available,
otherwise export standalone image_scene shots and optional audio with ffmpeg.
"""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from .drawing_mode import draw_shot

def export_episode(spec_path, output=None, ffmpeg='ffmpeg'):
    spec_path=Path(spec_path).resolve(); spec=json.loads(spec_path.read_text(encoding='utf8'))
    if spec.get('visual_mode')!='DESENHO':raise ValueError('Only DESENHO mode supported by standalone exporter')
    fps=int(spec.get('fps',24));size=tuple(spec.get('size',[1080,1920]));shots=sorted(spec['shots'],key=lambda s:s['start'])
    if fps<=0 or min(size)<=0:raise ValueError('Invalid fps or size')
    if not shots or any(s.get('image_scene') is None or s['end']<=s['start'] for s in shots):
        raise ValueError('Every shot must have image_scene and positive duration')
    binary=shutil.which(ffmpeg)
    if not binary:raise RuntimeError('ffmpeg executable not found')
    output=Path(output or spec_path.parent/spec.get('out','desenho.mp4')).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    duration=float(spec.get('total',max(s['end'] for s in shots)))
    command=[binary,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{size[0]}x{size[1]}',
             '-r',str(fps),'-i','pipe:0']
    audio=spec.get('audio')
    if audio:
        audio_path=(spec_path.parent/audio).resolve()
        if not audio_path.is_relative_to(spec_path.parent) or not audio_path.is_file():raise ValueError('Invalid audio path')
        command+=['-i',str(audio_path)]
    command+=['-c:v','libx264','-pix_fmt','yuv420p','-crf','20']
    if audio:command+=['-c:a','aac','-shortest']
    command.append(str(output))
    proc=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for frame in range(round(duration*fps)):
            t=frame/fps
            shot=next((s for s in shots if s['start']<=t<s['end']),None)
            if shot is None:
                from PIL import Image
                img=Image.new('RGB',size,(0,0,0))
            else:img=draw_shot(shot,t,spec_path.parent,size)
            proc.stdin.write(img.convert('RGB').tobytes())
        proc.stdin.close();stderr=proc.stderr.read();code=proc.wait()
        if code:raise RuntimeError(f'ffmpeg failed: {stderr.decode(errors="replace")[-2000:]}')
    except BaseException:
        if proc.poll() is None:proc.kill()
        proc.wait();raise
    finally:
        if proc.stderr: proc.stderr.close()
    return output

def main():
    p=argparse.ArgumentParser();p.add_argument('episode');p.add_argument('--out');a=p.parse_args()
    print(export_episode(a.episode,a.out))
if __name__=='__main__':main()
