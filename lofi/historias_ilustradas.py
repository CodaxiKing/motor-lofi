"""Modo opcional: histórias editáveis montadas com elenco e cenários ilustrados reais.

Não substitui o rig, o modo imagens existente ou a produção das séries atuais.
O gerador usa um arco editorial explícito; não é uma chamada oculta a um LLM.
"""
import copy
import json
import math
import os
from pathlib import Path
from PIL import Image
from .perfis_duracao import planejar

RAIZ = Path(__file__).resolve().parents[1]
CATALOGO = RAIZ / 'biblioteca' / 'ilustrada' / 'v1' / 'catalogo.json'


def carregar(caminho=CATALOGO):
    return json.loads(Path(caminho).read_text(encoding='utf-8'))


def arquivo(catalogo_path, nome):
    if not isinstance(nome, str) or not nome or '\\' in nome:
        raise ValueError('Identificador de imagem inválido')
    raiz = Path(catalogo_path).resolve().parent / 'imagens'
    alvo = (raiz / (nome + '.png')).resolve()
    if not alvo.is_relative_to(raiz.resolve()): raise ValueError('Identificador de imagem inválido')
    return alvo



def validar_catalogo(caminho=CATALOGO):
    catalogo = carregar(caminho); problemas = []
    for chave, pessoa in catalogo.get('personagens', {}).items():
        for pose, item in {**pessoa.get('poses', {}), **pessoa.get('microposes', {})}.items():
            p = arquivo(caminho, item['img'])
            if not p.is_file():
                problemas.append(f'{chave}/{pose}: PNG ausente')
                continue
            with Image.open(p) as im:
                if 'A' not in im.getbands() or im.getchannel('A').getextrema()[0] == 255 or im.getchannel('A').getextrema()[1] == 0:
                    problemas.append(f'{chave}/{pose}: precisa de recorte visível com transparência')
            ancora = item.get('ancora', [.5, 1])
            if len(ancora) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 1 for v in ancora):
                problemas.append(f'{chave}/{pose}: âncora inválida')
    for chave, lugar in catalogo.get('cenarios', {}).items():
        p = arquivo(caminho, lugar['img'])
        if not p.is_file(): problemas.append(f'{chave}: cenário ausente')
        for vizinho in lugar.get('ligacoes', []):
            if vizinho not in catalogo['cenarios']: problemas.append(f'{chave}: ligação inexistente {vizinho}')
    if not catalogo.get('personagens') or not catalogo.get('cenarios'):
        problemas.append('Catálogo precisa de personagens e cenários')
    return problemas


def inventario(caminho=CATALOGO):
    c = carregar(caminho)
    return {'personagens': {k: {'nome': p['nome'], 'tipo': p.get('tipo', 'pessoa'), 'poses': list(p['poses'])}
                            for k, p in c['personagens'].items()},
            'cenarios': {k: p['descricao'] for k, p in c['cenarios'].items()},
            'modo': 'ilustrado opcional; os modos existentes permanecem disponíveis'}


