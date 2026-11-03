import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from lofi.image_scene_animator import sample, render_frame, render_frames
from lofi.character_motion import facial_state, render_character
from lofi.auto_rig import generate_rig, draw_preview

class AnimationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        Image.new('RGBA',(32,32),(255,0,0,255)).save(self.root/'background.png')
        Image.new('RGBA',(8,8),(0,255,0,255)).save(self.root/'actor.png')
    def tearDown(self):self.tmp.cleanup()
    def test_keyframes(self):
        self.assertEqual(sample([0,10],.5),5)
        self.assertEqual(sample([[0,0],[.5,20],[1,10]],.75),15)
    def test_scene_render_and_effects(self):
        scene={'size':[32,32],'duration':1,'layers':[{'path':'background.png','x':0,'y':0,'z':0},
          {'path':'actor.png','x':[0,16],'y':8,'z':1}], 'effects':[{'type':'flicker','strength':.1},{'type':'fog','alpha':5}]}
        first=render_frame(scene,0,self.root)
        later=render_frame(scene,.9,self.root)
        self.assertEqual(first.size,(32,32))
        self.assertNotEqual(first.tobytes(),later.tobytes())
        self.assertEqual(render_frames(scene,self.root/'frames',self.root,4),4)
    def test_facial(self):
        self.assertEqual(facial_state(0)['eyes'],'closed')
        self.assertEqual(facial_state(.5)['eyes'],'open')
        self.assertEqual(facial_state(.5,mouth_cues=[{'start':0,'end':1,'shape':'A'}])['mouth'],'A')
        im=render_character([{'name':'body','path':'actor.png','x':1,'y':2}],{'size':[32,32]},.5,self.root)
        self.assertEqual(im.getpixel((2,3)),(0,255,0,255))
    def test_rig(self):
        rig=generate_rig(self.root/'actor.png',overrides={'head':[4,2]})
        self.assertEqual(rig['landmarks']['head'],[4,2])
        self.assertTrue(rig['requires_manual_review'])
        draw_preview(self.root/'actor.png',rig,self.root/'preview.png')
        self.assertTrue((self.root/'preview.png').exists())
    def test_rig_rejects_nontransparent(self):
        Image.new('RGB',(32,32),'red').save(self.root/'opaque.png')
        with self.assertRaises(ValueError): generate_rig(self.root/'opaque.png')

if __name__=='__main__':unittest.main()
