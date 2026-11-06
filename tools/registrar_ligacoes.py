"""Importa 32 desenhos completos de ligação por personagem, com marcos de mão."""
import copy,json,shutil,sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.registrar_expansao import empacotar_corpos
BASE=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def salvar(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def registrar(id,item):
    pasta=BASE/'imagens'/id;atlas_nome=id+'/ligacoes_atlas_v1';path=BASE/'imagens'/(atlas_nome+'.png')
    with Image.open(item['source']) as raw:
        if 'A' not in raw.getbands() or raw.getchannel('A').getextrema()[0]>10:raise ValueError('Corrija transparência da arte')
    shutil.copyfile(item['source'],pasta/'ligacoes_original_v1.png')
    empacotar_corpos(item['source'],path,32)
    (BASE/f'ligacoes_prompt_{id}_v1.txt').write_text(item['prompt']+'\n',encoding='utf-8')
    with Image.open(path) as im:
        w,h=im.size;lado=w/4;frames=[]
        for i in range(32):
            reg=[i%4/4,i//4/8,(i%4+1)/4,(i//4+1)/8]
            crop=im.crop((round(i%4*lado),round(i//4*lado),round((i%4+1)*lado),round((i//4+1)*lado)))
            a=np.asarray(crop.getchannel('A'));yy,xx=np.where(a>100);bottom=yy.max()+1
            marcos={'linha_solo':bottom/lado}
            head=a[int(yy.min()):round(yy.min()+(bottom-yy.min())*.18)]>100
            hy,hx=np.where(head)
            marcos.update(centro_rosto=[float((hx.min()+hx.max()+1)/2/lado),float((yy.min()+(bottom-yy.min())*.1)/lado)],
                          topo_cabeca=float(yy.min()/lado),largura_rosto=float((hx.max()-hx.min()+1)/lado))
            if i>=24:
                # Only the extended hand at chest/waist height is used for
                # locking; lower frames remain useful approach drawings.
                band=a[round(lado*.25):round(lado*.70)]>100
                ys,xs=np.where(band);tip=xs.max();near=xs>=tip-2
                marcos['mao_d']=[float(tip/lado),float((np.median(ys[near])+round(lado*.25))/lado)]
                marcos['palma_d']=[max(0,marcos['mao_d'][0]-.025),marcos['mao_d'][1]]
            frames.append({'regiao':reg,'ancora':[.5,bottom/lado],'apoio':True,'marcos':marcos})
        first=im.crop((0,0,round(lado),round(lado)));box=first.getchannel('A').point(lambda a:255 if a>100 else 0).getbbox()
        ref=(box[3]-box[1])/lado
    ficha_path=pasta/'personagem.json';f=json.loads(ficha_path.read_text(encoding='utf-8'));trans=f.setdefault('transicoes',{});ciclos=f['ciclos_quadros']
    for j,name in enumerate(['iniciar_andar','acelerar_corrida','frear_corrida','interagir']):
        c={'version':1,'tipo':'corpo_inteiro','atlas':atlas_nome,'fps_quadros':16 if j<3 else 12,
           'aspecto_celula':1,'referencia':{'altura_corpo':ref,'altura_referencia':.98},'frames':frames[j*8:j*8+8],'acao':name}
        path_rel=id+'/'+name+'_v1.json';salvar(BASE/'imagens'/path_rel,c)
        if j<3:
            chave=['parado>andar','andar>correr','correr>parado'][j]
            trans[chave]={'ciclo':path_rel,'duracao':.5}
        else:ciclos['interagir']=path_rel;ciclos['alcancar']=path_rel
        if j==0:
            idle=copy.deepcopy(c);idle.update(frames=[frames[0]],fps_quadros=1,acao='parado')
            idle_path=id+'/parado_ligacoes_v1.json';salvar(BASE/'imagens'/idle_path,idle);ciclos['parado']=idle_path
            stop=copy.deepcopy(c);stop['ordem']=list(range(7,-1,-1));stop_path=id+'/frear_andar_v1.json';salvar(BASE/'imagens'/stop_path,stop)
            trans['andar>parado']={'ciclo':stop_path,'duracao':.5}
    for chave,v in trans.items():
        origem=chave.split('>')[0]
        if origem in ciclos:
            origem_json=json.loads((BASE/'imagens'/ciclos[origem]).read_text(encoding='utf-8'))
            v['periodo_origem']=len(origem_json['frames'])/origem_json['fps_quadros']
    salvar(ficha_path,f)


if __name__=='__main__':
    for id,item in json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')).items():registrar(id,item)
