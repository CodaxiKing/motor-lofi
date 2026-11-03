"""Deterministic facial timeline and Rhubarb TSV/JSON cue adapter."""
from __future__ import annotations
import json
from pathlib import Path


def active_key(keys, t, default=None):
    if not keys: return default
    result=default
    for at, value in sorted(keys, key=lambda k: float(k[0])):
        if float(at)>t: break
        result=value
    return result


def read_mouth_cues(path):
    """Read Rhubarb JSON (mouthCues) or TSV: start TAB end TAB shape."""
    path=Path(path)
    if path.suffix.lower()=='.json':
        obj=json.loads(path.read_text(encoding='utf8'))
        rows=obj['mouthCues'] if isinstance(obj,dict) else obj
    else:
        rows=[]
        for line in path.read_text(encoding='utf8').splitlines():
            if not line.strip() or line.lstrip().startswith('#'): continue
            fields=line.split('\t')
            if len(fields)!=3: raise ValueError('Expected TSV: start\tend\tshape')
            rows.append(dict(start=fields[0],end=fields[1],shape=fields[2]))
    cues=[]
    for row in rows:
        start=float(row['start']);end=float(row['end']);shape=str(row.get('shape',row.get('value','')))
        if not 0<=start<end or not shape: raise ValueError('Invalid mouth cue')
        cues.append(dict(start=start,end=end,shape=shape))
    return sorted(cues,key=lambda x:x['start'])


def expression_at(state, t):
    return active_key(state.get('expression_keys'),t,state.get('expression','neutral'))


def gaze_at(state,t):
    return active_key(state.get('gaze_keys'),t,state.get('gaze','center'))
