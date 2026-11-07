import copy
import json
import pytest
from PIL import Image, ImageDraw
from lofi.composicao import planejar, aplicar_episodio, auditar, validar_mapa
from lofi import imagens


@pytest.fixture
def biblioteca(tmp_path):
    root=tmp_path/'imagens';root.mkdir()
    Image.new('RGB',(180,320),(20,30,40)).save(root/'fundo_sala.png')
    for nome,size,bbox in [('a',(100,200),(30,5,70,195)),
                           ('a_passo',(100,200),(4,5,96,195)),
                           ('b',(160,280),(50,80,110,250))]:
        im=Image.new('RGBA',size);ImageDraw.Draw(im).rectangle(bbox,fill='orange');im.save(root/(nome+'.png'))
    return tmp_path


def config():
    return {'fundo':'fundo_sala','mapa_composicao':{'zonas':{
        'frente':{'x':[.04,.96],'chao':.94,'altura':.70},
        'fundo':{'x':[.4,.7],'chao':.65,'altura':.30,'altura_minima':.2}}},
        'personagens':[{'id':'a','img':'a','ancora':[.5,.98],'pos':-.2,'altura':.95,'chao':1},
                       {'id':'b','img':'b','ancora':[.5,.90],'pos':1.3,'altura':.2,'chao':.5}]}


@pytest.mark.parametrize('size',[(432,768),(108,192),(768,432)])
def test_escala_visivel_padronizada_sem_cortes(biblioteca,size):
    cfg=config();original=copy.deepcopy(cfg)
    out,report=planejar(cfg,biblioteca,size)
    assert cfg==original
    a,b=out['personagens']
    # A área transparente de cada canvas não muda a altura física no cenário.
    assert a['altura']*191/200 == pytest.approx(b['altura']*171/280)
    assert a['chao']==b['chao']
    assert not any(x['code'] in ('corte_personagem','sobreposicao') for x in report['achados'])
    assert out['aproximar']==0


def test_percurso_reserva_todas_poses_e_profundidade(biblioteca):
    cfg=config();cfg['personagens'][0].update(poses=[[0,'a'],[.2,'a_passo']],andar=[-1,2])
    cfg['personagens'].append(dict(id='vilao',img='a',zona='fundo',pos=.1,altura=.9,chao=.9))
    out,report=planejar(cfg,biblioteca,(432,768))
    assert out['personagens'][0]['id']=='vilao'
    assert out['personagens'][0]['altura']<out['personagens'][1]['altura']
    assert not any(f['code']=='corte_personagem' for f in report['achados'])
    assert out['personagens'][1]['andar'][0]>=0


def test_troca_de_pose_nao_reorganiza_grupo(biblioteca):
    cfg=config();cfg2=copy.deepcopy(cfg);cfg2['personagens'][0]['img']='a_passo'
    spec={'shots':[{'imagens':cfg},{'imagens':cfg2}]}
    ep=aplicar_episodio(spec,biblioteca)
    a,b=[s['imagens']['personagens'] for s in ep['shots']]
    assert [(p['pos'],p['altura']) for p in a]==[(p['pos'],p['altura']) for p in b]
    assert 'composicao_relatorio' not in spec


def test_manual_preserva_bloqueio_e_reporta_falhas(biblioteca):
    cfg=config();cfg['composicao']='manual'
    out,report=planejar(cfg,biblioteca,(432,768))
    assert cfg==out and any(f['code']=='corte_personagem' for f in report['achados'])
    out['personagens'][0]['pos']=.5;out['personagens'][1].update(pos=.5,chao=1)
    assert any(f['code']=='sobreposicao' for f in auditar(out,biblioteca,(432,768)))


def test_renderer_aplica_mapa_sem_mutar_spec(biblioteca):
    shot={'start':0,'end':2,'imagens':config()};original=copy.deepcopy(shot)
    im=imagens.quadro(shot,1,str(biblioteca),(108,192))
    assert im.size==(108,192) and shot==original


def test_fundo_em_subpasta_usa_mesma_projecao_e_render(biblioteca):
    pasta=biblioteca/'imagens/cenarios/portas';pasta.mkdir(parents=True)
    (pasta/'fundo_sala.png').write_bytes((biblioteca/'imagens/fundo_sala.png').read_bytes())
    original=config();aninhado=copy.deepcopy(original)
    aninhado['fundo']='cenarios/portas/fundo_sala'
    a,_=planejar(original,biblioteca,(108,192))
    b,_=planejar(aninhado,biblioteca,(108,192))
    assert a['personagens']==b['personagens']
    a=imagens.quadro({'start':0,'end':2,'imagens':original},1,biblioteca,(108,192))
    b=imagens.quadro({'start':0,'end':2,'imagens':aninhado},1,biblioteca,(108,192))
    assert a.tobytes()==b.tobytes()


def test_rejeita_zona_desconhecida_e_mapa_invalido(biblioteca):
    cfg=config();cfg['personagens'][0]['zona']='teto'
    with pytest.raises(ValueError,match='Zona inexistente'):planejar(cfg,biblioteca,(432,768))
    with pytest.raises(ValueError):validar_mapa({'zonas':{'x':{'x':[.5,.2],'altura':.5,'chao':.9}}})


def test_mapear_existente_exige_fundo_conhecido(biblioteca):
    from lofi.composicao import mapear
    cfg=config();mapa=cfg.pop('mapa_composicao')
    catalogo={'personagens':{},'cenarios':{'sala':{'img':'fundo_sala','mapa_composicao':mapa}}}
    ep=mapear({'shots':[{'imagens':cfg}]},catalogo,biblioteca)
    assert ep['shots'][0]['imagens']['mapa_composicao']==mapa
    assert ep['composicao_relatorio']['planos']
    cfg['fundo']='fundo_sem_mapa'
    with pytest.raises(ValueError,match='Calibre um mapa'):
        mapear({'shots':[{'imagens':cfg}]},catalogo,biblioteca)
