"""Manifesto de assets externos, sem depender de provedor específico de IA."""
import json
from pathlib import Path

def build_asset_manifest(episode):
    if not isinstance(episode, dict):
        raise TypeError('episode deve ser dict')
    scenes = sorted({s['scene'] for s in episode.get('shots', []) if s.get('scene')})
    actors = sorted({a['char'] for s in episode.get('shots', []) for a in s.get('actors', []) if a.get('char')})
    style = episode.get('visual_profile', 'lofi_classic')
    return {'visual_style': style, 'scenes': [
        {'id': sc, 'suggested_filename': f'assets/backgrounds/{sc}.png',
         'prompt': f'2D cartoon background, {sc}, {style}, vertical 9:16, no text, no characters',
         'status': 'optional'} for sc in scenes],
        'characters': [{'id': char, 'status': 'rendered_by_builtin_rig',
                        'reference_prompt': f'Character design sheet of {char}, {style}, consistent proportions, no text'}
                       for char in actors]}

def write_asset_manifest(episode, path):
    result = build_asset_manifest(episode)
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return result
