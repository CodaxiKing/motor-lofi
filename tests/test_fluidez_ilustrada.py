import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from lofi import atuacao_voz as A, camadas_cenario as C, wavio
from lofi.locomocao_ilustrada import fase, correcao_apoio, mundo


def test_passada_depende_da_distancia_e_para_junto_com_o_corpo():
    p={'pos':.2,'altura':.5,'trajeto':{'pos':[[0,.2],[2,.4],[4,.4]]}}
    c={'deslocamento_corpo_ciclo':.4,'fps_quadros':8,'frames':[{}]*8}
    ac={'inicio':0,'fim':4}
    assert fase(p,{},c,ac,2,(400,800),4)==pytest.approx(.5)
    assert fase(p,{},c,ac,4,(400,800),4)==pytest.approx(.5)
    assert fase(p,{},c,ac,2,(800,1600),4)==pytest.approx(.5)
    volta=dict(p,trajeto={'pos':[[0,.4],[2,.2],[4,.4]]})
    assert fase(volta,{},c,ac,4,(400,800),4)==pytest.approx(1)
    assert fase(p,{},c,ac,1,(400,800),4)<fase(p,{},c,ac,2,(400,800),4)


def test_passada_combina_travelling_piso_e_ordem_de_exposicoes():
    p={'pos':.3,'altura':.5,'seguir_travelling':True}
    c={'deslocamento_corpo_ciclo':.4,'fps_quadros':8,'frames':[{}]*8,'ordem':list(range(8))*2}
    ac={'inicio':0,'fim':2};cfg={'travelling':{'velocidades':[[0,.1]]}}
    assert fase(p,cfg,c,ac,2,(400,800),2)==pytest.approx(1)
    assert fase(p,{},c,ac,2,(400,800),2)==pytest.approx(1)  # dois segundos / 16 exposições a 8 fps
    andando=dict(p,seguir_piso='rampa',trajeto={'pos':[[0,.2],[2,.4]]})
    mapa={'mapa_composicao':{'pisos':{'rampa':[[0,.7],[1,.9]]}}}
    assert mundo(andando,mapa,1,(400,800),2)[1]==pytest.approx(.76)
    assert fase(andando,mapa,c,ac,2,(400,800),2)>.5


def test_posicoes_nomeadas_legadas_continuam_compativeis():
    p={'pos':'centro','altura':.5,'andar':['esquerda','direita']}
    assert mundo(p,{},1,(400,800),2)[0]==pytest.approx(.25)
    c={'deslocamento_corpo_ciclo':.4,'fps_quadros':8,'frames':[{}]*8}
    assert fase(p,{},c,{'inicio':0,'fim':2},2,(400,800),2)==pytest.approx(1.1)


def test_ficha_do_lucas_e_floresta_usam_os_novos_recursos():
    from lofi.historias_ilustradas import carregar
    cat=carregar()
    assert cat['personagens']['lucas']['composicao']['ciclos_quadros']['andar'].endswith('andar_apoios_v2.json')
    camadas=cat['cenarios']['floresta']['camadas_cenario']
    assert {c['tipo'] for c in camadas}=={'imagem','nevoa','luz'}


def test_calibracao_real_fecha_apoios_sem_acumular_deriva_por_ciclo():
    from lofi.ciclos_quadros import carregar
    base=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'
    c=carregar(base,'lucas/hd/andar_apoios_v2.json')
    p={'pos':.5,'altura':.46,'chao':.92,'seguir_travelling':True,'travar_apoios':True}
    cfg={'travelling':{'velocidades':[[0,p['altura']*c['deslocamento_corpo_ciclo']]]}}
    ac={'inicio':0,'fim':4}
    for t in (1,2,3,4):
        dx,dy=correcao_apoio(p,cfg,c,ac,t,(270,480),4,base)
        assert max(abs(dx),abs(dy))<.001


