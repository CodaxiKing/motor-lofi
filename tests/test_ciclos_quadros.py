import copy
import pytest
from PIL import Image,ImageDraw
from lofi.ciclos_quadros import validar,indice,quadro,ativo,revisar


def ciclo():
    return {'tipo':'corpo_inteiro','fps_quadros':8,'atlas':'a','referencia':{'altura_corpo':.74,'altura_referencia':.98},
            'frames':[{'regiao':[i/4,0,(i+1)/4,1],'ancora':[.5,.96]} for i in range(4)]}


def test_ordem_loop_ida_volta_e_parada():
    c=ciclo();assert validar(c)==c
    assert [indice(c,i/8) for i in range(6)]==[0,1,2,3,0,1]
    assert [indice(c,i/8,'ida_volta') for i in range(8)]==[0,1,2,3,2,1,0,1]
    assert indice(c,10,'uma_vez')==3
    with pytest.raises(ValueError):indice(c,0,'desconhecido')


def test_braco_alto_nao_reescala_corpo_ou_muda_ancora():
    c=ciclo();atlas=Image.new('RGBA',(160,100))
    d=ImageDraw.Draw(atlas)
    for i in range(4):
        d.rectangle((i*40+12,22,i*40+27,95),fill='orange')
        if i:d.line((i*40+25,50,i*40+30,5),fill='orange',width=4)
    original=copy.deepcopy(c)
    a,anchor,scale,_=quadro(c,atlas,0);b,anchor2,scale2,_=quadro(c,atlas,.125)
    assert a.size==b.size and anchor==anchor2 and scale==scale2
    assert c==original and revisar(c,atlas)['frames']==4


def test_nao_mistura_dois_corpos_no_mesmo_instante():
    a=[{'inicio':0,'fim':1,'ciclo':'a'},{'inicio':1,'fim':2,'ciclo':'b'}]
    assert ativo(a,1)['ciclo']=='b' and ativo(a,3) is None
    with pytest.raises(ValueError):ativo(a+[{'inicio':0,'fim':2,'ciclo':'c'}],.5)


def test_metadados_invalidos_sao_rejeitados():
    c=ciclo();c['frames'][0]['ancora']=[.5,1.2]
    with pytest.raises(ValueError):validar(c)


def test_linhas_de_alturas_diferentes_preservam_escala_por_pixel():
    c=ciclo();c['referencia']['altura_celula_px']=100
    c['frames']=[{'regiao':[0,0,1,.6],'ancora':[.5,.95]},
                 {'regiao':[0,.6,1,1],'ancora':[.5,.95]}]
    atlas=Image.new('RGBA',(100,200),'orange')
    a,_,sa,_=quadro(c,atlas,0);b,_,sb,_=quadro(c,atlas,.125)
    assert sa/a.height==pytest.approx(sb/b.height)
