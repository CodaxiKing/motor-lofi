"""Passada por distância percorrida e trava de apoio para ciclos calibrados."""
import math
import json
from functools import lru_cache

from .composicao import animar


def estado_ator(p, t, duracao):
    out = animar(p, t)
    if p.get('andar'):
        from .imagens import POS
        a, b = [POS.get(v,v) if isinstance(v,str) else v for v in p['andar']]
        if not all(isinstance(v, (int, float)) for v in (a, b)):
            raise ValueError('Passada calibrada exige posições numéricas')
        out['pos'] = a + (b-a)*min(1, max(0, t/duracao))
    return out


def mundo(p, cfg, t, size, duracao):
    v = estado_ator(p, t, duracao)
    if p.get('seguir_piso'):
        from .interacoes_ilustradas import aplicar
        info=None
        if cfg.get('_fundo_pixels'):
            w,h=cfg['_fundo_pixels'];W,H=size;s=max(W/w,H/h)*1.03
            x=(W-w*s)/2
            if cfg.get('travelling'):
                from .travelling import deslocamento
                x,_=deslocamento(cfg['travelling'],t,size,(w,h))
            info=((w,h),x,(H-h*s)*cfg.get('fundo_y',.5),s)
        v=aplicar(dict(v,interacoes=[]),cfg,t,size,info)
    camera = 0
    if cfg.get('travelling') and p.get('seguir_travelling'):
        from .travelling import estado
        camera = estado(cfg['travelling'], t)[0]
    from .imagens import POS
    pos=v.get('pos',.5)
    if isinstance(pos,str):pos=POS.get(pos,.5)
    return pos*size[0]/size[1]+camera, v.get('chao', .93), v.get('altura', .6)


def periodo(ciclo):
    return len(ciclo.get('ordem',ciclo['frames']))/ciclo['fps_quadros']


def fase(p, cfg, ciclo, animacao, t, size, duracao):
    """Integra distância em alturas de corpo; não muda com FPS, seek ou ordem do render."""
    inicio = animacao['inicio']
    stride = ciclo.get('deslocamento_corpo_ciclo')
    inicial = animacao.get('fase_inicial', 0)
    velocidade=animacao.get('velocidade',1)
    if not isinstance(velocidade,(int,float)) or not math.isfinite(velocidade) or velocidade<=0:
        raise ValueError('Velocidade de ciclo inválida')
    movel = p.get('trajeto') or p.get('andar') or cfg.get('travelling') and p.get('seguir_travelling')
    if not stride or not movel or p.get('sincronizar_passada') is False:
        return inicial + max(0, t-inicio)*velocidade/periodo(ciclo)
    if not math.isfinite(stride) or stride <= 0:
        raise ValueError('Comprimento da passada inválido')
    distancia = distancia_normalizada(p,cfg,inicio,t,size,duracao)
    if 'fase_final' in animacao:
        total = distancia_normalizada(p,cfg,inicio,animacao['fim'],size,duracao)
        inicial = (animacao['fase_final']-total/stride)%1
    return inicial + distancia/stride


def distancia_normalizada(p,cfg,inicio,t,size,duracao):
    # Pontos fixos de integração garantem resultados estáveis entre resoluções e FPS.
    fim = max(inicio, t)
    keys = {inicio, fim}
    keys.update(v for v, _ in p.get('trajeto', {}).get('pos', []) if inicio < v < fim)
    keys.update(v for v, _ in p.get('trajeto', {}).get('altura', []) if inicio < v < fim)
    keys.update(v for v, _ in cfg.get('travelling', {}).get('velocidades', []) if inicio < v < fim)
    keys.update(i/60 for i in range(math.ceil(inicio*60), math.floor(fim*60)+1))
    distancia = 0
    pontos = sorted(keys)
    for a, b in zip(pontos, pontos[1:]):
        xa, ya, ha = mundo(p, cfg, a, size, duracao)
        xb, yb, hb = mundo(p, cfg, b, size, duracao)
        distancia += math.hypot(xb-xa,yb-ya)/max(.001, (ha+hb)/2)
    return distancia


@lru_cache(maxsize=512)
def _tempo_fase(p_json,cfg_json,ciclo_json,anim_json,size,duracao,alvo):
    p,cfg,ciclo,animacao=(json.loads(v) for v in (p_json,cfg_json,ciclo_json,anim_json))
    a,b=animacao['inicio'],animacao['fim']
    if alvo<=fase(p,cfg,ciclo,animacao,a,size,duracao):return a
    for _ in range(28):
        meio=(a+b)/2
        if fase(p,cfg,ciclo,animacao,meio,size,duracao)<alvo:a=meio
        else:b=meio
    return b


def correcao_apoio(p, cfg, ciclo, animacao, t, size, duracao, base, espelhado=False):
    """Trava um ponto de contato desenhado sem deformar pernas ou alterar a escala."""
    if not p.get('travar_apoios'):
        return (0., 0.)
    from .ciclos_quadros import indice, imagem_frame
    contatos = ciclo.get('contatos_solo', [])
    if not contatos:
        raise ValueError('Trava de pés exige contatos_solo calibrados no ciclo')
    atual = fase(p, cfg, ciclo, animacao, t, size, duracao)
    inicial=fase(p,cfg,ciclo,animacao,animacao['inicio'],size,duracao)
    assinatura=tuple(json.dumps(v,sort_keys=True) for v in (p,cfg,ciclo,animacao))
    def tempo(alvo):
        if alvo<=inicial:return animacao['inicio']
        return _tempo_fase(*assinatura,tuple(size),duracao,alvo)

    def pe(tempo,marco):
        f = fase(p, cfg, ciclo, animacao, tempo, size, duracao)
        n = indice(ciclo, f*periodo(ciclo))
        frame = ciclo['frames'][n]
        ponto = frame.get('marcos', {}).get(marco)
        if ponto is None:
            raise ValueError('Marco de apoio ausente: '+marco)
        im = imagem_frame(ciclo, n, base=base)
        ax, ay = frame['ancora']; px, py = ponto
        if espelhado: px, ax = 1-px, 1-ax
        x, y, altura = mundo(p, cfg, tempo, size, duracao)
        fator = ciclo['referencia'].get('altura_referencia', .98)/ciclo['referencia']['altura_corpo']
        fator *= im.height/ciclo['referencia'].get('altura_celula_px', im.height)
        return x+(px-ax)*im.width/im.height*altura*fator, y+(py-ay)*altura*fator
    # Conserva o deslocamento acumulado ao trocar o apoio. Reiniciar a correção
    # em cada contato criaria saltos da raiz, mesmo com a sola presa corretamente.
    trechos=[]
    for c in contatos:
        for volta in range(math.floor(inicial-c['fim']),math.floor(atual-c['inicio'])+1):
            a=max(inicial,volta+c['inicio']);b=min(atual,volta+c['fim'])
            if a<b:trechos.append((a,b,c['marco'],b>=volta+c['fim']-1e-10))
    dx=dy=0.
    for a,b,marco,encerrado in sorted(trechos):
        ta=tempo(a);tb=max(ta,tempo(b)-1e-7) if encerrado else t
        x0,y0=pe(ta,marco);x1,y1=pe(tb,marco)
        dx+=(x0-x1)*size[1];dy+=(y0-y1)*size[1]
    limite = p.get('limite_correcao_apoio', .08)*size[1]
    if max(abs(dx), abs(dy)) > limite:
        raise ValueError('Apoio incompatível com a passada; recalibre o ciclo ou o trajeto')
    return dx, dy
