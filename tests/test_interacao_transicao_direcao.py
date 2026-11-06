import copy
import pytest
from lofi.interacoes_ilustradas import aplicar
from lofi.transicoes_ilustradas import planejar
from lofi.direcao_ilustrada import planejar as dirigir


def test_ligacao_ocupa_inicio_do_estado_sem_sobrepor_ou_alterar_duracao():
    mov=[{'acao':'parado','inicio':0,'fim':1},{'acao':'andar','inicio':1,'fim':3},{'acao':'correr','inicio':3,'fim':5}]
    seq=planejar(mov,{'parado':'idle','andar':'walk','correr':'run'},
                 {'parado>andar':{'ciclo':'start','duracao':.5},'andar>correr':{'ciclo':'accel','duracao':.5}})
    assert [x['ciclo'] for x in seq]==['idle','start','walk','accel','run']
    assert all(a['fim']==b['inicio'] for a,b in zip(seq,seq[1:])) and seq[-1]['fim']==5
    with pytest.raises(ValueError,match='ligação'):planejar(mov,{'parado':'idle','andar':'walk','correr':'run'},{})
    with pytest.raises(ValueError,match='insuficiente'):planejar(mov,{'parado':'i','andar':'w','correr':'r'},{'parado>andar':{'ciclo':'x','duracao':3}})


def ciclo():
    f={'ancora':[.5,.95],'marcos':{'mao_d':[.8,.4]}}
    return {'referencia':{'altura_corpo':1,'altura_referencia':1},'aspecto_celula':1,'frames':[f]},f


def test_mao_chega_no_alvo_sem_esticar_desenho_e_escala_nao_muda():
    p={'altura':.4,'pos':.4,'chao':.9,'interacoes':[{'inicio':0,'fim':2,'alvo':'macaneta','modo':'posicionar'}]}
    original=copy.deepcopy(p);c,f=ciclo();cfg={'pontos_interacao':{'macaneta':[.7,.5]}}
    out=aplicar(p,cfg,1,(400,800),None,c,f)
    assert out['pos']+(.8-.5)*out['altura']*800/400==pytest.approx(.7)
    assert out['chao']+(.4-.95)*out['altura']==pytest.approx(.5)
    assert out['altura']==p['altura'] and p==original
    p['interacoes'][0]['modo']='contato'
    with pytest.raises(ValueError,match='incompatíveis'):aplicar(p,cfg,1,(400,800),None,c,f)


def test_piso_linear_sem_degrau_e_contato_espelhado():
    p={'altura':.4,'pos':.5,'chao':.9,'seguir_piso':'trilha'}
    cfg={'mapa_composicao':{'pisos':{'trilha':[[0,.7],[1,.9]]}}}
    assert aplicar(p,cfg,0,(400,800),None)['chao']==pytest.approx(.8)
    c,f=ciclo();p.pop('seguir_piso');p['interacoes']=[{'inicio':0,'fim':2,'alvo':'a'}]
    out=aplicar(p,{'pontos_interacao':{'a':[.3,.5]}},1,(400,800),None,c,f,True)
    assert out['pos']+(.2-.5)*out['altura']*800/400==pytest.approx(.3)


def test_direcao_prioriza_reacao_e_prepara_susto_sem_reiniciar_ator():
    batidas=[{'tipo':'acao','inicio':0,'fim':8},{'tipo':'fala','alvo':'lucas','inicio':2,'fim':4},
             {'tipo':'reacao','alvo':'teo','inicio':4,'fim':5.5},{'tipo':'pre_susto','inicio':5.5,'fim':7},
             {'tipo':'susto','inicio':7,'fim':8}]
    cortes=dirigir(batidas,8,[{'id':'lucas'},{'id':'teo'}])
    assert [x['plano'] for x in cortes]==['inteiro','medio','close','conjunto','aberto']
    with pytest.raises(ValueError):dirigir([{'tipo':'fala','inicio':0,'fim':9}],8,[])


def test_elenco_tem_ligacoes_reais_e_maos_calibradas():
    from pathlib import Path
    from lofi.historias_ilustradas import carregar,validar_catalogo
    from lofi.ciclos_quadros import carregar as ler
    base=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'
    for p in carregar()['personagens'].values():
        f=p['composicao']
        assert {'parado>andar','andar>correr','correr>parado'}<=f['transicoes'].keys()
        assert all(len(ler(base,t['ciclo'])['frames'])==8 for t in f['transicoes'].values())
        frame=ler(base,f['ciclos_quadros']['interagir'])['frames'][-1]
        assert {'palma_d','centro_rosto','topo_cabeca'}<=frame['marcos'].keys()
    assert validar_catalogo()==[]


def test_objeto_oculta_atras_e_personagem_passa_a_frente(tmp_path):
    from PIL import Image
    from lofi.imagens import quadro
    root=tmp_path/'imagens';root.mkdir()
    a=Image.new('RGBA',(50,100),'red');a.putpixel((0,0),(0,0,0,0));a.save(root/'a.png')
    o=Image.new('RGBA',(20,20),'green');o.putpixel((0,0),(0,0,0,0));o.save(root/'o.png')
    p={'img':'a','pos':.5,'altura':.6,'chao':.7,'ancora':[.5,1],'piscar':False,'respirar':0}
    s={'start':0,'end':2,'imagens':{'personagens':[p],'sombras':False,'aproximar':0,'balanco':0,
       'oclusores':[{'img':'o','x':.5,'y':.65,'altura':.2,'chao':.75}]}}
    back=quadro(s,0,str(tmp_path),(100,200));p['chao']=.9;front=quadro(s,0,str(tmp_path),(100,200))
    assert back.getpixel((50,130))==(0,128,0) and front.getpixel((50,130))==(255,0,0)
