"""Agenda desenhos de ligação reais, sem dissolver dois corpos sobrepostos."""
import math
import json
from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=32)
def _ficha(path,stamp):return json.loads(Path(path).read_text(encoding='utf-8'))


def preparar_ator(p,base):
    if not p.get('movimentos'):return p
    raiz=(Path(base)/'imagens').resolve();id=p.get('id',p.get('img','').split('/')[0]);path=(raiz/id/'personagem.json').resolve()
    if not path.is_relative_to(raiz):raise ValueError('Ficha fora da biblioteca')
    ficha=_ficha(str(path),path.stat().st_mtime_ns)
    if p.get('animacoes_quadros'):raise ValueError('Escolha movimentos ou animacoes_quadros, sem duplicar a agenda')
    out=dict(p,animacoes_quadros=planejar(p['movimentos'],ficha.get('ciclos_quadros',{}),ficha.get('transicoes',{})))
    out['movimentos_origem']=out.pop('movimentos');return out


def planejar(movimentos,ciclos,transicoes):
    saida=[];anterior=None;fim_anterior=0.
    for item in movimentos:
        acao=item['acao'];inicio=item['inicio'];fim=item['fim']
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (inicio,fim)) or inicio<fim_anterior or fim<=inicio:
            raise ValueError('Movimentos precisam de intervalos positivos, ordenados e sem sobreposição')
        if acao not in ciclos:raise ValueError(f'Desenhos ausentes para movimento: {acao}')
        origem=anterior if inicio==fim_anterior and anterior is not None else 'parado'
        if origem!=acao:
            ponte=transicoes.get(origem+'>'+acao)
            if ponte:
                if saida and saida[-1].get('modo')=='loop' and ponte.get('periodo_origem'):
                    prev=saida[-1];prev.setdefault('fase_inicial',(-(prev['fim']-prev['inicio'])/ponte['periodo_origem'])%1)
                dur=ponte['duracao']
                if not isinstance(dur,(int,float)) or not math.isfinite(dur) or not 0<dur<fim-inicio:
                    raise ValueError(f'Tempo insuficiente para transição {origem}>{acao}')
                saida.append({'acao':origem+'>'+acao,'ciclo':ponte['ciclo'],'inicio':inicio,'fim':inicio+dur,
                              'modo':'uma_vez','transicao_real':True})
                inicio+=dur
            elif anterior is not None and acao not in ('interagir','alcancar'):
                raise ValueError(f'Gere desenhos de ligação para {origem}>{acao}')
        modo=item.get('modo','uma_vez' if acao in ('parado','interagir','alcancar') else 'loop')
        saida.append(dict(item,ciclo=ciclos[acao],inicio=inicio,modo=modo))
        anterior=acao;fim_anterior=fim
    return saida
