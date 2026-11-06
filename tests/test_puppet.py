import copy
import json
import numpy as np
import pytest
from PIL import Image,ImageDraw
from lofi.puppet import validar, alvos, deformar
from lofi.fichas_ilustradas import perfil


def rig():
    return {'colunas':8,'pins':{'topo':{'pos':[.5,.2],'amplitude':[.02,0],'periodo':4},
        'quadril':{'pos':[.5,.6],'fixo':True},'pe_e':{'pos':[.35,.9],'fixo':True},
        'pe_d':{'pos':[.65,.9],'fixo':True}}}


def test_pins_movem_continuamente_e_pes_ficam_fixos():
    r=rig();original=copy.deepcopy(r);src,dst=alvos(r,1)
    assert dst[0,0]==pytest.approx(.52)
    assert np.array_equal(src[1:],dst[1:]) and r==original
    _,a=alvos(r,.50);_,b=alvos(r,.51)
    assert np.max(np.abs(a-b))<.001


def test_deformacao_identidade_alfa_e_movimento():
    im=Image.new('RGBA',(80,120));d=ImageDraw.Draw(im);d.rectangle((30,10,50,110),fill='orange')
    before=im.tobytes();r=rig()
    assert deformar(im,r,0).tobytes()==before
    out=deformar(im,r,1)
    assert out.mode=='RGBA' and out.size==im.size and out.getchannel('A').getextrema()[0]==0
    assert out.tobytes()!=before and im.tobytes()==before


def test_pins_invalidos_rejeitados():
    r=rig();r['pins']['topo']['amplitude']=[.5,0]
    with pytest.raises(ValueError):validar(r)
    r=rig();r['pins']['topo']['pos']=r['pins']['quadril']['pos']
    with pytest.raises(ValueError):validar(r)


def test_altura_pertence_a_ficha_e_nao_ao_canvas(tmp_path):
    (tmp_path/'imagens/a').mkdir(parents=True)
    p=tmp_path/'imagens/a/personagem.json';p.write_text(json.dumps({'altura_m':2.10}))
    cadastro={'arquivo_ficha':'a/personagem.json'}
    assert perfil(tmp_path,cadastro)['escala_relativa']==pytest.approx(2.10/1.70)
    p.write_text(json.dumps({'altura_m':1.60}))
    assert perfil(tmp_path,cadastro)['escala_relativa']==pytest.approx(1.60/1.70)
    p.write_text(json.dumps({'altura_m':0}))
    with pytest.raises(ValueError):perfil(tmp_path,cadastro)
