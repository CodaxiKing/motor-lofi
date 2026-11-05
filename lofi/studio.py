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
    for name in ('serie', 'personagens', 'elenco', 'cenarios', 'acontecimentos', 'estilo_visual', 'continuidade'):
        path = series_dir / (name + '.json')
        if path.exists():
            result[name] = json.loads(path.read_text(encoding='utf-8'))
    return result

def initialize_series(series_dir, title, *, visual_style='horror_illustrated', duration_profile='tradicional'):
    from .perfis_duracao import planejar
    planejar(duration_profile)
    folder = Path(series_dir)
    folder.mkdir(parents=True, exist_ok=True)
    defaults = {'serie': {'title': title, 'last_episode': 0, 'branches': {}, 'duration_profile': duration_profile},
                'personagens': {}, 'elenco': {}, 'cenarios': {}, 'acontecimentos': [],
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
    for f in episode.get('staging_findings', []):
        findings.append(dict(f, severity='warning'))
    for chave, ficha in episode.get('cast', {}).items():
        if ficha.get('reference_status') == 'missing':
            add('warning', 'missing_character_reference', f'Referência ausente: {chave}')
    identidades = {}
    for chave, ficha in episode.get('cast', {}).items():
        ident = ficha.get('identity_hash')
        if ident in identidades:
            add('warning', 'indistinguishable_cast', f'{chave} e {identidades[ident]} têm a mesma identidade visual; revise a silhueta ou o figurino')
        identidades[ident] = chave
    if not shots: add('error', 'no_shots', 'Nenhum plano gerado')
    if episode.get('duration_profile'):
        from .perfis_duracao import planejar
        try:
            contrato = planejar(episode['duration_profile'], episode.get('total'))
            if len([s for s in shots if not s.get('hook') and s.get('type', 'scene') == 'scene']) < contrato['min_cenas']:
                add('warning', 'too_few_shots', f"Perfil pede pelo menos {contrato['min_cenas']} cenas; desenvolva mais acontecimentos")
        except ValueError as exc:
            add('error', 'duration_profile', str(exc))
    if shots and abs(shots[-1].get('end', 0) - episode.get('total', 0)) > .05:
        add('error', 'total_mismatch', 'Fim da timeline difere da duração declarada')
    for falta in episode.get('narrative_plan', {}).get('pendencias', []):
        add('warning', 'narrative_' + falta, f'Revisar estrutura narrativa: {falta} sem evidência no texto')
    from .dramaturgia import avaliar_texto
    fonte = story or episode.get('source_story') or episode.get('studio', {}).get('source_story')
    drama = avaliar_texto(fonte) if fonte else episode.get('narrative_plan', {}).get('dramaturgia', {})
    findings.extend(dict(f, code='drama_' + f['code']) for f in drama.get('findings', []))
    audio = episode.get('audio_plan', {})
    if audio.get('target_s') and audio.get('estimated_s', 0) / audio['target_s'] < .6:
        add('warning', 'insufficient_story', 'Texto insuficiente para o tempo planejado: desenvolva ação/falas ou revise o perfil; não preencher com silêncio')
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
            'findings': findings, 'dramaturgy': drama, 'rendered_video': False,
            'notes': 'Relatório estático; não comprova renderização, voz ou sincronização.'}

def plan_episode(story, *, series_dir, episode_number=1, branch=None, actor='roberta', scene='apartamento', mode='hybrid', duration=None, duration_profile=None, opening='A', elenco=None):
    if mode not in ('automatic', 'professional', 'hybrid'):
        raise ValueError('Modo deve ser automatic, professional ou hybrid')
    folder = Path(series_dir)
    bible = read_bible(folder)
    if not bible.get('serie'):
        raise ValueError('Série não inicializada: execute init antes')
    if branch and branch not in bible.get('continuidade', {}).get('decisions', {}):
        raise ValueError(f'Ramo {branch} não existe nas decisões registradas')
    style = bible.get('estilo_visual', {}).get('profile', 'horror_illustrated')
    from .perfis_duracao import selecionar
    # Metadados explícitos do episódio vencem o padrão da série.
    explicit = duration_profile
    if explicit is None and not re.search(r'Perfil de dura[çc][ãa]o\s*:', story, re.I):
        explicit = bible['serie'].get('duration_profile')
    profile, _ = selecionar(story, folder / 'ep.json', explicit)
    ep = compile_story(story, title=bible['serie']['title'], episode=episode_number,
                       actor=actor, scene=scene, visual_profile=style, duration=duration,
                       duration_profile=profile, opening=opening, elenco=elenco if elenco is not None else bible.get('elenco'),
                       locked_characters=bible.get('personagens'),
                       world_state=bible.get('continuidade', {}).get('world_state'))
    ep['studio'] = {'mode': mode, 'branch': branch, 'source_story': story,
                    'requires_review': True, 'auto_generated': True}
    # Preserve human-editable episode and never silently rewrite series memory.
    ep_path = folder / 'episodios' / f'ep{episode_number:02d}.json'
    ep_path.parent.mkdir(parents=True, exist_ok=True)
    if ep_path.exists():
        raise FileExistsError(f'Episódio já existe: {ep_path}; edite manualmente ou escolha outro número')
    from .personagens import salvar_referencias
    salvar_referencias(ep, ep_path.with_suffix('.references'))
    state_path = ep_path.with_suffix('.state.json')
    state_path.write_text(json.dumps(ep['world_state'], ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    ep_path.write_text(json.dumps(ep, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    assets = build_asset_manifest(ep)
    asset_path = ep_path.with_suffix('.assets.json')
    asset_path.write_text(json.dumps(assets, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    report = quality_report(ep, story=story, bible=bible, episode_path=ep_path)
    report_path = ep_path.with_suffix('.quality.json')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    from .dramaturgia import formatar_relatorio
    drama_path = ep_path.with_suffix('.dramaturgia.md')
    drama_path.write_text(formatar_relatorio(report['dramaturgy']), encoding='utf-8')
    opening_path = ep_path.with_suffix('.openings.json')
    opening_path.write_text(json.dumps({'candidatos': ep.get('opening_variants', []),
                            'selecionada': opening}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    from .experimentos import registrar_variantes
    registrar_variantes(str(folder), episode_number, ep.get('opening_variants', []), opening,
                        'Pacote de abertura escolhido pelo autor; sem previsão de desempenho')
    return {'episode': str(ep_path), 'assets': str(asset_path), 'quality': str(report_path),
            'openings': str(opening_path),
            'dramaturgy': str(drama_path),
            'world_state': str(state_path),
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
    episodio = json.loads((folder / 'episodios' / f'ep{episode_number:02d}.json').read_text(encoding='utf-8'))
    if episodio.get('world_state'):
        cont['world_state'] = episodio['world_state']
    cont.setdefault('facts', []).extend(facts or [])
    cont.setdefault('open_threads', []).extend(open_threads or [])
    if choice:
        cont.setdefault('decisions', {})[f'ep{episode_number:02d}'] = choice
    (folder / 'continuidade.json').write_text(json.dumps(cont, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    serie = bible['serie']
    serie['last_episode'] = max(serie.get('last_episode', 0), episode_number)
    (folder / 'serie.json').write_text(json.dumps(serie, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return cont
