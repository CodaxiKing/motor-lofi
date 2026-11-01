import json, tempfile, unittest
from pathlib import Path
from PIL import Image
from lofi.layers import composite_layers
from lofi.continuity import validate_episode
class Motor2Tests(unittest.TestCase):
    def test_layers(self):
        with tempfile.TemporaryDirectory() as d:
            Image.new('RGBA',(8,8),(255,0,0,255)).save(Path(d)/'layer.png')
            base=Image.new('RGB',(20,20),'black')
            out=composite_layers(base,[{'path':'layer.png','x':2,'y':3}],d)
            self.assertEqual(out.getpixel((3,4)),(255,0,0))
            self.assertEqual(base.getpixel((3,4)),(0,0,0))
    def test_path_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                composite_layers(Image.new('RGB',(20,20)),[{'path':'../secret.png'}],d)
    def test_continuity(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ep.json';p.write_text(json.dumps({'shots':[{'start':2,'end':1}]}))
            self.assertTrue(validate_episode(p))
if __name__=='__main__': unittest.main()
