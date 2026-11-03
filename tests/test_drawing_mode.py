import tempfile
import unittest
from pathlib import Path
from PIL import Image
from lofi.drawing_mode import draw_shot

class DrawingModeTests(unittest.TestCase):
    def test_full_scene_and_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            Image.new('RGBA',(40,40),(80,20,10,255)).save(root/'bg.png')
            shot={'start':3,'end':5,'image_scene':{'layers':[{'path':'bg.png'}],
                'effects':[{'type':'flicker','strength':.3}]}}
            a=draw_shot(shot,3,root,(40,40));b=draw_shot(shot,3.1,root,(40,40))
            self.assertEqual(a.size,(40,40));self.assertNotEqual(a.tobytes(),b.tobytes())
    def test_facial_layer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            Image.new('RGBA',(10,10),(0,255,0,255)).save(root/'face.png')
            shot={'start':0,'end':2,'image_scene':{'layers':[{'x':5,'y':6,
                'character':{'parts':[{'name':'face','path':'face.png'}], 'state':{'size':[10,10]}}}]}}
            self.assertEqual(draw_shot(shot,1,root,(32,32)).getpixel((6,7)),(0,255,0))
    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                draw_shot({'start':0,'end':1,'image_scene':'../secrets.json'},0,tmp,(16,16))
if __name__=='__main__':unittest.main()
