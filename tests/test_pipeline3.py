import unittest
from lofi.autodirect import compile_story
from lofi.performance import plan_performance
from lofi.asset_plan import build_asset_manifest

class Pipeline3Tests(unittest.TestCase):
    def test_acting(self):
        self.assertEqual(plan_performance('Ele correu com medo')['movement'], 'run')
        self.assertEqual(plan_performance('Ele correu com medo')['emotion'], 'fear')
        self.assertEqual(plan_performance('Ela bateu na porta')['pose'], 'knock')
    def test_presente_gerundio_e_plural(self):
        casos = {
            'João corre pela rua': ('run', 'run'), 'Eles correm para o carro': ('run', 'run'),
            'Ela foge do mercado': ('run', 'run'), 'Bia anda devagar': ('walk', 'walk'),
            'Ele se aproxima da janela': ('walk', 'walk'), 'Alguém bate na porta': ('knock', 'idle'),
            'Ela aponta para o corredor': ('point', 'idle'), 'Rafa se esconde atrás do balcão': ('hide', 'hide'),
            'Ele se agacha': ('hide', 'hide'), 'Ela senta no chão': ('sit', 'sit'),
            'João pega a lanterna': ('hold', 'idle'), 'Ela segura a chave': ('hold', 'idle'),
            'Ele liga para o pai': ('phone', 'idle'), 'Cida olha pela fresta': ('idle', 'idle'),
        }
        for frase, (pose, movimento) in casos.items():
            p = plan_performance(frase)
            self.assertEqual((p['pose'], p['movement']), (pose, movimento), frase)
        self.assertEqual(plan_performance('Ela se esconde')['look'], -15)
    def test_sem_falsos_positivos(self):
        for frase in ('O corredor está escuro', 'Ele mora no segundo andar', 'Você está segura aqui',
                      'A sentença foi lida', 'O correio chegou'):
            p = plan_performance(frase)
            self.assertEqual((p['pose'], p['movement']), ('idle', 'idle'), frase)
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
