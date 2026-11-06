import copy
import hashlib
import json

import pytest
from PIL import Image, ImageChops

from lofi import historias_ilustradas as H, interface, perfis_referencia as P

BASE = H.CATALOGOS['cronicas'].parent


def historia():
    situacao = 'Mara está presa no quarto enquanto alguém testa a janela.'
    premissa = 'Ela precisa descobrir de onde vem o ruído antes de abrir a porta.'
    cenas = []
    for i in range(9):
        c = {'n': i+1, 'composicao_ref': 'janela_close' if i % 2 else 'quarto_janela',
             'narracao': situacao+' '+premissa if i == 0 else 'Mara espera o ruído voltar.',
             'acontecimento': 'O ruído se repete.', 'consequencia': 'Mara mantém a janela fechada.'}
        if i:
            c['causa'] = {'cena': i, 'texto': 'A repetição exige observar por mais tempo.'}
        cenas.append(c)
    return {'titulo': 'Teste de direção', 'perfil': 'curto', 'duracao': 90,
            'biblioteca': 'cronicas', 'perfil_direcao': 'cronicas_situacional_v1',
            'abertura': {'situacao': situacao, 'premissa': premissa},
            'producao': {'etapa': 'previa_visual'}, 'cenas': cenas,
            'escolhas': {'A': {'label': 'ESPERAR', 'texto': 'Esperar o ruído voltar',
                               'ganha': 'proteção do quarto', 'perde': 'tempo', 'motivo': 'A origem ainda é incerta'},
                         'B': {'label': 'INVESTIGAR', 'texto': 'Abrir a porta para investigar',
                               'ganha': 'informação', 'perde': 'proteção', 'motivo': 'O perigo pode estar dentro'}}}


def test_assets_separados_transparentes_e_rastreaveis():
    catalogo = H.carregar(H.CATALOGOS['cronicas'])
    assert set(catalogo['personagens']) == {'mara'}
    assert len(catalogo['cenarios']) == 13
    assert sum(bool(c.get('criacao_original')) for c in catalogo['cenarios'].values()) == 6
    assert H.validar_catalogo(H.CATALOGOS['cronicas']) == []
    pessoa = catalogo['personagens']['mara']
    assert len(pessoa['poses']) == 4
    assert not pessoa['composicao']['ciclos_quadros']
    for a in list(pessoa['poses'].values()) + list(catalogo['cenarios'].values()):
        caminho = H.arquivo(H.CATALOGOS['cronicas'], a['img'])
        assert caminho.is_relative_to(BASE)
        assert hashlib.sha256(caminho.read_bytes()).hexdigest() == a['sha256']
    for pose in pessoa['poses'].values():
        with Image.open(H.arquivo(H.CATALOGOS['cronicas'], pose['img'])) as im:
            assert im.getchannel('A').getextrema() == (0, 255)
    padrao = json.loads((BASE/'padrao_criacao.json').read_text(encoding='utf-8'))
    assert not padrao['legados']
    plano = json.loads((BASE/'imagens/personagens/mara/ficha_animacao_planejada.json').read_text(encoding='utf-8'))
    assert len(plano['ciclos_direcionais']) == 10
    assert all(v is None for a in plano['ciclos_direcionais'].values() for v in a.values())
    assert H.catalogo_historia({}) == H.CATALOGO
    assert H.catalogo_historia(historia()) == H.CATALOGOS['cronicas']
    with pytest.raises(ValueError, match='desconhecida'):
        H.catalogo_historia({'biblioteca': 'ausente'})


def test_direcao_opt_in_preserva_historia_e_cameras(tmp_path):
    h = historia(); antes = copy.deepcopy(h)
    normal = P.aplicar(h, BASE)
    assert h == antes
    assert normal['cenas'][0]['personagens'][0]['id'] == 'mara'
    assert normal['cenas'][0]['camera'] != normal['cenas'][1]['camera']
    ep = H.compilar(h, pasta_saida=tmp_path)
    assert ep['abertura_review']['ok']
    assert ep['biblioteca_estado'] == 'estudo_visual'
    assert ep['interface']['layout'] == 'sobrevivencia_compacta'
    assert 'hook' not in ep['shots'][0]
    assert ep['shots'][0]['imagens']['personagens'][0]['id'] == 'mara'
    assert not ep['voices']
    salvo = H.salvar(h, tmp_path/'compilada')
    from lofi.imagens import faltam
    assert faltam(salvo['episode']) == []
    assert P.aplicar({'cenas': []}) == {'cenas': []}


