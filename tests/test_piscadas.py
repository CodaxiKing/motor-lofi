import copy
import json
from pathlib import Path
import numpy as np
import pytest
from PIL import Image,ImageDraw,ImageChops
from lofi.piscadas import compor
from lofi.puppet import alvos
from lofi import imagens


def test_piscada_local_nao_altera_corpo_nem_canvas():
    base=Image.new('RGBA',(60,100),(200,100,30,255))
    outra=Image.new('RGBA',(80,120),(50,180,90,255))
    original=base.tobytes()
    out=compor(base,outra,[{'destino':[.2,.1,.8,.3]}])
    assert out.size==base.size and base.tobytes()==original
    assert out.crop((0,30,60,100)).tobytes()==base.crop((0,30,60,100)).tobytes()
    assert out.tobytes()!=original


def test_renderer_preserva_ancora_base_ao_piscar(tmp_path):
    pasta=tmp_path/'imagens';pasta.mkdir()
    for nome,cor in [('base','orange'),('fechado','green')]:
        im=Image.new('RGBA',(40,80));ImageDraw.Draw(im).rectangle((5,2,35,78),fill=cor);im.save(pasta/(nome+'.png'))
    p={'img':'base','pos':.5,'altura':.7,'chao':.95,'ancora':[.5,.98],
       'piscadas':{'base':'fechado'},'piscadas_locais':{'base':[{'destino':[.2,.1,.8,.3]}]},
       'ancoras':{'fechado':[.2,.7]},'respirar':0,'piscar':False}
    shot={'start':0,'end':1,'imagens':{'personagens':[p],'aproximar':0,'balanco':0}}
    closed=imagens.quadro(shot,0,str(tmp_path),(100,180))
    opened=copy.deepcopy(shot);opened['imagens']['personagens'][0]['piscadas']={}
    normal=imagens.quadro(opened,0,str(tmp_path),(100,180))
    assert closed.crop((0,100,100,180)).tobytes()==normal.crop((0,100,100,180)).tobytes()
    assert ImageChops.difference(closed,normal).getbbox() is not None


def test_ciclos_da_previa_fecharam_sem_salto():
    root=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1/imagens'
    for char in ('lucas','teo'):
        r=json.loads((root/char/'puppet_neutro_v1.json').read_text(encoding='utf-8'))
        _,a=alvos(r,0);_,b=alvos(r,8)
        assert np.allclose(a,b,atol=1e-10)


def test_rejeita_regiao_invertida():
    with pytest.raises(ValueError):compor(Image.new('RGBA',(10,10)),Image.new('RGBA',(10,10)),[{'destino':[.8,0,.2,1]}])
