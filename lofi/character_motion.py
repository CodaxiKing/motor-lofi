"""Subtle character motions, facial sprite swapping and simple articulated cutouts."""
from __future__ import annotations
import math
from pathlib import Path
from PIL import Image
from .facial_timeline import expression_at, gaze_at, read_mouth_cues


def facial_state(t, *, blink_interval=3.8, blink_duration=.14, expression='neutral', mouth_cues=None):
    """Return deterministic facial state; cues are [{start,end,shape}]."""
    if blink_interval <= 0 or blink_duration < 0: raise ValueError('Invalid blink timing')
    eyes = 'closed' if t % blink_interval < blink_duration else 'open'
    mouth = 'rest'
    for cue in mouth_cues or []:
        if float(cue['start']) <= t < float(cue['end']): mouth = cue['shape']; break
    return {'eyes':eyes,'mouth':mouth,'expression':expression}


def render_character(parts, state, time_seconds=0, base_dir='.'):
    """Compose a layered character from transparent cutouts. Part positions are pixels."""
    size = tuple(state['size'])
    canvas = Image.new('RGBA', size, (0,0,0,0))
    breathing = math.sin(2*math.pi*time_seconds*float(state.get('breaths_per_minute',12))/60)
    cues = state.get('mouth_cues')
    if state.get('mouth_cues_file'):
        cue_path=(Path(base_dir)/state['mouth_cues_file']).resolve()
        if not cue_path.is_relative_to(Path(base_dir).resolve()): raise ValueError('Unsafe mouth cue path')
        cues=read_mouth_cues(cue_path)
    face = facial_state(time_seconds, blink_interval=state.get('blink_interval',3.8),
                        expression=expression_at(state,time_seconds), mouth_cues=cues)
    for part in sorted(parts, key=lambda p:p.get('z',0)):
        variants=part.get('variants',{})
        name=part['name']
        selection = (face['eyes'] if name in ('eyes','eyelids') else
                     face['mouth'] if name=='mouth' else
                     gaze_at(state,time_seconds) if name in ('pupils','gaze') else
                     face['expression'])
        path=variants.get(selection, part.get('path'))
        if not path: continue
        target=(Path(base_dir)/path).resolve()
        if not target.is_relative_to(Path(base_dir).resolve()): raise ValueError('Unsafe character image path')
        with Image.open(target) as source: im=source.convert('RGBA')
        x=int(part.get('x',0)); y=int(part.get('y',0))
        if part.get('breathing'): y+=round(float(part.get('amplitude',2))*breathing)
        if part.get('head_sway'): x+=round(float(part.get('amplitude',2))*math.sin(time_seconds*1.3))
        if name in ('pupils','gaze'):
            x += round(float(state.get('gaze_x',0)))
            y += round(float(state.get('gaze_y',0)))
        angle=float(part.get('rotation',0))
        if part.get('sway'): angle+=float(part.get('sway'))*math.sin(time_seconds*1.3)
        if part.get('rig'):
            from .advanced_rig import warp_rig
            rig_file=(Path(base_dir)/part['rig']).resolve()
            if not rig_file.is_relative_to(Path(base_dir).resolve()): raise ValueError('Unsafe rig path')
            import json
            rig=json.loads(rig_file.read_text(encoding='utf8'))
            im=warp_rig(im,rig,part.get('target_landmarks',{}))
        if angle: im=im.rotate(angle,expand=True,resample=Image.Resampling.BICUBIC)
        canvas.alpha_composite(im,(x,y))
    return canvas
