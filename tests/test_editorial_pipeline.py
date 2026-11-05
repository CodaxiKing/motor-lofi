import copy
import json

import pytest

from lofi.autodirect import compile_story, write_episode
from lofi.aberturas import aplicar
from lofi.editorial import estruturar
from lofi.experimentos import carregar, publicar, registrar_variantes
from lofi.studio import initialize_series, plan_episode, quality_report


HISTORIA = '''Lia quer encontrar a saída.
Ela pega a chave.
Mas a porta está trancada.
Ela abre a porta.
Lia corre pela rua com medo.
Ela descobre uma passagem.
Então consegue escapar.
A sombra aparece na rua.
Ela aponta para a ponte.
A) Voltar, mas perde a chave.
B) Seguir, mas corre risco de se perder.'''


def test_estrutura_e_evidencias():
    plano = estruturar(HISTORIA)
    assert plano['pendencias'] == []
    assert plano['batidas']['objetivo'][0]['texto'] in HISTORIA
    assert 'objetivo' in estruturar('Uma casa vazia.')['pendencias']


def test_atuacao_e_timeline_real():
    ep = compile_story(HISTORIA, duration_profile='curto', duration=90)
    assert len(ep['shots']) == 10
    assert ep['shots'][-1]['type'] == 'choice'
    assert ep['shots'][1]['actors'][0]['prop'] == 'key'
    assert ep['shots'][3]['actors'][0]['pose'] == 'open_door'
    corredor = ep['shots'][4]['actors'][0]
    assert corredor['run'] and corredor['mark']
    assert corredor['x'][0][1] != corredor['x'][-1][1]
    assert ep['shots'][0]['director_notes']['narrative_roles'] == ['objetivo']
    assert ep['total'] == ep['shots'][-1]['end'] == 90
    assert ep['audio_plan']['synced'] is False


@pytest.mark.parametrize('duracao', [89, 121, float('nan'), float('inf'), True])
def test_perfil_rejeita_duracao(duracao):
    with pytest.raises(ValueError):
        compile_story(HISTORIA, duration_profile='curto', duration=duracao)


def test_aberturas_renderizaveis_preservam_corpo():
    ep = compile_story(HISTORIA, duration_profile='curto')
    original = copy.deepcopy(ep)
    for letra in 'ABC':
        variante = aplicar(ep, letra)
        assert variante['total'] == ep['total']
        assert variante['shots'][0]['hook']['text']
        assert variante['shots'][0]['end'] == 3
        assert variante['shots'][1]['start'] == 3
        assert variante['shots'][2:] == ep['shots'][1:]
        assert variante['sfx'][0]['name'] in ('heartbeat', 'impact', 'whoosh')
        assert all(a['end'] == b['start'] for a, b in zip(variante['shots'], variante['shots'][1:]))
    assert ep == original
    assert ep['opening_variants'][0]['primeiro_quadro'] != ep['opening_variants'][1]['primeiro_quadro']


def test_publicacao_guarda_pacote_imutavel(tmp_path):
    ep = compile_story(HISTORIA, duration_profile='curto')
    registrar_variantes(str(tmp_path), 1, ep['opening_variants'], 'B')
    publicar(str(tmp_path), 1, 'B', 'youtube', '2026-11-05', pub_id='pub')
    antes = carregar(str(tmp_path))['experimentos'][0]['publicacoes'][0]['variante_publicada']
    ep['opening_variants'][1]['som'] = 'bang'
    registrar_variantes(str(tmp_path), 1, ep['opening_variants'], 'B')
    dados = carregar(str(tmp_path))['experimentos'][0]
    assert dados['historico']
    assert dados['publicacoes'][0]['variante_publicada'] == antes


def test_nao_troca_abertura_com_audio_sincronizado():
    ep = compile_story(HISTORIA, duration_profile='curto')
    ep['clips'] = [{'t': 0, 'voice': 'lia'}]
    with pytest.raises(ValueError, match='sincronização'):
        aplicar(ep, 'B')


def test_integracao_studio_e_revisao(tmp_path):
    initialize_series(tmp_path, 'Teste', duration_profile='curto')
    saida = plan_episode(HISTORIA, series_dir=tmp_path, opening='C')
    ep = json.loads(open(saida['episode'], encoding='utf-8').read())
    assert ep['duration_profile'] == 'curto'
    assert ep['opening_selected'] == 'C'
    assert json.loads(open(saida['openings'], encoding='utf-8').read())['selecionada'] == 'C'
    assert carregar(str(tmp_path))['experimentos'][0]['selecionada'] == 'C'
    assert 'insufficient_story' in [f['code'] for f in saida['report']['findings']]
    ep['total'] = 89
    assert not quality_report(ep)['ok']


def test_arquivo_usa_biblia_e_argumento(tmp_path):
    (tmp_path / 'biblia.md').write_text('Perfil de duração: curto', encoding='utf-8')
    texto = tmp_path / 'historia.txt'
    texto.write_text(HISTORIA, encoding='utf-8')
    ep = write_episode(texto, tmp_path / 'ep.json')
    assert ep['duration_profile'] == 'curto'
    ep = write_episode(texto, tmp_path / 'ep.json', duration_profile='medio')
    assert ep['total'] == 120


def test_exportacao_preserva_original_e_recusa_sobrescrita(tmp_path):
    from lofi.aberturas import exportar
    origem = tmp_path / 'ep.json'
    ep = compile_story(HISTORIA, duration_profile='curto', opening='A')
    origem.write_text(json.dumps(ep), encoding='utf-8')
    antes = origem.read_bytes()
    destino = tmp_path / 'ep_b.json'
    exportar(origem, destino, 'B')
    assert origem.read_bytes() == antes
    assert json.loads(destino.read_text())['opening_selected'] == 'B'
    with pytest.raises(FileExistsError):
        exportar(origem, destino, 'C')


def test_renderiza_abertura_acao_e_escolha(tmp_path):
    from lofi.render import Episode
    ep = compile_story(HISTORIA, duration_profile='curto', opening='C')
    origem = tmp_path / 'ep.json'
    origem.write_text(json.dumps(ep), encoding='utf-8')
    render = Episode(str(origem))
    for segundo in (1, 45, 89):
        quadro = render.frame(segundo)
        assert quadro.width > 0 and quadro.height > 0
