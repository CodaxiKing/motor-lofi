"""Optional ML landmarks and triangle-based sprite deformation.

MediaPipe Tasks requires a separately supplied compatible pose_landmarker.task model.
No model is downloaded implicitly. Coordinates are image pixels.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw
from .auto_rig import generate_rig, BONES

MP_NAMES = {'head':0,'left_shoulder':11,'right_shoulder':12,'left_elbow':13,
 'right_elbow':14,'left_wrist':15,'right_wrist':16,'left_knee':25,
 'right_knee':26,'left_ankle':27,'right_ankle':28,'hip':23,'neck':11}

def detect_pose(image_path, model_path=None, confidence=.45):
    """Use MediaPipe PoseLandmarker when installed and a local model is provided.
    Fallback heuristic is explicitly labeled; never misrepresent it as ML.
    """
    rig=generate_rig(image_path)
    if not model_path:
        rig['detection']='heuristic';return rig
    if not Path(model_path).is_file(): raise FileNotFoundError(model_path)
    try:
        import mediapipe as mp
        from mediapipe.tasks import python as tasks
        from mediapipe.tasks.python import vision
    except ImportError as exc:
        raise RuntimeError('Install optional mediapipe to use --model') from exc
    options=vision.PoseLandmarkerOptions(base_options=tasks.BaseOptions(model_asset_path=str(model_path)),
                                          running_mode=vision.RunningMode.IMAGE,num_poses=1)
    with vision.PoseLandmarker.create_from_options(options) as detector:
        result=detector.detect(mp.Image.create_from_file(str(image_path)))
    if not result.pose_landmarks:
        rig['detection']='heuristic_no_pose_detected';return rig
    lm=result.pose_landmarks[0]; w,h=rig['image_size']; detected={}
    for name,idx in MP_NAMES.items():
        p=lm[idx]
        if getattr(p,'visibility',1.)>=confidence:
            detected[name]=[round(p.x*w),round(p.y*h)]
    if 'left_shoulder' in detected and 'right_shoulder' in detected:
        a,b=detected['left_shoulder'],detected['right_shoulder']
        detected['neck']=[round((a[0]+b[0])/2),round((a[1]+b[1])/2)]
    if 'hip' in detected and 24<len(lm):
        a,b=lm[23],lm[24];detected['hip']=[round((a.x+b.x)*w/2),round((a.y+b.y)*h/2)]
    rig['landmarks'].update(detected)
    rig['detection']='mediapipe_partial' if len(detected)<len(MP_NAMES) else 'mediapipe'
    rig['detected_landmarks']=sorted(detected)
    rig['requires_manual_review']=True
    return rig

def deform_sprite(image, source_points, target_points, triangles=None):
    """Piecewise affine deformation of RGBA sprite via triangulated mesh.
    Requires scipy; triangle boundaries are masked to avoid overwriting neighbors.
    Source and target are matching lists of pixel coordinates. Not ARAP.
    """
    import numpy as np
    try: from scipy.spatial import Delaunay
    except ImportError as exc: raise RuntimeError('scipy is required for deformation') from exc
    from PIL import ImageChops
    src=np.asarray(source_points,dtype=float); dst=np.asarray(target_points,dtype=float)
    if src.shape!=dst.shape or src.ndim!=2 or src.shape[1]!=2 or len(src)<3:
        raise ValueError('At least three matching 2D points required')
    if not np.isfinite(src).all() or not np.isfinite(dst).all(): raise ValueError('Nonfinite landmark')
    if triangles is None: triangles=Delaunay(src).simplices
    original=image.convert('RGBA'); output=Image.new('RGBA',original.size)
    for tri in triangles:
        a=src[list(tri)]; b=dst[list(tri)]
        mat=np.column_stack((b,np.ones(3)))
        try: coeff=np.linalg.solve(mat,a)
        except np.linalg.LinAlgError: continue
        # Pillow affine coefficients map output (destination) to input (source).
        affine=(float(coeff[0,0]),float(coeff[1,0]),float(coeff[2,0]),
                float(coeff[0,1]),float(coeff[1,1]),float(coeff[2,1]))
        transformed=original.transform(original.size,Image.Transform.AFFINE,affine,
                                        resample=Image.Resampling.BILINEAR)
        mask=Image.new('L',original.size,0)
        ImageDraw.Draw(mask).polygon([tuple(map(float,p)) for p in b],fill=255)
        transformed.putalpha(ImageChops.multiply(transformed.getchannel('A'),mask))
        output.alpha_composite(transformed)
    return output

def warp_rig(image, rig, target_landmarks):
    """Warp a character based on reviewed landmarks plus image boundary anchors.
    Keep corner anchors fixed to avoid unfilled background near edges.
    """
    w,h=image.size; names=list(rig['landmarks']); src=[rig['landmarks'][n] for n in names]
    dst=[target_landmarks.get(n,rig['landmarks'][n]) for n in names]
    anchors=[(0,0),(w-1,0),(0,h-1),(w-1,h-1),(w//2,0),(w//2,h-1)]
    return deform_sprite(image,src+anchors,dst+anchors)
