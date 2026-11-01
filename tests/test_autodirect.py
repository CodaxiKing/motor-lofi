import unittest
from lofi.autodirect import compile_story

class AutoDirectorTest(unittest.TestCase):
    def test_compile(self):
        spec = compile_story('Ouvi barulho na porta.\nA cidade estava em silêncio.', duration=8)
        self.assertEqual(len(spec['shots']), 2)
        self.assertAlmostEqual(spec['total'], 8, places=2)
        self.assertEqual(spec['shots'][0]['start'], 0)
        self.assertEqual(spec['shots'][1]['start'], spec['shots'][0]['end'])
        self.assertEqual(spec['shots'][1]['scene'], 'rua')

    def test_invalid(self):
        with self.assertRaises(ValueError): compile_story('')
        with self.assertRaises(ValueError): compile_story('teste', visual_profile='unknown')
        with self.assertRaises(ValueError): compile_story('teste', actor='../../bad')

if __name__ == '__main__': unittest.main()
