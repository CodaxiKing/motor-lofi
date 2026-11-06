"""Prepara cenas de revisão da biblioteca; vídeos são exportados separadamente."""
import copy
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lofi.historias_ilustradas import carregar

BASE=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def preparar():
    cat=carregar()
    def ator(id,acoes,altura=None):
        p=cat['personagens'][id];f=p['composicao']
        if altura is None:altura=cat['cenarios']['entrada']['mapa_composicao']['zonas']['frente']['altura']
        return {'id':id,'img':p['poses']['neutro']['img'],'pos':.5,'altura':altura*f['altura_m']/1.7,'chao':.94,
                'orientacao':'manual','espelhar':False,'piscar':False,'respirar':0,
                'animacoes_quadros':[dict(inicio=a,fim=b,ciclo=f['ciclos_quadros'][acao],modo=modo,**extra)
                                     for acao,a,b,modo,extra in acoes]}
    def shot(start,end,fundo,pessoas,**cfg):
        return {'start':start,'end':end,'imagens':dict(fundo=fundo,personagens=pessoas,aproximar=0,balanco=0,plano='aberto',**cfg)}
    def salvar(nome,shots,size=(432,768)):
        spec={'fps':24,'size':list(size),'total':shots[-1]['end'],'narrado':True,'loop':False,'shots':shots}
        (BASE/(nome+'.json')).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    humanos=[]
    acoes=[('andar',0,1,'loop',{}),('correr',1,2,'loop',{}),
           ('levantar_braco',2,3,'loop',{'velocidade':2.5}),
           ('agachar',3,4,'uma_vez',{}),('levantar',4,5.01,'uma_vez',{})]
    for i,id in enumerate(['lucas','teo','clara','amanha']):
        humanos.append(shot(i*5,(i+1)*5,'fundo_entrada_v1',[ator(id,acoes)]))
    salvar('expansao_elenco_demo_v2',humanos)
    esconder=[]
    for i,(camera,id) in enumerate([('esquerda','lucas'),('direita','clara'),('baixo','teo')]):
        p=ator(id,[('agachar',0,2.5,'uma_vez',{}),('levantar',2.5,4.01,'uma_vez',{})],.46)
        p['chao']=.91
        # Chest/cabinet stand on the same floor and cover the lowered silhouette.
        obj=copy.deepcopy(cat['objetos']['bau' if i!=1 else 'armario_baixo'])
        obj.update(x=.5,y=.94-.34/2,altura=.34)
        esconder.append(shot(i*4,(i+1)*4,'fundo_entrada_'+camera+'_v2',[p],frente=[obj]))
    salvar('expansao_esconder_demo_v2',esconder)
    criatura=[('andar',0,1.2,'loop',{}),('correr',1.2,2.4,'loop',{}),
              ('levantar_braco',2.4,3.6,'loop',{'velocidade':2}),('agachar',3.6,4.6,'uma_vez',{}),
              ('levantar',4.6,5.6,'uma_vez',{}),('espreitar',5.6,7.1,'loop',{}),('avancar',7.1,9.01,'uma_vez',{})]
    salvar('expansao_criatura_demo_v2',[shot(0,9,'fundo_entrada_v1',[ator('mimico',criatura,.59)])],size=(768,768))


if __name__=='__main__':preparar()
