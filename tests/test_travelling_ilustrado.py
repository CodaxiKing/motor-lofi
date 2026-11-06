import pytest
from lofi.travelling import estado,deslocamento


def test_distancia_integrada_e_aceleracao_continua():
    cfg={'velocidades':[[0,.1],[3,.1],[4,.3],[8,.3]]}
    assert estado(cfg,3)==pytest.approx((.3,.1))
    assert estado(cfg,4)==pytest.approx((.5,.3))
    assert estado(cfg,8)==pytest.approx((1.7,.3))
    assert abs(estado(cfg,3.999)[1]-estado(cfg,4.001)[1])<1e-5


def test_panorama_nao_deixa_borda_vazia():
    cfg={'velocidades':[[0,.1],[8,.1]]}
    x,v=deslocamento(cfg,8,(432,768),(3072,1024))
    assert x<0 and v==pytest.approx(.1)
    with pytest.raises(ValueError):deslocamento({'velocidades':[[0,2]]},8,(432,768),(100,100))


def test_corrida_e_caminhada_tem_apoio_e_animacao_distintos():
    from pathlib import Path
    from lofi.articulado import carregar,angulos,juntas
    base=Path(__file__).resolve().parents[1]/'tests/fixtures/articulado'
    rig=carregar(base,'lucas/rig_camadas_v1.json')
    walk=[{'tipo':'caminhar','start':0,'end':8}];run=[{'tipo':'correr','start':0,'end':8}]
    assert angulos(rig,.2,walk)!=angulos(rig,.2,run)
    assert abs(juntas(rig,(981,1604),.2,run)['pe_e'][2])<1e-6
    with pytest.raises(ValueError):angulos(rig,1,[{'tipo':'correr','start':0,'end':8,'ciclo':0}])


@pytest.mark.parametrize('tipo,tempos,start,ciclo,fase',[('caminhar',(1,1.1),-.3,1.2,0),('correr',(5,5.04),4,.62,(4.3/1.2)%1)])
def test_pe_em_apoio_acompanha_solo_do_panorama(tipo,tempos,start,ciclo,fase):
    from pathlib import Path
    from lofi.articulado import carregar,juntas
    base=Path(__file__).resolve().parents[1]/'tests/fixtures/articulado'
    rig=carregar(base,'lucas/rig_perfil_v1.json');W,H=rig['canvas']
    trilho={'velocidades':[[0,.09],[3.7,.09],[4.4,.22],[8,.22]]};fator=H/W/.68
    a={'tipo':tipo,'start':start,'end':8.5,'ciclo':ciclo,'fase_inicial':fase,'trilho':trilho,'fator_trilho':fator}
    valores=[]
    for t in tempos:
        x,y,_=juntas(rig,(W,H),t,[a])['pe_e']
        valores.append((x+estado(trilho,t)[0]*fator*W,y))
    assert valores[0]==pytest.approx(valores[1],abs=1e-5)
