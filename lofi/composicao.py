"""Composição geométrica de recortes: mapas calibrados, não reconhecimento por IA."""
import copy
import json
import math
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw


@lru_cache(maxsize=512)
def _medida(path, stamp):
    with Image.open(path) as im:
        rgba = im.convert('RGBA')
        box = rgba.getchannel('A').point(lambda a: 255 if a > 20 else 0).getbbox()
        if box is None: raise ValueError(f'Recorte vazio: {path}')
        return im.size, box


def medida(base, nome):
    raiz = (Path(base) / 'imagens').resolve()
    path = (raiz / (nome + '.png')).resolve()
    if not path.is_relative_to(raiz): raise ValueError('Imagem fora da biblioteca')
    return _medida(str(path), path.stat().st_mtime_ns)


def identidade(p):
    return p.get('id') or p['img'].split('/')[0]


def espelhamento(p, pos, nome=None):
    """Sprites das laterais olham para o centro; direção original é metadado."""
    atual=bool(p.get('espelhar',False))
    if p.get('orientacao') != 'centro': return atual
    original=p.get('direcoes_originais',{}).get(nome or p['img'],p.get('direcao_original'))
    if original not in ('direita','esquerda'): return atual
    if abs(pos-.5)<.04: return atual
    desejada='direita' if pos<.5 else 'esquerda'
    return original != desejada


def orientar(p, pos):
    if not p.get('direcao_original') and not p.get('direcoes_originais'): return p
    p.setdefault('orientacao','centro')
    p['espelhar']=espelhamento(p,pos)
    return p


def animar(p, t):
    """Posição, chão e escala seguem keyframes contínuos; não altera a ficha."""
    from .core import keyframe
    out=dict(p)
    for campo,keys in p.get('trajeto',{}).items():
        if campo not in ('pos','chao','altura'): raise ValueError(f'Campo de trajetória inválido: {campo}')
        valor=keyframe(keys,t)
        if not isinstance(valor,(float,int)) or not math.isfinite(valor): raise ValueError('Trajetória inválida')
        if campo=='altura' and valor<=0: raise ValueError('Altura de trajetória inválida')
        out[campo]=valor
    return out


def nomes(p):
    return set([p['img']] + [n for _, n in p.get('poses', [])]
               + list(p.get('piscadas', {}).values()) + list(p.get('olhares', {}).values())
               + list(p.get('bocas', {}).values()) + p.get('envelope_poses', [])
               + [p[k] for k in ('boca','piscar') if isinstance(p.get(k), str)])


def validar_mapa(mapa):
    if not mapa.get('zonas'): raise ValueError('Mapa sem zonas')
    for nome, zona in mapa['zonas'].items():
        if len(zona.get('x', [])) != 2: raise ValueError(f'Faixa inválida: {nome}')
        vals = [*zona['x'], zona['chao'], zona['altura']]
        if not all(isinstance(v, (float, int)) and math.isfinite(v) and 0 <= v <= 1 for v in vals):
            raise ValueError(f'Zona inválida: {nome}')
        if zona['x'][0] >= zona['x'][1] or not 0 < zona['altura'] < zona['chao']:
            raise ValueError(f'Zona sem espaço: {nome}')
    from .portais import validar
    for portal in mapa.get('portais',{}).values(): validar(portal)
    return mapa


def _projetar(cfg, base, size):
    """Mesmo cover, margem 3% e deslocamento do fundo usados no renderer."""
    W, H = size
    from .imagens import nome_fundo
    nome = nome_fundo(cfg['fundo'])
    (w, h), _ = medida(base, nome)
    scale = max(W/w, H/h) * 1.03
    ox = (W-w*scale)/2; oy = (H-h*scale)*cfg.get('fundo_y', .5)
    return lambda x: (x*w*scale+ox)/W, lambda y: (y*h*scale+oy)/H, h*scale/H


