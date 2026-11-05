"""Ação antes da câmera: elenco, blocking, atuação e estado físico entre planos.

Resolução linguística conservadora. Ambiguidades ficam no relatório; SUJEITO e
DESTINATÁRIO por cena permitem direção explícita sem adivinhar pronomes.
"""
import copy
import re
from .personagens import normalizar, preparar_elenco
from .performance import plan_performance

OBJETOS = {'chave': 'key', 'lanterna': 'flashlight', 'celular': 'phone', 'telefone': 'phone',
           'radio': 'radio', 'mochila': 'bag'}


def unidades(texto):
    from .dramaturgia import ler_texto
    cenas, _, _ = ler_texto(texto)
    if not cenas:
        from .editorial import unidades_visuais
        resultado = []
        for t in unidades_visuais(texto).splitlines():
            fala = re.match(r'^([\wÀ-ÿ -]+):\s*(.+)', t)
            resultado.append({'text': fala[2], 'speaker': fala[1]} if fala else {'text': t})
        return resultado
    resultado = []
    for cena in cenas:
        corpo = '\n'.join(cena['corpo'])
        def campo(nome):
            m = re.search(rf'^\s*{nome}:\s*(.+)', corpo, re.M | re.I)
            return m[1].strip('` ') if m else None
        contexto = {'source_scene': cena['n'], 'participants': campo('PERSONAGENS'),
                    'location': campo('CEN[AÁ]RIO'), 'subject': campo('SUJEITO'),
                    'recipient': campo('DESTINAT[AÁ]RIO'), 'mark': campo('MARCA')}
        nar = campo('NARRAÇÃO') or cena.get('acontecimento')
        if nar:
            resultado.append(dict(contexto, text=nar))
        for fala in cena['falas']:
            if fala.get('texto'):
                resultado.append(dict(contexto, text=fala['texto'], speaker=fala['personagem'],
                                      recipient=fala.get('alvo')))
    return resultado


