import unittest
from lofi.autodirect import compile_story
from lofi.performance import plan_performance
from lofi.asset_plan import build_asset_manifest

class Pipeline3Tests(unittest.TestCase):
    def test_acting(self):
        self.assertEqual(plan_performance('Ele correu com medo')['movement'], 'run')
        self.assertEqual(plan_performance('Ele correu com medo')['emotion'], 'fear')
        self.assertEqual(plan_performance('Ela bateu na porta')['pose'], 'knock')
    def test_episode(self):
        ep = compile_story('Ela bateu na porta.\nEle correu com medo.', visual_profile='horror_illustrated')
        self.assertEqual(len(ep['shots']), 2)
        self.assertEqual(ep['shots'][0]['actors'][0]['pose'], 'knock')
        self.assertTrue(ep['shots'][1]['actors'][0]['run'])
        self.assertEqual(len(build_asset_manifest(ep)['scenes']), 1)
    def test_input(self):
        with self.assertRaises(TypeError): plan_performance(None)
        with self.assertRaises(TypeError): build_asset_manifest([])

if __name__ == '__main__': unittest.main()
