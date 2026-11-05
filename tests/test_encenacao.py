import copy
import json
from pathlib import Path

import pytest

from lofi.autodirect import compile_story, write_episode
from lofi.asset_plan import build_asset_manifest
from lofi.personagens import preparar_elenco, folha_referencia
from lofi.render import Episode, val
from lofi.studio import initialize_series, plan_episode, commit_continuity


ROTEIRO = '''## CENA 1
CENÁRIO: entrada
PERSONAGENS: lia, rafa
SUJEITO: lia
ACONTECIMENTO: Lia pega a chave.
## CENA 2
CENÁRIO: entrada
PERSONAGENS: lia, rafa
SUJEITO: lia
DESTINATÁRIO: rafa
ACONTECIMENTO: Lia entrega a chave para Rafa.
## CENA 3
CENÁRIO: entrada
PERSONAGENS: lia, rafa
SUJEITO: rafa
ACONTECIMENTO: Rafa abandona a chave.
## CENA 4
CENÁRIO: entrada
SUJEITO: lia
ACONTECIMENTO: Lia abre a porta.
## CENA 5
CENÁRIO: entrada
SUJEITO: rafa
ACONTECIMENTO: Rafa olha a porta.
FALA: RAFA | ALVO: LIA | INTENÇÃO: convencer | OBJETIVO: fazê-la entrar | TEXTO: Vamos entrar agora.
'''


def gerar(texto=ROTEIRO, **kwargs):
    return compile_story(texto, duration_profile='curto', duration=90, **kwargs)


def test_elenco_acao_e_transferencia_sem_teletransporte():
    ep = gerar()
    assert set(ep['cast']) == {'lia', 'rafa'}
    assert ep['shots'][0]['blocking']['subject'] == 'lia'
    entrega = ep['shots'][1]
    assert entrega['state_before']['objects']['key']['owner'] == 'lia'
    assert entrega['state_after']['objects']['key']['owner'] == 'rafa'
    atores = {a['char']: a for a in entrega['actors']}
    assert val(atores['lia']['prop_track'], 0, 0) == 'key'
    assert val(atores['lia']['prop_track'], 15, 1) is None
    assert val(atores['rafa']['prop_track'], 15, 1) == 'key'
    assert ep['shots'][2]['state_after']['objects']['key']['owner'] is None
    assert ep['shots'][4]['ground_objects'][0]['id'] == 'key'


def test_porta_permanece_aberta_e_atores_no_chao():
    from lofi.mapa import no_chao
    ep = gerar()
    assert ep['shots'][3]['actors'][0]['mark'] == 'porta'
    assert ep['shots'][4]['props']['door'] == 1
    for s in ep['shots']:
        for a in s['actors']:
            assert no_chao(s['scene'], val(a['x'], 0, 0), val(a['y'], 0, 0), 0)


def test_falante_e_ouvinte_tem_atuacao_e_olhares_diferentes():
    fala = gerar()['shots'][-1]
    atores = {a['char']: a for a in fala['actors']}
    assert atores['rafa']['lipsync'] and not atores['lia']['lipsync']
    assert atores['rafa']['facing'] == -atores['lia']['facing']
    assert 'pose_track' in atores['lia']
    assert fala['director_notes']['shot'] == 'two_shot'


def test_microacoes_preservam_antecipacao_contato_e_reacao():
    a = gerar()['shots'][0]['actors'][0]
    assert a['pose_track'][0][1] == 'idle'
    assert a['pose_track'][1][1] == 'reach'
    assert a['pose_track'][-1][1] == 'hold'


def test_nao_entrega_objeto_que_nao_possui():
    ep = gerar('Lia entrega a chave para Rafa.')
    assert 'key' not in ep['world_state']['objects']
    assert any(a['code'] == 'object_not_owned' for a in ep['staging_findings'])


def test_acao_negada_nao_abre_porta_nem_pega_objeto():
    ep = gerar('Lia não abre a porta.\nLia não pega a chave.')
    assert all(l['door'] == 0 for l in ep['world_state']['locations'].values())
    assert 'key' not in ep['world_state']['objects']


