"""Registra o estudo visual Crônicas sem alterar o catálogo da biblioteca ilustrada."""
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
from lofi.padrao_personagens import modelo
from lofi.historias_ilustradas import arquivo

RAIZ=Path(__file__).resolve().parents[1]
BASE=RAIZ/'biblioteca/cronicas/v1'


def ler(path):return json.loads(path.read_text(encoding='utf-8'))
def salvar(path,doc):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def registrar():
    original=RAIZ/'biblioteca/ilustrada/v1/catalogo.json'
    antes=hashlib.sha256(original.read_bytes()).hexdigest()
    perfil_path=BASE/'perfis/cronicas_situacional_v1.json';perfil=ler(perfil_path)
    path=BASE/'catalogo.json'
    cat=ler(path) if path.exists() else {'version':1,'nome':'Biblioteca Crônicas',
        'biblioteca':'cronicas','estado_producao':'estudo_visual','padrao_criacao':'padrao_criacao.json',
        'direcao_padrao':'cronicas_situacional_v1','escala_referencia_m':1.70,
        'personagens':{},'cenarios':{},'objetos':{}}
    fundos=ler(BASE/'atlas/geracao_fundos_v1.json')['fundos']
    mapa_ligacoes=[('quarto_janela','quarto_deitado'),('quarto_janela','cozinha_escuta'),
                  ('quarto_janela','portao_dentro'),('portao_dentro','fachada_rua'),
                  ('fachada_rua','rua_alta'),('rua_alta','laje_cidade'),('quarto_janela','laje_cidade')]
    pisos={
        'quarto_janela':[[0,.72],[.38,.61],[.62,.61],[1,.76],[1,1],[0,1]],
        'quarto_deitado':[[0,.42],[1,.42],[1,1],[0,1]],
        'cozinha_escuta':[[0,.95],[1,.95],[1,1],[0,1]],
        'portao_dentro':[[0,.66],[1,.66],[1,1],[0,1]],
        'fachada_rua':[[0,.58],[1,.58],[1,1],[0,1]],
        'laje_cidade':[[0,.51],[1,.51],[1,1],[0,1]],
        'rua_alta':[[.28,.6],[.7,.6],[1,1],[0,1]],
    }
    for f in fundos:
        png=arquivo(path,f['img'])
        with Image.open(png) as im:
            if im.width<900 or im.height<1400:raise ValueError('Fundo com resolução insuficiente')
            if 'A' in im.getbands() and im.getchannel('A').getextrema()[0]<255:raise ValueError('Fundo precisa ser opaco')
            pixels=list(im.size)
        cat['cenarios'][f['id']]={'img':f['img'],'descricao':f['nome'],'pixels':pixels,
            'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'estilo_visual':'cronicas',
            'ligacoes':[b if a==f['id'] else a for a,b in mapa_ligacoes if f['id'] in (a,b)],
            'iluminacao':{'espaco':'cenario','ambiente':.22,'piso':pisos[f['id']],
                'luzes':[{'id':'luz_fraca','tipo':'pontual','posicao':[.6,.72],'altura_m':3,
                          'intensidade':.28,'suavidade':.9}],
                'calibracao':'Inicial para estudo; conferir contatos e luz antes de certificar a cena.'}}
    padrao_path=BASE/'padrao_criacao.json'
    if not padrao_path.exists():
        padrao=ler(RAIZ/'biblioteca/ilustrada/v1/padrao_criacao.json')
        padrao['legados']=[]
        padrao['biblioteca']='cronicas'
        salvar(padrao_path,padrao)
    padrao=ler(padrao_path)
    poses=ler(BASE/'atlas/geracao_mara_v1.json')['poses']
    pessoa=cat['personagens'].setdefault('mara',{'nome':'Mara','tipo':'humano','estado_producao':'estudo_visual',
        'arquivo_ficha':'personagens/mara/personagem.json','poses':{},'microposes':{},'ciclos':{}})
    for f in poses:
        png=arquivo(path,f['img'])
        with Image.open(png) as im:
            if 'A' not in im.getbands() or im.getchannel('A').getextrema()[0]!=0:raise ValueError('Pose precisa de transparência real')
            box=im.getchannel('A').point(lambda a:255 if a>30 else 0).getbbox()
            if not box:raise ValueError('Pose vazia')
            w,h=im.size
        pessoa['poses'][f['pose']]={'img':f['img'],'ancora':[(box[0]+box[2])/2/w,box[3]/h],
            'pixels':[w,h],'caixa_visivel':list(box),'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),
            'descricao':f['nome'],'estado':'pose_estatica'}
    ficha_path=BASE/'imagens/personagens/mara/personagem.json'
    if not ficha_path.exists():
        salvar(ficha_path,{'version':2,'id':'mara','nome':'Mara','altura_m':1.68,
            'tipo_movimento':'humano','padrao_criacao':1,'estado_producao':'rascunho',
            'preferencia_animacao':'quadros','ciclos_quadros':{},'ciclos_direcionais':{},
            'plano_animacao':'personagens/mara/ficha_animacao_planejada.json',
            'visual':{'cabeca':'esfera redonda cinza, olhos pretos simples, sem nariz',
                      'identidade':'Mara original: cabelo preto curto, presilha cobre, jaqueta verde-petróleo'},
            'marcos_camera':{'cintura':.54,'joelhos':.79,'ombros':.3,'centro_rosto':.12,'largura_rosto':.28}})
    plano_path=BASE/'imagens/personagens/mara/ficha_animacao_planejada.json'
    if not plano_path.exists():
        plano=modelo('mara','humano',padrao)
        plano.update(nome='Mara',altura_m=1.68)
        salvar(plano_path,plano)
    for preset in perfil['composicoes'].values():
        if not preset.get('pose'):continue
        pose=pessoa['poses'][preset['pose']];l,t,r,b=pose['caixa_visivel'];w,h=pose['pixels']
        x0,y0,x1,y1=preset['caixa'];escala=min((x1-x0)*720/(r-l),(y1-y0)*1280/(b-t))
        preset['ator']={'id':'mara','pose':preset['pose'],'pos':(x0+x1)/2,
            'altura':h*escala/1280,'chao':(y0+y1)/2+(b-t)*escala/1280/2,
            'orientacao':'manual','espelhar':False,'respirar':0,'balanco_corpo':0}
        preset['caixa_resultante']=[(x0+x1)/2-(r-l)*escala/720/2,(y0+y1)/2-(b-t)*escala/1280/2,
                                   (x0+x1)/2+(r-l)*escala/720/2,(y0+y1)/2+(b-t)*escala/1280/2]
    salvar(perfil_path,perfil)
    salvar(path,cat)
    if hashlib.sha256(original.read_bytes()).hexdigest()!=antes:raise AssertionError('Catálogo original foi alterado')
    print(json.dumps({'biblioteca':str(BASE),'fundos':len(fundos),'poses_mara':len(poses),
                      'estado':cat['estado_producao'],'biblioteca_original':'preservada'},ensure_ascii=False))


if __name__=='__main__':registrar()
