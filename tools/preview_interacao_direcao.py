"""Demonstra contato, oclusão, ligações de movimento e direção narrativa."""
import copy,json,sys
from pathlib import Path
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lofi.historias_ilustradas import carregar
from lofi.ciclos_quadros import carregar as ler_ciclo
from lofi.interacoes_ilustradas import aplicar
from lofi.direcao_ilustrada import planejar
from lofi.imagens import quadro

BASE=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def preparar():
    cat=carregar();p=cat['personagens']['lucas'];f=p['composicao'];pose=p['poses']['neutro']
    comum={'id':'lucas','img':pose['img'],'referencia_escala':pose['img'],'ancora':pose['ancora'],
           'altura_m':f['altura_m'],'marcos_camera':f['marcos_camera'],'pos':.2,'chao':.85,
           'altura':.43,'piscar':False,'respirar':0,'orientacao':'manual','espelhar':False}
    mov=[{'acao':'parado','inicio':0,'fim':.6},{'acao':'andar','inicio':.6,'fim':2.5},
         {'acao':'correr','inicio':2.5,'fim':4.4},{'acao':'parado','inicio':4.4,'fim':6}]
    actor=dict(comum,movimentos=mov,seguir_piso='passagem',
               trajeto={'pos':[[0,.18],[.6,.18],[1.1,.21],[2.5,.38],[3,.44],[4.4,.72],[4.9,.76],[6,.76]],
                        'altura':[[0,.34],[2.5,.37],[4.9,.43],[6,.43]]})
    mapa=copy.deepcopy(cat['cenarios']['entrada']['mapa_composicao']);mapa['pisos']={'passagem':[[.1,.81],[.8,.92]]}
    armario=dict(cat['objetos']['armario_baixo'],x=.54,y=.735,altura=.25,chao=.86)
    cfg={'fundo':'fundo_entrada_v1','personagens':[actor],'mapa_composicao':mapa,'composicao':'manual',
         'camera_ilustrada':{'plano':'inteiro','alvo':'lucas','zoom_max':1.15},'aproximar':0,'balanco':0,'oclusores':[armario]}
    shots=[{'start':0,'end':6,'imagens':cfg}]
    ciclo=ler_ciclo(BASE,f['ciclos_quadros']['interagir'])
    reach=dict(comum,altura=.29,animacoes_quadros=[{'ciclo':f['ciclos_quadros']['interagir'],'inicio':0,'fim':4.5,'modo':'uma_vez'}],
               interacoes=[{'alvo':'macaneta','inicio':0,'fim':4.5,'marco':'palma_d','modo':'posicionar'}])
    cfg2={'fundo':'fundo_entrada_v1','personagens':[reach],'mapa_composicao':mapa,'composicao':'manual','aproximar':0,'balanco':0}
    cfg2['camera_ilustrada']={'plano':'auto','cortes':planejar([
        {'tipo':'interacao','inicio':0,'fim':1.3,'alvo':'lucas'},
        {'tipo':'fala','inicio':1.3,'fim':2.4,'alvo':'lucas'},
        {'tipo':'descoberta','inicio':2.4,'fim':3.4,'alvo':'lucas'},
        {'tipo':'pre_susto','inicio':3.4,'fim':4.5}],4.5,[reach])}
    shots.append({'start':6,'end':10.5,'imagens':cfg2})
    jump=json.loads((BASE/'jumpscare_skinwalker_demo_v1.json').read_text(encoding='utf-8'))['shots']
    for shot in jump:shot['start']+=10.5;shot['end']+=10.5
    spec={'fps':24,'preview_size':[432,768],'total':14.1,'loop':False,'narrado':True,'shots':shots+jump}
    (BASE/'interacao_direcao_demo_v1.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    samples=[(.8,'Início'),(3,'Corrida'),(6.9,'Contato'),(8.7,'Reação')]
    panel=Image.new('RGB',(432*4,798),(10,14,20));d=ImageDraw.Draw(panel)
    for i,(t,label) in enumerate(samples):
        sh=next(s for s in spec['shots'] if s['start']<=t<s['end']);panel.paste(quadro(sh,t,str(BASE),(432,768)),(i*432,30));d.text((i*432+12,8),label,fill='white')
    panel.save(BASE/'interacao_direcao_comparacao_v1.png')


if __name__=='__main__':preparar()
