"""Prepara comparação de contato/luz e cenas de movimento para revisão."""
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
    c=carregar()
    def ator(id,x,altura=None):
        p=c['personagens'][id];f=p['composicao'];pose=p['poses']['neutro']
        if altura is None:altura=c['cenarios']['entrada']['mapa_composicao']['zonas']['frente']['altura']
        return {'id':id,'img':pose['img'],'ancora':pose['ancora'],'pos':x,
                'altura':altura*f['escala_relativa'],'altura_m':f['altura_m'],
                'chao':.90,'piscar':False,'respirar':0,'orientacao':'centro',
                'direcao_original':f.get('direcao_original','direita')}
    cfg={'fundo':'fundo_entrada_v1','personagens':[ator('lucas',.34),ator('teo',.70)],'plano':'aberto','aproximar':0,'balanco':0}
    shot={'start':0,'end':3,'imagens':cfg}
    antes=copy.deepcopy(shot);antes['imagens']['sombras']=False
    imgs=[('SEM SOMBRAS',quadro(antes,1,str(BASE),(432,768))),('LUZ DO CENÁRIO',quadro(shot,1,str(BASE),(432,768)))]
    # An off-camera lamp from the opposite side demonstrates relighting.
    relit=copy.deepcopy(shot);relit['imagens']['iluminacao']={'ambiente':.22,'luzes':[{'tipo':'pontual','espaco':'tela','posicao':[.06,.82],'altura_m':3.2,'intensidade':1,'suavidade':.45}]}
    imgs.append(('LUZ PELA ESQUERDA',quadro(relit,1,str(BASE),(432,768))))
    painel=Image.new('RGB',(1296,808),(12,16,24));draw=ImageDraw.Draw(painel)
    try:font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',21)
    except OSError:font=ImageFont.load_default()
    for i,(label,im) in enumerate(imgs):draw.text((i*432+14,9),label,font=font,fill='white');painel.paste(im,(i*432,40))
    painel.save(BASE/'sombras_comparacao_v1.png')
    # The lamp sweeps off-camera while the actors retain a stable floor.
    movimento=copy.deepcopy(relit)
    movimento['imagens']['iluminacao']['luzes'][0]['trajeto']={'x':[[0,.06],[1,.06],[2,.94],[3,.94]]}
    walk=json.loads((BASE/'locomocao_quadros_demo_v2.json').read_text(encoding='utf-8'))['shots'][0]
    walk['start']=3;walk['end']=8.4
    jump=json.loads((BASE/'jumpscare_skinwalker_demo_v1.json').read_text(encoding='utf-8'))['shots']
    for s in jump:s['start']+=8.4;s['end']+=8.4
    spec={'fps':24,'preview_size':[432,768],'total':12,'loop':False,'narrado':True,'shots':[movimento,walk]+jump}
    (BASE/'sombras_demo_v1.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':preparar()
