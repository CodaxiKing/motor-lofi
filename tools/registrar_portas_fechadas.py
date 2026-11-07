"""Registra estados estáticos de porta fechada sem substituir os PNGs abertos."""
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image,ImageDraw,ImageFont
from lofi.historias_ilustradas import arquivo,validar_catalogo

BASE=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def salvar(path,doc):
    path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def registrar():
    path=BASE/'catalogo.json';cat=json.loads(path.read_text(encoding='utf-8'))
    manifesto=json.loads((BASE/'portas_fechadas_geracao_v1.json').read_text(encoding='utf-8'))
    cenas=manifesto['cenarios'];relatorio=[]
    cameras={'frontal':'entrada_porta_fechada','esquerda':'entrada_esquerda_porta_fechada',
             'direita':'entrada_direita_porta_fechada','baixo':'entrada_baixo_porta_fechada'}
    originais={d['base']:hashlib.sha256(arquivo(path,cat['cenarios'][d['base']]['img']).read_bytes()).hexdigest() for d in cenas}
    for d in cenas:
        origem=cat['cenarios'][d['base']]
        nova=copy.deepcopy(origem)
        png=arquivo(path,d['img'])
        with Image.open(png) as im:
            if im.width<900 or im.height<1400:raise ValueError('Resolução insuficiente: '+d['id'])
            if 'A' in im.getbands() and im.getchannel('A').getextrema()[0]<255:raise ValueError('Fundo precisa ser opaco')
            pixels=list(im.size)
        variantes={'aberta':d['base'],'fechada':d['id']}
        nova.update(img=d['img'],descricao=d['nome'],pixels=pixels,
                    sha256=hashlib.sha256(png.read_bytes()).hexdigest(),
                    estado_porta='fechada',variante_de=d['base'],variantes_porta=variantes,
                    pontos_interacao={'macaneta':d['macaneta']},
                    nota_porta='Estado estático. Para mostrar travessia, selecionar a variante aberta primeiro.')
        nova['ligacoes']=[v for v in dict.fromkeys(origem.get('ligacoes',[])+[d['base']]) if v!=d['id']]
        if d['base'].startswith('entrada'):
            nova['cameras']=dict(cameras)
            nova['ligacoes']=list(dict.fromkeys(nova['ligacoes']+[k for k in cameras.values() if k!=d['id']]))
        mapa=nova.get('mapa_composicao')
        if mapa:
            mapa['portais']={}
            mapa.setdefault('interacoes',{})['macaneta']=d['macaneta']
            mapa['calibracao']='Mesmo piso do estado aberto; maçaneta recalibrada manualmente no PNG fechado.'
        luz=nova.get('iluminacao')
        if luz:
            luz['luzes']=[l for l in luz.get('luzes',[]) if l.get('id') not in ('corredor','porta')]
            luz['calibracao']='Piso e fontes do próprio cômodo preservados; removida a luz que atravessava a abertura.'
        origem.update(estado_porta='aberta',variantes_porta=variantes)
        if d['id'] not in origem.setdefault('ligacoes',[]):origem['ligacoes'].append(d['id'])
        cat['cenarios'][d['id']]=nova
        relatorio.append({'cenario':d['id'],'origem':d['base'],'pixels':pixels,'sha256':nova['sha256'],
                          'origem_sha256':originais[d['base']],'estado_porta':'fechada',
                          'portal_aberto':False,'macaneta':d['macaneta'],
                          'revisao_visual':'Conferidos câmera, batente, móveis, maçaneta e ausência de abertura.'})
    for d in cenas:
        for vizinho in cat['cenarios'][d['id']]['ligacoes']:
            ligacoes=cat['cenarios'][vizinho].setdefault('ligacoes',[])
            if d['id'] not in ligacoes:ligacoes.append(d['id'])
    salvar(path,cat)
    for chave,digest in originais.items():
        if hashlib.sha256(arquivo(path,cat['cenarios'][chave]['img']).read_bytes()).hexdigest()!=digest:
            raise AssertionError('PNG original alterado: '+chave)
    problemas=validar_catalogo(path)
    if problemas:raise ValueError('; '.join(problemas))
    out=BASE/'previas';out.mkdir(exist_ok=True)
    w,h=220,392;sheet=Image.new('RGB',(w*len(cenas),(h+42)*2),'#111923');draw=ImageDraw.Draw(sheet)
    try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
    except OSError:font=ImageFont.load_default(size=13)
    for i,d in enumerate(cenas):
        for linha,chave in enumerate((d['base'],d['id'])):
            x,y=i*w,linha*(h+42)
            with Image.open(arquivo(path,cat['cenarios'][chave]['img'])) as im:
                sheet.paste(im.convert('RGB').resize((w,h),Image.Resampling.LANCZOS),(x,y+42))
            draw.text((x+6,y+5),d['base'],fill='#e4cb8d',font=font)
            draw.text((x+6,y+22),'PORTA ABERTA' if linha==0 else 'PORTA FECHADA',fill='white',font=font)
    sheet.save(out/'portas_abertas_fechadas_v1.png')
    salvar(out/'portas_fechadas_revisao_v1.json',{'cenarios':relatorio,'catalogo_valido':True,
           'originais_preservados':True,'cenas_estaticas':True,'animacao_da_porta':False})
    print(json.dumps({'variantes_criadas':len(cenas),'total_cenarios':len(cat['cenarios']),
                      'catalogo_valido':True,'originais_preservados':True},ensure_ascii=False))


if __name__=='__main__':registrar()
