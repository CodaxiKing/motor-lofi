import copy
import json

import pytest
from PIL import Image, ImageDraw
from lofi import historias_ilustradas as H, imagens
from lofi.autodirect import compile_story


@pytest.fixture
def catalogo(tmp_path):
    base = tmp_path / 'biblioteca'; base.mkdir(); (base/'imagens').mkdir()
    dados = {'personagens': {}, 'cenarios': {}}
    for chave in ('lucas', 'teo', 'clara', 'mimico'):
        pessoa = {'nome': chave.capitalize(), 'tipo': 'criatura' if chave == 'mimico' else 'humano', 'poses': {}}
        for pose in ('neutro', 'medo', 'macaneta', 'celular'):
            nome = chave+'_'+pose
            im = Image.new('RGBA', (40,80)); ImageDraw.Draw(im).rectangle((5,5,35,78), fill=(180,110,40,255))
            im.save(base/'imagens'/(nome+'.png'))
            pessoa['poses'][pose] = {'img': nome, 'ancora': [.5,.98]}
        dados['personagens'][chave] = pessoa
    for chave, ligacoes in (('entrada',['corredor']), ('corredor',['entrada','floresta']), ('floresta',['corredor'])):
        nome = 'fundo_'+chave
        Image.new('RGB', (100,180),(20,35,50)).save(base/'imagens'/(nome+'.png'))
        dados['cenarios'][chave] = {'img': nome, 'descricao': chave, 'ligacoes': ligacoes}
    path=base/'catalogo.json'; path.write_text(json.dumps(dados), encoding='utf-8')
    return path


def test_catalogo_com_assets_reais_e_historia_rastreavel(catalogo):
    assert H.validar_catalogo(catalogo) == []
    h=H.gerar_historia(catalogo)
    assert len(h['cenas']) == 9 and h['duracao'] == 90
    assert h['cenas'][1]['causa']['cena'] == 1
    assert H.validar_historia(h,H.carregar(catalogo))
    assert H.inventario(catalogo)['personagens']['mimico']['tipo'] == 'criatura'


def test_historia_compila_com_caminhos_de_biblioteca_e_sem_simular_audio(catalogo,tmp_path):
    h=H.gerar_historia(catalogo)
    out=H.salvar(h,tmp_path/'historia-nova',catalogo)
    ep=json.loads(open(out['episode'],encoding='utf-8').read())
    assert ep['total'] == ep['shots'][-1]['end'] == 90
    assert ep['shots'][-1]['type'] == 'choice'
    assert all(a['end'] == b['start'] for a,b in zip(ep['shots'],ep['shots'][1:]))
    assert ep['voices'] == {} and not ep['audio_plan']['synced']
    assert imagens.faltam(out['episode']) == []
    s=ep['shots'][0]
    im=imagens.quadro(s,1,str(tmp_path/'historia-nova'),(108,192))
    assert im.getbbox()
    with pytest.raises(FileExistsError): H.salvar(h,tmp_path/'historia-nova',catalogo)


@pytest.mark.parametrize('erro', ['pose','cenario','duracao','causa','salto','posicao','duplicado'])
def test_rejeita_falhas_sem_inventar_assets(catalogo,erro):
    h=H.gerar_historia(catalogo); c=H.carregar(catalogo)
    if erro=='pose': h['cenas'][0]['personagens'][0]['pose']='voando'
    if erro=='cenario': h['cenas'][0]['cenario']='lua'
    if erro=='duracao': h['duracao']=89
    if erro=='causa': h['cenas'][1]['causa']['cena']=9
    if erro=='salto': h['cenas'][2]['cenario']='floresta'
    if erro=='posicao': h['cenas'][0]['personagens'][0]['pos']=float('nan')
    if erro=='duplicado': h['cenas'][0]['personagens'].append(copy.deepcopy(h['cenas'][0]['personagens'][0]))
    with pytest.raises(ValueError): H.validar_historia(h,c)


def test_biblioteca_detecta_asset_apagado(catalogo):
    (catalogo.parent/'imagens'/'teo_medo.png').unlink()
    assert any('teo/medo' in a for a in H.validar_catalogo(catalogo))


def test_modos_anteriores_continuam_usando_rig():
    ep=compile_story('Roberta olha a porta.',duration=8)
    assert not ep.get('character_rendering')
    assert 'imagens' not in ep['shots'][0]


def test_apoio_alternativo_utiliza_pose_real(catalogo):
    h=H.gerar_historia(catalogo,apoio='clara')
    assert any(a['id']=='clara' for s in h['cenas'] for a in s['personagens'])
    assert 'Clara' in h['cenas'][0]['narracao']


def test_modo_persistido_e_override_sem_converter_serie(tmp_path):
    from lofi.studio import initialize_series, configure_render_mode, plan_episode, read_bible
    serie=tmp_path/'serie'
    initialize_series(serie,'Teste')
    configure_render_mode(serie,'illustrated_library')
    with pytest.raises(ValueError,match='historia.json'):
        plan_episode('texto simples',series_dir=serie)
    assert read_bible(serie)['serie']['render_mode']=='illustrated_library'
    ep=plan_episode('Uma porta bate. Lucas foge. Ele encontra uma pista.',series_dir=serie,render_mode='rig')
    assert json.loads(open(ep['episode'],encoding='utf-8').read()).get('character_rendering')!='illustrated_library'
    assert read_bible(serie)['serie']['render_mode']=='illustrated_library'


def test_pipeline_ilustrado_persistido(tmp_path):
    from lofi.studio import initialize_series, plan_episode
    serie=tmp_path/'serie';initialize_series(serie,'Teste',render_mode='illustrated_library')
    result=plan_episode(json.dumps(H.gerar_historia()),series_dir=serie)
    ep=json.loads(open(result['episode'],encoding='utf-8').read())
    assert ep['character_rendering']=='illustrated_library'
    assert imagens.faltam(result['episode'])==[]
    assert result['report']['ok']


def test_piscada_respeita_pose_e_movimento_desligavel(catalogo,tmp_path):
    c=H.carregar(catalogo)
    c['personagens']['teo']['microposes']={'neutro_piscando':{'img':'teo_pisca','ancora':[.5,.98]}}
    Image.new('RGBA',(40,80),(255,0,0,255)).save(catalogo.parent/'imagens/teo_pisca.png')
    # transparência real, como exigido pelo catálogo
    im=Image.open(catalogo.parent/'imagens/teo_pisca.png');im.putpixel((0,0),(0,0,0,0));im.save(catalogo.parent/'imagens/teo_pisca.png')
    catalogo.write_text(json.dumps(c),encoding='utf-8')
    ep=H.compilar(H.gerar_historia(catalogo),catalogo,tmp_path)
    pessoas=[p for s in ep['shots'] if 'imagens' in s for p in s['imagens']['personagens']]
    assert any(p.get('piscadas') for p in pessoas if p['img']=='teo_neutro')
    assert all(not p.get('piscadas') for p in pessoas if p['img']=='teo_medo')
    shot=ep['shots'][0];shot['imagens'].update(aproximar=0,balanco=0,plano='aberto')
    for p in shot['imagens']['personagens']: p.update(respirar=0,balanco_corpo=0,piscar=False,piscadas={})
    assert imagens.quadro(shot,1,tmp_path,(180,320)).tobytes()==imagens.quadro(shot,2,tmp_path,(180,320)).tobytes()
