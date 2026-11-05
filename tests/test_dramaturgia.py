import copy
from pathlib import Path

import pytest

from lofi.dramaturgia import avaliar_texto, ler_texto, revisar, avaliar_plano
from lofi.editorial import estruturar, unidades_visuais
from lofi.studio import quality_report
from lofi.validador_narrativo import validar_roteiro

EXEMPLO = Path(__file__).resolve().parents[1] / 'examples' / 'roteiro_dramatico.md'


def texto():
    return EXEMPLO.read_text(encoding='utf-8')


def codigos(relatorio):
    return {f['code'] for f in relatorio['findings']}


def test_seis_criterios_documentados_com_evidencias():
    resultado = avaliar_texto(texto())
    assert resultado['findings'] == []
    assert set(resultado['criteria'].values()) == {'documentado'}
    cenas, escolhas, final = ler_texto(texto())
    assert cenas[0]['falas'][0]['personagem'] == 'LIA'
    assert cenas[0]['falas'][0]['texto'].startswith('Você quer')
    assert escolhas['A']['ganha']
    assert not final


def test_sem_cenas_nao_declara_causalidade_documentada():
    r = avaliar_texto('Ela corre. Depois descobre tudo.')
    assert 'cenas_nao_documentadas' in codigos(r)
    assert r['criteria']['causalidade'] == 'revisar'


def test_causa_futura_e_custo_pessoal_ausente():
    t = texto().replace('CAUSA: CENA 1', 'CAUSA: CENA 3').replace('CONFLITO PESSOAL:', 'NOTA:')
    r = avaliar_texto(t)
    assert not r['ok']
    assert {'causa_invalida', 'conflito_pessoal_ausente'} <= codigos(r)
    achado = next(f for f in r['findings'] if f['code'] == 'causa_invalida')
    assert achado['scene'] == 2 and achado['line'] and achado['suggestion']


def test_palavra_conectiva_nao_comprova_causa():
    t = texto().replace('CAUSA: CENA 1 — O estalo da fechadura atrai passos no corredor.', 'NARRAÇÃO: Então ela entra.')
    assert 'elo_causal_ausente' in codigos(avaliar_texto(t))


def test_intencao_nao_basta_sem_alvo_e_objetivo():
    t = texto().replace('ALVO: RAFA', 'ALVO: ...').replace('Você quer voltar', 'Como você sabe, quer voltar')
    assert {'fala_sem_intencao', 'exposicao_compartilhada'} <= codigos(avaliar_texto(t))


def test_fala_convencional_e_detectada_sem_intencao():
    t = texto() + '\nJOÃO: Como você sabe, a porta estava marcada.\n'
    assert 'fala_sem_intencao' in codigos(avaliar_texto(t))


@pytest.mark.parametrize('origem,destino,codigo', [
    ('PLANTA: sinal_azul', 'PLANTA: outro', 'revelacao_sem_planta'),
    ('PAGA: sinal_azul', 'PAGA: outro', 'revelacao_sem_consequencia'),
    ('PERDE: confiar o remédio a um possível traidor', 'PERDE: ...', 'escolha_sem_troca'),
    ('ORIGEM: CENA 3', 'ORIGEM: CENA 99', 'origem_escolha_invalida'),
    ('RESOLVE: entrada', 'NOTA: entrada', 'episodio_sem_entrega'),
    ('ABRE: traicao', 'ABRE: entrada', 'episodio_sem_nova_pergunta'),
])
def test_lacunas_especificas(origem, destino, codigo):
    assert codigo in codigos(avaliar_texto(texto().replace(origem, destino)))


def test_final_entrega_sem_exigir_novo_suspense_ou_voto():
    cenas, _, _ = ler_texto(texto())
    cenas[-1]['abre'] = []
    r = revisar(cenas, final=True)
    assert not r['findings']
    assert r['criteria']['escolha_dificil'] == 'nao_se_aplica'


