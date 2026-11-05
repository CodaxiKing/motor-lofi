"""Compilador offline de texto para um episódio técnico compatível com lofi.render.

Não cria vozes nem imagens. Permite edição manual do JSON produzido.
"""
import json
import re
from pathlib import Path
from .director import suggest_shots
from .performance import plan_performance

SCENES = {
    'rua': r'rua|cidade|carro|calçada|avenida|prédio',
    'corredor': r'corredor|hall',
    'apartamento': r'apartamento|casa|quarto|cozinha|janela',
    'hospital': r'hospital|médic|enferm',
    'mercado': r'mercado|supermercado|loja',
    'floresta': r'floresta|árvore|mata',
    'escada': r'escada|degrau',
    'ponte': r'ponte',
    'igreja': r'igreja|altar',
    'metrô': r'metrô|trem|estação',
}
EMOTIONS = ((r'medo|assust|pânico|terror', 'fear'), (r'triste|chor', 'sad'),
            (r'raiva|furios|grit', 'angry'), (r'alegr|sorr|feliz', 'happy'))


def compile_story(story, *, title='NOVA SÉRIE', episode=1, actor='roberta',
                  scene='apartamento', visual_profile='lofi_classic', duration=None,
                  duration_profile=None, opening=None, elenco=None, locked_characters=None, world_state=None):
    """Compila parágrafos/linhas em planos editáveis; sem depender de IA externa.

    O modo profissional consiste em editar as propriedades de cada plano no JSON
    resultante. Campos não definidos não são sobrescritos.
    """
    if not isinstance(story, str) or not story.strip():
        raise ValueError('A história deve conter texto')
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', actor):
        raise ValueError('Identificador de personagem inválido')
    from .visual_profiles import resolve_profile
    resolve_profile(visual_profile)
    from .scenes import REGISTRY
    if scene not in REGISTRY:
        raise ValueError(f'Cenário inicial desconhecido: {scene}')
    from .editorial import estruturar, unidades_visuais
    visual_story = unidades_visuais(story)
    if not visual_story:
        raise ValueError('A história deve conter acontecimentos além dos metadados')
    contrato = None
    if duration_profile is not None:
        from .perfis_duracao import planejar
        estimativa = sum(s['duration_estimate'] for s in suggest_shots(visual_story))
        contrato = planejar(duration_profile, duration, estimativa)
        duration = contrato['alvo_s']
    suggestions = suggest_shots(visual_story, target_duration=duration)
    shots = []
    clock = 0.0
    current_scene = scene
    for item in suggestions:
        line = item['text']
        for candidate, pattern in SCENES.items():
            if re.search(pattern, line, re.I) and candidate in REGISTRY:
                current_scene = candidate
                break
        performance = plan_performance(line)
        emotion = performance['emotion']
        kind = item['shot']
        length = item['duration_estimate']
        end = round(clock + length, 3)
        camera = {'zoom': 1.28 if kind == 'close' else 1.12 if kind == 'detail' else 1.0}
        if kind == 'tracking':
            camera['x'] = [0, 45]
        elif kind == 'wide':
            camera['x'] = [-18, 18]
        shot = {'start': round(clock, 3), 'end': end, 'scene': current_scene,
                'camera': camera, 'actors': [{'char': actor, 'x': 540, 'y': 1650,
                                             'view': 'front', 'emotion': emotion,
                                             'pose': performance['pose'],
                                             'walk': performance['movement'] in ('walk', 'run'),
                                             'run': performance['movement'] == 'run',
                                             'look': performance['look']}],
                'director_notes': {'text': line, 'shot': kind, 'reason': item['reason'],
                                   'sound_cue': item['sound_cue'], 'performance': performance}}
        shots.append(shot)
        clock = end
    if duration is not None:
        shots[-1]['end'] = float(duration)
        clock = float(duration)
    spec = {'out': f'ep{episode:02d}.mp4', 'fps': 30, 'total': round(clock, 3),
            'series_title': title, 'episode': episode, 'episode_title': title,
            'visual_profile': visual_profile, 'voices': {}, 'clips': [], 'subs': [],
            'shots': shots}
    spec['source_story'] = story
    spec['narrative_plan'] = estruturar(story)
    for s in shots:
        texto = s['director_notes']['text']
        s['director_notes']['narrative_roles'] = [papel for papel, evidencias in
            spec['narrative_plan']['batidas'].items() if any(e['texto'] == texto for e in evidencias)]
    if contrato:
        spec['duration_profile'] = contrato['nome']
        spec['duration_plan'] = contrato
        spec['audio_plan'] = {'target_s': spec['total'], 'estimated_s': round(sum(
            len(s['director_notes']['text'].split()) / 3 for s in shots), 2),
            'synced': False}
    # Deslocamento é visível, em vez de apenas movimentar as pernas no mesmo lugar.
    for s in shots:
        a = s['actors'][0]
        performance = s['director_notes']['performance']
        if performance.get('prop'):
            a['prop'] = performance['prop']
        if a['walk']:
            a['x'] = [430, 650]
            a['view'] = 'side'
        if performance['pose'] == 'idle' and performance['emotion'] in ('fear', 'sad', 'angry'):
            a['pose'] = {'fear': 'scared', 'sad': 'chest', 'angry': 'punho'}[performance['emotion']]
    from .encenacao import compor
    compor(spec, story, elenco, locked_characters, world_state)
    escolhas = spec['narrative_plan']['escolhas']
    if all(escolhas.values()) and shots[-1]['end'] - shots[-1]['start'] >= 4:
        import copy
        ultimo = shots[-1]
        fim = ultimo['end']
        ultimo['end'] -= min(6, (fim - ultimo['start']) / 2)
        voto = {'start': ultimo['end'], 'end': fim, 'type': 'choice',
                'end_card': {'t': fim - 1, 'text': f'CONTINUA NO EPISÓDIO {episode + 1}'}}
        for chave, letra in (('a', 'A'), ('b', 'B')):
            voto[chave] = {'label': escolhas[letra], 'scene': ultimo['scene'],
                           'actors': copy.deepcopy(ultimo['actors'])}
        shots.append(voto)
    from .aberturas import gerar, aplicar
    if spec['total'] >= 3:
        spec['opening_variants'] = gerar(spec)
        if opening:
            spec = aplicar(spec, opening)
    elif opening:
        raise ValueError('Abertura exige pelo menos 3 segundos')
    return spec


def write_episode(story_path, output_path, **kwargs):
    text = Path(story_path).read_text(encoding='utf-8')
    from .perfis_duracao import selecionar
    profile, _ = selecionar(text, story_path, kwargs.get('duration_profile'))
    kwargs['duration_profile'] = profile
    from .personagens import carregar_elenco, salvar_referencias
    pasta = Path(story_path).resolve().parent
    if kwargs.get('elenco') is None and (pasta / 'elenco.json').is_file():
        kwargs['elenco'] = carregar_elenco(pasta / 'elenco.json')
    if kwargs.get('locked_characters') is None and (pasta / 'personagens.json').is_file():
        kwargs['locked_characters'] = json.loads((pasta / 'personagens.json').read_text(encoding='utf-8'))
    data = compile_story(text, **kwargs)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    salvar_referencias(data, Path(output_path).with_suffix('.references'))
    Path(output_path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    Path(output_path).with_suffix('.state.json').write_text(json.dumps(data['world_state'], ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    from .dramaturgia import formatar_relatorio
    Path(output_path).with_suffix('.dramaturgia.md').write_text(
        formatar_relatorio(data['narrative_plan']['dramaturgia']), encoding='utf-8')
    return data
