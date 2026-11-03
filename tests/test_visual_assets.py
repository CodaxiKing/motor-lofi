import tempfile
import unittest
from pathlib import Path
from PIL import Image
from lofi.visual_assets import VisualAssetLibrary
from lofi.visual_compositor import compose_shot

class LibraryTests(unittest.TestCase):
    def test_import_search_plan_and_dedup(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'rafa.png'
            Image.new('RGBA', (16, 16), (255, 0, 0, 255)).save(p)
            lib = VisualAssetLibrary(Path(d) / 'library')
            item, created = lib.import_asset(p, kind='character', name='Rafael',
                                              style='cartoon', subject='rafael', view='front', pose='sitting')
            self.assertTrue(created)
            self.assertFalse(lib.import_asset(p, kind='character', name='Rafael')[1])
            self.assertEqual(len(lib.search(subject='rafael')), 1)
            requests = [{'kind':'character','subject':'rafael','view':'front','pose':'sitting'},
                        {'kind':'character','subject':'rafael','view':'back','pose':'running'}]
            results = lib.plan(requests)
            self.assertEqual([x['status'] for x in results], ['reusable', 'missing'])
            self.assertIn('Crie um asset', results[1]['prompt'])
            lib.close()

    def test_composition(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'layer.png'
            Image.new('RGBA', (5, 5), (255, 0, 0, 255)).save(p)
            result = compose_shot((20, 20), [{'path': str(p), 'x': 3, 'y': 4}], Path(d) / 'out.png')
            with Image.open(result) as im:
                self.assertEqual(im.getpixel((3, 4)), (255, 0, 0, 255))

if __name__ == '__main__':
    unittest.main()