def envelope(p, base):
    """Unidade = altura visível da pose de referência; uniforme entre frames."""
    (w, h), box = medida(base, p.get('referencia_escala', p['img']))
    ref_h = (box[3]-box[1])/h
    left = right = 0
    for nome in nomes(p):
        (iw, ih), b = medida(base, nome)
        ax = p.get('ancoras', {}).get(nome, p.get('ancora', [.5, 1]))[0]
        l = (ax*iw-b[0])/ih/ref_h; r = (b[2]-ax*iw)/ih/ref_h
        if p.get('espelhar'): l, r = r, l
        left = max(left, l); right = max(right, r)
    if p.get('animacoes_quadros'):
        # Complete drawings are normalized by body landmarks, not the changing
        # silhouette (raised arms/crouching). Reserve every frame's width.
        ref_h=.98
        for l,t,r,b in caixas_quadros(p,base):
            left=max(left,-l/.98);right=max(right,r/.98)
    margem=p.get('margem_puppet',0) if p.get('puppets') or p.get('puppet') else 0
    return ref_h, left+margem, right+margem


@lru_cache(maxsize=128)
def _caixas_ciclo(base,nome,stamp,atlas_stamp):
    from .ciclos_quadros import carregar,imagem_frame
    c=carregar(base,nome);out=[]
    fator=c['referencia'].get('altura_referencia',.98)/c['referencia']['altura_corpo']
    for i,f in enumerate(c['frames']):
        im=imagem_frame(c,i,base=base)
        box=im.getchannel('A').point(lambda a:255 if a>20 else 0).getbbox()
        if not box:continue
        ax,ay=f['ancora'];iw,ih=im.size
        ff=fator*ih/c['referencia']['altura_celula_px'] if c['referencia'].get('altura_celula_px') else fator
        out.append(((box[0]-ax*iw)/ih*ff,(box[1]-ay*ih)/ih*ff,
                    (box[2]-ax*iw)/ih*ff,(box[3]-ay*ih)/ih*ff))
    return tuple(out)


def caixas_quadros(p,base):
    from .ciclos_quadros import carregar,arquivos
    for nome in {a['ciclo'] for a in p.get('animacoes_quadros',[])}:
        c=carregar(base,nome);root=Path(base)/'imagens'
        stamps=tuple((n,(root/(n+'.png')).stat().st_mtime_ns) for n in arquivos(c))
        for l,t,r,b in _caixas_ciclo(str(base),nome,(root/nome).stat().st_mtime_ns,stamps):
            yield (-r,t,-l,b) if p.get('espelhar') else (l,t,r,b)


