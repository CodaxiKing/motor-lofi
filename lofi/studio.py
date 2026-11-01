"""Orquestração offline, auditável e independente de provedores para a skill.

Não invoca serviços pagos, não fabrica áudio/vídeo e não altera fichas travadas.
"""
import json
import re
from pathlib import Path
from .autodirect import compile_story
from .asset_plan import build_asset_manifest
from .continuity import validate_episode

CAPABILITIES = ('python', 'ffmpeg', 'image_generation', 'speech_generation', 'sound_generation', 'mcp')

def detect_capabilities():
    import shutil
    return {'python': True, 'ffmpeg': bool(shutil.which('ffmpeg')),
            'image_generation': False, 'speech_generation': False,
            'sound_generation': False, 'mcp': False}

def read_bible(series_dir):
    series_dir = Path(series_dir)
    result = {}
    for name in ('serie', 'personagens', 'cenarios', 'acontecimentos', 'estilo_visual', 'continuidade'):
        path = series_dir / (name + '.json')
        if path.exists():
            result[name] = json.loads(path.read_text(encoding='utf-8'))
    return result

def initialize_series(series_dir, title, *, visual_style='horror_illustrated'):
    folder = Path(series_dir)
    folder.mkdir(parents=True, exist_ok=True)
    defaults = {'serie': {'title': title, 'last_episode': 0, 'branches': {}},
                'personagens': {}, 'cenarios': {}, 'acontecimentos': [],
                'estilo_visual': {'profile': visual_style, 'notes': 'Preservar aparência entre episódios'},
                'continuidade': {'facts': [], 'open_threads': [], 'decisions': {}}}
    for name, value in defaults.items():
        path = folder / (name + '.json')
        if not path.exists():
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (folder / 'episodios').mkdir(exist_ok=True)
    return read_bible(folder)

def _text_units(story):
    return [x.strip() for x in re.split(r'(?<=[.!?])\s+|\n+', story) if x.strip()]

def quality_report(episode, *, story='', bible=None, capabilities=None, episode_path=None):
    bible = bible or {}
    capabilities = capabilities if capabilities is not None else detect_capabilities()
    shots = episode.get('shots', [])
    findings = []
    def add(level, code, message):
        findings.append({'severity': level, 'code': code, 'message': message})
    if not shots: add('error', 'no_shots', 'Nenhum plano gerado')
    for i, shot in enumerate(shots):
        if shot.get('end', 0) <= shot.get('start', 0):
            add('error', 'bad_duration', f'Plano {i}: duração inválida')
        if i and abs(shot['start'] - shots[i-1]['end']) > .05:
            add('error', 'timeline_gap', f'Plano {i}: lacuna/sobreposição temporal')
    if len(shots) >= 3:
        kinds = [s.get('director_notes', {}).get('shot') for s in shots]
        if len(set(kinds)) == 1:
            add('warning', 'repetitive_camera', 'Todos os planos usam o mesmo enquadramento')
    for name, available in capabilities.items():
        if name in ('speech_generation', 'image_generation') and not available:
            add('info', f'{name}_unavailable', f'{name}: requer ferramenta externa opcional')
    if not episode.get('voices'):
        add('warning', 'no_voices', 'Narração não associada; não declarar áudio pronto')
    if not episode.get('subs'):
        add('warning', 'no_subtitles', 'Legendas não sincronizadas')
    if episode_path:
        for issue in validate_episode(episode_path):
            add('warning', 'continuity', issue)
    return {'ok': not any(f['severity'] == 'error' for f in findings),
            'shots': len(shots), 'duration': episode.get('total', 0),
            'findings': findings, 'rendered_video': False,
            'notes': 'Relatório estático; não comprova renderização, voz ou sincronização.'}

def plan_episode(story, *, series_dir, episode_number=1, branch=None, actor='roberta', scene='apartamento', mode='hybrid', duration=None):
    if mode not in ('automatic', 'professional', 'hybrid'):
        raise ValueError('Modo deve ser automatic, professional ou hybrid')
    folder = Path(series_dir)
    bible = read_bible(folder)
    if not bible.get('serie'):
        raise ValueError('Série não inicializada: execute init antes')
    if branch and branch not in bible.get('continuidade', {}).get('decisions', {}):
        raise ValueError(f'Ramo {branch} não existe nas decisões registradas')
    style = bible.get('estilo_visual', {}).get('profile', 'horror_illustrated')
    ep = compile_story(story, title=bible['serie']['title'], episode=episode_number,
                       actor=actor, scene=scene, visual_profile=style, duration=duration)
    ep['studio'] = {'mode': mode, 'branch': branch, 'source_story': story,
                    'requires_review': True, 'auto_generated': True}
    # Preserve human-editable episode and never silently rewrite series memory.
    ep_path = folder / 'episodios' / f'ep{episode_number:02d}.json'
    ep_path.parent.mkdir(parents=True, exist_ok=True)
    if ep_path.exists():
        raise FileExistsError(f'Episódio já existe: {ep_path}; edite manualmente ou escolha outro número')
    ep_path.write_text(json.dumps(ep, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    assets = build_asset_manifest(ep)
    asset_path = ep_path.with_suffix('.assets.json')
    asset_path.write_text(json.dumps(assets, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    report = quality_report(ep, story=story, bible=bible, episode_path=ep_path)
    report_path = ep_path.with_suffix('.quality.json')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return {'episode': str(ep_path), 'assets': str(asset_path), 'quality': str(report_path),
            'status': 'draft_needs_review', 'report': report}

def commit_continuity(series_dir, *, episode_number, facts=None, open_threads=None, choice=None):
    """Atualização explícita após revisão humana; nunca acontece durante plan_episode."""
    folder = Path(series_dir)
    bible = read_bible(folder)
    if not bible.get('serie'):
        raise ValueError('Série não inicializada')
    if not (folder / 'episodios' / f'ep{episode_number:02d}.json').exists():
        raise ValueError('Episódio não encontrado')
    cont = bible.get('continuidade', {})
    cont.setdefault('facts', []).extend(facts or [])
    cont.setdefault('open_threads', []).extend(open_threads or [])
    if choice:
        cont.setdefault('decisions', {})[f'ep{episode_number:02d}'] = choice
    (folder / 'continuidade.json').write_text(json.dumps(cont, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    serie = bible['serie']
    serie['last_episode'] = max(serie.get('last_episode', 0), episode_number)
    (folder / 'serie.json').write_text(json.dumps(serie, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return cont
