"""Generate image requests from a storyboard; no automatic image generation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .visual_assets import VisualAssetLibrary


def requirements(episode):
    """Explicit shot requirements: [{kind,subject,style,view,pose,...}]."""
    requests=[];seen=set()
    for i,shot in enumerate(episode.get('shots',[])):
        for item in shot.get('image_requirements',[]):
            req=dict(item)
            if req.get('kind') not in ('character','environment','prop','expression','pose','animation','full_scene'):
                raise ValueError('Unknown asset kind')
            req.setdefault('style',episode.get('visual_style',''))
            key=json.dumps(req,sort_keys=True,ensure_ascii=False)
            if key not in seen:
                requests.append(dict(req,shot_index=i));seen.add(key)
    return requests


def plan_episode(episode,library):
    reqs=requirements(episode)
    matches=library.plan([{k:v for k,v in r.items() if k!='shot_index'} for r in reqs])
    return {'visual_mode':episode.get('visual_mode','DESENHO'),
            'total_requests':len(matches),'reusable':sum(x['status']=='reusable' for x in matches),
            'missing':sum(x['status']=='missing' for x in matches),
            'items':[dict(match,shot_index=req['shot_index']) for req,match in zip(reqs,matches)]}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('episode');parser.add_argument('library');parser.add_argument('--out',default='image-plan.json');a=parser.parse_args()
    episode=json.loads(Path(a.episode).read_text(encoding='utf8'))
    lib=VisualAssetLibrary(a.library)
    try: result=plan_episode(episode,lib)
    finally:lib.close()
    Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(f"Assets: {result['reusable']} reutilizáveis, {result['missing']} pendentes")

if __name__=='__main__':main()
