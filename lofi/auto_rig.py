"""Semi-automatic 2D cutout rig bootstrap from alpha silhouette.

Not an ML pose detector: estimates landmarks on a standing, front-facing humanoid.
Manual landmark correction is required before production animation.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from PIL import Image

LANDMARKS = {
 'head':(.5,.11),'neck':(.5,.23),'left_shoulder':(.32,.28),
 'right_shoulder':(.68,.28),'left_elbow':(.23,.43),'right_elbow':(.77,.43),
 'left_wrist':(.19,.58),'right_wrist':(.81,.58),'hip':(.5,.56),
 'left_knee':(.4,.75),'right_knee':(.6,.75),'left_ankle':(.38,.97),
 'right_ankle':(.62,.97)
}
BONES = [('head','neck'),('neck','hip'),('neck','left_shoulder'),('neck','right_shoulder'),
 ('left_shoulder','left_elbow'),('left_elbow','left_wrist'),
 ('right_shoulder','right_elbow'),('right_elbow','right_wrist'),
 ('hip','left_knee'),('left_knee','left_ankle'),('hip','right_knee'),('right_knee','right_ankle')]


def generate_rig(image_path, alpha_threshold=20, overrides=None):
    with Image.open(image_path) as source:
        im=source.convert('RGBA')
        alpha=im.getchannel('A')
        if source.mode != 'RGBA' and 'transparency' not in source.info:
            raise ValueError('Auto rig requires an image with transparent background (alpha channel)')
        bbox=alpha.point(lambda a:255 if a>alpha_threshold else 0).getbbox()
    if bbox is None: raise ValueError('Empty silhouette')
    left,top,right,bottom=bbox; w=right-left; h=bottom-top
    points={key:[round(left+u*w),round(top+v*h)] for key,(u,v) in LANDMARKS.items()}
    for key,pt in (overrides or {}).items():
        if key not in points: raise ValueError(f'Unknown landmark: {key}')
        if len(pt)!=2: raise ValueError('Landmark must be [x,y]')
        points[key]=[round(pt[0]),round(pt[1])]
    return {'version':1,'source':str(image_path),'image_size':list(im.size),'bbox':list(bbox),
            'landmarks':points,'bones':[list(b) for b in BONES],
            'confidence':'heuristic_only','requires_manual_review':True,
            'notes':'Front-facing upright humanoid approximation; no segmentation or automatic cutouts.'}


def draw_preview(image_path, rig, output_path):
    from PIL import ImageDraw
    with Image.open(image_path) as source: im=source.convert('RGBA')
    draw=ImageDraw.Draw(im)
    for a,b in rig['bones']:
        draw.line((tuple(rig['landmarks'][a]),tuple(rig['landmarks'][b])),fill=(0,255,170,255),width=max(2,im.width//150))
    for pt in rig['landmarks'].values():
        x,y=pt; radius=max(2,im.width//100)
        draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=(255,80,70,255))
    im.save(output_path)


def main():
    parser=argparse.ArgumentParser(description='Estimate and preview a 2D character rig')
    parser.add_argument('image');parser.add_argument('--out',default='rig.json');parser.add_argument('--preview',default='rig-preview.png')
    parser.add_argument('--overrides',help='JSON file mapping landmark names to [x,y]')
    args=parser.parse_args()
    overrides=json.loads(Path(args.overrides).read_text(encoding='utf8')) if args.overrides else None
    rig=generate_rig(args.image,overrides=overrides)
    Path(args.out).write_text(json.dumps(rig,ensure_ascii=False,indent=2),encoding='utf8')
    draw_preview(args.image,rig,args.preview)
    print(f'Rig written to {args.out}; review landmark preview at {args.preview}')

if __name__=='__main__': main()