def test_pronome_resolvido_e_ambiguidade_reportada():
    ep = gerar('Lia olha Rafa.\nEla pega a chave.')
    assert ep['shots'][1]['blocking']['subject'] == 'lia'
    ep = gerar('Lia olha Roberta.\nEla pega a chave.')
    assert ep['shots'][1]['blocking']['subject'] is None
    assert 'key' not in ep['world_state']['objects']
    assert any(f['code'] == 'ambiguous_subject' for f in ep['staging_findings'])


def test_relacao_resolve_irma_e_novo_nome_cria_identidade():
    ep = gerar('Lia olha a irmã.\nA irmã pega a chave.', elenco={'lia': {'relacoes': {'irma': 'ana'}}, 'ana': {'genero': 'feminino'}})
    assert ep['shots'][1]['blocking']['subject'] == 'ana'
    joao = gerar('João pega a lanterna.')
    assert joao['shots'][0]['blocking']['subject'] == 'joao'
    assert joao['characters']['joao']['body']


def test_movimentos_distintos_e_identidade_travada():
    perfil = {'lia': {'movimento': 'contido', 'visual': {'top': [255, 0, 0]}}}
    antes = copy.deepcopy(perfil)
    ep = gerar('Lia caminha pela rua.', elenco=perfil, locked_characters={'lia': {'top': [0, 0, 255]}})
    assert ep['cast']['lia']['visual']['top'] == [0, 0, 255]
    assert 'lia' not in ep['characters']
    assert ep['shots'][0]['actors'][0]['sway'] == .35
    assert perfil == antes
    assert preparar_elenco({'ana': {}}) == preparar_elenco({'ana': {}})


def test_referencia_e_manifesto_apontam_mesma_identidade(tmp_path):
    fonte = tmp_path / 'historia.txt'; fonte.write_text('João pega a chave.', encoding='utf-8')
    ep = write_episode(fonte, tmp_path / 'ep.json')
    ref = Path(ep['cast']['joao']['referencia'])
    assert ref.is_file()
    from PIL import Image
    assert Image.open(ref).size == (1200, 1200)
    manifesto = build_asset_manifest(ep)
    assert manifesto['characters'][0]['reference'] == str(ref)
    assert manifesto['shot_references'][0]['characters'][0]['identity_hash'] == ep['cast']['joao']['identity_hash']


def test_referencia_externa_ausente_nao_e_substituida(tmp_path):
    fonte = tmp_path / 'historia.txt'; fonte.write_text('Lia pega a chave.', encoding='utf-8')
    ref = str(tmp_path / 'minha_referencia.png')
    ep = write_episode(fonte, tmp_path / 'ep.json', elenco={'lia': {'referencia': ref}})
    assert ep['cast']['lia']['referencia'] == ref
    assert ep['cast']['lia']['reference_status'] == 'missing'


def test_estado_cruza_episodios_so_apos_confirmacao(tmp_path):
    initialize_series(tmp_path, 'Teste')
    plan_episode(ROTEIRO, series_dir=tmp_path)
    assert 'world_state' not in json.loads((tmp_path / 'continuidade.json').read_text())
    commit_continuity(tmp_path, episode_number=1)
    out = plan_episode('Rafa olha a porta.', series_dir=tmp_path, episode_number=2, scene='entrada')
    ep = json.loads(Path(out['episode']).read_text())
    assert ep['shots'][0]['props']['door'] == 1
    assert ep['world_state']['objects']['key']['owner'] is None


def test_renderiza_microacoes_objetos_e_elenco(tmp_path):
    ep = gerar()
    p = tmp_path / 'ep.json'; p.write_text(json.dumps(ep), encoding='utf-8')
    render = Episode(str(p))
    frames = [render.frame(t).convert('RGB') for t in (1, 9, 24, 44, 64, 80)]
    assert frames[0].tobytes() != frames[1].tobytes()
    assert all(f.size == frames[0].size for f in frames)


def test_abertura_retemporiza_atuação():
    ep = gerar(opening='A')
    plano = ep['shots'][0]
    assert plano['end'] == 3
    assert plano['actors'][0]['prop_track'][-1][0] < 3
    assert ep['total'] == 90
