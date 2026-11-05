import copy
import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from lofi import imagens, recortes


def biblioteca(tmp_path):
    folder = tmp_path / 'imagens'; folder.mkdir()
    dados = {'personagem': 'lucas', 'poses': {}, 'fundos': {'entrada': 'fundo_entrada'}}
    for pose, cor in (('neutro', 'red'), ('celular', 'green'), ('medo', 'yellow'), ('falando', 'blue'), ('macaneta', 'purple')):
        im = Image.new('RGBA', (100, 200))
        ImageDraw.Draw(im).rectangle((20, 20, 80, 190), fill=cor)
        im.save(folder / f'lucas_{pose}.png')
        dados['poses'][pose] = {'img': 'lucas_' + pose, 'ancora': [.5, .95]}
    Image.new('RGB', (108, 192), (20, 20, 20)).save(folder / 'fundo_entrada.png')
    path = tmp_path / 'recortes.json'; path.write_text(json.dumps(dados), encoding='utf-8')
    return dados, path


def test_valida_alfa_e_detecta_arquivo_faltante(tmp_path):
    dados, path = biblioteca(tmp_path)
    assert recortes.validar(path) == []
    (tmp_path / 'imagens' / 'lucas_medo.png').unlink()
    assert 'ausente' in recortes.validar(path)[0]
    Image.new('RGB', (20, 20)).save(tmp_path / 'imagens' / 'lucas_medo.png')
    assert 'transparência' in recortes.validar(path)[0]


def test_troca_poses_no_mesmo_plano_e_preserva_audio_por_pose(tmp_path):
    dados, _ = biblioteca(tmp_path)
    ep = recortes.demo(dados)
    shot = ep['shots'][0]
    shot['imagens']['personagens'][0]['altura'] = .7
    neutro = imagens.quadro(shot, 1, tmp_path, (108, 192))
    celular = imagens.quadro(shot, 3, tmp_path, (108, 192), lambda v, t: 1)
    fala = imagens.quadro(shot, 1, tmp_path, (108, 192), lambda v, t: 1)
    assert neutro.tobytes() != celular.tobytes() != fala.tobytes()
    assert any(g > 90 and r < 30 and b < 30 for y in range(celular.height)
               for x in range(celular.width) for r, g, b in [celular.getpixel((x, y))])
    p = tmp_path / 'ep.json'; p.write_text(json.dumps(ep))
    assert imagens.faltam(str(p)) == []
    (tmp_path / 'imagens' / 'lucas_macaneta.png').unlink()
    assert imagens.faltam(str(p)) == [(0, 'lucas_macaneta')]


def test_aplicar_recortes_nao_muda_original(tmp_path):
    dados, _ = biblioteca(tmp_path)
    ep = {'shots': [{'scene': 'entrada', 'actors': [{'char': 'lucas', 'pose': 'open_door', 'x': 540}]}]}
    original = copy.deepcopy(ep)
    out = recortes.aplicar(ep, dados)
    assert ep == original
    assert out['shots'][0]['imagens']['personagens'][0]['img'] == 'lucas_macaneta'


@pytest.mark.parametrize('ator', [
    {'char': 'clara'}, {'char': 'lucas', 'walk': True}, {'char': 'lucas', 'pose': 'run'},
])
def test_nao_substitui_acao_ou_personagem_ausente_por_pose_generica(tmp_path, ator):
    dados, _ = biblioteca(tmp_path)
    with pytest.raises(ValueError): recortes.aplicar({'shots': [{'scene': 'entrada', 'actors': [ator]}]}, dados)


def test_ancoras_preservam_pes_ao_mudar_recorte(tmp_path):
    dados, _ = biblioteca(tmp_path)
    p = recortes.personagem(dados, altura=.6)
    s = {'start': 0, 'end': 10, 'imagens': {'personagens': [p], 'aproximar': 0, 'balanco': 0}}
    a = imagens.quadro(s, 1, tmp_path, (108, 192))
    p['img'] = dados['poses']['medo']['img']
    b = imagens.quadro(s, 1, tmp_path, (108, 192))
    def base(im):
        return max(y for y in range(im.height) for x in range(im.width) if max(im.getpixel((x,y))) > 80)
    assert base(a) == base(b)


def test_narrador_nao_movimenta_boca_do_personagem(tmp_path):
    dados, _ = biblioteca(tmp_path)
    ep = {'narrado': True, 'shots': [{'scene': 'entrada', 'actors': [{'char': 'lucas', 'pose': 'idle', 'voice': 'lucas'}]}]}
    assert recortes.aplicar(ep, dados)['shots'][0]['imagens']['personagens'][0]['fala'] is None
