import unittest
from lofi.director import suggest_shots

class DirectorV2Tests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(suggest_shots('  \n'), [])
    def test_existing_contract(self):
        result = suggest_shots('Abri a porta.\nA cidade estava vazia.')
        self.assertEqual(result[0]['shot'], 'detail')
        self.assertEqual(result[1]['shot'], 'wide')
        for key in ('text', 'shot', 'reason'):
            self.assertIn(key, result[0])
    def test_pacing_and_cues(self):
        result = suggest_shots('Três batidas na porta.\nUma sombra apareceu.', target_duration=20)
        self.assertAlmostEqual(sum(x['duration_estimate'] for x in result), 20, places=2)
        self.assertEqual(result[0]['sound_cue'], 'impact')
        self.assertEqual(result[1]['intensity'], 'high')
    def test_no_duplicate_close(self):
        result = suggest_shots('Ela sentiu medo.\nEle ficou assustado.')
        self.assertNotEqual(result[0]['shot'], result[1]['shot'])
    def test_invalid_duration(self):
        with self.assertRaises(ValueError):
            suggest_shots('Teste', target_duration=-1)

if __name__ == '__main__': unittest.main()