def test_planta_no_mesmo_plano_nao_e_preparacao():
    cenas, escolhas, _ = ler_texto(texto())
    cenas[-1]['planta'] = cenas[0].pop('planta')
    assert 'revelacao_sem_planta' in codigos(revisar(cenas, escolhas))


def test_ramos_nao_compartilham_pistas():
    plano = {'cadeia': [
        {'n': 1, 'voto': 'A', 'planta': ['segredo'], 'consequencia': 'Alguém marcou a porta'},
        {'n': 2, 'voto': 'B', 'revela': ['segredo'], 'consequencia': 'Ela muda de rota'},
    ]}
    r = avaliar_plano(plano)
    assert any(f['code'] == 'revelacao_sem_planta' and f['branch'] == 'B' for f in r['findings'])


def test_metadados_nao_viram_falas_e_relatorio_recalcula_fonte():
    visuais = unidades_visuais(texto())
    assert 'CAUSA:' not in visuais and 'CONFLITO PESSOAL:' not in visuais
    assert 'Você quer voltar' in visuais
    assert estruturar(texto())['dramaturgia']['findings'] == []
    ep = {'shots': [], 'source_story': texto().replace('RESOLVE: entrada', 'NOTA: entrada')}
    assert 'drama_episodio_sem_entrega' in {f['code'] for f in quality_report(ep)['findings']}


def test_validador_md_inclui_os_mesmos_achados(tmp_path):
    p = tmp_path / 'ep01_roteiro.md'
    p.write_text(texto().replace('CAUSA: CENA 1', 'CAUSA: CENA 99'), encoding='utf-8')
    assert 'drama_causa_invalida' in {f[1] for f in validar_roteiro(str(p))}


def test_memoria_guarda_pistas_sem_mutar_original():
    from lofi.narrativa import fechar
    memoria = {'personagens': {}, 'fatos': [], 'pendencias': [], 'fim': {}}
    antes = copy.deepcopy(memoria)
    plano = {'episodio': 1, 'cadeia': [
        {'n': 1, 'planta': [{'id': 'marca', 'texto': 'Tinta azul no metal'}]},
        {'n': 2, 'revela': [{'id': 'marca', 'texto': 'Rafa marcou a porta'}],
         'paga': [{'id': 'marca', 'texto': 'Lia muda de rota'}]},
    ]}
    nova = fechar(plano, memoria)
    assert memoria == antes
    assert nova['pistas'][0]['plantada_no_ep'] == nova['pistas'][0]['paga_no_ep'] == 1
    proximo = {'cadeia': [{'n': 1, 'revela': ['marca'], 'consequencia': 'Ela recusa a ajuda'}]}
    assert 'revelacao_sem_planta' not in codigos(avaliar_plano(proximo, nova))


def test_esqueleto_preserva_metadados_e_remapeia_referencias():
    from lofi.narrativa import esqueleto
    plano = {'episodio': 2, 'cadeia': [
        {'n': 4, 'acontecimento': 'O metal quebra', 'consequencia': 'Alguém ouve',
         'planta': [{'id': 'marca', 'texto': 'Tinta azul'}]},
        {'n': 7, 'causa': {'cena': 4, 'texto': 'O estalo atrai passos'},
         'acontecimento': 'Ela abandona a mochila', 'consequencia': 'Perde a água'},
    ], 'pergunta': {'A': {'texto': 'Voltar', 'ganha': 'tempo', 'perde': 'segurança',
                         'motivo': 'precisa de água', 'origem': 'CENA 7'}}}
    md = esqueleto(plano)
    assert 'CAUSA: CENA 1' in md and 'ORIGEM: CENA 2' in md
    assert 'PLANTA: marca | Tinta azul' in md


def test_relatorio_legivel_aponta_cena():
    from lofi.dramaturgia import formatar_relatorio
    r = avaliar_texto(texto().replace('CAUSA: CENA 1', 'CAUSA: CENA 99'))
    md = formatar_relatorio(r)
    assert 'Cena 2' in md and 'causa_invalida' in md
