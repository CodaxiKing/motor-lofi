import copy
from pathlib import Path
import pytest
from PIL import Image,ImageDraw
from lofi.camera_ilustrada import configurar,caixas,resolver
from lofi.imagens import quadro


@pytest.fixture
def bib(tmp_path):
    root=tmp_path/'imagens';root.mkdir()
    Image.new('RGB',(180,320),(20,30,40)).save(root/'fundo_sala.png')
    im=Image.new('RGBA',(100,200));d=ImageDraw.Draw(im)
    d.ellipse((30,5,70,45),fill='blue');d.rectangle((35,45,65,195),fill='orange');im.save(root/'a.png')
    return tmp_path


def atores():return [{'id':'a','img':'a','referencia_escala':'a','ancora':[.5,.98],'pos':.5,'altura':.65,'chao':.92,'respirar':0,'piscar':False}]


@pytest.mark.parametrize('size',[(432,768),(768,432),(768,768)])
def test_inteiro_conserva_cabeca_e_pes_em_todos_formatos(bib,size):
    p=atores();original=copy.deepcopy(p);W,H=size
    for t in (0,2):
        r=resolver({'plano':'corpo_inteiro','push':1},p,bib,size,t,2)
        a=caixas(p,bib,size,t)[0]
        assert 0<=a['top']*r['z']+r['oy']<H
        assert 0<a['bot']*r['z']+r['oy']<=H
    assert p==original


def test_cintura_corta_pernas_e_close_mantem_rosto(bib):
    p=atores();size=(432,768);a=caixas(p,bib,size,0)[0]
    medio=resolver({'plano':'cintura_para_cima'},p,bib,size)
    assert medio['plano']=='medio' and medio['corte_inferior_intencional']
    cintura=a['top']+a['h']*.56
    assert cintura*medio['z']+medio['oy']==pytest.approx(size[1])
    assert a['bot']*medio['z']+medio['oy']>size[1]
    close=resolver({'plano':'close'},p,bib,size)
    face=a['top']+a['h']*.12
    assert 0<face*close['z']+close['oy']<size[1]*.6


def test_alvo_resolvido_por_identidade_antes_de_ordenar_profundidade(bib):
    p=atores()+[dict(atores()[0],id='b',pos=.7,chao=.7)]
    cfg=configurar({'plano':'medio','alvo':0},p)
    assert cfg['alvo']==['a']
    assert resolver(cfg,list(reversed(p)),bib,(432,768))['alvos']==['a']
    with pytest.raises(ValueError):configurar({'alvo':'nao_existe'},p)


def test_renderer_aplica_camera_nova_depois_do_mapa_sem_mutar(bib):
    cfg={'fundo':'fundo_sala','personagens':atores(),'aproximar':0,'balanco':0,
         'camera_ilustrada':{'plano':'medio'},
         'mapa_composicao':{'zonas':{'frente':{'x':[.04,.96],'altura':.7,'chao':.94}}}}
    s={'start':0,'end':2,'imagens':cfg};original=copy.deepcopy(s)
    a=quadro(s,0,str(bib),(108,192))
    full=copy.deepcopy(s);full['imagens']['camera_ilustrada']['plano']='inteiro'
    b=quadro(full,0,str(bib),(108,192))
    assert a.tobytes()!=b.tobytes() and s==original


def test_compilador_aceita_angulo_e_modelo_camera_do_motor_juntos():
    from lofi.historias_ilustradas import gerar_historia,compilar
    h=gerar_historia();h['cenas'][0]['camera']={'angulo':'esquerda','plano':'cintura','alvo':'lucas','push':.3}
    cfg=compilar(h)['shots'][0]['imagens']
    assert cfg['fundo']=='fundo_entrada_esquerda_v2'
    assert cfg['camera_ilustrada']['plano']=='medio' and cfg['camera_ilustrada']['alvo']==['lucas']


def test_camera_manual_e_atalhos_do_motor(bib):
    p=atores()
    assert configurar({'close':0,'close_in':.2},p)['plano']=='close'
    assert configurar({'follow':0},p)['alvo']==['a']
    r=resolver({'zoom':[1,2],'cx':.5,'cy':.3},p,bib,(432,768),2,2)
    assert r['z']==2 and r['ox']==-216 and r['oy']==pytest.approx(-768*.3)
    with pytest.raises(ValueError):resolver({'zoom':.5},p,bib,(432,768))


def test_auto_nao_muda_zoom_ao_iniciar_ciclo(bib):
    p=atores();p[0]['animacoes_quadros']=[{'acao':'andar','ciclo':'lucas/andar_corpo_v1.json','inicio':1,'fim':2}]
    # Plan selection is tested without requiring external artwork in fixture.
    from unittest.mock import patch
    with patch('lofi.composicao.envelope',return_value=(.98,.15,.15)):
        a=resolver({'plano':'auto'},p,bib,(432,768),0,3)
        b=resolver({'plano':'auto'},p,bib,(432,768),1.5,3)
    assert a['plano']==b['plano']=='inteiro' and a['z']==b['z']


def test_corte_usa_relogio_local_sem_reiniciar_trajeto_do_ator(bib):
    p=atores();p[0]['trajeto']={'pos':[[0,.2],[2,.8]]}
    camera={'plano':'aberto','cortes':[{'inicio':1,'fim':2,'zoom':[1,2]}]}
    from unittest.mock import patch
    with patch('lofi.camera_ilustrada.caixas',wraps=caixas):
        r=resolver(camera,p,bib,(432,768),1.5,2)
    assert r['z']==pytest.approx(1.5)
    assert caixas(p,bib,(432,768),1.5)[0]['x']>432*.5