def gerar_historia(caminho=CATALOGO, *, titulo='A voz que ficou lá fora', protagonista='lucas', apoio='teo', vilao='mimico', ideia=None, duracao=90):
    c = carregar(caminho)
    vilao = c.get('aliases', {}).get(vilao, vilao)
    for p in (protagonista, apoio, vilao):
        if p not in c['personagens']: raise ValueError(f'Personagem não disponível: {p}')
    if len({protagonista, apoio, vilao}) < 3:
        raise ValueError('Use identidades diferentes para protagonista, apoio e ameaça')
    if c['personagens'][protagonista].get('tipo') == 'criatura' or c['personagens'][apoio].get('tipo') == 'criatura':
        raise ValueError('Este arco precisa de dois protagonistas humanos')
    planejar('curto', duracao)
    nome = c['personagens'][apoio]['nome']
    # Rascunho com causa, pista, descoberta, entrega e custo; texto editável antes do áudio.
    textos = [
        f'Prometi voltar com {nome} antes de amanhecer. A chuva parou. Ninguém veio buscar a gente. Então ouço três batidas e uma voz conhecida atrás da porta.',
        f'É a voz de {nome}. Mas {nome} está aqui comigo. A voz repete a frase inteira. Até a tosse no final sai exatamente igual.',
        f'Alcanço a maçaneta. A porta está aberta. {nome} pede que eu não responda. Quero investigar, mas prometi proteger quem veio comigo. Seguimos sem nos separar.',
        'O chamado vem da porta dos fundos. A frase se repete sem mudar uma sílaba. Faço uma pergunta que só nós sabemos responder. Silêncio.',
        f'{nome} reconhece a gravação que fez antes de chegarmos. Alguém está copiando o áudio. A entrada principal se fechou. Precisamos procurar saída pela porta dos fundos.',
        f'Chegamos juntos à trilha atrás do abrigo. A voz vem das árvores. Eu paro. {nome} está ao meu lado. Não precisamos seguir aquele chamado.',
        'Uma forma alta aparece entre os troncos. O rosto está errado, mas a voz continua perfeita. Não era alguém perdido. Era uma armadilha.',
        f'Recuo para perto de {nome}. A criatura para quando deixamos de responder. Descobrimos quem chamou, mas ainda não saímos daqui. Uma luz aparece entre as árvores.',
        f'Cumpri a promessa de não abandonar {nome}. Agora precisamos decidir: seguir a luz e arriscar outra imitação, ou esperar juntos, sem abrigo, com a criatura por perto.'
    ]
    locais = ['entrada', 'entrada', 'entrada', 'corredor', 'corredor', 'floresta', 'floresta', 'floresta', 'floresta']
    causas = ['', 'As batidas exigem conferir de onde vem a voz', 'A duplicação da voz faz o grupo investigar sem se separar',
              'O corredor vazio leva a testar o chamado', 'A repetição exata permite reconhecer a gravação',
              'A entrada fechada obriga a buscar saída pela porta dos fundos', 'O chamado da trilha faz o grupo parar e observar',
              'A presença da criatura revela o perigo de responder', 'Recusar o chamado preserva o grupo, mas deixa a fuga sem solução']
    resultados = ['O chamado inicia a investigação', 'O grupo sabe que não é a voz da pessoa presente',
                  'A investigação continua com os dois juntos', 'A voz falha ao responder uma pergunta',
                  'O grupo identifica a gravação e precisa buscar outra saída', 'O grupo interrompe a aproximação ao chamado',
                  'O imitador é identificado como ameaça', 'O grupo deixa de responder e se reúne', 'Uma escolha com risco em ambos os caminhos fica aberta']
    def pose(p, preferida):
        if preferida not in c['personagens'][p]['poses']:
            raise ValueError(f'Gere a pose {preferida} de {p} antes de usar este arco')
        return preferida
    cenas = []
    for i, texto in enumerate(textos):
        pp = ('celular' if i == 0 else 'macaneta' if i == 2 else 'medo' if i >= 5 else 'neutro')
        atores = [{'id': protagonista, 'pose': pose(protagonista, pp), 'pos': .3},
                  {'id': apoio, 'pose': pose(apoio, 'medo' if i >= 5 else 'neutro'), 'pos': .72}]
        if i == 2:
            # Blocking para a maçaneta do fundo de entrada, não para o outro ator.
            atores[0].update(pos=.48, altura=.52, chao=.82, espelhar=False)
            atores[1].update(pos=.17)
        if i in (6, 7):
            atores.insert(0, {'id': vilao, 'pose': pose(vilao, 'neutro'), 'pos': .58, 'altura': .43, 'chao': .69})
        cena = {'n': i+1, 'cenario': locais[i], 'narracao': texto, 'acontecimento': resultados[i],
                'consequencia': resultados[i], 'personagens': atores}
        if i: cena['causa'] = {'cena': i, 'texto': causas[i]}
        cenas.append(cena)
    cenas[0]['conflito_pessoal'] = {'personagem': protagonista, 'desejo': f'Proteger {nome} e voltar', 'custo': 'Investigar o chamado pode separar o grupo'}
    cenas[1]['planta'] = [{'id': 'voz_gravada', 'texto': 'A frase e a tosse se repetem exatamente'}]
    cenas[4]['revela'] = [{'id': 'voz_gravada', 'texto': 'A mensagem do celular está sendo imitada'}]
    cenas[4]['paga'] = [{'id': 'voz_gravada', 'texto': 'O grupo deixa de tratar a voz como pessoa pedindo socorro'}]
    cenas[7]['resolve'] = [{'id': 'quem_chama', 'texto': 'O chamado vem de um imitador tentando atrair o grupo'}]
    cenas[8]['abre'] = [{'id': 'luz_segura', 'texto': 'A luz é uma saída ou outra armadilha?'}]
    return {'version': 1, 'titulo': titulo, 'ideia_do_usuario': ideia, 'metodo': 'rascunho por arco editorial editável; sem LLM oculto',
            'perfil': 'curto', 'duracao': duracao, 'narrador': protagonista, 'cenas': cenas,
            'escolhas': {'A': {'label': 'SEGUIR A LUZ', 'texto': 'Seguir a luz', 'ganha': 'chance de encontrar a estrada',
                              'perde': 'segurança de ficar junto ao abrigo', 'motivo': 'A criatura pode imitar uma saída'},
                         'B': {'label': 'ESPERAR JUNTOS', 'texto': 'Esperar juntos', 'ganha': 'evitar seguir o chamado',
                              'perde': 'tempo e abrigo antes da madrugada', 'motivo': 'A criatura continua perto da trilha'}}}


