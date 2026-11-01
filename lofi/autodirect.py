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
    'corredor': r'corredor|porta|maçaneta|hall',
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
                  scene='apartamento', visual_profile='lofi_classic', duration=None):
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
    suggestions = suggest_shots(story, target_duration=duration)
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
    return {'out': f'ep{episode:02d}.mp4', 'fps': 30, 'total': round(clock, 3),
            'series_title': title, 'episode': episode, 'episode_title': title,
            'visual_profile': visual_profile, 'voices': {}, 'clips': [], 'subs': [],
            'shots': shots}


def write_episode(story_path, output_path, **kwargs):
    text = Path(story_path).read_text(encoding='utf-8')
    data = compile_story(text, **kwargs)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return data
