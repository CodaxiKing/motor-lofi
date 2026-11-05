"""Biblioteca de personagens recortados por pose para o renderizador de imagens.

python -m lofi.recortes validar series/visto-amanha/lucas_recortes_v1.json
python -m lofi.recortes aplicar episodio.json biblioteca.json saida.json
"""
import copy
import json
from pathlib import Path
from PIL import Image


def carregar(caminho):
    caminho = Path(caminho).resolve()
    biblioteca = json.loads(caminho.read_text(encoding='utf-8'))
    if not biblioteca.get('personagem') or not biblioteca.get('poses'):
        raise ValueError('Biblioteca precisa de personagem e poses')
    return biblioteca


def validar(caminho):
    caminho = Path(caminho).resolve()
    biblioteca = carregar(caminho)
    achados = []
    for pose, ficha in biblioteca['poses'].items():
        nome = ficha.get('img', '')
        if not nome or Path(nome).name != nome or '/' in nome or '\\' in nome:
            achados.append(f'{pose}: nome de imagem inválido')
            continue
        imagem = caminho.parent / 'imagens' / (nome + '.png')
        if not imagem.is_file():
            achados.append(f'{pose}: imagem ausente: {imagem.name}')
            continue
        with Image.open(imagem) as im:
            if 'A' not in im.getbands() or im.getchannel('A').getextrema()[0] == 255:
                achados.append(f'{pose}: precisa de transparência real')
            elif im.getchannel('A').getextrema()[1] == 0:
                achados.append(f'{pose}: imagem totalmente transparente')
        ancora = ficha.get('ancora', [.5, 1])
        if not isinstance(ancora, list) or len(ancora) != 2 or not all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in ancora):
            achados.append(f'{pose}: âncora inválida')
    return achados


def personagem(biblioteca, pose='neutro', **opcoes):
    if pose not in biblioteca['poses']:
        raise ValueError(f'Pose não disponível: {pose}; gere um recorte específico')
    ficha = biblioteca['poses'][pose]
    p = {'img': ficha['img'], 'altura': .75, 'ancora': ficha.get('ancora', [.5, 1]),
         'ancoras': {f['img']: f.get('ancora', [.5, 1]) for f in biblioteca['poses'].values()},
         'piscar': False, **opcoes}
    if pose == 'neutro' and 'falando' in biblioteca['poses']:
        p['bocas'] = {ficha['img']: biblioteca['poses']['falando']['img']}
    return p


def aplicar(episodio, biblioteca):
    """Opt-in: não modifica o episódio original e recusa ações sem arte correspondente."""
    ep = copy.deepcopy(episodio)
    quem = biblioteca['personagem']
    def converter(shot):
        pessoas = []
        for a in shot.get('actors', []):
            if a['char'] != quem:
                raise ValueError(f'Falta biblioteca de recortes de {a["char"]}')
            pose = 'neutro'
            if a.get('prop') == 'phone': pose = 'celular'
            elif a.get('pose') == 'open_door': pose = 'macaneta'
            elif a.get('emotion') in ('fear', 'shock'): pose = 'medo'
            elif a.get('pose', 'idle') not in ('idle', 'ouvir', 'pensativo', 'scared', 'cross'):
                raise ValueError(f'Ação {a["pose"]} precisa de recorte próprio; nenhuma pose será improvisada')
            if a.get('walk') or a.get('run'):
                raise ValueError('Andar/correr precisa de poses próprias; recorte parado não é ciclo de caminhada')
            x = a.get('x', 540)
            if not isinstance(x, (int, float)):
                raise ValueError('Trajetória animada exige direção manual dos recortes')
            voz = a.get('voice', quem) if a.get('lipsync', True) and not ep.get('narrado') else None
            pessoas.append(personagem(biblioteca, pose, pos=x / 1080, fala=voz))
        fundo = biblioteca.get('fundos', {}).get(shot.get('scene'))
        if not fundo:
            raise ValueError(f'Falta fundo ilustrado para {shot.get("scene")}; registre em fundos na biblioteca')
        shot['imagens'] = {'fundo': fundo, 'personagens': pessoas, 'aproximar': .3, 'balanco': .25}
    for shot in ep.get('shots', []):
        if shot.get('type') == 'choice':
            for lado in ('a', 'b'): converter(shot[lado])
        elif shot.get('type', 'scene') == 'scene':
            converter(shot)
    ep['character_rendering'] = 'cutout_poses'
    return ep


def demo(biblioteca):
    ordem = [p for p in ('neutro', 'celular', 'falando', 'medo', 'macaneta') if p in biblioteca['poses']]
    p = personagem(biblioteca)
    p['poses'] = [[i * 2.5, biblioteca['poses'][pose]['img']] for i, pose in enumerate(ordem)]
    p['fala'] = biblioteca['personagem']
    return {'out': biblioteca['personagem'] + '_recortes_preview.mp4', 'fps': 24,
            'total': len(ordem)*2.5, 'modo_redes': False, 'loop': False, 'bloom': False,
            'character_rendering': 'cutout_poses', 'purpose': 'teste visual de poses, não episódio narrativo',
            'shots': [{'start': 0, 'end': len(ordem)*2.5, 'imagens': {'personagens': [p],
                        'aproximar': 0, 'balanco': 0}}], 'voices': {}, 'clips': [], 'subs': []}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('validar'); p.add_argument('biblioteca')
    p = sub.add_parser('demo'); p.add_argument('biblioteca'); p.add_argument('saida')
    p = sub.add_parser('aplicar'); p.add_argument('episodio'); p.add_argument('biblioteca'); p.add_argument('saida')
    args = parser.parse_args()
    problemas = validar(args.biblioteca)
    if problemas:
        for problema in problemas: print('[ERRO]', problema)
        raise SystemExit(1)
    if args.command == 'validar':
        print('Biblioteca de recortes válida')
    else:
        destino = Path(args.saida).resolve()
        if destino.exists(): raise FileExistsError(destino)
        if destino.parent != Path(args.biblioteca).resolve().parent:
            raise ValueError('Salve ao lado da biblioteca para preservar caminhos de imagens')
        if args.command == 'aplicar' and Path(args.episodio).resolve().parent != destino.parent:
            raise ValueError('Episódio, biblioteca e saída devem ficar na mesma pasta para preservar caminhos de áudio e assets')
        dados = demo(carregar(args.biblioteca)) if args.command == 'demo' else aplicar(
            json.loads(Path(args.episodio).read_text(encoding='utf-8')), carregar(args.biblioteca))
        destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(destino)
