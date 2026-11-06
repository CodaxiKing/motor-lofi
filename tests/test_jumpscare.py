import json
from pathlib import Path
import numpy as np
from lofi.ciclos_quadros import carregar,indice,validar
from lofi.historias_ilustradas import inventario,validar_catalogo
from lofi.sincronia import ler_audio

BASE=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def test_close_mantem_expressao_aberta_do_salto_e_para_no_final():
    salto=carregar(BASE,'mimico/jumpscare_salto_v1.json')
    rosto=carregar(BASE,'mimico/jumpscare_rosto_v1.json')
    assert len(salto['frames'])==16 and len(rosto['frames'])==8
    assert rosto['tipo']=='retrato' and validar(rosto)
    assert indice(salto,100,'uma_vez')==15
    assert indice(rosto,0,'uma_vez')>=3
    assert 'jumpscare' in inventario()['personagens']['mimico']['sustos']
    assert validar_catalogo()==[]


def test_previa_tem_timeline_continua_e_audio_sem_clipping():
    d=json.loads((BASE/'jumpscare_skinwalker_demo_v1.json').read_text(encoding='utf-8'))
    assert d['shots'][0]['start']==0 and d['shots'][-1]['end']==d['total']
    assert all(a['end']==b['start'] for a,b in zip(d['shots'],d['shots'][1:]))
    x,sr=ler_audio(BASE/d['voices']['susto'])
    assert abs(len(x)/sr-d['total'])<.01 and np.max(np.abs(x))<=.66
    assert np.sqrt(np.mean(x[int(1.85*sr):int(2.05*sr)]**2))>np.sqrt(np.mean(x[:sr]**2))
