import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from lofi.providers import synthesize, comfyui_image, ProviderError
from lofi.production import prepare, status

class Skill31Tests(unittest.TestCase):
    def test_piper_missing_model(self):
        with tempfile.TemporaryDirectory() as d:
            with patch('lofi.providers.shutil.which',return_value='/usr/bin/piper'):
                with self.assertRaises(ProviderError): synthesize('Olá',Path(d)/'out.wav',model=Path(d)/'missing.onnx')
    def test_piper_does_not_call_paid_api(self):
        with tempfile.TemporaryDirectory() as d:
            with patch('lofi.providers.shutil.which',return_value=None):
                with self.assertRaises(ProviderError): synthesize('Olá',Path(d)/'out.wav')
    def test_elevenlabs_requires_credentials(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.dict('os.environ',{},clear=True):
                with self.assertRaises(ProviderError): synthesize('Olá',Path(d)/'out.mp3',provider='elevenlabs')
    def test_comfy_rejects_remote(self):
        with self.assertRaises(ValueError): comfyui_image('cidade','a.png',workflow_path='nao_existe.json',base_url='https://example.com')
    def test_prepare_and_status(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'story.txt').write_text('O silêncio tomou a cidade.\nA porta se abriu.',encoding='utf-8')
            result=prepare(p/'story.txt',p/'ep.json')
            self.assertEqual(result['shots'],2)
            self.assertTrue((p/'ep.assets.json').exists())
            self.assertTrue(status(p/'story.txt',p/'ep.json')['render_ready'])
            self.assertFalse(status(p/'story.txt',p/'ep.json')['audio_synced'])
if __name__=='__main__': unittest.main()
