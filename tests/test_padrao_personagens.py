import copy
import json

import pytest
from PIL import Image, ImageDraw

from lofi import padrao_personagens as P


def test_modelos_guardam_dez_vistas_e_coreografias_distintas():
    p = P.carregar()
    h = P.modelo('nova_pessoa', 'humano')
    z = P.modelo('novo_zumbi', 'zumbi')
    s = P.modelo('novo_skinwalker', 'skinwalker')
    assert len(h['ciclos_direcionais']) == 10
    assert {'cima', 'baixo'} <= h['ciclos_direcionais'].keys()
    assert all({'andar', 'correr', 'agachar', 'levantar', 'pular', 'segurar_item'} <= a.keys() for a in h['ciclos_direcionais'].values())
    assert z['perfil_movimento']['correr'] != s['perfil_movimento']['correr']
    assert z['pasta_assets'] == 'monstros/novo_zumbi' and not z['items_direcionais']
    assert all(len(views) == 10 for views in h['items_direcionais'].values())
    assert p['acoes_monstros']['rastejar']['min_quadros'] == 16


@pytest.fixture
def pronto(tmp_path):
    # Contrato reduzido para testar os mesmos validadores com arte pequena.
    p = copy.deepcopy(P.carregar())
    p.update(angulos=['frente', 'baixo'], acoes_comuns={'parado': {'min_quadros': 2}},
             acoes_monstros={'espreitar': {'min_quadros': 2}}, transicoes=['parado>andar'],
             min_quadros_transicao=2)
    p['qualidade']['min_altura_corpo_px'] = 1
    f = P.modelo('fera', 'skinwalker', p)
    f.update(altura_m=2, estado_producao='pronto')
    f['revisao_visual'] = dict.fromkeys(p['qualidade']['revisao'], True)
    pasta = tmp_path/'imagens/monstros/fera'
    pasta.mkdir(parents=True)
    atlas = Image.new('RGBA', (40, 20))
    d = ImageDraw.Draw(atlas)
    d.rectangle((4, 4, 14, 18), fill='red')
    d.rectangle((24, 4, 36, 18), fill='blue')
    atlas.save(pasta/'atlas.png')
    for angulo in p['angulos']:
        for acao in ['parado', 'espreitar', 'parado>andar']:
            nome = f'monstros/fera/{angulo}_{acao.replace(">", "_")}.json'
            ciclo = {'version':1, 'tipo':'corpo_inteiro', 'identidade':'fera', 'angulo':angulo, 'acao':acao,
                     'atlas':'monstros/fera/atlas', 'fps_quadros':8, 'referencia':{'altura_corpo':.9},
                     'frames':[{'regiao':[0,0,.5,1], 'ancora':[.5,.95]},
                               {'regiao':[.5,0,1,1], 'ancora':[.5,.95]}]}
            (tmp_path/'imagens'/nome).write_text(json.dumps(ciclo), encoding='utf-8')
            if '>' in acao: f['transicoes_direcionais'][angulo][acao]['ciclo'] = nome
            else: f['ciclos_direcionais'][angulo][acao] = nome
    return f, tmp_path, p


def test_valida_arte_real_e_rejeita_angulo_ausente_e_corpo_emprestado(pronto):
    f, base, p = pronto
    assert P.validar_ficha(f, base, p) == []
    f['ciclos_direcionais'].pop('baixo')
    f['ciclos_direcionais']['frente']['espreitar'] = 'personagens/lucas/andar.json'
    erros = P.validar_ficha(f, base, p)
    assert any('baixo/parado' in e for e in erros)
    assert any('própria identidade' in e for e in erros)


def test_rejeita_repeticao_de_desenho_disfarcada_por_ancoras(pronto):
    f, base, p = pronto
    caminho = base/'imagens'/f['ciclos_direcionais']['frente']['espreitar']
    c = json.loads(caminho.read_text())
    c['frames'][1] = dict(c['frames'][0], ancora=[.6,.95])
    caminho.write_text(json.dumps(c))
    assert any('Exposições repetidas' in e for e in P.validar_ficha(f, base, p))


def test_novas_identidades_nao_podem_pular_contrato(tmp_path):
    (tmp_path/'padrao_criacao.json').write_text(json.dumps(P.carregar()), encoding='utf-8')
    r = P.auditar_catalogo({'personagens':{'lucas':{}, 'novo':{}}}, tmp_path)
    assert r['lucas']['estado'] == 'legado'
    assert r['novo']['estado'] == 'pendente'


def test_rascunho_nao_e_certificado_como_pronto():
    erros = P.validar_ficha(P.modelo('zumbi', 'zumbi'))
    assert 'Ficha ainda é rascunho' in erros
    assert any('cima/pular' in e for e in erros)
