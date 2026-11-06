import copy
import numpy as np
import pytest
from PIL import Image,ImageDraw
from lofi.qualidade_visual import redimensionar,ajustar_camera,escolher,substituir
from lofi.ciclos_quadros import validar,quadro


def test_png_por_quadro_preserva_pixels_e_protege_caminho(tmp_path):
    root=tmp_path/'imagens';root.mkdir();Image.new('RGBA',(512,768),'orange').save(root/'frame.png')
    c={'tipo':'corpo_inteiro','fps_quadros':8,'referencia':{'altura_corpo':.8},'frames':[{'img':'frame','ancora':[.5,.95]}]}
    validar(c);im,anchor,fator,idx=quadro(c,None,0,base=tmp_path)
    assert im.size==(512,768) and anchor==[.5,.95] and idx==0
    c['frames'][0]['img']='../../fora'
    with pytest.raises(ValueError,match='fora'):quadro(c,None,0,base=tmp_path)


def test_reamostragem_nao_cria_borda_preta_em_pixel_transparente():
    im=Image.new('RGBA',(8,8));ImageDraw.Draw(im).rectangle((2,2,5,5),fill=(255,0,0,255))
    a=np.asarray(redimensionar(im,(64,64)));edge=(a[:,:,3]>10)&(a[:,:,3]<240)
    assert edge.any() and np.min(a[:,:,0][edge])>=250 and np.max(a[:,:,1][edge])==0


def test_limite_puxa_camera_sem_encolher_personagem_ou_mudar_foco():
    im=Image.new('RGBA',(200,300));layer=(im,10,20,.8,1,None,{'ator':True,'id':'a','fonte':'pequena'})
    cam={'z':4,'ox':-600,'oy':-1200,'alvos':['a'],'plano':'close'}
    out,report=ajustar_camera(cam,[layer],{},(400,800))
    assert out['z']==pytest.approx(1.25/.8) and layer[3]==.8
    assert (200-out['ox'])/out['z']==pytest.approx((200-cam['ox'])/cam['z'])
    assert report[0]['ampliacao']<=1.25
    bad=(im,0,0,3,1,None,{'ator':True,'id':'a'})
    out,report=ajustar_camera(cam,[bad],{},(400,800))
    assert out['z']==1 and report[0]['insuficiente_na_origem']


def test_nao_troca_corrida_contato_ou_fala_por_rosto_estatico():
    arte={'img':'hd','rosto':[.1,.1,.9,.5]};p={'id':'a','img':'a','arte_por_plano':{'close':{'neutro':arte}},'piscar_hd':False}
    assert escolher('.',p,'close',1,{'acao':'parado'})[0]==arte
    assert escolher('.',p,'close',1,{'acao':'correr'})[0] is None
    assert escolher('.',dict(p,interacoes=[{}]),'close',1)[0] is None
    q=dict(p,eventos_fala=[{'start':2,'end':3}])
    assert escolher('.',q,'close',0,tempo_global=2.5)[0] is None
    assert escolher('.',q,'close',0,tempo_global=3.5)[0]==arte


def test_variante_preserva_centro_e_largura_do_rosto(tmp_path):
    root=tmp_path/'imagens';root.mkdir();im=Image.new('RGBA',(600,1600));ImageDraw.Draw(im).rectangle((30,10,570,1599),fill='orange');im.save(root/'hd.png')
    layer=(Image.new('RGBA',(60,120)),0,0,1,1,None,{'ator':True,'id':'a','espelhado':False})
    r={'face_x':80,'face_y':70,'face_width':100};a={'img':'hd','rosto':[.2,.05,.8,.35]}
    out=substituir(layer,a,r,tmp_path,{'z':2,'ox':0,'oy':0},(200,400))
    assert out is not None
    sprite,x,y,s,*_=out
    assert x+sprite.width*.5*s==pytest.approx(80)
    assert y+sprite.height*.2*s==pytest.approx(70)
    assert sprite.width*.6*s==pytest.approx(100)


def test_closes_reais_dos_cinco_personagens_usam_arte_hd():
    import json
    from pathlib import Path
    from lofi.imagens import quadro as render
    base=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'
    spec=json.loads((base/'nitidez_demo_v1.json').read_text(encoding='utf-8'))
    vistos=set()
    for shot in spec['shots'][1:7]:
        diag=[]
        render(shot,(shot['start']+shot['end'])/2,str(base),(432,768),diagnostico=diag)
        assert diag and diag[0]['variante_hd'],diag
        assert diag[0]['ampliacao']<=1.251
        vistos.add(diag[0]['personagem'])
    assert vistos=={'lucas','teo','clara','amanha','mimico'}
