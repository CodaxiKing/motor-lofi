"""Importa arte gerada e registra ciclos completos sem recortar membros.

Uso: python tools/registrar_expansao.py manifesto.json
O manifesto contém id: {source, prompt}. Mantém os PNGs originais.
"""
import copy
import json
import shutil
import sys
from pathlib import Path
import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parents[1] / 'biblioteca/ilustrada/v1'


def salvar(path, dados):
    path.write_text(json.dumps(dados, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def importar(manifesto):
    catalogo = json.loads((BASE/'catalogo.json').read_text(encoding='utf-8'))
    for nome, item in manifesto.items():
        (BASE/f'expansao_prompt_{nome}.txt').write_text(item['prompt']+'\n',encoding='utf-8')
        if nome.startswith('camera-'):
            angulo=nome.removeprefix('camera-');id='entrada_'+angulo
            img='fundo_'+id+'_v2'
            shutil.copyfile(item['source'], BASE/'imagens'/(img+'.png'))
            lugar=copy.deepcopy(catalogo['cenarios']['entrada'])
            lugar.pop('cameras',None)
            lugar.update(img=img, descricao='Mesmo abrigo; câmera '+angulo, ambiente='entrada',camera=angulo)
            lugar['mapa_composicao']['zonas']={'frente':{'x':[.08,.92],'chao':.94,'altura':.68}}
            lugar['mapa_composicao'].pop('portais',None)
            lugar['mapa_composicao']['interacoes']={}
            lugar['mapa_composicao']['calibracao']='Zona frontal revisada; porta precisa de polígono próprio antes de atravessar'
            lugar['ligacoes']=['entrada','corredor']
            catalogo['cenarios'][id]=lugar
            catalogo['cenarios']['entrada'].setdefault('cameras',{})[angulo]=id
        elif nome=='objetos':
            pasta=BASE/'imagens/objetos';pasta.mkdir(exist_ok=True)
            shutil.copyfile(item['source'],pasta/'esconderijos_atlas_v2.png')
            with Image.open(item['source']) as atlas:
                for i,id in enumerate(['bau','armario_baixo','batente','arvore']):
                    w,h=atlas.size;x=i%2;y=i//2
                    # Generated props use a shorter top row; exclude the next
                    # object's lintel rather than importing a disconnected strip.
                    top,bottom=(0,.44) if y==0 else (.45,1)
                    im=atlas.crop((round(x*w/2),round(top*h),round((x+1)*w/2),round(bottom*h))).convert('RGBA')
                    box=im.getchannel('A').point(lambda v:255 if v>20 else 0).getbbox()
                    if not box:raise ValueError(f'Objeto vazio: {id}')
                    im.crop(box).save(pasta/(id+'_v2.png'))
                    catalogo.setdefault('objetos',{})[id]={'img':'objetos/'+id+'_v2','altura':.4,'x':.5,'y':.74}
        elif nome.startswith('mimico-'):
            registrar_criatura(nome.removeprefix('mimico-'),item)
        else:
            registrar_personagem(nome,item)
    salvar(BASE/'catalogo.json',catalogo)


def registrar_criatura(acao,item):
    pasta=BASE/'imagens/mimico';nome='mimico/'+acao+'_16_atlas_v2'
    shutil.copyfile(item['source'],BASE/'imagens'/(nome+'_original.png'))
    # Atlas import, not new artwork: isolate the sixteen connected whole-body
    # silhouettes before packing. Some generated coats cross nominal cell edges.
    empacotar_corpos(item['source'],BASE/'imagens'/(nome+'.png'))
    item=dict(item,source=str(BASE/'imagens'/(nome+'.png')))
    frames=[]
    with Image.open(item['source']) as atlas:
        if 'A' not in atlas.getbands() or atlas.getchannel('A').getextrema()[0]>10:
            raise ValueError('Atlas de criatura sem transparência')
        w,h=atlas.size
        alpha=np.asarray(atlas.getchannel('A'))
        # Find real empty row gutters: generated sheets are not always an
        # exact uniform grid. Cutting at 25% can sever an otherwise whole foot.
        edges=[0]
        for j in (1,2,3):
            mid=round(j*h/4);radius=round(h*.06);lo=max(0,mid-radius);hi=min(h,mid+radius)
            counts=np.count_nonzero(alpha[lo:hi]>100,axis=1)
            indices=np.flatnonzero(counts==counts.min())
            edges.append(lo+int(np.median(indices)))
        edges.append(h)
        referencia_px=edges[1]-edges[0]
        for i in range(16):
            r=[i%4/4,edges[i//4]/h,(i%4+1)/4,edges[i//4+1]/h]
            im=atlas.crop(tuple(round(v*(w if j%2==0 else h)) for j,v in enumerate(r)))
            box=im.getchannel('A').point(lambda a:255 if a>30 else 0).getbbox()
            if not box:raise ValueError('Quadro vazio da criatura')
            frames.append({'regiao':r,'ancora':[.5,box[3]/im.height],'apoio':True})
    first=atlas_first_box(item['source'],frames[0]['regiao'])
    ciclo={'version':1,'tipo':'corpo_inteiro','atlas':nome,'fps_quadros':12,'acao':acao,
           'grupo':'criaturas','referencia':{'altura_corpo':min(1,first/referencia_px),'altura_referencia':.98,'altura_celula_px':referencia_px},'frames':frames}
    caminho='mimico/'+acao+'_16_corpo_v2.json';salvar(BASE/'imagens'/caminho,ciclo)
    ficha_path=pasta/'personagem.json';ficha=json.loads(ficha_path.read_text(encoding='utf-8'))
    ficha['ciclos_quadros'][acao]=caminho;salvar(ficha_path,ficha)


def empacotar_corpos(source,destino,n_corpos=16):
    from scipy.ndimage import label, find_objects, binary_dilation
    with Image.open(source) as raw:
        raw=raw.convert('RGBA');arr=np.asarray(raw);labels,n=label(arr[:,:,3]>100)
        counts=np.bincount(labels.ravel());slices=find_objects(labels)
        ids=[i for i in range(1,n+1) if counts[i]>1000]
        if len(ids)!=n_corpos:raise ValueError(f'Esperados {n_corpos} corpos conectados; encontrados {len(ids)}')
        ids.sort(key=lambda i:(slices[i-1][0].start+slices[i-1][0].stop)/2)
        ordem=[]
        for row in range(n_corpos//4):ordem+=sorted(ids[row*4:(row+1)*4],key=lambda i:slices[i-1][1].start)
        cortes=[];extent=0;maxh=0
        for k,i in enumerate(ordem):
            ys,xs=slices[i-1];x0=max(0,xs.start-3);x1=min(raw.width,xs.stop+3);y0=max(0,ys.start-3);y1=min(raw.height,ys.stop+3)
            eixo=(k%4+.5)*raw.width/4
            extent=max(extent,eixo-x0,x1-eixo);maxh=max(maxh,y1-y0)
            crop=arr[y0:y1,x0:x1].copy();keep=binary_dilation(labels[y0:y1,x0:x1]==i,iterations=2)
            crop[:,:,3]=np.where(keep,crop[:,:,3],0)
            cortes.append((Image.fromarray(crop),x0-eixo))
        lado=int(max(2*extent,maxh)+24)
        atlas=Image.new('RGBA',(lado*4,lado*(n_corpos//4)))
        for k,(im,dx) in enumerate(cortes):
            atlas.alpha_composite(im,(round((k%4+.5)*lado+dx),(k//4+1)*lado-12-im.height))
        atlas.save(destino)


def atlas_first_box(path,regiao):
    with Image.open(path) as im:
        w,h=im.size;im=im.crop(tuple(round(v*(w if j%2==0 else h)) for j,v in enumerate(regiao)))
        b=im.getchannel('A').point(lambda a:255 if a>100 else 0).getbbox()
        return b[3]-b[1]


def registrar_personagem(id,item):
    pasta=BASE/'imagens'/id
    n=8 if id=='lucas' else 48 if id=='mimico' else 32
    atlas_nome=id+'/movimentos_corpo_atlas_v2'
    shutil.copyfile(item['source'],BASE/'imagens'/(atlas_nome+'.png'))
    acoes=['agachar'] if id=='lucas' else ['andar','correr','levantar_braco','agachar']
    if id=='mimico':acoes+=['espreitar','avancar']
    with Image.open(item['source']) as atlas:
        if 'A' not in atlas.getbands() or atlas.getchannel('A').getextrema()[0]>10:
            raise ValueError(f'Atlas sem fundo realmente transparente: {id}')
        w,h=atlas.size;linhas=n//4;altura_celula=h/linhas
        caixas=[]
        for i in range(n):
            regiao=[(i%4)/4,(i//4)/linhas,(i%4+1)/4,(i//4+1)/linhas]
            im=atlas.crop(tuple(round(v*(w if j%2==0 else h)) for j,v in enumerate(regiao))).convert('RGBA')
            arr=np.asarray(im.getchannel('A'))>30
            yy,xx=np.where(arr)
            if not len(yy):raise ValueError(f'Célula vazia: {id}/{i}')
            caixas.append((regiao,im,(xx.min(),yy.min(),xx.max()+1,yy.max()+1)))
        # Referência física fixa tomada da postura ereta, nunca do agachamento.
        ref=caixas[0];span=(ref[2][3]-ref[2][1])/ref[1].height
        # Ground comes from contact frames, not jump height or raised hands.
        solo=float(np.median([b[2][3]/b[1].height for b in caixas[:8]]))
        if id=='lucas':solo=ref[2][3]/ref[1].height
        ficha_path=pasta/'personagem.json';ficha=json.loads(ficha_path.read_text(encoding='utf-8'))
        ficha.update(preferencia_animacao='quadros',grupo_animacao='criaturas' if id=='mimico' else 'personagens')
        ciclos=ficha.setdefault('ciclos_quadros',{})
        for a,acao in enumerate(acoes):
            frames=[]
            for i in range(a*8,(a+1)*8):
                regiao,im,box=caixas[i]
                apoio=acao not in ('correr','avancar')
                chao=box[3]/im.height if apoio else solo
                frames.append({'regiao':regiao,'ancora':[.5,chao],'apoio':apoio,
                               'marcos':{'linha_solo':solo,'eixo_corpo_x':.5}})
            ciclo={'version':1,'tipo':'corpo_inteiro','atlas':atlas_nome,'fps_quadros':10 if acao=='correr' else 8,
                   'referencia':{'altura_corpo':span,'altura_referencia':.98,'metodo':'Escala fixa da postura ereta; chão virtual constante'},
                   'frames':frames,'grupo':ficha['grupo_animacao'],'acao':acao,
                   'deslocamento_corpo_ciclo':.294 if acao=='andar' else .588 if acao=='correr' else 0}
            if acao=='levantar_braco':ciclo['ordem']=[0,0,1,2,3,4,5,6,7,7,7,7,6,5,4,3,2,1,0,0]
            path=id+'/'+acao+'_corpo_v2.json';salvar(BASE/'imagens'/path,ciclo);ciclos[acao]=path
            if acao=='agachar':
                levantar=copy.deepcopy(ciclo);levantar.update(acao='levantar',ordem=list(range(7,-1,-1)))
                path=id+'/levantar_corpo_v2.json';salvar(BASE/'imagens'/path,levantar);ciclos['levantar']=path
                ciclos['abaixar']=ciclos['agachar'];ciclos['se_esconder']=ciclos['agachar']
        salvar(ficha_path,ficha)


if __name__=='__main__':
    importar(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
