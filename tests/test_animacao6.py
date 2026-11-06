import copy
import json
from pathlib import Path
import numpy as np
import pytest
from PIL import Image,ImageChops
from lofi import wavio
from lofi.dialogos import compilar
from lofi.boca_local import estado,compor
from lofi.atuacao import envoltoria,aplicar
from lofi.articulado import carregar,renderizar,juntas,angulos
from lofi.continuidade_animacao import analisar
from lofi.sincronia import canais,analisar as analisar_voz


@pytest.fixture
def wav(tmp_path):
    sr=44100;x=np.zeros(sr);x[sr//4:sr//2]=.2*np.sin(2*np.pi*220*np.arange(sr//4)/sr)
    p=tmp_path/'fala.wav';wavio.write(p,x,sr);return p


def test_dialogos_tem_audio_tempos_e_legenda_do_renderer(wav,tmp_path):
    cenas=[{'personagens':[{'id':'a'}],'falas':[{'personagem':'a','texto':'Olá','audio':wav.name,'inicio':.5}]}]
    shots=[{'start':2,'end':5,'imagens':{'personagens':[{'id':'a'}]}}]
    events,voices,clips,subs=compilar(cenas,shots,tmp_path,tmp_path)
    assert events[0]['start']==2.5 and events[0]['end']==3.5
    assert clips[0]['at']==2.5 and subs[0]['text']==['Olá'] and 'src' in subs[0]
    assert shots[0]['imagens']['personagens'][0]['eventos_fala']==events


def test_falas_pendentes_nao_fabricam_voz(tmp_path):
    cenas=[{'personagens':[{'id':'a'}],'falas':[{'personagem':'a','texto':'Olá'}]}]
    shots=[{'start':0,'end':4,'imagens':{'personagens':[{'id':'a'}]}}]
    ev,vozes,clips,subs=compilar(cenas,shots,tmp_path)
    assert not ev[0]['audio_pronto'] and vozes=={} and clips==[] and subs==[]
    with pytest.raises(ValueError):compilar([dict(cenas[0],falas=[{'personagem':'outro','texto':'x'}])],shots,tmp_path)
    with pytest.raises(ValueError):compilar([dict(cenas[0],falas=[{'personagem':'a','texto':'x','duracao':10}])],shots,tmp_path)


def test_audio_seco_silencio_e_corte_no_tempo_do_video(wav,tmp_path):
    spec={'total':2,'fps':24,'voices':{'a':wav.name},'clips':[{'voice':'a','src':[0,1],'at':.5}]}
    nivel,vis,_=canais(spec,tmp_path)
    assert nivel('a',.1)==0 and nivel('a',.85)>.1 and nivel('a',1.8)==0
    assert vis('a',.1)==0
    r=analisar_voz(wav);assert r['aproximado'] and r['cues']


def test_so_falante_ativo_mexendo_boca_e_narracao_quieta():
    p={'eventos_fala':[{'voice':'a','start':1,'end':2,'mouth_cues':[]} ]}
    assert estado(p,1.5,lambda v,t:1,lambda v,t:4)[0]=='O'
    assert estado(p,.5,lambda v,t:1,lambda v,t:4)[0]=='rest'
    assert estado(p,1.5,lambda v,t:1,lambda v,t:4,False)[0]=='rest'


def test_boca_local_preserva_todo_corpo():
    base=Image.new('RGBA',(100,180),'orange');atlas=Image.new('RGBA',(60,60),'gray')
    cfg={'regiao':[.3,.1,.7,.2],'formas':{'A':[0,0,1,1]}}
    out=compor(base,atlas,cfg,'A')
    assert out.crop((0,40,100,180)).tobytes()==base.crop((0,40,100,180)).tobytes()
    assert compor(base,atlas,cfg,'rest').tobytes()==base.tobytes()


def test_preparacao_e_acomodacao_suaves_sem_mutar_rig():
    assert envoltoria(.5,1,2)==0 and envoltoria(1,1,2)==1 and envoltoria(2.5,1,2)==0
    r={'pins':{'mao_d':{'pos':[.5,.5]}},'grupos_rigidos':[{'pins':[],'centro':[.5,.5],'graus':1}]}
    original=copy.deepcopy(r)
    out=aplicar(r,[{'start':1,'end':2,'intencao':'alertar'}],1.5)
    assert r==original and out['pins']['mao_d']['offset'][1]<0


def test_pecas_reais_pivos_ik_e_pe_plano():
    base=Path(__file__).resolve().parents[1]/'tests/fixtures/articulado'
    r=carregar(base,'lucas/rig_camadas_v1.json')
    with Image.new('RGBA',(512,512),(240,140,40,255)) as atlas:
        acoes=[{'tipo':'caminhar','start':0,'end':4}]
        im=renderizar(r,atlas,(196,320),.3,acoes)
    assert im.getbbox() and im.mode=='RGBA'
    js=juntas(r,(981,1604),.3,acoes)
    assert abs(js['pe_e'][2])<1e-6 and abs(js['pe_d'][2])<1e-6
    with pytest.raises(ValueError):angulos(r,1,[{'tipo':'inexistente','start':0,'end':2}])


def test_auditoria_detecta_salto_escala_e_loop(tmp_path):
    root=tmp_path/'imagens';root.mkdir();im=Image.new('RGBA',(40,80),'orange');im.putpixel((0,0),(0,0,0,0));im.save(root/'a.png')
    a={'img':'a','id':'a','altura':.5,'chao':.9,'pos':.3,'piscar':False,'respirar':0}
    b=dict(a,pos=.8,altura=.8)
    spec={'total':2,'seamless_loop':True,'shots':[{'start':0,'end':1,'imagens':{'personagens':[a],'aproximar':0}},
          {'start':1,'end':2,'imagens':{'personagens':[b],'aproximar':0}}]}
    codes={f['code'] for f in analisar(spec,tmp_path)['achados']}
    assert {'salto_posicao','salto_escala','loop_descontinuo'}<=codes


def test_historia_dialogada_compativel_com_renderer_e_audio_real(wav,tmp_path):
    from lofi.historias_ilustradas import gerar_historia,compilar
    from lofi.render import Episode
    h=gerar_historia();h['cenas'][0]['narracao']=''
    h['cenas'][0]['falas']=[{'personagem':'lucas','texto':'Olá','audio':str(wav)}]
    ep=compilar(h,pasta_saida=tmp_path,pasta_audio=tmp_path)
    assert not ep['narrado'] and ep['dialogue_events'][0]['audio_pronto']
    assert ep['subs'][0]['text']==['Olá']
    path=tmp_path/'ep.json';path.write_text(json.dumps(ep),encoding='utf-8')
    obj=Episode(str(path));assert obj.subs and obj.clips


def test_cues_de_arquivo_e_silencio_sao_verificados(wav,tmp_path):
    p=tmp_path/'cues.json';p.write_text(json.dumps({'cue_format':'viseme','cues':[{'start':0,'end':.1,'shape':'A'}]}))
    shots=[{'start':0,'end':2,'imagens':{'personagens':[{'id':'a'}]}}]
    cenas=[{'personagens':[{'id':'a'}],'falas':[{'personagem':'a','texto':'Olá','audio':wav.name,'mouth_cues_file':p.name}]}]
    ev,v,c,subs=compilar(cenas,shots,tmp_path,tmp_path)
    spec={'total':2,'voices':v,'clips':c,'dialogue_events':ev,'shots':shots}
    assert ev[0]['mouth_cues'][0]['shape']=='A'
    assert any(f['code']=='boca_no_silencio' for f in analisar(spec,tmp_path)['achados'])
