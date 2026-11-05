"""Elenco, identidade visual determinística e folhas de referência do rig local."""
import copy
import hashlib
import json
import re
import unicodedata
from pathlib import Path


MOVIMENTOS = {
    'equilibrado': {'velocidade': 1.0, 'sway': 1.0, 'breath': 1.0, 'reacao_s': .25, 'postura': 'idle'},
    'contido': {'velocidade': .8, 'sway': .35, 'breath': .6, 'reacao_s': .5, 'postura': 'cross'},
    'energico': {'velocidade': 1.25, 'sway': 1.4, 'breath': 1.2, 'reacao_s': .15, 'postura': 'maos_na_cintura'},
    'cauteloso': {'velocidade': .65, 'sway': .5, 'breath': .85, 'reacao_s': .4, 'postura': 'pensativo'},
}


def normalizar(s):
    return ''.join(c for c in unicodedata.normalize('NFD', str(s).lower())
                   if unicodedata.category(c) != 'Mn')


def identidade(nome):
    """Novo design estável por nome; os presets e fichas travadas têm precedência."""
    digest = hashlib.sha256(nome.encode('utf-8')).digest()
    paleta = ((70, 140, 150), (160, 80, 100), (170, 130, 65), (90, 100, 160), (85, 145, 95))
    return {'top': paleta[digest[0] % len(paleta)], 'body': ('normal', 'tall', 'thin', 'fat')[digest[1] % 4],
            'hair': ('short', 'bob', 'curly', 'long')[digest[2] % 4],
            'top_style': ('shirt', 'hoodie', 'sweater')[digest[3] % 3],
            'face_shape': ('round', 'square')[digest[6] % 2],
            'head_scale': .94 + (digest[4] % 4) * .04, 'torso_scale': .92 + (digest[5] % 4) * .06}


def preparar_elenco(elenco=None, travados=None):
    from .rig import CHARS
    resultado = {}
    for chave, ficha in (elenco or {}).items():
        if chave.startswith('_'):
            continue
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', chave) or not isinstance(ficha, dict):
            raise ValueError('Elenco deve mapear identificadores válidos para fichas')
        p = copy.deepcopy(ficha)
        if not isinstance(p.get('visual', {}), dict) or not isinstance(p.get('aliases', []), list) or not all(isinstance(a, str) for a in p.get('aliases', [])):
            raise ValueError('visual deve ser um objeto e aliases uma lista de nomes')
        if not isinstance(p.get('relacoes', {}), dict) or not all(isinstance(v, str) for v in p.get('relacoes', {}).values()):
            raise ValueError('relacoes deve mapear papéis para identificadores de personagem')
        p.setdefault('nome', chave)
        p.setdefault('aliases', [])
        if chave in ('roberta', 'lia', 'medica', 'executiva', 'bruxa', 'rainha', 'vovo', 'estudante2'):
            p.setdefault('genero', 'feminino')
        elif chave in ('rafa', 'valter', 'soldado', 'executivo', 'vovo2', 'policial', 'cowboy', 'pirata'):
            p.setdefault('genero', 'masculino')
        p.setdefault('movimento', 'equilibrado')
        if p['movimento'] not in MOVIMENTOS:
            raise ValueError(f'Perfil de movimento desconhecido: {p["movimento"]}')
        visual = {**(CHARS[chave] if chave in CHARS else identidade(chave)), **p.get('visual', {}),
                  **(travados or {}).get(chave, {})}
        # A ficha da série continua sendo a autoridade de aparência.
        p['visual'] = visual
        p['identity_hash'] = hashlib.sha256(json.dumps(visual, sort_keys=True).encode()).hexdigest()[:16]
        p['motion'] = dict(MOVIMENTOS[p['movimento']])
        resultado[chave] = p
    return resultado


def carregar_elenco(caminho):
    pasta = Path(caminho).resolve().parent
    dados = json.loads(Path(caminho).read_text(encoding='utf-8'))
    for ficha in dados.values():
        if isinstance(ficha, dict) and ficha.get('referencia'):
            ref = Path(ficha['referencia'])
            ficha['referencia'] = str(ref if ref.is_absolute() else (pasta / ref).resolve())
    return dados


def folha_referencia(chave, ficha, destino):
    """Arte produzida pelo mesmo rig do vídeo, sem serviços externos."""
    from PIL import Image, ImageDraw
    from .rig import render_char, paste_char, LIGHTS
    from .core import font
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagem = Image.new('RGB', (1200, 1200), (240, 238, 230))
    desenho = ImageDraw.Draw(imagem)
    estados = [('front', 'neutral'), ('side', 'neutral'), ('back', 'neutral'), ('3q', 'neutral'),
               ('front', 'happy'), ('front', 'fear'), ('front', 'sad'), ('front', 'angry'), ('front', 'shock')]
    for i, (vista, emocao) in enumerate(estados):
        x, y = (i % 3) * 400, (i // 3) * 400
        sprite, ancora = render_char(chave, view=vista, emotion=emocao, custom=ficha['visual'],
                                     light=LIGHTS['neutra'], scale=.42, sway=0, breath=0)
        paste_char(imagem, sprite, ancora, x + 200, y + 350)
        desenho.text((x + 20, y + 15), f'{chave}: {vista} / {emocao}', fill=(35, 35, 40), font=font('mono', 18))
    imagem.save(destino)
    return str(destino)


def salvar_referencias(episodio, destino):
    destino = Path(destino)
    for chave, ficha in episodio.get('cast', {}).items():
        referencia = ficha.get('referencia')
        if referencia:
            # Referências do usuário são preservadas; ausência é reportada, sem substituição silenciosa.
            ficha['reference_status'] = 'available' if Path(referencia).is_file() else 'missing'
        else:
            ficha['referencia'] = str((destino / f'{chave}.png').resolve())
            folha_referencia(chave, ficha, ficha['referencia'])
            ficha['reference_status'] = 'generated_by_rig'


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='comando', required=True)
    criar = sub.add_parser('criar'); criar.add_argument('destino'); criar.add_argument('nomes', nargs='+')
    folha = sub.add_parser('folha'); folha.add_argument('elenco'); folha.add_argument('personagem'); folha.add_argument('destino')
    args = parser.parse_args()
    if args.comando == 'criar':
        p = Path(args.destino)
        if p.exists(): raise FileExistsError(p)
        dados = preparar_elenco({nome: {} for nome in args.nomes})
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(dados, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    else:
        dados = preparar_elenco(carregar_elenco(args.elenco))
        if Path(args.destino).exists(): raise FileExistsError(args.destino)
        folha_referencia(args.personagem, dados[args.personagem], args.destino)
