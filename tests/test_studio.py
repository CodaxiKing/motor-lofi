import json
import tempfile
import unittest
from pathlib import Path
from lofi.studio import initialize_series, plan_episode, quality_report, commit_continuity, detect_capabilities

class StudioTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)/'serie'
        initialize_series(self.folder, 'Arquivo Zero')
    def tearDown(self): self.temp.cleanup()
    def test_initialization_non_destructive(self):
        f=self.folder/'personagens.json'; f.write_text('{"joao":{"cabelo":"preto"}}',encoding='utf-8')
        initialize_series(self.folder,'Outro Nome')
        self.assertEqual(json.loads(f.read_text())['joao']['cabelo'],'preto')
    def test_pipeline(self):
        out=plan_episode('Ouvi batidas na porta. O corredor estava vazio.',series_dir=self.folder)
        self.assertTrue(Path(out['episode']).exists())
        self.assertTrue(Path(out['assets']).exists())
        self.assertTrue(Path(out['quality']).exists())
        self.assertEqual(out['status'],'draft_needs_review')
        self.assertFalse(out['report']['rendered_video'])
    def test_does_not_overwrite(self):
        plan_episode('A porta abriu.',series_dir=self.folder)
        with self.assertRaises(FileExistsError): plan_episode('Outro texto.',series_dir=self.folder)
    def test_choice_requires_record(self):
        with self.assertRaises(ValueError): plan_episode('A porta abriu.',series_dir=self.folder,branch='B')
    def test_continuity_explicit(self):
        plan_episode('A porta abriu.',series_dir=self.folder)
        commit_continuity(self.folder,episode_number=1,facts=['João viu uma sombra'],choice='B')
        out=plan_episode('Ele correu.',series_dir=self.folder,episode_number=2,branch='ep01')
        self.assertTrue(Path(out['episode']).exists())
    def test_report_catches_bad_timeline(self):
        ep={'shots':[{'start':0,'end':1},{'start':2,'end':3}], 'total':3}
        r=quality_report(ep)
        self.assertFalse(r['ok'])
        self.assertIn('timeline_gap',[x['code'] for x in r['findings']])
    def test_capabilities_are_explicit(self):
        c=detect_capabilities()
        self.assertFalse(c['image_generation'])
        self.assertFalse(c['speech_generation'])

if __name__=='__main__': unittest.main()
