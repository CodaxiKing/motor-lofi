import sys,unittest,tempfile,json
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lofi.facial_timeline import read_mouth_cues,expression_at
from lofi.character_motion import render_character
from lofi.storyboard_planner import plan_episode
from lofi.visual_assets import VisualAssetLibrary
from lofi.image_scene_animator import render_frame

class V4(unittest.TestCase):
 def test_rhubarb(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'cues.json';p.write_text(json.dumps({'mouthCues':[{'start':0,'end':.2,'value':'A'}]}))
   self.assertEqual(read_mouth_cues(p)[0]['shape'],'A')
 def test_expressions(self):
  self.assertEqual(expression_at({'expression':'neutral','expression_keys':[[.3,'fear']]},.4),'fear')
 def test_character(self):
  with tempfile.TemporaryDirectory() as d:
   Image.new('RGBA',(6,6),'red').save(Path(d)/'head.png')
   img=render_character([{'name':'head','path':'head.png'}],{'size':[10,10]},.1,d)
   self.assertEqual(img.getpixel((2,2))[0],255)
 def test_storyboard(self):
  with tempfile.TemporaryDirectory() as d:
   lib=VisualAssetLibrary(d)
   episode={'visual_mode':'DESENHO','shots':[{'image_requirements':[{'kind':'environment','subject':'hospital'}]}]}
   try:self.assertEqual(plan_episode(episode,lib)['missing'],1)
   finally:lib.close()
 def test_environment(self):
  with tempfile.TemporaryDirectory() as d:
   Image.new('RGBA',(10,10),'red').save(Path(d)/'door.png')
   scene={'size':[30,30],'duration':2,'layers':[{'path':'door.png','motion':{'sway_rotation':3,'float':True}}], 'effects':[{'type':'light_pulse'}]}
   self.assertEqual(render_frame(scene,.5,d).size,(30,30))
if __name__=='__main__':unittest.main()
