import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from lofi.advanced_rig import detect_pose, deform_sprite, warp_rig
from lofi.lipsync_pipeline import remap_cues
from lofi.episode_export import export_episode

class V5Tests(unittest.TestCase):
    def test_warp_identity(self):
        im=Image.new('RGBA',(30,30),(100,80,60,255))
        points=[(0,0),(29,0),(0,29),(29,29)]
        out=deform_sprite(im,points,points)
        self.assertEqual(out.size,im.size)
        self.assertEqual(out.getpixel((12,12)),im.getpixel((12,12)))
    def test_bad_points(self):
        with self.assertRaises(ValueError):deform_sprite(Image.new('RGBA',(10,10)),[(0,0)],[(1,1)])
    def test_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'c.png';im=Image.new('RGBA',(30,50));im.paste((255,0,0,255),(5,2,25,48));im.save(p)
            self.assertEqual(detect_pose(p)['detection'],'heuristic')
    def test_clip_timing(self):
        cues=[{'start':1,'end':2,'shape':'A'},{'start':2,'end':4,'shape':'B'}]
        self.assertEqual(remap_cues(cues,1.5,2.5,10),[{'start':10.0,'end':10.5,'shape':'A'},{'start':10.5,'end':11.0,'shape':'B'}])
    def test_export(self):
        import shutil
        if not shutil.which('ffmpeg'):self.skipTest('ffmpeg unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);Image.new('RGBA',(64,64),(200,100,50,255)).save(base/'bg.png')
            episode={'visual_mode':'DESENHO','fps':4,'size':[64,64],'total':.5,
                     'shots':[{'start':0,'end':.5,'image_scene':{'layers':[{'path':'bg.png'}]}}]}
            (base/'ep.json').write_text(json.dumps(episode))
            out=export_episode(base/'ep.json')
            self.assertTrue(out.is_file());self.assertGreater(out.stat().st_size,100)
if __name__=='__main__':unittest.main()
