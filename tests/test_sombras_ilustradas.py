import copy
from pathlib import Path
import numpy as np
import pytest
from PIL import Image,ImageDraw
from lofi.sombras_ilustradas import fontes,geometria,gerar,iluminacao,recortar_piso
from lofi.imagens import quadro


def ator():
    im=Image.new('RGBA',(80,160));d=ImageDraw.Draw(im)
    d.ellipse((24,5,56,38),fill='orange');d.rectangle((28,35,52,120),fill='orange')
    d.rectangle((23,115,35,155),fill='orange');d.rectangle((46,115,59,155),fill='orange')
    return im,{'id':'a','img':'a','altura':.6,'altura_m':1.7,'chao':.90}


def luz(x=.2):return {'ambiente':.25,'luzes':[{'tipo':'pontual','espaco':'tela','posicao':[x,.8],'altura_m':3.2,'intensidade':1,'suavidade':.4}]}


def test_sombra_vai_para_lado_oposto_a_luz_e_encurta_com_fonte_alta():
    _,left=fontes(luz(.1),(400,700),None,0);_,right=fontes(luz(.9),(400,700),None,0)
    a=geometria(left[0],(200,630),400,1.7,0);b=geometria(right[0],(200,630),400,1.7,0)
    assert a['vetor'][0]>0>b['vetor'][0]
    high=dict(left[0],altura_m=7)
    assert np.linalg.norm(geometria(high,(200,630),400,1.7,0)['vetor'])<np.linalg.norm(a['vetor'])


def test_luz_animada_e_projecao_do_cenario_acompanham_travelling():
    cfg=luz();cfg['luzes'][0].update(espaco='cenario',trajeto={'x':[[0,.1],[2,.9]]})
    _,a=fontes(cfg,(400,700),((1200,700),-100,0,1),0)
    _,b=fontes(cfg,(400,700),((1200,700),-200,0,1),2)
    assert a[0]['xy'][0]==pytest.approx(20) and b[0]['xy'][0]==pytest.approx(880)


def test_salto_deixa_sombra_no_chao_e_retira_contato():
    im,p=ator();cfg={};original=copy.deepcopy(p)
    # Scale1, soles at ground180. Raise only the body by50 pixels.
    p.update(chao=.9,altura=.75)
    grounded=gerar(im,60,25,1,p,cfg,luz(),(200,200),None,0)
    airborne=gerar(im,60,-25,1,p,cfg,luz(),(200,200),None,0)
    assert len(grounded)>len(airborne)==1
    assert airborne[0][1]!=grounded[0][1]  # light ray offsets the airborne cast
    assert p['chao']==.9 and original['id']==p['id']
    barely=gerar(im,60,23,1,p,cfg,luz(),(200,200),None,0)
    assert len(barely)>1
    assert barely[-1][2]+barely[-1][0].height/2==pytest.approx(179)
    assert grounded[-1][2]+grounded[-1][0].height/2==pytest.approx(181)


def test_retrato_sem_pes_nao_ganha_sombra_e_opcao_desliga():
    im,p=ator()
    assert gerar(im,0,0,1,p,{},luz(),(200,200),None,0,ciclo={'tipo':'retrato'})==[]
    assert gerar(im,0,0,1,p,{'sombras':False},luz(),(200,200),None,0)==[]


def test_mascara_piso_e_camera_impedem_pintar_parede():
    spr=Image.new('RGBA',(100,100),(0,0,0,180))
    out=recortar_piso(spr,(0,0),[(0,50),(100,50),(100,100),(0,100)],(1,0,0))
    assert out.getpixel((20,20))[3]==0 and out.getpixel((20,80))[3]==180
    moved=recortar_piso(spr,(0,0),[(0,50),(100,50),(100,100),(0,100)],(2,0,-50))
    assert moved.getpixel((20,20))[3]==0 and moved.getpixel((20,80))[3]==180


def test_renderer_pinta_sombra_antes_do_corpo_e_nao_muda_spec(tmp_path):
    root=tmp_path/'imagens';root.mkdir();Image.new('RGB',(180,320),(100,90,80)).save(root/'fundo_sala.png')
    im,p=ator();im.save(root/'a.png');p.update(ancora=[.5,.975],pos=.5,piscar=False,respirar=0)
    shot={'start':0,'end':2,'imagens':{'fundo':'fundo_sala','personagens':[p],'aproximar':0,'balanco':0,'iluminacao':luz()}}
    before=copy.deepcopy(shot);on=quadro(shot,0,str(tmp_path),(180,320))
    off=copy.deepcopy(shot);off['imagens']['sombras']=False;plain=quadro(off,0,str(tmp_path),(180,320))
    assert shot==before and on.tobytes()!=plain.tobytes()
    assert on.getpixel((90,180))==plain.getpixel((90,180)) # body isn't darkened by its own cast


def test_todos_cenarios_da_biblioteca_tem_luzes_calibradas():
    from lofi.historias_ilustradas import carregar
    base=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'
    for lugar in carregar()['cenarios'].values():
        config=iluminacao({'fundo':lugar['img']},base)
        assert config['luzes'] and config['piso']
        fontes(config,(432,768),None,0)


def test_sombra_em_todo_elenco_com_altura_da_ficha():
    from lofi.historias_ilustradas import carregar
    from lofi.sombras_ilustradas import altura_fisica
    base=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'
    c=carregar()
    for id,personagem in c['personagens'].items():
        pose=personagem['poses']['neutro']
        p={'id':id,'img':pose['img'],'ancora':pose['ancora'],'pos':.5,'altura':.6,'chao':.9,'respirar':0,'piscar':False}
        assert altura_fisica(p,base)==personagem['composicao']['altura_m']
        s={'start':0,'end':2,'imagens':{'fundo':'fundo_entrada_v1','personagens':[p],'aproximar':0,'balanco':0}}
        on=quadro(s,0,str(base),(144,256));s['imagens']['sombras']=False;off=quadro(s,0,str(base),(144,256))
        assert np.count_nonzero(np.any(np.asarray(on)!=np.asarray(off),axis=2))>20
