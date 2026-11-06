"""Importa retratos independentes e ciclos com quatro desenhos por folha.

Uso: python tools/registrar_arte_hd.py manifesto.json
Entradas: <id>-<neutro|medo|piscando> e lucas-<andar|correr>-<0|1>.
"""
import copy,json,shutil,sys,filecmp
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lofi.historias_ilustradas import carregar
BASE=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def salvar(path,d):path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def copiar(source,dest):
    if dest.is_file() and filecmp.cmp(source,dest,shallow=False):return
    shutil.copyfile(source,dest)


def rosto(im):
    a=np.asarray(im.getchannel('A'))>100;h,w=a.shape
    # Find the neck below the widest section of the head; exclude shoulders.
    widths=np.array([np.ptp(np.flatnonzero(row))+1 if row.any() else 0 for row in a])
    top=int(np.flatnonzero(widths)[0]);peak=top+int(np.argmax(widths[top:round(h*.48)]))
    neck=next((y for y in range(max(peak+1,round(h*.32)),round(h*.68)) if widths[y]<widths[peak]*.56),round(h*.47))
    yy,xx=np.where(a[top:neck]);return [float(xx.min()/w),top/h,float((xx.max()+1)/w),neck/h]


def importar_retratos(m):
    catalogo=carregar()
    for key,item in m.items():
        if key.startswith('lucas-andar-') or key.startswith('lucas-correr-'):continue
        id,estado=key.split('-',1);pasta=BASE/'imagens'/id/'hd';pasta.mkdir(exist_ok=True)
        nome=id+'/hd/retrato_'+estado+'_v1';dest=BASE/'imagens'/(nome+'.png')
        with Image.open(item['source']) as raw:
            if 'A' not in raw.getbands() or raw.getchannel('A').getextrema()[0]>10:raise ValueError('Retrato sem transparência')
            face=rosto(raw);size=list(raw.size)
        copiar(item['source'],dest)
        (BASE/f'hd_prompt_{key}.txt').write_text(item['prompt']+'\n',encoding='utf-8')
        path=BASE/'imagens'/id/'personagem.json';f=json.loads(path.read_text(encoding='utf-8'));arte=f.setdefault('arte_por_plano',{})
        if estado!='neutro' and 'neutro' in arte.get('close',{}):face=arte['close']['neutro']['rosto']
        base_pose=catalogo['personagens'][id]['poses']['neutro']['img']
        arte.setdefault('close',{})[estado]={'img':nome,'rosto':face,'pixels_origem':size,'cobertura':'retrato','poses_compativeis':[base_pose]}
        if id=='mimico' and estado=='medo':arte['close']['ameaca']=copy.deepcopy(arte['close'][estado])
        if estado=='neutro':
            pose=catalogo['personagens'][id]['poses']['neutro']
            with Image.open(BASE/'imagens'/(pose['img']+'.png')) as src:
                box=src.getchannel('A').point(lambda v:255 if v>30 else 0).getbbox();w,h=src.size;bh=box[3]-box[1]
                marcos=f['marcos_camera'];cx=pose['ancora'][0]*w;cy=box[1]+bh*marcos['centro_rosto'];fw=bh*marcos['largura_rosto']
                half=min(fw*.45,cy,h-cy)
                r=[max(0,(cx-fw/2)/w),(cy-half)/h,min(1,(cx+fw/2)/w),(cy+half)/h]
            arte.setdefault('medio',{})['neutro']={'img':pose['img'],'rosto':r,'pixels_origem':[w,h],'cobertura':'corpo_inteiro','poses_compativeis':[base_pose]}
        salvar(path,f)


def importar_ciclos(m):
    pasta=BASE/'imagens/lucas/hd';pasta.mkdir(exist_ok=True)
    ficha_path=BASE/'imagens/lucas/personagem.json';ficha=json.loads(ficha_path.read_text(encoding='utf-8'))
    for acao in ('andar','correr'):
        if not all('lucas-'+acao+'-'+str(i) in m for i in (0,1)):continue
        frames=[];ref=None;head0=None
        for parte in (0,1):
            key='lucas-'+acao+'-'+str(parte);item=m[key]
            copiar(item['source'],pasta/(acao+'_folha_'+str(parte)+'_v1.png'))
            (BASE/f'hd_prompt_{key}.txt').write_text(item['prompt']+'\n',encoding='utf-8')
            with Image.open(item['source']) as atlas:
                if 'A' not in atlas.getbands() or atlas.getchannel('A').getextrema()[0]>10:raise ValueError('Folha HD sem transparência')
                w,h=atlas.size
                for j in range(4):
                    im=atlas.crop((round(j%2*w/2),round(j//2*h/2),round((j%2+1)*w/2),round((j//2+1)*h/2))).convert('RGBA')
                    a=np.asarray(im.getchannel('A'));ys,xs=np.where(a>100);top=ys.min();bottom=ys.max()+1
                    if ref is None:ref=(bottom-top)/im.height
                    head=a[top:round(top+(bottom-top)*.18)]>100;hy,hx=np.where(head)
                    face=[float((hx.min()+hx.max()+1)/2/im.width),float((top+(bottom-top)*.1)/im.height)]
                    index=parte*4+j;nome='lucas/hd/'+acao+'_'+str(index).zfill(2)+'_v1';dest=BASE/'imagens'/(nome+'.png')
                    if not dest.exists():im.save(dest)
                    frames.append({'img':nome,'ancora':[.5,bottom/im.height],'apoio':not (acao=='correr' and index in (2,6)),
                                   'marcos':{'centro_rosto':face,'topo_cabeca':float(top/im.height),'largura_rosto':float((hx.max()-hx.min()+1)/im.width)}})
        # Flight uses the contact baseline, preserving the drawn airborne gap.
        baseline=float(np.median([fr['ancora'][1] for fr in frames if fr['apoio']]))
        for fr in frames:
            if not fr['apoio']:fr['ancora'][1]=baseline
        nome='lucas/hd/'+acao+'_quadros_v1.json'
        ciclo={'version':2,'tipo':'corpo_inteiro','acao':acao,'fps_quadros':8 if acao=='andar' else 14,
               'aspecto_celula':1,'referencia':{'altura_corpo':ref,'altura_referencia':.98},'frames':frames,
               'deslocamento_corpo_ciclo':.294 if acao=='andar' else .588,'formato':'png_por_quadro'}
        salvar(BASE/'imagens'/nome,ciclo)
        ficha.setdefault('ciclos_anteriores',{}).setdefault(acao,ficha['ciclos_quadros'][acao])
        ficha['ciclos_quadros'][acao]=nome
    salvar(ficha_path,ficha)


if __name__=='__main__':
    m=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'));importar_retratos(m);importar_ciclos(m)
