import json
from pathlib import Path

import pytest

from lofi.skill_bridge import contexto, converter_evals, listar


def serie(tmp_path):
    (tmp_path / 'biblia.md').write_text('Perfil de duração: curto\nFormato: 100% narrado', encoding='utf-8')
    (tmp_path / 'personagens.json').write_text('{"lia":{"top":[0,100,180]}}', encoding='utf-8')
    return tmp_path


def test_contexto_sem_metricas_nao_inventa_e_nao_modifica_serie(tmp_path):
    pasta = serie(tmp_path)
    antes = {p.name: p.read_bytes() for p in pasta.iterdir()}
    c = contexto(pasta, 1)
    assert c['duration_plan']['alvo_s'] == 90
    assert c['evidence']['evidencia'] == 'insuficiente'
    assert c['experiments']['experimentos'] == []
    assert c['locked_characters']['lia']['top'] == [0, 100, 180]
    assert antes == {p.name: p.read_bytes() for p in pasta.iterdir()}


def test_contexto_visual_preserva_referencia_e_formatos(tmp_path):
    pasta = serie(tmp_path)
    (pasta / 'ep01.json').write_text(json.dumps({'cast': {'lia': {'referencia': 'hero.png'}}}), encoding='utf-8')
    c = contexto(pasta, 1, skill='canvas-design')
    assert c['references']['lia'] == 'hero.png'
    assert c['formats']['youtube'] == [1280, 720]
    assert Path(c['fonts']).is_dir()


def test_perfil_explicito_e_duracao_existente(tmp_path):
    pasta = serie(tmp_path)
    (pasta / 'ep01.json').write_text('{"duration_profile":"medio","total":150}', encoding='utf-8')
    assert contexto(pasta, 1)['duration_plan']['alvo_s'] == 150
    assert contexto(pasta, 1, perfil='curto', duracao=100)['duration_plan']['nome'] == 'curto'
    with pytest.raises(ValueError): contexto(pasta, 1, duracao=30)


def test_exporta_evals_oficiais_sem_perder_expectativas(tmp_path):
    p = tmp_path / 'evals.json'
    p.write_text(json.dumps({'casos': [{'id': 'caso', 'prompt': 'Faça um roteiro', 'espera': ['Não alterar cânone']}]}), encoding='utf-8')
    c = converter_evals(p, 'motor-lofi-studio')
    assert c['skill_name'] == 'motor-lofi-studio'
    assert c['evals'][0]['id'] == 1
    assert c['evals'][0]['expectations'] == ['Não alterar cânone']
    assert 'results' not in c


def test_tres_pacotes_com_licenca_e_origem():
    for pacote in listar():
        assert pacote['installed_in_project']
        pasta = Path(pacote['entrypoint']).parent
        assert (pasta / 'LICENSE.txt').is_file()
        assert len(json.loads((pasta / 'UPSTREAM.json').read_text())['commit']) == 40
        assert (pasta / 'references' / 'motor-lofi.md').is_file()


def test_contexto_rejeita_episodio_invalido(tmp_path):
    for n in (0, -1, True):
        with pytest.raises(ValueError): contexto(tmp_path, n)
