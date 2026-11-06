"""Revisa proporção do protagonista em relação ao elenco e à porta."""
import json
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lofi.historias_ilustradas import carregar
from lofi.imagens import quadro

BASE=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def preparar():
    c=carregar();pessoas=[]
    referencia=c['cenarios']['entrada']['mapa_composicao']['zonas']['frente']['altura']
    for id,x in [('lucas',.34),('teo',.70)]:
        p=c['personagens'][id];f=p['composicao'];pose=p['poses']['neutro']
        pessoas.append({'id':id,'img':pose['img'],'ancora':pose['ancora'],'pos':x,
                        'altura':referencia*f['escala_relativa'],'altura_m':f['altura_m'],
                        'chao':.90,'piscar':False,'respirar':0,'orientacao':'centro',
                        'direcao_original':f.get('direcao_original','direita')})
    spec={'fps':24,'preview_size':[432,768],'total':3,'narrado':True,'loop':False,
          'shots':[{'start':0,'end':3,'imagens':{'fundo':'fundo_entrada_v1','personagens':pessoas,'plano':'aberto','aproximar':0,'balanco':0}}]}
    (BASE/'altura_protagonista_demo_v1.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    im=quadro(spec['shots'][0],1,str(BASE),(432,768))
    out=Image.new('RGB',(432,808),(12,16,24));out.paste(im,(0,40));draw=ImageDraw.Draw(out)
    try:font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',18)
    except OSError:font=ImageFont.load_default()
    draw.text((15,10),'LUCAS 1,45 m   /   TÉO 1,60 m',font=font,fill='white')
    out.save(BASE/'altura_protagonista_preview_v1.png')


if __name__=='__main__':preparar()
