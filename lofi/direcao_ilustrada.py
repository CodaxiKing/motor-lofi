"""Escolhas de câmera por batidas declaradas; não adivinha intenção por palavras."""
import math

PLANOS={'acao':'inteiro','interacao':'inteiro','fala':'medio','reacao':'close',
        'descoberta':'close','pre_susto':'conjunto','susto':'aberto'}
PRIORIDADE={'acao':1,'fala':2,'interacao':3,'reacao':4,'descoberta':5,'pre_susto':6,'susto':7}


def planejar(batidas,duracao,pessoas):
    if not batidas:return []
    ids={p['id'] for p in pessoas};eventos=[]
    for b in batidas:
        a=b['inicio'];z=b['fim'];tipo=b['tipo']
        if tipo not in PLANOS:raise ValueError(f'Batida narrativa desconhecida: {tipo}')
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (a,z)) or not 0<=a<z<=duracao:
            raise ValueError('Batida narrativa fora da cena')
        if b.get('alvo') is not None and b['alvo'] not in ids:raise ValueError('Alvo narrativo ausente')
        if z-a<.35:raise ValueError('Batida curta demais para um corte legível')
        eventos.append(b)
    limites=sorted({0.,duracao,*[v for b in eventos for v in (b['inicio'],b['fim'])]})
    cortes=[]
    for a,z in zip(limites,limites[1:]):
        ativos=[b for b in eventos if b['inicio']<=a<b['fim']]
        b=max(ativos,key=lambda b:PRIORIDADE[b['tipo']]) if ativos else None
        tipo=b['tipo'] if b else 'acao';plano=PLANOS[tipo]
        c={'inicio':a,'fim':z,'plano':plano,'motivo':tipo,'push':.3 if tipo in ('reacao','descoberta') else 0}
        if b and b.get('alvo'):c['alvo']=b['alvo']
        if cortes and all(c.get(k)==cortes[-1].get(k) for k in ('plano','alvo','motivo')):
            cortes[-1]['fim']=z
        else:cortes.append(c)
    return cortes
