"""Demonstra passada calibrada, voz de teste com pausas e cenário em camadas."""
import copy
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lofi.historias_ilustradas import carregar
from lofi.dialogos import compilar
from lofi.atuacao_voz import preparar, gestos

BASE=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def preparar_demo():
    cat=carregar();p=cat['personagens']['lucas'];f=p['composicao'];pose=p['poses']['neutro']
    comum={'id':'lucas','img':pose['img'],'ancora':pose['ancora'],'altura':.46,'altura_m':f['altura_m'],
           'pos':.3,'chao':.92,'orientacao':'manual','espelhar':False,'respirar':0,
           'marcos_camera':f['marcos_camera'],'bocas_locais':f['bocas_locais'],'puppets':f['puppets']}
    walking=dict(comum,pos=.5,travar_apoios=True,seguir_travelling=True,
                 animacoes_quadros=[{'ciclo':'lucas/hd/andar_apoios_v2.json','inicio':0,'fim':4,'modo':'loop'}])
    camadas=[{'id':'nevoa_fundo','tipo':'nevoa','plano':'fundo','faixa':[.46,1],'opacidade':.12,'velocidade':.035,'profundidade':.4},
             {'id':'arvore_frente','tipo':'imagem','img':'objetos/arvore_v2','plano':'frente','x':3,'y':.51,'altura':1.05,'opacidade':1,'profundidade':1.4},
             {'id':'nevoa_frente','tipo':'nevoa','plano':'frente','faixa':[.74,1],'opacidade':.12,'velocidade':-.03,'profundidade':1.2},
             {'id':'luar','tipo':'luz','plano':'fundo','x':.66,'y':.3,'opacidade':.12,'cor':[150,185,220],'raio':[.4,.45],'pulsar':.08}]
    ciclo=json.loads((BASE/'imagens/lucas/hd/andar_apoios_v2.json').read_text(encoding='utf-8'))
    velocidade=comum['altura']*ciclo['deslocamento_corpo_ciclo']
    s1={'start':0,'end':4,'scene':'trilha_lateral','imagens':{'fundo':'fundo_trilha_lateral_v1','personagens':[walking],
         'travelling':{'velocidades':[[0,velocidade],[4,velocidade]]},
         'camadas_cenario':camadas,'aproximar':0,'balanco':0,'camera_ilustrada':{'plano':'inteiro','alvo':'lucas','zoom_max':1.05}}}
    falando=dict(comum,pos=.5,altura=.63,puppets=f['puppets'],piscadas={'lucas/lucas_34_neutro_recorte_v1':'lucas/lucas_neutro_piscando_v1'},
                 piscadas_locais=f['piscadas_locais'])
    micro=p.get('microposes',{}).get('neutro_olhar')
    if micro:falando['olhares']={pose['img']:micro['img']}
    s2={'start':4,'end':8,'scene':'entrada','corte_intencional':True,'imagens':{'fundo':'fundo_entrada_v1','personagens':[falando],
         'aproximar':0,'balanco':0,'camera_ilustrada':{'plano':'medio','alvo':'lucas'},
         'camadas_cenario':[{'id':'luz_abrigo','tipo':'luz','plano':'fundo','opacidade':.08,'cor':[245,184,92],'pulsar':.08}]}}
    cenas=[{'personagens':[{'id':'lucas'}],'falas':[]},
           {'personagens':[{'id':'lucas'}],'falas':[{'personagem':'lucas','texto':'Olha!','audio':'audio/lucas_olha.wav','inicio':.5,'intencao':'alertar'},
                                                  {'personagem':'lucas','texto':'Olha!','audio':'audio/lucas_olha.wav','inicio':2.1,'intencao':'perguntar'}]}]
    historia=preparar({'cenas':cenas},BASE,previa=True)
    eventos,vozes,clips,subs=compilar(historia['cenas'],[s1,s2],BASE,BASE)
    falando['gestos']=[g for e in eventos for g in gestos(e)]
    spec={'fps':24,'preview_size':[432,768],'total':8,'loop':False,'narrado':False,
          'voices':vozes,'clips':clips,'subs':subs,'dialogue_events':eventos,'shots':[s1,s2],
          'nota':'Demonstração com voz de teste existente; não é gravação final nem episódio de série.'}
    destino=BASE/'fluidez_demo_v1.json'
    destino.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(destino)


if __name__=='__main__':preparar_demo()
