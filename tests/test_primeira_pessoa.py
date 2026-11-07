import hashlib
import json
from pathlib import Path

from PIL import Image
import pytest

from lofi import historias_ilustradas as H, imagens

BASE = Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def test_fundos_pov_tem_arte_opaca_e_compilam_sem_corpo_do_observador():
    cat = H.carregar()
    ids = H.inventario()['primeira_pessoa']
    assert len(ids) >= 8  # Vistas adicionais, como porta fechada, também são fundos POV.
    for identidade in ids:
        c = cat['cenarios'][identidade]
        arquivo = H.arquivo(H.CATALOGO, c['img'])
        assert hashlib.sha256(arquivo.read_bytes()).hexdigest() == c['sha256']
        with Image.open(arquivo) as im:
            assert list(im.size) == c['pixels'] and im.width >= 900 and im.height >= 1400
            assert 'A' not in im.getbands() or im.getchannel('A').getextrema() == (255,255)
    h = H.gerar_historia()
    for cena in h['cenas']:
        cena.update(cenario='pov_hospital', personagens=[])
    spec = H.compilar(h)
    cfg = spec['shots'][0]['imagens']
    assert cfg['perspectiva'] == 'primeira_pessoa' and cfg['personagens'] == []
    assert cfg['fundo'].startswith('cenarios/primeira_pessoa/fundo_')


def test_renderer_preserva_opacidade_do_fundo_em_subpasta(tmp_path, monkeypatch):
    pasta = tmp_path/'imagens/cenarios/primeira_pessoa'
    pasta.mkdir(parents=True)
    Image.new('RGB',(90,160),(12,24,36)).save(pasta/'fundo_teste.png')
    def proibido(*args):
        raise AssertionError('Fundo não pode passar pela remoção de fundo de personagens')
    monkeypatch.setattr(imagens, 'tirar_fundo', proibido)
    shot = {'start':0,'end':1,'imagens':{'fundo':'cenarios/primeira_pessoa/fundo_teste',
            'personagens':[], 'aproximar':0,'balanco':0}}
    im = imagens.quadro(shot,0,tmp_path,(90,160))
    assert im.getpixel((45,80))[:3] == (12,24,36)


def test_compilador_seleciona_ciclo_e_parado_na_vista_pedida(monkeypatch):
    cat = H.carregar()
    h = H.gerar_historia()
    perfil = cat['personagens']['lucas']['composicao']
    perfil['ciclos_direcionais'] = {
        'frente':{'andar':perfil['ciclos_quadros']['andar'], 'parado':perfil['ciclos_quadros']['parado']},
        'baixo':{'andar':perfil['ciclos_quadros']['correr'], 'parado':perfil['ciclos_quadros']['agachar']},
    }
    monkeypatch.setattr(H, 'carregar', lambda *args: cat)
    monkeypatch.setattr(H, 'validar_catalogo', lambda *args: [])
    ator = h['cenas'][0]['personagens'][0]
    ator.update(angulo='baixo', pos=.8, animacao='quadros',
                animacoes_quadros=[{'acao':'andar','inicio':0,'fim':1}])
    spec = H.compilar(h)
    render_ator = spec['shots'][0]['imagens']['personagens'][0]
    assert render_ator['orientacao'] == 'manual' and render_ator['espelhar'] is False
    assert spec['shots'][0]['imagens']['personagens'][0]['animacoes_quadros'][0]['ciclo'] == perfil['ciclos_quadros']['correr']
    ator.pop('animacoes_quadros')
    spec = H.compilar(h)
    assert spec['shots'][0]['imagens']['personagens'][0]['animacoes_quadros'][0]['ciclo'] == perfil['ciclos_quadros']['agachar']
    ator['angulo'] = 'inexistente'
    with pytest.raises(ValueError, match='Ângulo ausente'):
        H.compilar(h)