def validar_historia(historia, catalogo):
    regras = planejar(historia.get('perfil', 'curto'), historia.get('duracao', 90))
    cenas = historia.get('cenas', [])
    if len(cenas) < regras['min_cenas']: raise ValueError(f"Perfil exige {regras['min_cenas']} cenas")
    numeros = [s.get('n') for s in cenas]
    if numeros != list(range(1, len(cenas)+1)): raise ValueError('Cenas precisam de numeração contínua e única')
    for i, s in enumerate(cenas):
        if s.get('cenario') not in catalogo['cenarios']: raise ValueError(f'Cenário ausente: {s.get("cenario")}')
        if not s.get('narracao', '').strip(): raise ValueError(f'Cena {i+1} sem narração')
        if i and s['cenario'] != cenas[i-1]['cenario'] and s['cenario'] not in catalogo['cenarios'][cenas[i-1]['cenario']].get('ligacoes', []):
            raise ValueError(f'Não há ligação entre cenários na cena {i+1}')
        if i and (s.get('causa') or {}).get('cena') != i: raise ValueError(f'Cena {i+1} sem causa ligada à anterior')
        ids = [a.get('id') for a in s.get('personagens', [])]
        if len(ids) != len(set(ids)): raise ValueError(f'Personagem duplicado na cena {i+1}')
        for a in s.get('personagens', []):
            if a.get('id') not in catalogo['personagens']: raise ValueError(f'Personagem ausente: {a.get("id")}')
            if a.get('pose') not in catalogo['personagens'][a['id']]['poses']: raise ValueError(f'Pose ausente: {a["id"]}/{a.get("pose")}')
            for campo, padrao in (('pos', .5), ('altura', .6), ('chao', .93)):
                valor = a.get(campo, padrao)
                if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor) or not 0 < valor <= 1:
                    raise ValueError(f'Posição/escala inválida: {campo}')
    if set(historia.get('escolhas', {})) != {'A', 'B'}: raise ValueError('História interativa precisa das escolhas A/B')
    return regras


def roteiro_md(historia):
    linhas = [f'# {historia["titulo"]}', '', f'Perfil de duração: {historia["perfil"]}',
              'Formato: 100% narrado', '', 'EPISÓDIO 1/? · rascunho independente', '']
    for s in historia['cenas']:
        linhas += [f'## CENA {s["n"]}', f'CENÁRIO: {s["cenario"]}', f'ACONTECIMENTO: {s["acontecimento"]}',
                   f'CONSEQUÊNCIA: {s["consequencia"]}']
        if s.get('causa'): linhas.append(f'CAUSA: CENA {s["causa"]["cena"]} — {s["causa"]["texto"]}')
        if s.get('conflito_pessoal'):
            p = s['conflito_pessoal']; linhas.append(f'CONFLITO PESSOAL: {p["personagem"]} | DESEJO: {p["desejo"]} | CUSTO: {p["custo"]}')
        for campo in ('planta', 'revela', 'paga', 'resolve', 'abre'):
            for p in s.get(campo, []): linhas.append(f'{campo.upper()}: {p["id"]} | {p["texto"]}')
        linhas += ['RECORTES: ' + ', '.join(a['id']+'/'+a['pose'] for a in s['personagens']), f'NARRAÇÃO: {s["narracao"]}', '']
    linhas += ['## ESCOLHA']
    for letra, op in historia['escolhas'].items():
        linhas.append(f'{letra}) {op["texto"]} | GANHA: {op["ganha"]} | PERDE: {op["perde"]} | MOTIVO: {op["motivo"]}')
    return '\n'.join(linhas)+'\n'


