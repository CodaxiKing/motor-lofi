"""Compara a ampliação de um atlas pequeno com arte dedicada por plano."""
import copy,json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lofi.historias_ilustradas import carregar
from lofi.imagens import quadro
from lofi.qualidade_visual import analisar
BASE=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def preparar():
    cat=carregar()
    def ator(id):
        p=cat['personagens'][id];f=p['composicao'];pose=p['poses']['neutro']
        return {'id':id,'img':pose['img'],'referencia_escala':pose['img'],'ancora':pose['ancora'],
                'pos':.5,'chao':.9,'altura':.50*f['escala_relativa'],'altura_m':f['altura_m'],
                'marcos_camera':f['marcos_camera'],'piscar':False,'respirar':0,'orientacao':'manual','espelhar':False,
                'animacoes_quadros':[{'ciclo':f['ciclos_quadros']['parado'],'inicio':0,'fim':20,'modo':'uma_vez'}]}
    def shot(a,b,p,plano='close',qualidade=None):
        cfg={'fundo':'fundo_entrada_v1','personagens':[p],'camera_ilustrada':{'plano':plano,'alvo':p['id']},'aproximar':0,'balanco':0}
        if qualidade is not None:cfg['qualidade_visual']=qualidade
        return {'start':a,'end':b,'imagens':cfg}
    antes=ator('lucas');antes['usar_variantes']=False
    shots=[shot(0,2,antes,qualidade={'limitar_zoom':False}),shot(2,4,ator('lucas')),
           shot(4,6,dict(ator('lucas'),expressao='medo'))]
    for i,id in enumerate(['teo','clara','amanha','mimico']):shots.append(shot(6+i*1.5,7.5+i*1.5,ator(id)))
    for i,acao in enumerate(['andar','correr']):
        p=ator('lucas');p['animacoes_quadros']=[{'ciclo':cat['personagens']['lucas']['composicao']['ciclos_quadros'][acao],'inicio':0,'fim':2,'modo':'loop'}]
        shots.append(shot(12+i*2,14+i*2,p,'inteiro'))
    spec={'fps':24,'preview_size':[432,768],'total':16,'narrado':True,'loop':False,'shots':shots}
    (BASE/'nitidez_demo_v1.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    painel=Image.new('RGB',(1080,1000),(12,16,24));draw=ImageDraw.Draw(painel)
    try:font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',21)
    except OSError:font=ImageFont.load_default()
    for i,(label,t) in enumerate([('ATLAS PEQUENO AMPLIADO',.7),('RETRATO HD AUTOMÁTICO',2.7)]):
        sh=next(s for s in shots if s['start']<=t<s['end']);diag=[]
        im=quadro(sh,t,str(BASE),(540,960),diagnostico=diag)
        draw.text((i*540+14,10),label,font=font,fill='white');painel.paste(im,(i*540,40))
        print(label,diag)
    painel.save(BASE/'nitidez_comparacao_v1.png')
    report=analisar(spec,BASE)
    (BASE/'nitidez_revisao_v1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':preparar()