def compor(episodio, texto, elenco=None, travados=None, estado_inicial=None):
    from .rig import CHARS
    from .mapa import marcas, no_chao
    fontes = unidades(texto)
    perfis = copy.deepcopy(elenco or {})
    for unit in fontes:
        nomes = [unit.get('speaker'), unit.get('subject')]
        m = re.match(r'^([A-ZÀ-Ý][a-zà-ÿ]+)\s+(?:pega|abre|corre|caminha|olha|entrega|abandona|aponta|empurra|abraça|segura|fala|senta)\b', unit['text'])
        if m and normalizar(m[1]) not in ('ela', 'ele', 'alguem', 'depois', 'entao'):
            nomes.append(m[1])
        for nome in filter(None, nomes):
            chave = re.sub(r'[^a-z0-9_-]', '_', normalizar(nome))
            if chave and chave not in CHARS and chave not in perfis:
                perfis[chave] = {'nome': nome}
    usados = {episodio['shots'][0]['actors'][0]['char']}
    normal = normalizar(texto)
    for chave in set(CHARS) | set(travados or {}) | set(perfis):
        ficha = perfis.get(chave, {})
        nomes = [chave, ficha.get('nome', chave)] + ficha.get('aliases', [])
        if any(re.search(r'\b' + re.escape(normalizar(n)) + r'\b', normal) for n in nomes):
            usados.add(chave)
    # Perfis não citados podem ser alvos de relações ("a irmã") e direções explícitas.
    for chave in list(usados):
        usados.update(perfis.get(chave, {}).get('relacoes', {}).values())
    cast = preparar_elenco({k: perfis.get(k, {}) for k in sorted(usados)}, travados)
    aliases = {}
    for k, p in cast.items():
        for nome in [k, p['nome']] + p.get('aliases', []):
            alias = normalizar(nome)
            if alias in aliases and aliases[alias] != k:
                raise ValueError(f'Alias ambíguo no elenco: {nome}')
            aliases[alias] = k
    def resolver(nome):
        return aliases.get(normalizar(str(nome).strip('` ')))
    def mencoes(t):
        encontrados = [(m.start(), chave) for nome, chave in aliases.items()
                        for m in re.finditer(r'\b' + re.escape(nome) + r'\b', normalizar(t))]
        return list(dict.fromkeys(k for _, k in sorted(encontrados)))
    estado = copy.deepcopy(estado_inicial or {'locations': {}, 'objects': {}})
    estado.setdefault('locations', {}); estado.setdefault('objects', {})
    for k, perfil in cast.items():
        for item in perfil.get('inventario', []):
            obj = OBJETOS.get(normalizar(item), item)
            estado['objects'].setdefault(obj, {'owner': k, 'scene': None})
        if perfil['visual'].get('backpack'):
            estado['objects'].setdefault('bag', {'owner': k, 'scene': None})
    avisos, presentes, anterior = [], [], None
    for indice, shot in enumerate(episodio['shots']):
        unit = fontes[indice]
        linha = unit['text']; texto_n = normalizar(linha)
        dur = shot['end'] - shot['start']
        citados = mencoes(linha)
        ambigua = False
        declarados = mencoes(unit.get('participants') or '')
        sujeito = resolver(unit.get('speaker') or unit.get('subject'))
        if not sujeito and anterior:
            for papel, pessoa in cast[anterior].get('relacoes', {}).items():
                if re.match(r'^(?:a|o) ' + re.escape(normalizar(papel)) + r'\b', texto_n):
                    sujeito = pessoa
                    break
        pronome = bool(re.match(r'^(?:entao )?(?:ela|ele|a irma|o irmao)\b', texto_n))
        if not sujeito and citados and not pronome:
            sujeito = citados[0]
        if not sujeito:
            # Um pronome só resolve quando há um antecedente compatível sem competição.
            genero = 'feminino' if re.match(r'^(?:entao )?(?:ela|a irma)\b', texto_n) else 'masculino' if re.match(r'^(?:entao )?ele\b', texto_n) else None
            candidatos = [k for k in presentes if cast[k].get('genero') == genero] if genero else []
            if len(candidatos) == 1:
                sujeito = candidatos[0]
            elif anterior and len(presentes) <= 1:
                sujeito = anterior
            elif len(presentes) > 1:
                ambigua = True
                avisos.append({'code': 'ambiguous_subject', 'shot': indice + 1,
                               'message': 'Sujeito ambíguo; use SUJEITO na cena'})
        sujeito = sujeito or anterior or episodio['shots'][0]['actors'][0]['char']
        for relacao, alvo in cast[sujeito].get('relacoes', {}).items():
            if re.search(r'\b(?:a|o) ' + re.escape(normalizar(relacao)) + r'\b', texto_n):
                if re.match(r'^(?:a|o) ' + re.escape(normalizar(relacao)) + r'\b', texto_n):
                    sujeito = alvo
                if alvo not in citados: citados.append(alvo)
        alvo = resolver(unit.get('recipient'))
        if not alvo:
            alvo = next((k for k in citados if k != sujeito), None)
        ativos = list(dict.fromkeys([sujeito] + declarados + citados))
        # Só mantém ouvintes automaticamente enquanto continuamos no mesmo ambiente.
        explicito = unit.get('location')
        if indice and not explicito and not re.search(r'\b(?:rua|cidade|hospital|mercado|floresta|escada|ponte|igreja|metro|corredor|apartamento|quarto|cozinha)\b', texto_n):
            shot['scene'] = episodio['shots'][indice-1]['scene']
        if explicito:
            from .scenes import REGISTRY
            nome = explicito.split('`')[0].split()[0]
            if nome in REGISTRY: shot['scene'] = nome
            else: avisos.append({'code': 'unknown_location', 'shot': indice + 1, 'message': f'Cenário desconhecido: {nome}'})
        if indice and shot['scene'] == episodio['shots'][indice-1]['scene'] and not declarados:
            ativos = list(dict.fromkeys(ativos + presentes))
        performance = plan_performance(linha)
        if ambigua or re.search(r'\bnao\s+(?:abre|pega|entrega|fecha|empurra|corre|abandona)\b', texto_n):
            performance = dict(performance, pose='idle', movement='idle', prop=None)
        if performance['emotion'] == 'tense': performance['emotion'] = 'suspicious'
        if performance['pose'] in ('open_door', 'knock') and 'porta' not in marcas(shot['scene']) and not explicito:
            shot['scene'] = 'entrada'
        local = estado['locations'].setdefault(shot['scene'], {'door': 0})
        antes = copy.deepcopy(estado)
        objeto = next((obj for palavra, obj in OBJETOS.items() if re.search(r'\b' + palavra + r'\b', texto_n)), None)
        negada = bool(re.search(r'\bnao\s+(?:entrega|passa|devolve|abandona|larga|solta|deixa|fecha)\b', texto_n))
        transferencia = not ambigua and not negada and objeto and alvo and bool(re.search(r'\b(?:entrega|entregou|passa|passou|devolve|devolveu)\b', texto_n))
        larga = not ambigua and not negada and objeto and bool(re.search(r'\b(?:abandona|abandonou|larga|largou|solta|soltou|deixa|deixou)\b', texto_n))
        pega = objeto and performance['pose'] in ('hold', 'phone')
        evento = None
        if transferencia or larga:
            dono = estado['objects'].get(objeto, {}).get('owner')
            if dono != sujeito:
                avisos.append({'code': 'object_not_owned', 'shot': indice + 1,
                               'message': f'{sujeito} não possui {objeto}; entrega/abandono não aplicado'})
            else:
                estado['objects'][objeto] = {'owner': alvo if transferencia else None, 'scene': shot['scene'], 'mark': 'centro'}
                evento = 'entrega' if transferencia else 'abandono'
        elif pega:
            dono = estado['objects'].get(objeto, {}).get('owner')
            if dono and dono != sujeito:
                avisos.append({'code': 'object_already_owned', 'shot': indice + 1,
                               'message': f'{objeto} está com {dono}; falta entrega explícita'})
            else:
                estado['objects'][objeto] = {'owner': sujeito, 'scene': shot['scene']}
                evento = 'pega'
        elif objeto and re.search(r'\bencontra|\bve\b', texto_n):
            estado['objects'].setdefault(objeto, {'owner': None, 'scene': shot['scene'], 'mark': 'centro'})
            evento = 'descoberta'
        if performance['pose'] == 'open_door': local['door'] = 1
        if not negada and not ambigua and re.search(r'\b(?:fecha|fechou)\b.*porta', texto_n): local['door'] = 0
        shot['props'] = dict(shot.get('props', {}), door=local['door'])
        if antes['locations'][shot['scene']]['door'] != local['door']:
            shot['props']['door'] = [[0, antes['locations'][shot['scene']]['door']], [dur * .55, local['door']]]
        marks = marcas(shot['scene'])
        marca = unit.get('mark')
        if marca and marca not in marks:
            avisos.append({'code': 'unknown_mark', 'shot': indice+1, 'message': f'Marca inexistente: {marca}'})
            marca = None
        if not marca:
            preferencias = ('porta', 'frente_porta') if performance['pose'] in ('open_door', 'knock') else ('sofa', 'banco', 'cama') if performance['pose'] == 'sit' else ('balcao', 'carro', 'sofa', 'frente_esq') if performance['pose'] == 'hide' else ('frente_porta', 'centro', 'meio', 'frente')
            marca = next((m for m in preferencias if m in marks), next(iter(marks), None))
        actors = []
        for pos, chave in enumerate(ativos):
            principal = chave == sujeito
            motion = cast[chave]['motion']
            marca_ator = marca if principal else next((m for m in ('lado_esq', 'frente_esq', 'calcada_esq', 'tapete_esq', 'esq') if m in marks and m != marca), marca)
            mk = marks.get(marca_ator, {'x': 540, 'y': 1700})
            ator = {'char': chave, 'mark': marca_ator, 'x': mk['x'], 'y': mk['y'],
                    'view': mk.get('view', '3q') if principal and performance['pose'] in ('open_door', 'knock') else '3q', 'facing': 1 if pos == 0 else -1,
                    'pose': performance['pose'] if principal else motion['postura'],
                    'emotion': performance['emotion'] if principal else 'neutral',
                    'walk': principal and performance['movement'] in ('walk', 'run'),
                    'run': principal and performance['movement'] == 'run', 'look': 12 if pos == 0 else -12,
                    'sway': motion['sway'], 'breath': motion['breath'], 'motion_speed': motion['velocidade'],
                    'lipsync': False, 'voice': chave}
            if not marca_ator: ator.pop('mark')
            # Personagens na mesma marca ocupam pontos distintos que continuam no chão.
            if pos and any(a['x'] == ator['x'] and a['y'] == ator['y'] for a in actors):
                for dx in (150, -150, 90, -90):
                    if no_chao(shot['scene'], mk['x'] + dx, mk['y'], 0):
                        ator['x'] = mk['x'] + dx; break
            if ator['walk']:
                destino = next((m for m in ('frente', 'calcada_dir', 'tapete_dir', 'lado_dir', 'centro') if m in marks and m != marca_ator), None)
                if destino:
                    ator['mark'] = [[0, marca_ator], [dur / motion['velocidade'] if motion['velocidade'] > 1 else dur, destino]]
                    fracao = min(1, motion['velocidade'])
                    ator['x'] = [[0, mk['x']], [dur / max(1, motion['velocidade']), mk['x'] + (marks[destino]['x']-mk['x']) * fracao]]
                    ator['y'] = [[0, mk['y']], [dur / max(1, motion['velocidade']), mk['y'] + (marks[destino]['y']-mk['y']) * fracao]]
                    ator['view'] = 'side'
            carregados = [obj for obj, estado_obj in estado['objects'].items() if estado_obj.get('owner') == chave]
            anteriores = [obj for obj, estado_obj in antes['objects'].items() if estado_obj.get('owner') == chave]
            ator['prop'] = next((o for o in carregados if o != 'bag'), 'bag' if 'bag' in carregados and not cast[chave]['visual'].get('backpack') else None)
            ator['equipment'] = {'backpack': 'bag' in carregados}
            if ('bag' in anteriores) != ('bag' in carregados):
                ator['equipment']['backpack'] = [[0, 'bag' in anteriores], [dur * .55, 'bag' in carregados]]
            atraso = min(motion['reacao_s'], dur * .15)
            if principal and (evento or performance['pose'] == 'open_door'):
                acao = 'reach' if evento in ('pega', 'entrega', 'abandono', 'descoberta') else 'open_door'
                ator['pose_track'] = [[0, motion['postura']], [atraso, acao], [dur * .7, 'hold' if ator['prop'] else motion['postura']]]
                ator['emotion_track'] = [[0, 'neutral'], [dur * .7, performance['emotion']]]
            if objeto and evento in ('pega', 'entrega', 'abandono') and (principal or chave == alvo):
                inicial = objeto if objeto in anteriores else None
                final = objeto if objeto in carregados else None
                ator['prop_track'] = [[0, inicial], [dur * .55, final]]
            if not principal:
                ator['emotion_track'] = [[0, 'neutral'], [atraso, performance['emotion'] if performance['emotion'] != 'neutral' else 'suspicious' if transferencia else 'neutral']]
                ator['pose_track'] = [[0, motion['postura']], [atraso, 'ouvir']]
            actors.append(ator)
        if len(actors) > 1:
            def x_inicial(a): return a['x'][0][1] if isinstance(a['x'], list) else a['x']
            for a in actors:
                outro = next(o for o in actors if o['char'] != a['char'])
                a['facing'] = 1 if x_inicial(outro) >= x_inicial(a) else -1
                a['look'] = 12 * a['facing']
        if alvo and performance['pose'] in ('hug', 'push'):
            agente = actors[0]
            receptor = next((a for a in actors if a['char'] == alvo), None)
            if receptor and isinstance(agente['x'], (int, float)):
                ponto = agente['x'] + 110 * agente['facing']
                if no_chao(shot['scene'], ponto, agente['y'], 0):
                    receptor['x'], receptor['y'] = ponto, agente['y']
                    receptor['pose_track'] = [[0, 'ouvir'], [dur*.55, 'hug' if performance['pose'] == 'hug' else 'proteger_rosto']]
                    if performance['pose'] == 'push' and no_chao(shot['scene'], ponto + 70*agente['facing'], agente['y'], 0):
                        receptor['x'] = [[0, ponto], [dur*.5, ponto], [dur*.8, ponto + 70*agente['facing']]]
        if unit.get('speaker'):
            for a in actors: a['lipsync'] = a['char'] == sujeito
        shot['actors'] = actors
        shot['blocking'] = {'subject': None if ambigua else sujeito, 'recipient': alvo, 'participants': ativos,
                            'action': performance['pose'], 'object': objeto, 'event': evento,
                            'source_scene': unit.get('source_scene'), 'speaker': sujeito if unit.get('speaker') else None}
        shot['state_before'], shot['state_after'] = antes, copy.deepcopy(estado)
        shot['ground_objects'] = [dict(v, id=k) for k, v in estado['objects'].items()
                                  if v.get('owner') is None and v.get('scene') == shot['scene']]
        for obj in shot['ground_objects']:
            if obj['id'] == objeto and evento == 'abandono':
                obj['visible_after'] = dur * .55
                estado['objects'][objeto]['mark'] = marca
                obj['mark'] = marca
        if evento == 'pega' and objeto in antes['objects'] and antes['objects'][objeto].get('owner') is None:
            shot['ground_objects'].append(dict(antes['objects'][objeto], id=objeto, visible_until=dur * .55))
        shot['state_after'] = copy.deepcopy(estado)
        if objeto and evento:
            shot['camera'] = {'zoom': 1.22, 'focus': 0}
            shot['director_notes']['shot'] = 'detail' if evento == 'descoberta' else 'medium'
            shot['director_notes']['reason'] = 'Mostrar a relação entre agente, objeto e consequência'
        elif unit.get('speaker') and len(actors) > 1:
            shot['camera'] = {'zoom': 1.08}
            shot['director_notes']['shot'] = 'two_shot'
            shot['director_notes']['reason'] = 'Manter falante e ouvinte visíveis com eixo de olhar consistente'
        presentes, anterior = ativos, sujeito
    usados = {a['char'] for s in episodio['shots'] for a in s['actors']}
    episodio['cast'] = {k: v for k, v in cast.items() if k in usados}
    episodio['characters'] = {k: v['visual'] for k, v in episodio['cast'].items() if k not in (travados or {})}
    episodio['staging_findings'] = avisos
    episodio['world_state'] = estado
    return episodio
