"""Pacotes de abertura renderizáveis, derivados exclusivamente dos planos do episódio."""
import copy


def ajustar_tempo(plano, fator=1, corte=0):
    """Transforma relógios locais de atuação junto com o plano, sem reiniciar gestos."""
    from .core import keyframe
    def converter(v):
        if isinstance(v, list) and v and isinstance(v[0], list) and len(v[0]) == 2 and isinstance(v[0][0], (int, float)):
            saida = [[0, keyframe(v, corte)]]
            saida += [[(t-corte)*fator, valor] for t, valor in v if t > corte]
            return saida
        return v
    for grupo in [plano.get('props', {}), plano.get('camera', {})] + plano.get('actors', []):
        for chave, valor in list(grupo.items()):
            grupo[chave] = converter(valor)
        if 'equipment' in grupo:
            grupo['equipment'] = {k: converter(v) for k, v in grupo['equipment'].items()}
    for obj in plano.get('ground_objects', []):
        for chave in ('visible_after', 'visible_until'):
            if chave in obj: obj[chave] = max(0, (obj[chave]-corte)*fator)
    return plano


def gerar(episodio):
    planos = [s for s in episodio.get('shots', []) if s.get('type', 'scene') == 'scene']
    if not planos:
        return []
    fontes = [0, next((i for i, s in enumerate(planos) if s['actors'][0]['emotion'] != 'neutral'), 0),
              next((i for i, s in enumerate(planos) if s['actors'][0].get('walk')), len(planos)-1)]
    saida = []
    for letra, estrategia, indice, zoom, som in zip('ABC', ('situacao', 'reacao', 'acao'), fontes,
                                                   (1.12, 1.4, 1.22), ('heartbeat', 'impact', 'whoosh')):
        plano = copy.deepcopy(planos[indice])
        ajustar_tempo(plano, 3 / max(.001, plano['end'] - plano['start']))
        texto = plano['director_notes']['text']
        legenda = ' '.join(texto.split()[:8])
        plano.update(start=0, end=3, hook={'text': legenda})
        plano['camera'] = {'zoom': zoom}
        saida.append({'id': letra, 'estrategia': estrategia, 'texto': texto,
                      'duracao_s': 3, 'fonte_plano': indice + 1,
                      'primeiro_quadro': {'cenario': plano['scene'], 'camera': plano['camera'],
                                          'atores': copy.deepcopy(plano['actors'])},
                      'acao': plano['director_notes'].get('performance'), 'legenda': legenda,
                      'som': som, 'plano': plano})
    return saida


def aplicar(episodio, variante):
    """Troca só a janela inicial; preserva o corpo após 3s e a duração total."""
    if episodio.get('clips') or episodio.get('subs'):
        raise ValueError('Selecione a abertura antes da sincronização; áudio e legendas precisam ser realinhados')
    ep = copy.deepcopy(episodio)
    candidato = next((c for c in ep.get('opening_variants', []) if c['id'] == variante), None)
    if candidato is None:
        raise ValueError(f'Abertura desconhecida: {variante}')
    limite = candidato['duracao_s']
    corpo = []
    for plano in ep['shots']:
        if plano['end'] <= limite:
            continue
        if plano['start'] < limite:
            ajustar_tempo(plano, corte=limite-plano['start'])
            plano['start'] = limite
        corpo.append(plano)
    ep['shots'] = [copy.deepcopy(candidato['plano'])] + corpo
    ep['sfx'] = [s for s in ep.get('sfx', []) if s.get('t', 0) >= limite]
    ep['sfx'].append({'t': 0, 'name': candidato['som']})
    ep['opening_selected'] = variante
    return ep


def exportar(caminho, destino, variante):
    """Exporta uma variante para revisão; preserva o episódio original."""
    import json
    from pathlib import Path
    from .protecao import bloquear
    origem, saida = Path(caminho), Path(destino)
    if saida.exists():
        raise FileExistsError(f'Arquivo já existe: {saida}')
    ep = aplicar(json.loads(origem.read_text(encoding='utf-8')), variante)
    if origem.resolve().parent != saida.resolve().parent:
        raise ValueError('Exporte ao lado do original para preservar caminhos relativos dos assets e áudios')
    bloquear(str(saida))
    ep['out'] = saida.stem + '.mp4'
    saida.write_text(json.dumps(ep, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return {'episode': str(saida), 'opening': variante}
