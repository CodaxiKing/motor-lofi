"""Run optional Rhubarb binary on recorded speech and save timed mouth cues."""
import json
import shutil
import subprocess
from pathlib import Path
from .facial_timeline import read_mouth_cues

def generate_cues(audio_file, output_file, executable='rhubarb', dialog_file=None):
    audio_file=Path(audio_file);output_file=Path(output_file)
    if not audio_file.is_file():raise FileNotFoundError(audio_file)
    binary=shutil.which(executable)
    if not binary:raise RuntimeError('Rhubarb executable not found. Install separately or provide --executable.')
    command=[binary,'-f','json','-o',str(output_file)]
    if dialog_file:command+=['-d',str(dialog_file)]
    command.append(str(audio_file))
    subprocess.run(command,check=True,capture_output=True,text=True,timeout=300)
    return read_mouth_cues(output_file)

def remap_cues(cues, src_start, src_end, video_start):
    """Map source audio cues onto episode clip time, including cropped clips."""
    if src_end<=src_start:raise ValueError('Invalid audio crop')
    result=[]
    for cue in cues:
        a=max(src_start,float(cue['start']));b=min(src_end,float(cue['end']))
        if b>a:result.append({'start':a-src_start+video_start,'end':b-src_start+video_start,'shape':cue['shape']})
    return result