def auditar(cfg, base, size):
    """Verifica envelope de todas as poses e extremos do percurso, sem renderizar."""
    if any(p.get('trajeto') for p in cfg.get('personagens',[])):
        tempos={0.0}
        for p in cfg['personagens']:
            for keys in p.get('trajeto',{}).values(): tempos.update(float(t) for t,_ in keys)
        fim=max(tempos)
        tempos.update(fim*i/32 for i in range(33))
        encontrados={}
        for t in sorted(tempos):
            amostra=dict(cfg);amostra['personagens']=[]
            for p in cfg['personagens']:
                p=animar(p,t);p.pop('trajeto',None)
                amostra['personagens'].append(p)
            for f in auditar(amostra,base,size): encontrados[(f['code'],f['message'])]=f
        return list(encontrados.values())
    W,H=size; achados=[]; caixas=[]
    for p in cfg.get('personagens', []):
        pos=p.get('pos', .5)
        if not isinstance(pos, (int,float)): continue
        if p.get('orientacao')=='centro' and espelhamento(p,pos)!=bool(p.get('espelhar',False)):
            achados.append({'code':'orientacao_externa','message':f'{identidade(p)}: orientação contrária ao centro'})
        caminho=p.get('andar', [pos,pos])
        retangulos=[]
        for nome in nomes(p):
            (w,h),b=medida(base,nome)
            ax,ay=p.get('ancoras', {}).get(nome,p.get('ancora',[.5,1]))
            if p.get('espelhar'):
                b=(w-b[2],b[1],w-b[0],b[3]); ax=1-ax
            scale=p['altura']*H/h
            retangulos.append(((min(caminho)*W+(b[0]-ax*w)*scale)/W,
                               (p['chao']*H+(b[1]-ay*h)*scale)/H,
                               (max(caminho)*W+(b[2]-ax*w)*scale)/W,
                               (p['chao']*H+(b[3]-ay*h)*scale)/H))
        for l,t,r,b in caixas_quadros(p,base):
            alt=p['altura']
            retangulos.append((min(caminho)+l*alt*H/W,p['chao']+t*alt,
                               max(caminho)+r*alt*H/W,p['chao']+b*alt))
        b=(min(r[0] for r in retangulos),min(r[1] for r in retangulos),
           max(r[2] for r in retangulos),max(r[3] for r in retangulos))
        ident=identidade(p); caixas.append((p,b))
        if b[0]<0 or b[1]<0 or b[2]>1 or b[3]>1:
            achados.append({'code':'corte_personagem','message':f'{ident}: alguma pose/percurso sai do quadro'})
    for i,(p,a) in enumerate(caixas):
        for q,b in caixas[i+1:]:
            if abs(p['chao']-q['chao'])>.025:
                # Estimativa da cabeça pela parte superior da silhueta; revisão visual continua necessária.
                longe,perto=(a,b) if p['chao']<q['chao'] else (b,a)
                face=(longe[0],longe[1],longe[2],longe[1]+.28*(longe[3]-longe[1]))
                coberto=max(0,min(face[2],perto[2])-max(face[0],perto[0]))*max(0,min(face[3],perto[3])-max(face[1],perto[1]))
                if coberto > .45*(face[2]-face[0])*(face[3]-face[1]):
                    achados.append({'code':'cabeca_oculta','message':f'{identidade(p)}/{identidade(q)}: revisar oclusão da região da cabeça'})
                continue
            area=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
            menor=min((a[2]-a[0])*(a[3]-a[1]),(b[2]-b[0])*(b[3]-b[1]))
            if area>menor*.12 and not cfg.get('permitir_sobreposicao'):
                achados.append({'code':'sobreposicao','message':f'{identidade(p)}/{identidade(q)}: silhuetas se sobrepõem no mesmo plano'})
    return achados


def planejar(cfg, base, size, *, auditoria=True):
    """Retorna cópia ajustada + relatório; nunca modifica o plano original."""
    out = copy.deepcopy(cfg); mapa = validar_mapa(out['mapa_composicao'])
    W, H = size; achados = []; ajustes = []
    px, py, ratio = _projetar(out, base, size)
    if out.get('composicao') == 'manual':
        for p in out.get('personagens',[]):
            if isinstance(p.get('pos'),(int,float)): orientar(p,p['pos'])
        return out, {'ajustes': [], 'achados': auditar(out,base,size) if auditoria else []}
    # O mapa determina o enquadramento; zoom automático cortaria os limites calculados.
    out.update(plano='aberto', aproximar=0, balanco=0)
    grupos = {}
    for p in out.get('personagens', []):
        zona = p.get('zona', 'frente')
        if zona not in mapa['zonas']: raise ValueError(f'Zona inexistente: {zona}')
        grupos.setdefault(zona, []).append(p)
    for nome_zona, pessoas in grupos.items():
        z = mapa['zonas'][nome_zona]
        lo = max(.025, px(z['x'][0])); hi = min(.975, px(z['x'][1]))
        if hi <= lo: raise ValueError(f'Zona {nome_zona} fora do enquadramento')
        floor = min(.96, max(.1, py(z['chao'])))
        if not .1 <= py(z['chao']) <= .96:
            achados.append({'code':'mapa_cortado','message':f'{nome_zona}: chão original fora do enquadramento; revisar formato do fundo'})
        altura = min(z['altura']*ratio, floor-.05)
        gap = .025
        # Ordem estável por identidade, preservada nas trocas de pose.
        pessoas.sort(key=lambda p: (p.get('ordem', 0), identidade(p)))
        for i,p in enumerate(pessoas): orientar(p,lo+(hi-lo)*(i+.5)/len(pessoas))
        env = [envelope(p, base) for p in pessoas]
        fisicas = [float(p.get('escala_relativa', 1)) for p in pessoas]
        if any(not math.isfinite(f) or f <= 0 for f in fisicas): raise ValueError('Escala relativa inválida')
        altura = min(altura, (floor-.05)/max(fisicas))
        largura = sum((l+r)*f for (_, l, r), f in zip(env, fisicas))*H/W
        altura = min(altura, max(.01, hi-lo-gap*(len(pessoas)-1))/max(.001, largura))
        if altura < z.get('altura_minima', mapa.get('altura_minima', .48)):
            achados.append({'code': 'grupo_apertado', 'message': f'{nome_zona}: dividir elenco em planos; pouco espaço'})
        widths = [(l+r)*altura*f*H/W for (_, l, r), f in zip(env, fisicas)]
        cursor = (lo+hi-sum(widths)-gap*(len(pessoas)-1))/2
        for p, (ref_h, l, r), f, width in zip(pessoas, env, fisicas, widths):
            antes = {k: p.get(k) for k in ('pos', 'altura', 'chao', 'andar')}
            centro = cursor + l*altura*f*H/W
            p.update(pos=centro, altura=altura*f/ref_h, chao=floor)
            # Caminhada permanece dentro da faixa reservada para TODAS as poses.
            if p.get('andar'):
                folga = min(.025, max(0, gap/3))
                direcao = 1 if p['andar'][1] >= p['andar'][0] else -1
                p['andar'] = [centro-direcao*folga/2, centro+direcao*folga/2]
            ajustes.append({'id': identidade(p), 'zona': nome_zona, 'antes': antes,
                            'depois': {k: p.get(k) for k in ('pos', 'altura', 'chao', 'andar')}})
            cursor += width+gap
    # Pintura do fundo para a frente, conforme profundidade do chão.
    out['personagens'].sort(key=lambda p: (p.get('chao', .94), identidade(p)))
    if auditoria: achados.extend(auditar(out,base,size))
    return out, {'ajustes': ajustes, 'achados': achados}


