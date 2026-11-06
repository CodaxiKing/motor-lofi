from pathlib import Path
import pytest
from PIL import Image
from lofi.historias_ilustradas import carregar, compilar, gerar_historia, inventario, validar_catalogo
from lofi.ciclos_quadros import carregar as ler_ciclo, indice, quadro

BASE=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def test_elenco_tem_ciclos_proprios_e_criatura_tem_mais_desenhos():
    cat=carregar();inv=inventario()
    assert inv['grupos']['criaturas']==['mimico']
    for id,p in cat['personagens'].items():
        ciclos=p['composicao']['ciclos_quadros']
        assert {'andar','correr','levantar_braco','agachar','levantar','se_esconder'}<=ciclos.keys()
        a=ler_ciclo(BASE,ciclos['agachar']);b=ler_ciclo(BASE,ciclos['levantar'])
        assert len(a['frames'])==8 and indice(a,10,'uma_vez')==7 and indice(b,10,'uma_vez')==0
        assert a['atlas'].startswith(id+'/')
        if id=='mimico':
            assert {'espreitar','avancar'}<=ciclos.keys()
            assert all(len(ler_ciclo(BASE,ciclos[n])['frames'])==16 for n in ('espreitar','avancar'))
    assert validar_catalogo()==[]


def test_camera_e_objeto_chegam_ao_renderer_sem_mudar_ambiente():
    h=gerar_historia();s=h['cenas'][0]
    s.update(camera='esquerda',frente=[{'objeto':'bau','x':.4,'altura':.38}])
    s['personagens'][0].update(animacao='quadros',animacoes_quadros=[{'acao':'se_esconder','inicio':0,'fim':3,'modo':'uma_vez'}])
    ep=compilar(h);cfg=ep['shots'][0]['imagens']
    assert cfg['fundo']=='fundo_entrada_esquerda_v2'
    assert cfg['frente'][0]['img']=='objetos/bau_v2' and cfg['frente'][0]['x']==.4
    assert cfg['personagens'][0]['animacoes_quadros'][0]['ciclo'].endswith('agachar_corpo_v2.json')
    s['camera']='inexistente'
    with pytest.raises(ValueError,match='Câmera'):compilar(h)


def test_agachar_preserva_escala_fisica_e_diminui_silhueta():
    c=ler_ciclo(BASE,'lucas/agachar_corpo_v2.json')
    with Image.open(BASE/'imagens'/(c['atlas']+'.png')) as atlas:
        a,_,sa,_=quadro(c,atlas,0,'uma_vez');b,_,sb,_=quadro(c,atlas,10,'uma_vez')
    assert sa==sb
    boxa=a.getchannel('A').point(lambda v:255 if v>30 else 0).getbbox()
    boxb=b.getchannel('A').point(lambda v:255 if v>30 else 0).getbbox()
    assert boxb[3]-boxb[1] < .8*(boxa[3]-boxa[1])


def test_mapeamento_reserva_toda_a_extensao_dos_bracos_da_criatura():
    from lofi.composicao import planejar
    cat=carregar();p=cat['personagens']['mimico']
    cfg={'fundo':'fundo_entrada_v1','mapa_composicao':cat['cenarios']['entrada']['mapa_composicao'],
         'personagens':[{'id':'mimico','img':p['poses']['neutro']['img'],'pos':.5,'altura':.7,'chao':.94,
                         'animacoes_quadros':[{'ciclo':p['composicao']['ciclos_quadros']['avancar'],'inicio':0,'fim':3}]}]}
    out,report=planejar(cfg,BASE,(432,768))
    assert out['personagens'][0]['altura']>0
    assert not any(f['code']=='corte_personagem' for f in report['achados'])