def compilar(historia, caminho=CATALOGO, pasta_saida=None):
    c = carregar(caminho); validar_historia(historia, c)
    pendencias = validar_catalogo(caminho)
    if pendencias: raise ValueError('; '.join(pendencias))
    base = Path(caminho).resolve().parent
    pasta = Path(pasta_saida or base).resolve()
    raiz_relativa = os.path.relpath(base, pasta)
    total = historia['duracao']; corpo = total-6; shots = []; clock = 0
    duracoes = [len(s['narracao'].split()) for s in historia['cenas']]
    for i, s in enumerate(historia['cenas']):
        fim = round(clock + corpo * duracoes[i]/sum(duracoes), 3)
        if i == len(duracoes)-1: fim = corpo
        pessoas = []
        for a in s['personagens']:
            p = c['personagens'][a['id']]; ficha = p['poses'][a['pose']]
            pessoas.append({'img': ficha['img'], 'pos': a.get('pos', .5), 'altura': a.get('altura', .6),
                            'chao': a.get('chao', .93), 'ancora': ficha.get('ancora', [.5,1]),
                            'espelhar': a.get('espelhar', a.get('pos', .5) > .5), 'piscar': False,
                            'respirar': a.get('respirar', .5), 'balanco_corpo': a.get('balanco_corpo', .5)})
            micro = p.get('microposes', {}).get(a['pose'] + '_piscando')
            if micro:
                pessoas[-1]['piscadas'] = {ficha['img']: micro['img']}
                pessoas[-1]['ancoras'] = {micro['img']: micro.get('ancora', ficha.get('ancora', [.5, 1]))}
            olhar = p.get('microposes', {}).get(a['pose'] + '_olhar')
            if olhar: pessoas[-1]['olhares'] = {ficha['img']: olhar['img']}
        plano = s.get('plano', 'medio' if i in (0, 3, 7) else 'aberto')
        cfg = {'pasta_biblioteca': raiz_relativa, 'fundo': c['cenarios'][s['cenario']]['img'],
               'personagens': pessoas, 'aproximar': .2, 'balanco': .15, 'plano': plano, 'alvo': 0}
        shot = {'start': clock, 'end': fim, 'imagens': cfg, 'scene': s['cenario'],
                'director_notes': {'text': s['narracao'], 'source_scene': s['n'], 'shot': plano}}
        if i == 0: shot['hook'] = {'text': 'A VOZ ERA IGUAL.\nMAS VINHA DE FORA.'}
        shots.append(shot); clock = fim
    lados = {letra.lower(): {'label': op['label'], 'scene': historia['cenas'][-1]['cenario'],
                             'imagens': copy.deepcopy(shots[-1]['imagens'])}
             for letra, op in historia['escolhas'].items()}
    shots.append(dict(start=clock, end=total, type='choice', **lados))
    from .editorial import estruturar
    texto = roteiro_md(historia)
    estimado = sum(duracoes)/3
    return {'out': 'episodio_ilustrado.mp4', 'fps': 24, 'total': total, 'episode': 1, 'loop': False,
            'duration_profile': historia['perfil'], 'character_rendering': 'illustrated_library', 'narrado': True,
            'series_title': historia['titulo'], 'shots': shots, 'voices': {}, 'clips': [], 'subs': [],
            'source_story': texto, 'narrative_plan': estruturar(texto),
            'audio_plan': {'target_s': total, 'estimated_s': round(estimado,1), 'synced': False},
            'production_status': 'rascunho visual; gravar e sincronizar narração antes do vídeo final'}


def salvar(historia, destino, caminho=CATALOGO):
    destino = Path(destino).resolve()
    ep = compilar(historia, caminho, destino)
    if destino.exists(): raise FileExistsError(f'Escolha uma pasta nova: {destino}')
    from .studio import quality_report
    from .dramaturgia import formatar_relatorio
    relatorio = quality_report(ep)
    destino.mkdir(parents=True)
    for nome, dado in (('historia.json', historia), ('episodio.json', ep), ('qualidade.json', relatorio)):
        (destino/nome).write_text(json.dumps(dado, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (destino/'roteiro.md').write_text(roteiro_md(historia), encoding='utf-8')
    (destino/'narracao.txt').write_text('\n\n'.join(s['narracao'] for s in historia['cenas']), encoding='utf-8')
    (destino/'dramaturgia.md').write_text(formatar_relatorio(relatorio['dramaturgy']), encoding='utf-8')
    return {'folder': str(destino), 'episode': str(destino/'episodio.json'), 'status': 'draft_needs_review'}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogo', default=str(CATALOGO))
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('listar'); sub.add_parser('validar')
    p = sub.add_parser('criar'); p.add_argument('destino'); p.add_argument('--titulo', default='A voz que ficou lá fora')
    p.add_argument('--ideia'); p.add_argument('--protagonista', default='lucas'); p.add_argument('--apoio', default='teo')
    p.add_argument('--vilao', default='mimico'); p.add_argument('--duration', type=float, default=90)
    p = sub.add_parser('compilar'); p.add_argument('historia'); p.add_argument('destino')
    args = parser.parse_args()
    if args.command == 'listar': resultado = inventario(args.catalogo)
    elif args.command == 'validar':
        resultado = validar_catalogo(args.catalogo)
        print(json.dumps(resultado, ensure_ascii=False, indent=2)); raise SystemExit(bool(resultado))
    else:
        historia = carregar(args.historia) if args.command == 'compilar' else gerar_historia(args.catalogo,
            titulo=args.titulo, protagonista=args.protagonista, apoio=args.apoio, vilao=args.vilao, ideia=args.ideia, duracao=args.duration)
        resultado = salvar(historia, args.destino, args.catalogo)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