def aplicar_episodio(spec, base, size=None):
    """Resolve cada cenário e conserva a mesma referência de escala no episódio."""
    out = copy.deepcopy(spec); size = tuple(size or out.get('preview_size', [432,768]))
    # Inclui todo o ciclo na ocupação da faixa, mesmo em planos que mostram outra pose.
    grupos = {}
    configs = []
    for s in out.get('shots', []):
        configs.extend([s['imagens']] if s.get('imagens') else [])
        configs.extend(s[l]['imagens'] for l in ('a', 'b') if s.get(l, {}).get('imagens'))
    for cfg in configs:
        for p in cfg.get('personagens', []):
            ident = identidade(p)
            grupos.setdefault(ident, set()).update(nomes(p))
    referencias = {}
    for cfg in configs:
        for p in cfg.get('personagens', []):
            ident = identidade(p)
            referencias.setdefault(ident, p.get('referencia_escala', p['img']))
            p['referencia_escala'] = referencias[ident]
            # Usado só para reservar espaço; não altera a sequência de animação.
            p['envelope_poses'] = sorted(grupos[ident])
    relatorios = []
    for cfg in configs:
        if not cfg.get('mapa_composicao'): continue
        rel = cfg.get('pasta_biblioteca', '.')
        pasta = (Path(base)/rel).resolve()
        resolvido, report = planejar(cfg, pasta, size)
        cfg.clear(); cfg.update(resolvido)
        relatorios.append(report)
    out['composicao_relatorio'] = {'size': size, 'planos': relatorios,
                                  'metodo': 'geometria e mapas calibrados; revisar interação e perspectiva'}
    return out