@pytest.mark.parametrize('flip',[False,True])
def test_trava_ponto_do_pe_no_mundo_com_seek_e_espelhamento(tmp_path,flip):
    pasta=tmp_path/'imagens';pasta.mkdir()
    im=Image.new('RGBA',(40,80),(255,0,0,255));im.save(pasta/'frame.png')
    f={'img':'frame','ancora':[.5,.95],'marcos':{'pe':[.7,.95]}}
    c={'tipo':'corpo_inteiro','referencia':{'altura_corpo':1,'altura_referencia':1},
       'deslocamento_corpo_ciclo':.4,'fps_quadros':2,'frames':[f,f],
       'contatos_solo':[{'inicio':0,'fim':.5,'marco':'pe'}]}
    p={'pos':.2,'altura':.5,'chao':.9,'travar_apoios':True,'limite_correcao_apoio':.5,
       'trajeto':{'pos':[[0,.2],[1,.4]]}}
    ac={'inicio':0,'fim':1};valores=[]
    for t in (.4,.1,.3,.4):
        dx,dy=correcao_apoio(p,{},c,ac,t,(400,800),1,tmp_path,flip)
        x,y,_=mundo(p,{},t,(400,800),1)
        valores.append((x+(-.05 if flip else .05)+dx/800,y+dy/800))
    assert all(v==pytest.approx(valores[0],abs=1e-7) for v in valores)
    c.pop('contatos_solo')
    with pytest.raises(ValueError,match='calibrados'):correcao_apoio(p,{},c,ac,.1,(400,800),1,tmp_path)


def test_troca_de_apoio_nao_reinicia_correcao_da_raiz(tmp_path):
    pasta=tmp_path/'imagens';pasta.mkdir()
    Image.new('RGBA',(40,80),'red').save(pasta/'frame.png')
    f={'img':'frame','ancora':[.5,.95],'marcos':{'pe':[.7,.95]}}
    c={'tipo':'corpo_inteiro','referencia':{'altura_corpo':1,'altura_referencia':1},
       'deslocamento_corpo_ciclo':.4,'fps_quadros':2,'frames':[f,f],
       'contatos_solo':[{'inicio':0,'fim':.25,'marco':'pe'},{'inicio':.25,'fim':1,'marco':'pe'}]}
    p={'pos':.2,'altura':.5,'travar_apoios':True,'limite_correcao_apoio':1,
       'trajeto':{'pos':[[0,.2],[1,.4]]}}
    ac={'inicio':0,'fim':1}
    a=correcao_apoio(p,{},c,ac,.4999,(400,800),1,tmp_path)
    b=correcao_apoio(p,{},c,ac,.5001,(400,800),1,tmp_path)
    assert abs(b[0]-a[0])<.1


