import pytest
from PIL import Image
from lofi.portais import recortar, validar
from lofi.composicao import espelhamento, animar
from lofi import imagens


def test_orientacao_dos_dois_lados_e_excecao_explicita():
    p={'img':'a','direcao_original':'direita','orientacao':'centro'}
    assert not espelhamento(p,.25)
    assert espelhamento(p,.75)
    assert espelhamento(dict(p,direcao_original='esquerda'),.25)
    assert not espelhamento(dict(p,orientacao='manual'),.75)
    assert not espelhamento(dict(p,direcao_original='frente'),.75)


@pytest.mark.parametrize('size',[(100,100),(180,320)])
def test_mascara_porta_preserva_fora_da_abertura(size):
    spr=Image.new('RGBA',size,(255,0,0,255))
    mask={'poligono':[[.3,.2],[.7,.2],[.7,.8],[.3,.8]]}
    out=recortar(spr,(0,0),mask,size,size)
    assert out.getpixel((size[0]//2,size[1]//2))[3]==255
    assert out.getpixel((0,0))[3]==0
    assert spr.getpixel((0,0))[3]==255


def test_trajetoria_interpolada_nao_muta_personagem():
    p={'img':'a','pos':.5,'chao':.5,'altura':.2,
       'trajeto':{'altura':[[0,.2],[2,.6]],'chao':[[0,.5],[2,.9]]}}
    out=animar(p,1)
    assert out['altura']==pytest.approx(.4) and out['chao']==pytest.approx(.7)
    assert p['altura']==.2
    with pytest.raises(ValueError):animar({'trajeto':{'outro':[[0,1]]}},0)


def test_renderer_porta_oculta_corpo_ate_cruzar_limiar(tmp_path):
    pasta=tmp_path/'imagens';pasta.mkdir()
    Image.new('RGB',(100,100),(10,20,30)).save(pasta/'fundo_sala.png')
    sprite=Image.new('RGBA',(100,100),(255,0,0,255))
    sprite.putpixel((0,0),(0,0,0,0))
    sprite.save(pasta/'monstro.png')
    p={'img':'monstro','pos':.5,'altura':1,'chao':1,'ancora':[.5,1],
       'piscar':False,'respirar':0,'portal':{'nome':'porta','ate_chao':1.1}}
    cfg={'fundo':'fundo_sala','personagens':[p],'aproximar':0,'balanco':0,
         'portais':{'porta':{'poligono':[[.3,.1],[.7,.1],[.7,.9],[.3,.9]]}}}
    shot={'start':0,'end':2,'imagens':cfg}
    im=imagens.quadro(shot,1,str(tmp_path),(100,100))
    assert im.getpixel((50,50))==(255,0,0)
    assert im.getpixel((10,50))==(10,20,30)
    p['portal']['ate_chao']=.9
    im=imagens.quadro(shot,1,str(tmp_path),(100,100))
    assert im.getpixel((10,50))==(255,0,0)
    p['portal']='desconhecido'
    with pytest.raises(ValueError,match='Portal inexistente'):imagens.quadro(shot,1,str(tmp_path),(100,100))


def test_portal_invalido_rejeitado():
    with pytest.raises(ValueError):validar({'poligono':[[0,0],[1,1]]})
