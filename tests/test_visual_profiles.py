import unittest
from PIL import Image
from lofi.visual_profiles import PROFILES, resolve_profile, apply_profile
from lofi.director import suggest_shots
class VisualProfilesTest(unittest.TestCase):
    def test_original_unchanged(self):
        im = Image.new("RGB", (12, 12), (100, 150, 200))
        self.assertIs(apply_profile(im, resolve_profile()), im)
    def test_presets(self):
        im = Image.new("RGB", (12, 12), (100, 150, 200))
        for name in PROFILES:
            self.assertEqual(apply_profile(im, resolve_profile(name)).size, im.size)
    def test_invalid(self):
        for kw in ({"name":"unknown"}, {"overrides":{"contrast":-1}}, {"overrides":{"bogus":1}}):
            with self.assertRaises(ValueError): resolve_profile(**kw)
    def test_director(self):
        shots = suggest_shots("Ela abriu a porta.\nO silêncio tomou a cidade.")
        self.assertEqual(shots[0]["shot"], "detail")
        self.assertEqual(shots[1]["shot"], "wide")
if __name__ == "__main__": unittest.main()