def mapear(spec, catalogo, base, size=None):
    """Anexa mapas conhecidos ao modo imagens existente, por correspondência de fundo."""
    out=copy.deepcopy(spec)
    por_fundo={l['img']: l.get('mapa_composicao') for l in catalogo['cenarios'].values()}
    for shot in out.get('shots', []):
        configs=([shot['imagens']] if shot.get('imagens') else [])
        configs += [shot[k]['imagens'] for k in ('a','b') if shot.get(k,{}).get('imagens')]
        for cfg in configs:
            fundo=cfg.get('fundo','')
            mapa=por_fundo.get(fundo) or por_fundo.get('fundo_'+fundo)
            if not mapa: raise ValueError(f'Calibre um mapa para o cenário: {fundo}')
            cfg.setdefault('mapa_composicao',copy.deepcopy(mapa))
            for p in cfg.get('personagens', []):
                ident=identidade(p)
                from .fichas_ilustradas import perfil as ler_perfil
                perfil=ler_perfil((Path(base)/cfg.get('pasta_biblioteca','.')).resolve(),catalogo['personagens'].get(ident,{}),catalogo.get('escala_referencia_m',1.70))
                p.setdefault('id',ident)
                if perfil.get('referencia_escala'): p.setdefault('referencia_escala',perfil['referencia_escala'])
                p['escala_relativa']=p.get('escala_override',perfil.get('escala_relativa',p.get('escala_relativa',1)))
                if perfil.get('altura_m'): p['altura_m']=perfil['altura_m']
                p.setdefault('puppets',perfil.get('puppets',{}))
                p.setdefault('piscadas_locais',perfil.get('piscadas_locais',{}))
                p.setdefault('bocas_locais',perfil.get('bocas_locais',{}))
                p.setdefault('margem_puppet',perfil.get('margem_puppet',0))
                p.setdefault('direcao_original',perfil.get('direcao_original','direita'))
                direcoes={}
                char=catalogo['personagens'].get(ident,{})
                for ciclo in char.get('ciclos',{}).values():
                    direcoes.update({f['img']:f.get('direcao_original',p['direcao_original']) for f in ciclo['frames']})
                if direcoes: p.setdefault('direcoes_originais',direcoes)
                p.setdefault('orientacao','centro')
                if 'zona' not in p:
                    zona=min(mapa['zonas'],key=lambda z:abs(mapa['zonas'][z]['chao']-p.get('chao',.94)))
                    p['zona']=zona
    return aplicar_episodio(out,base,size)


def diagnostico(cfg, base, size, output):
    from .imagens import quadro
    cfg = copy.deepcopy(cfg); mapa=cfg.pop('mapa_composicao', None)
    im = quadro({'start': 0, 'end': 1, 'imagens': cfg}, .5, str(base), size)
    d = ImageDraw.Draw(im); W,H=size
    if mapa:
        px,py,ratio=_projetar(cfg,base,size)
        for nome,z in mapa['zonas'].items():
            d.rectangle((px(z['x'][0])*W,(py(z['chao'])-z['altura']*ratio)*H,
                         px(z['x'][1])*W,py(z['chao'])*H),outline='#55bbff',width=2)
            d.text((max(3,px(z['x'][0])*W),max(3,(py(z['chao'])-z['altura']*ratio)*H)),nome,fill='#55bbff')
        for nome,(x,y) in mapa.get('interacoes',{}).items():
            x,y=px(x)*W,py(y)*H
            d.ellipse((x-4,y-4,x+4,y+4),outline='#ff77cc',width=2)
            d.text((x+6,y),nome,fill='#ff77cc')
    for p in cfg.get('personagens', []):
        x=p['pos']*W; y=p['chao']*H
        d.line((0,y,W,y), fill='#44eeaa', width=2)
        d.line((x,y,x,y-p['altura']*H), fill='#ffcc44', width=2)
        d.text((max(3,x-30),max(3,y-p['altura']*H-14)), identidade(p), fill='white')
    im.save(output)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('episode'); parser.add_argument('output')
    parser.add_argument('--catalogo',default=str(Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1/catalogo.json'))
    args=parser.parse_args()
    source=Path(args.episode).resolve()
    result=mapear(json.loads(source.read_text(encoding='utf-8')),
                  json.loads(Path(args.catalogo).read_text(encoding='utf-8')),source.parent)
    destination=Path(args.output).resolve()
    if destination.parent != source.parent: raise ValueError('Saída deve ficar na mesma pasta para preservar caminhos relativos')
    if destination.exists(): raise FileExistsError(destination)
    destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