def test_previa_nao_e_producao_final(tmp_path):
    h = historia(); h['producao']['etapa'] = 'final'
    with pytest.raises(ValueError, match='estudo visual'):
        H.compilar(h, pasta_saida=tmp_path)
    h = historia(); h['cenas'][0]['narracao'] = 'Uma frase vaga de suspense.'
    assert not P.auditar_abertura(h)['ok']
    h['producao']['etapa'] = 'final'
    with pytest.raises(ValueError, match='situação'):
        P.auditar_abertura(h)
    from lofi.render import Episode
    path = tmp_path/'episodio.json'
    path.write_text(json.dumps({'biblioteca_estado': 'estudo_visual', 'producao': {'etapa': 'final'}}))
    with pytest.raises(ValueError, match='estudo visual'):
        Episode(path)


@pytest.mark.parametrize('size', [(270, 480), (720, 1280)])
def test_interface_responsiva_estado_e_insertos(size):
    cfg = copy.deepcopy(P.carregar('cronicas_situacional_v1', BASE)['interface'])
    cfg['vinheta'] = 0
    shots = [{'start': 0, 'end': 2}, {'start': 2, 'end': 4, 'status': {'CEL': [.1, '10%']}, 'hora': '23:00'}]
    spec = {'interface': cfg, 'shots': shots}
    antes = copy.deepcopy(spec)
    fundo = Image.new('RGB', size, (70, 80, 90))
    a = interface.desenhar_previa(spec, BASE, fundo, shots[0], 1)
    b = interface.desenhar_previa(spec, BASE, fundo, shots[1], 3)
    assert a.size == b.size == size
    assert a.tobytes() != b.tobytes()
    assert a.getpixel((size[0]//2, size[1]//2)) == fundo.getpixel((0, 0))
    # O HUD padrão ocupa somente a região do horário, sem recursos ou atalhos.
    bbox=ImageChops.difference(a,fundo).getbbox()
    assert bbox[2]<=round(size[0]*.24)+1 and bbox[1]>=round(size[1]*.665)
    assert bbox[3]<=round(size[1]*.698)+1
    hidden = dict(shots[0], interface=False)
    assert interface.desenhar_previa(spec, BASE, fundo, hidden, 1).tobytes() == fundo.tobytes()
    for chave, valor in [('telefone', {'contato': 'Irmã'}),
                         ('escolha_ref', {'opcoes': ['IR', 'ESPERAR']}),
                         ('dialogo', {'nome': 'Mara', 'texto': 'Está muito perto.'}),
                         ('notificacao', {'titulo': 'Nova mensagem'}),
                         ('alerta', {'titulo': 'Feche a janela'})]:
        shot = dict(hidden, **{chave: valor})
        assert ImageChops.difference(interface.desenhar_previa(spec, BASE, fundo, shot, 1), fundo).getbbox()
    assert spec == antes


def test_telefone_sem_hud_global():
    shot = {'start': 0, 'end': 2, 'telefone': {'contato': 'Rádio'}}
    spec = {'shots': [shot]}
    im = Image.new('RGB', (270, 480), 'navy')
    assert interface.desenhar_previa(spec, BASE, im, shot, 1).tobytes() != im.tobytes()


def test_direcao_padrao_livre_e_overrides(tmp_path):
    from lofi.cronicas import rascunho
    h=rascunho();antes=copy.deepcopy(h)
    assert 'perfil_direcao' not in h
    normal=P.aplicar(h,BASE)
    assert h==antes
    assert normal['perfil_direcao']=='cronicas_situacional_v1'
    assert normal['interface']['layout']=='sobrevivencia_compacta'
    assert normal['interface']['relogio']['seg_por_min']==60
    assert normal['interface']['somente_horario'] is True
    assert not any(k in normal['interface'] for k in ('status','missao','atalhos'))
    assert normal['cenas'][0]['camera']=={'plano':'aberto','zoom':1}
    assert normal['cenas'][1]['camera']['cx']==.12  # detalhe explicitamente dirigido
    assert normal['cenas'][2]['camera']['zoom']==[1,1.035]
    assert normal['cenas'][-1]['camera']['plano']=='close'
    ep=H.compilar(h,pasta_saida=tmp_path)
    assert ep['abertura_review']['ok'] and ep['total']==120
    assert ep['biblioteca']=='cronicas'
    assert ep['shots'][-1]['type']=='choice' and ep['shots'][-1]['escolha_ref']['opcoes']==['SUBIR À TORRE','IR AO MERCADO']
    assert ep['shots'][-1]['imagens']['camera_ilustrada']=={'plano':'aberto','zoom':1}
    assert ep['shots'][0]['imagens']['fundo'].endswith('abrigo_radio_v1')
    from lofi.camera_ilustrada import resolver
    cam=normal['cenas'][2]['camera']
    assert resolver(cam,[],BASE,(270,480),rel=0,duracao=3)['z']==1
    assert resolver(cam,[],BASE,(270,480),rel=3,duracao=3)['z']==pytest.approx(1.035)
    assert P.aplicar({'cenas':[]})=={'cenas':[]}  # biblioteca antiga não herda o estilo
    normal=P.aplicar({'cenas':[{'cenario':'posto_estrada','camera':{'plano':'aberto','zoom':1.2}}]},BASE)
    assert normal['cenas'][0]['camera']['zoom']==1.2
    with pytest.raises(ValueError,match='Batida visual'):
        P.aplicar({'cenas':[{'cenario':'posto_estrada','batida_visual':'inventada'}]},BASE)


def test_decisao_compilada_usa_interface_cronicas(tmp_path,monkeypatch):
    from lofi.cronicas import rascunho
    from lofi.render import Episode
    r=H.salvar(rascunho(),tmp_path/'rascunho')
    ep=Episode(r['episode']);shot=ep.shots[-1];t=shot['start']+2
    fundo=Image.new('RGB',(270,480),'navy')
    monkeypatch.setattr(ep,'scene_frame',lambda s,t:fundo.copy())
    esperado=interface.desenhar(ep,fundo,shot,t)
    assert ep.choice_frame(shot,t).tobytes()==esperado.tobytes()
    assert esperado.tobytes()!=fundo.tobytes()


def test_serie_cronicas_seleciona_biblioteca_e_aceita_override(tmp_path):
    from lofi.cronicas import rascunho
    from lofi.studio import initialize_series,plan_episode,configure_render_mode
    serie=tmp_path/'serie'
    bible=initialize_series(serie,'Crônicas novas',visual_style='cronicas')
    assert bible['serie']['biblioteca']=='cronicas'
    assert bible['serie']['render_mode']=='illustrated_library'
    h=rascunho();h.pop('biblioteca')
    r=plan_episode(json.dumps(h),series_dir=serie)
    ep=json.loads(open(r['episode'],encoding='utf-8').read())
    assert ep['perfil_direcao']=='cronicas_situacional_v1'
    assert ep['shots'][0]['imagens']['fundo'].endswith('abrigo_radio_v1')
    h=H.gerar_historia();h['biblioteca']='ilustrada'
    r=plan_episode(json.dumps(h),series_dir=serie,episode_number=2)
    ep=json.loads(open(r['episode'],encoding='utf-8').read())
    assert 'perfil_direcao' not in ep
    assert ep['shots'][0]['imagens']['fundo'].endswith('fundo_entrada_v1')
    data=configure_render_mode(serie,'illustrated_library',biblioteca='cronicas')
    assert data['biblioteca']=='cronicas'
    with pytest.raises(ValueError,match='desconhecida'):
        configure_render_mode(serie,'illustrated_library',biblioteca='ausente')
