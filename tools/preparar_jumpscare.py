"""Registra salto frontal e retratos completos; monta prévia do skinwalker.

python tools/preparar_jumpscare.py manifesto.json
Manifesto: salto/rosto: {source, prompt}. Arte vem do imagegen integrado.
"""
import json
import shutil
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.signal import butter, sosfilt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lofi import wavio

BASE=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def salvar(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def registrar(tipo,item):
    nome='mimico/jumpscare_'+tipo+'_atlas_v1';dest=BASE/'imagens'/(nome+'.png')
    shutil.copyfile(item['source'],dest)
    (BASE/f'jumpscare_prompt_{tipo}_v1.txt').write_text(item['prompt']+'\n',encoding='utf-8')
    rows=4 if tipo=='salto' else 2;n=rows*4;frames=[]
    with Image.open(dest) as atlas:
        if 'A' not in atlas.getbands() or atlas.getchannel('A').getextrema()[0]>10:
            raise ValueError('Corrija a transparência antes de registrar o susto')
        w,h=atlas.size
        for i in range(n):
            r=[i%4/4,i//4/rows,(i%4+1)/4,(i//4+1)/rows]
            im=atlas.crop(tuple(round(v*(w if j%2==0 else h)) for j,v in enumerate(r)))
            a=np.asarray(im.getchannel('A'));ys,xs=np.where(a>100)
            if not len(ys):raise ValueError('Quadro vazio')
            # Track the spherical face, not the moving hands or the feet.
            top=ys.min();face_band=a[top:round(top+im.height*(.13 if tipo=='salto' else .4))]>100
            fy,fx=np.where(face_band)
            cx=(fx.min()+fx.max()+1)/2/im.width
            cy=(top+im.height*(.095 if tipo=='salto' else .30))/im.height
            frames.append({'regiao':r,'ancora':[float(cx),float(cy)],'apoio':False,'marcos':{'foco':'rosto'}})
    c={'version':1,'tipo':'corpo_inteiro' if tipo=='salto' else 'retrato','acao':'jumpscare_'+tipo,
       'grupo':'criaturas','atlas':nome,'fps_quadros':20 if tipo=='salto' else 12,
       'referencia':{'altura_corpo':1,'altura_referencia':1},'frames':frames}
    if tipo=='salto':c['ordem']=[0]*20+list(range(16))+[15]*4
    else:c['ordem']=[3,4,5,6,7,6,5,7,6,5,6,7,6,5,7,6]
    path='mimico/jumpscare_'+tipo+'_v1.json';salvar(BASE/'imagens'/path,c)
    return path


def som():
    sr=44100;total=3.6;t=np.arange(round(sr*total))/sr;rng=np.random.default_rng(27)
    noise=rng.normal(0,1,t.size)
    grave=sosfilt(butter(3,110,fs=sr,output='sos'),noise)
    whoosh=sosfilt(butter(2,[180,2400],btype='bandpass',fs=sr,output='sos'),noise)
    envelope=np.clip((t-1.22)/.5,0,1)*np.exp(-np.maximum(0,t-1.85)*12)
    hit=np.maximum(0,t-1.85)
    impacto=(np.sin(2*np.pi*(82*hit-18*hit**2))+.7*whoosh)*np.exp(-hit*8)*(t>=1.85)
    out=.06*grave+.20*whoosh*envelope+.43*impacto
    out*=np.minimum(1,t/.1)*np.minimum(1,np.maximum(0,3.1-t)/.2)
    out*=.65/max(.65,float(np.abs(out).max()))
    pasta=BASE/'audio';pasta.mkdir(exist_ok=True);wavio.write(pasta/'jumpscare_skinwalker_v1.wav',out,sr)


def preparar(manifesto):
    ciclos={tipo:registrar(tipo,item) for tipo,item in manifesto.items()}
    p=BASE/'imagens/mimico/personagem.json';f=json.loads(p.read_text(encoding='utf-8'))
    f['ciclos_quadros'].update({'jumpscare_'+k:v for k,v in ciclos.items()})
    f.setdefault('sustos',{})['jumpscare']={'salto':ciclos['salto'],'rosto':ciclos['rosto'],'corte_intencional':True}
    salvar(p,f);som()
    comum={'id':'mimico','img':'mimico/mimico_neutro_v1','pos':.5,'chao':.5,'altura':.38,
           'orientacao':'manual','piscar':False,'respirar':0,'balanco_corpo':0}
    corpo=dict(comum,animacoes_quadros=[{'ciclo':ciclos['salto'],'inicio':0,'fim':1.85,'modo':'uma_vez'}],
               sombra={'chao':[[0,.745],[1.35,.745],[1.65,1.2],[1.85,2]],
                       'elevacao':[[0,0],[1.35,0],[1.6,.10],[1.85,.22]]},
               trajeto={'altura':[[0,.46],[1.17,.46],[1.32,.44],[1.45,.57],[1.6,.85],[1.73,1.3],[1.85,1.8]],
                        'chao':[[0,.35],[1.17,.35],[1.30,.4],[1.55,.46],[1.85,.5]],'pos':[[0,.58],[1.35,.58],[1.85,.5]]})
    rosto=dict(comum,altura=1.1,animacoes_quadros=[{'ciclo':ciclos['rosto'],'inicio':0,'fim':1.15,'modo':'uma_vez'}],
               trajeto={'altura':[[0,1.1],[.13,1.23],[.24,1.4],[.8,1.42],[1.15,1.4]],
                        'pos':[[0,.5],[.13,.485],[.24,.515],[.36,.5],[1.15,.5]]})
    def cfg(p):return {'fundo':'fundo_entrada_v1','personagens':[p],'plano':'aberto','aproximar':0,'balanco':0}
    spec={'fps':30,'preview_size':[432,768],'total':3.6,'loop':False,'narrado':True,
          'production_status':'prévia de susto com efeito sonoro sintético original',
          'voices':{'susto':'audio/jumpscare_skinwalker_v1.wav'},'clips':[{'voice':'susto','src':[0,3.6],'at':0}],
          'shots':[{'start':0,'end':1.85,'imagens':cfg(corpo)},
                   {'start':1.85,'end':3,'corte_intencional':True,'imagens':cfg(rosto)},
                   {'start':3,'end':3.6,'corte_intencional':True,'imagens':{'personagens':[]}}]}
    salvar(BASE/'jumpscare_skinwalker_demo_v1.json',spec)


if __name__=='__main__':preparar(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
