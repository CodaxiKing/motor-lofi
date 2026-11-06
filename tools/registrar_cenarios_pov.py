"""Registra fundos POV existentes e gera uma galeria pelo compositor real."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont
from lofi import imagens

BASE = Path(__file__).resolve().parents[1] / 'biblioteca/ilustrada/v1'


def registrar(manifesto, base=BASE):
    base = Path(base)
    dados = json.loads(Path(manifesto).read_text(encoding='utf-8'))
    path = base/'catalogo.json'
    cat = json.loads(path.read_text(encoding='utf-8'))
    ids = {c['id'] for c in dados['cenarios']}
    for c in dados['cenarios']:
        nome = c['img']
        raiz = (base/'imagens').resolve()
        png = (raiz/(nome+'.png')).resolve()
        if not png.is_relative_to(raiz) or not nome.startswith('cenarios/primeira_pessoa/fundo_'):
            raise ValueError('Cenário deve ficar em cenarios/primeira_pessoa/fundo_*')
        if c['id'] in cat['cenarios'] and cat['cenarios'][c['id']]['img'] != nome:
            raise ValueError('Não substituir cenário existente: '+c['id'])
        with Image.open(png) as im:
            if im.width < 900 or im.height < 1400:
                raise ValueError('Cenário abaixo da resolução mínima')
            if 'A' in im.getbands() and im.getchannel('A').getextrema()[0] < 255:
                raise ValueError('Fundo precisa ser opaco')
            pixels = list(im.size)
        if not set(c.get('ligacoes', [])) <= ids | cat['cenarios'].keys():
            raise ValueError('Ligação desconhecida')
        cat['cenarios'][c['id']] = {
            'img':nome, 'descricao':c['nome'], 'ligacoes':c.get('ligacoes', []),
            'categoria':'dark_cinematic_pov', 'perspectiva':'primeira_pessoa',
            'periodo':'noite', 'pixels':pixels, 'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),
            'camera_altura_m':1.6, 'composicao_observacao':'POV sem corpo do observador; atores externos precisam de blocking próprio.',
            'iluminacao':c['iluminacao'],
        }
    path.write_text(json.dumps(cat, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return dados


def previa(dados, base=BASE):
    base = Path(base)
    folha = Image.new('RGB', (1080, 1024), '#080b10')
    draw = ImageDraw.Draw(folha)
    try: font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 15)
    except OSError: font = ImageFont.load_default(size=15)
    shots = []
    for i, c in enumerate(dados['cenarios']):
        cfg = {'fundo':c['img'], 'personagens':[], 'perspectiva':'primeira_pessoa', 'aproximar':0, 'balanco':0}
        shot = {'start':i*3, 'end':(i+1)*3, 'imagens':cfg}
        shots.append(shot)
        x, y = i%4*270, i//4*512
        folha.paste(imagens.quadro(shot, i*3, base, (270,480)), (x,y+32))
        draw.text((x+6,y+8), c['nome'].split(' — ')[0], font=font, fill='#e1d1b8')
    pasta = base/'previas'
    pasta.mkdir(exist_ok=True)
    destino = pasta/'primeira_pessoa_v1.png'
    folha.save(destino)
    spec = {'fps':24, 'size':[432,768], 'total':len(shots)*3, 'narrado':True, 'loop':False, 'shots':shots}
    (base/'primeira_pessoa_demo_v1.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(destino)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifesto', type=Path)
    args = parser.parse_args()
    previa(registrar(args.manifesto))
