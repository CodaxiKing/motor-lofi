"""Handoffs locais para skills criativas. Não chama modelos nem inventa métricas."""
import json
from pathlib import Path
from .perfis_duracao import selecionar, planejar

RAIZ = Path(__file__).resolve().parents[1]
SKILLS = ('video-script', 'skill-creator', 'canvas-design')


def listar():
    return [{'skill': nome, 'entrypoint': str(RAIZ / 'skills' / nome / 'SKILL.md'),
             'installed_in_project': (RAIZ / 'skills' / nome / 'SKILL.md').is_file()}
            for nome in SKILLS]


def _json(pasta, nome, padrao=None):
    p = pasta / nome
    return json.loads(p.read_text(encoding='utf-8')) if p.is_file() else padrao


def contexto(pasta, episodio, *, skill='video-script', perfil=None, duracao=None):
    if skill not in ('video-script', 'canvas-design'):
        raise ValueError('Contexto criativo deve ser video-script ou canvas-design')
    if isinstance(episodio, bool) or not isinstance(episodio, int) or episodio < 1:
        raise ValueError('Episódio deve ser um inteiro positivo')
    pasta = Path(pasta).resolve()
    if not pasta.is_dir():
        raise FileNotFoundError(pasta)
    nome = f'ep{episodio:02d}'
    md = pasta / f'{nome}_roteiro.md'
    texto = md.read_text(encoding='utf-8') if md.is_file() else ''
    serie = _json(pasta, 'serie.json', {})
    ep = _json(pasta, f'{nome}.json') or _json(pasta / 'episodios', f'{nome}.json', {})
    escolha = perfil
    if escolha is None and not any('perfil de duração:' in linha.lower() for linha in texto.splitlines()):
        escolha = ep.get('duration_profile') or serie.get('duration_profile')
    perfil, _ = selecionar(texto, md, escolha)
    contrato = planejar(perfil, duracao if duracao is not None else ep.get('total') if ep.get('total', 0) >= 90 else None)
    biblia = pasta / 'biblia.md'
    resultado = {'skill': skill, 'series_dir': str(pasta), 'episode': episodio,
                 'duration_plan': contrato, 'language': 'pt-BR',
                 'bible': biblia.read_text(encoding='utf-8') if biblia.is_file() else None,
                 'series': serie, 'script': texto or None, 'technical_episode': ep or None,
                 'narrative_plan': _json(pasta / 'planos', f'{nome}.json'),
                 'locked_characters': _json(pasta, 'personagens.json', {}),
                 'cast': _json(pasta, 'elenco.json', {}),
                 'world': _json(pasta, 'mundo.json'), 'memory': _json(pasta, 'memoria.json'),
                 'constraints': ['Mínimo de 90 segundos por episódio',
                                 'Preservar cânone, fichas e escolhas anteriores',
                                 'Métricas ausentes permanecem ausentes',
                                 'Prompts e planos não são mídia gerada']}
    if skill == 'video-script':
        from .experimentos import carregar, recomendar
        resultado.update(goal='alcance', experiments=carregar(str(pasta)),
                         evidence=recomendar(str(pasta)),
                         deliverables=['ideia e promessa', 'três aberturas e suas segundas frases',
                                       'roteiro por cena: tempo/fala/imagem', 'seis critérios dramáticos',
                                       'narração por voz e hipóteses a testar'])
    else:
        resultado.update(formats={'tiktok': [1080, 1920], 'instagram': [1080, 1920], 'youtube': [1280, 720]},
                         references={k: v.get('referencia') for k, v in ep.get('cast', {}).items()},
                         deliverables=['direção de arte em Markdown', 'capa PNG ou PDF real',
                                       'revisão visual de texto, margens e identidade'],
                         fonts=str(RAIZ / 'skills' / 'canvas-design' / 'canvas-fonts'))
    return resultado


def converter_evals(origem=None, skill_name='serie-lofi-interativa'):
    """Adapta casos existentes para o schema oficial do skill-creator, sem executá-los."""
    dados = json.loads(Path(origem or RAIZ / 'tests' / 'evals.json').read_text(encoding='utf-8'))
    return {'skill_name': skill_name, 'evals': [
        {'id': i, 'prompt': c['prompt'], 'expected_output': '\n'.join(c['espera']),
         'expectations': c['espera'], 'files': []}
        for i, c in enumerate(dados['casos'], 1)]}