def test_voz_congelada_controla_pausas_gestos_e_detecta_troca(tmp_path):
    sr=44100;t=np.arange(sr//3)/sr
    x=np.concatenate([np.zeros(sr//5),.3*np.sin(2*np.pi*220*t),np.zeros(sr//3),.2*np.sin(2*np.pi*300*t)])
    path=tmp_path/'voz.wav';wavio.write(path,x,sr)
    h={'cenas':[{'falas':[{'personagem':'lucas','texto':'Uma fala. Outra frase.','audio':'voz.wav','audio_final':True}]}]}
    out=A.preparar(h,tmp_path)
    f=out['cenas'][0]['falas'][0];v=f['atuacao_voz']
    assert len(v['janelas_fala'])==2 and v['pausas']
    assert v['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    assert out['producao']['etapa']=='animacao' and 'atuacao_voz' not in h['cenas'][0]['falas'][0]
    A.validar_snapshot(out,tmp_path)
    g=A.gestos({'start':10,'end':12,'audio_pronto':True,'atuacao_voz':v})
    assert g[0]['end']<g[1]['start'] and g[0]['start']>=10.19
    assert A.gestos({'start':10,'end':12,'audio_pronto':False})==[]
    wavio.write(path,x*.5,sr)
    with pytest.raises(ValueError,match='Voz alterada'):A.validar_snapshot(out,tmp_path)


def test_voz_de_teste_serve_para_previa_mas_nao_para_etapa_final(tmp_path):
    wavio.write(tmp_path/'voz.wav',np.sin(np.arange(44100)*.1)*.2,44100)
    h={'cenas':[{'falas':[{'personagem':'lucas','texto':'Teste','audio':'voz.wav'}]}]}
    with pytest.raises(ValueError,match='Voz final'):A.preparar(h,tmp_path)
    out=A.preparar(h,tmp_path,previa=True)
    A.validar_snapshot(out,tmp_path)
    out['producao']['etapa']='final'
    with pytest.raises(ValueError,match='voz final'):A.validar_snapshot(out,tmp_path)


def test_camadas_nevoa_luz_e_paralaxe_sao_deterministicas_e_independentes():
    camadas=[{'id':'n','tipo':'nevoa','plano':'frente','opacidade':.3},
             {'id':'l','tipo':'luz','pulsar':.3},
             {'id':'arvore','tipo':'imagem','img':'a','profundidade':1.2}]
    original=copy.deepcopy(camadas);im=Image.new('RGBA',(20,30),'white')
    a=C.gerar(camadas,1,(100,180),lambda n:im)
    b=C.gerar(camadas,2,(100,180),lambda n:im)
    assert a[0][0].tobytes()!=b[0][0].tobytes()
    assert a[0][0].tobytes()==C.gerar(camadas,1,(100,180),lambda n:im)[0][0].tobytes()
    tv=C.gerar(camadas,1,(100,180),lambda n:im,{'velocidades':[[0,.1]]})
    assert tv[2][1]<a[2][1] and camadas==original
    assert tv[0][1]==a[0][1] and tv[0][0].tobytes()!=a[0][0].tobytes()
    assert im.getchannel('A').getextrema()==(255,255)
    with pytest.raises(ValueError,match='único'):C.validar(camadas+[camadas[0]])


def test_pausas_fecham_boca_mesmo_com_cue_aberto():
    from lofi.boca_local import estado
    e={'start':0,'end':2,'voice':'v','mouth_cues':[{'start':0,'end':2,'shape':'A'}],
       'atuacao_voz':{'pausas':[{'inicio':.5,'fim':1}]}}
    assert estado({'eventos_fala':[e]},.75)[0]=='rest'
    assert estado({'eventos_fala':[e]},.25)[0]=='A'


def test_transicao_fecha_fase_mesmo_com_mudanca_de_velocidade():
    from lofi.transicoes_ilustradas import planejar
    ciclos={'andar':'walk','correr':'run'}
    pontes={'andar>correr':{'ciclo':'ponte','duracao':.5,'periodo_origem':1,'fase_origem':.25,'fase_destino':.5}}
    seq=planejar([{'acao':'andar','inicio':0,'fim':2},{'acao':'correr','inicio':2,'fim':4}],ciclos,pontes)
    c={'deslocamento_corpo_ciclo':.4,'fps_quadros':8,'frames':[{}]*8}
    p={'altura':.5,'trajeto':{'pos':[[0,.2],[1,.21],[2,.6],[4,.8]]}}
    assert fase(p,{},c,seq[0],2,(400,800),4)%1==pytest.approx(.25)
    assert seq[2]['fase_inicial']==.5


def test_revisao_exporta_clip_com_audio_no_tempo_local_e_relatorio(tmp_path):
    from lofi.revisao_cenas import revisar
    from lofi.sincronia import ler_audio
    imagens=tmp_path/'imagens';imagens.mkdir()
    Image.new('RGB',(100,180),(12,24,36)).save(imagens/'fundo_teste.png')
    x=.2*np.sin(2*np.pi*220*np.arange(8820)/44100)
    wavio.write(tmp_path/'voz.wav',x,44100)
    spec={'fps':24,'total':3,'voices':{'v':'voz.wav'},'clips':[{'voice':'v','src':[0,.2],'at':2.1}],
          'narrado':True,'shots':[{'start':2,'end':2.4,'scene':'teste','imagens':{'fundo':'fundo_teste',
          'personagens':[],'aproximar':0,'balanco':0,'sombras':False}}]}
    out=tmp_path/'revisao'
    r=revisar(spec,tmp_path,out,size=(90,160),fps=10)
    assert r['ok_tecnico'] and r['cenas'][0]['audio']['voz_presente']
    assert (out/'cena_001.mp4').stat().st_size>1000
    assert (out/'index.html').is_file() and (out/'relatorio.json').is_file()
    y,sr=ler_audio(out/'cena_001_voz.wav')
    assert np.max(np.abs(y[:round(.08*sr)]))<1e-5
    assert np.max(np.abs(y[round(.12*sr):round(.2*sr)]))>.1
    with pytest.raises(FileExistsError):revisar(spec,tmp_path,out,size=(90,160),fps=10)
