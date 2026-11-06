"""Compara planos cinematográficos sobre o mesmo personagem e cenário."""
import copy
import json
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lofi.historias_ilustradas import carregar
from lofi.imagens import quadro

BASE=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def preparar():
    c=carregar();p=c['personagens']['lucas'];f=p['composicao'];pose=p['poses']['neutro']
    ator={'id':'lucas','img':pose['img'],'ancora':pose['ancora'],'referencia_escala':pose['img'],
          'pos':.5,'altura':.5,'chao':.94,'piscar':False,'respirar':0,
          'marcos_camera':f['marcos_camera'],'altura_m':f['altura_m'],'escala_relativa':f['escala_relativa']}
    shots=[];samples=[]
    planos=[('inteiro','CORPO INTEIRO'),('americano','PLANO AMERICANO'),('medio','CINTURA PARA CIMA'),('close','CLOSE')]
    for i,(plano,label) in enumerate(planos):
        cfg={'fundo':c['cenarios']['entrada']['img'],'personagens':[copy.deepcopy(ator)],
             'mapa_composicao':c['cenarios']['entrada']['mapa_composicao'],'aproximar':0,'balanco':0,
             'camera_ilustrada':{'plano':plano,'alvo':'lucas','push':.4}}
        shot={'start':i*3,'end':(i+1)*3,'imagens':cfg};shots.append(shot)
        samples.append((label,quadro(shot,i*3+1.5,str(BASE),(432,768))))
    spec={'fps':24,'preview_size':[432,768],'total':12,'narrado':True,'loop':False,'shots':shots}
    (BASE/'camera_planos_demo_v1.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    painel=Image.new('RGB',(432*4,808),(12,16,24));d=ImageDraw.Draw(painel)
    try:font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',21)
    except OSError:font=ImageFont.load_default()
    for i,(label,im) in enumerate(samples):
        d.text((i*432+15,9),label,font=font,fill='white');painel.paste(im,(i*432,40))
    painel.save(BASE/'camera_planos_comparacao_v1.png')


if __name__=='__main__':preparar()
