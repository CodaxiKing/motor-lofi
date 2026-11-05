"""Estrutura editorial rastreável: extrai evidências, não inventa acontecimentos."""
import re

PADROES = {
    'objetivo': r'quer|precisa|decide|objetivo|tent[ao]|busca',
    'obstaculo': r'mas|porém|impede|tranc|bloque|não consegue|obstáculo',
    'virada': r'descobre|revela|afinal|na verdade|de repente|virada',
    'consequencia': r'por isso|então|consequência|perde|consegue|escapa|salva',
}


def estruturar(texto):
    unidades = [x.strip() for x in re.split(r'(?<=[.!?])\s+|\n+', texto) if x.strip()]
    batidas = {}
    for campo, padrao in PADROES.items():
        evidencias = [{'texto': t, 'unidade': i + 1} for i, t in enumerate(unidades)
                      if re.search(padrao, t, re.I)]
        batidas[campo] = evidencias
    escolhas = {}
    for letra in 'AB':
        m = re.search(rf'^\s*{letra}\)\s*(.+)$', texto, re.M)
        escolhas[letra] = m.group(1) if m else None
    faltas = [k for k, v in batidas.items() if not v]
    if not all(escolhas.values()):
        faltas.append('escolha_ab')
    custos = all(v and re.search(r'perde|risco|custa|sacrifica|mas', v, re.I) for v in escolhas.values())
    if all(escolhas.values()) and not custos:
        faltas.append('custo_das_escolhas')
    from .dramaturgia import avaliar_texto
    return {'metodo': 'heuristica_requer_revisao', 'batidas': batidas, 'dramaturgia': avaliar_texto(texto),
            'escolhas': escolhas, 'pendencias': faltas}


def unidades_visuais(texto):
    """Metadados editoriais não viram falas nem planos de personagens parados."""
    from .dramaturgia import ler_texto
    cenas, _, _ = ler_texto(texto)
    if cenas:
        visuais = []
        for cena in cenas:
            corpo = '\n'.join(cena['corpo'])
            nar = re.search(r'^\s*NARRAÇÃO:\s*(.+)', corpo, re.M | re.I)
            acao = cena.get('acontecimento')
            if nar or acao:
                visuais.append(nar[1] if nar else acao)
            for fala in cena['falas']:
                if fala.get('texto'):
                    visuais.append(fala['texto'])
        return '\n'.join(visuais)
    return '\n'.join(t.strip() for t in re.split(r'(?<=[.!?])\s+|\n+', texto)
                     if t.strip() and not re.match(r'^(?:Perfil de duração:|[AB]\))', t.strip(), re.I))
