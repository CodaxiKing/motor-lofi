"""Revisão rastreável dos seis critérios dramáticos, sem reescrever a história.

python -m lofi.dramaturgia roteiro.md
Campos documentados em examples/roteiro_dramatico.md. Declarações editoriais
não comprovam causalidade ou qualidade literária: o autor revisa as evidências.
"""
import json
import re
import unicodedata


def norm(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto).lower())
                   if unicodedata.category(c) != 'Mn').strip()


def preenchido(texto):
    return bool(str(texto or '').strip()) and norm(texto) not in (
        '...', 'nenhum', 'nenhuma', 'n/a', 'a definir', 'todo', 'tbd', '?', '-')


def partes(valor):
    pedacos = [p.strip() for p in valor.split('|')]
    campos = {'texto': pedacos[0]}
    for p in pedacos[1:]:
        if ':' in p:
            k, v = p.split(':', 1)
            campos[norm(k)] = v.strip()
    return campos


def ler_texto(texto):
    cenas, atual, escolhas = [], None, {}
    final = bool(re.search(r'^\s*(?:ENCERRAMENTO:\s*final|(?:#+\s*)?FIM[.!]?)\s*$', texto, re.M | re.I))
    for numero, linha in enumerate(texto.splitlines(), 1):
        m = re.match(r'^\s*#+\s*CENA\s+(\d+)\b', linha, re.I)
        if m:
            n = int(m[1])
            atual = {'n': n, 'linha': numero, 'falas': [], 'planta': [], 'revela': [],
                     'paga': [], 'resolve': [], 'abre': [], 'corpo': []} if n else None
            if atual is not None:
                cenas.append(atual)
            continue
        op = re.match(r'^\s*([AB])\)\s*(.+)', linha)
        if op:
            escolhas[op[1]] = partes(op[2])
            continue
        if re.match(r'^\s*#+\s+', linha):
            atual = None
            continue
        if atual is None:
            continue
        atual['corpo'].append(linha)
        campo = re.match(r'^\s*(?:\*\*)?([^:]+?)(?:\*\*)?\s*:\s*(.+)', linha)
        if not campo:
            continue
        chave, valor = norm(campo[1]), campo[2].strip()
        if chave == 'causa':
            ref = re.match(r'CENA\s+(\d+)\s*(?:[—:|-]\s*)?(.*)', valor, re.I)
            atual['causa'] = {'cena': int(ref[1]), 'texto': ref[2]} if ref else {'texto': valor}
        elif chave in ('acontecimento', 'consequencia'):
            atual[chave] = valor
        elif chave == 'conflito pessoal':
            atual['conflito_pessoal'] = partes(valor)
        elif chave in ('planta', 'revela', 'paga', 'resolve', 'abre'):
            identificador, _, explicacao = valor.partition('|')
            atual[chave].append({'id': identificador.strip(), 'texto': explicacao.strip()})
        elif chave == 'fala':
            fala = partes(valor)
            fala['personagem'] = valor.split('|')[0].strip()
            fala['texto'] = fala.get('texto_fala', fala.get('fala', ''))
            # TEXTO: é o conteúdo dito; o primeiro segmento identifica o falante.
            for p in valor.split('|')[1:]:
                if norm(p.split(':', 1)[0]) == 'texto' and ':' in p:
                    fala['texto'] = p.split(':', 1)[1].strip()
            atual['falas'].append(fala)
        elif re.fullmatch(r'[A-ZÀ-Ú_ ]{2,30}', campo[1]) and chave not in METADADOS:
            atual['falas'].append({'personagem': campo[1], 'texto': valor})
    return cenas, escolhas, final


METADADOS = set(map(norm, ('CENÁRIO', 'CENARIO', 'PERSONAGENS', 'PERSONAGEM', 'PLANO',
    'TRANSIÇÃO', 'CÂMERA', 'LUZ', 'LUZ E DETALHES', 'SOM', 'SONS', 'NARRAÇÃO', 'LEGENDA',
    'LIGAÇÃO', 'INSERÇÃO', 'IMAGENS', 'VIRADA', 'PENSAMENTO', 'O PLANO', 'CONFLITO',
    'SUBTRAMA', 'SEQUÊNCIA', 'TEXTO', 'FALA DO GANCHO', 'PLANO DE DETALHE', 'ENTRA',
    'SAI', 'PEGA', 'LARGA', 'ANIMAÇÃO', 'CONSEQUÊNCIA', 'CAUSA', 'ACONTECIMENTO',
    'CONFLITO PESSOAL', 'PLANTA', 'REVELA', 'PAGA', 'RESOLVE', 'ABRE', 'PERGUNTA',
    'ENCERRAMENTO', 'INTENÇÃO', 'IMAGENS POR FRASE', 'SUJEITO', 'DESTINATÁRIO', 'MARCA')))


CRITERIOS = ('causalidade', 'conflito_pessoal', 'dialogo_intencional',
             'revelacao_preparada', 'escolha_dificil', 'entrega_episodio')
INTENCOES = {'convencer', 'esconder', 'provocar', 'conseguir', 'proteger',
            'ameacar', 'investigar', 'recusar', 'negociar', 'consolar'}


def revisar(cenas, escolhas=None, final=False, pistas_anteriores=()):
    achados = []
    def aviso(criterio, codigo, cena, mensagem, sugestao, nivel='warning'):
        achados.append({'criterion': criterio, 'code': codigo, 'scene': cena,
                        'line': next((c.get('linha') for c in cenas if c['n'] == cena), None),
                        'severity': nivel, 'message': mensagem, 'suggestion': sugestao})
    if not cenas:
        aviso('causalidade', 'cenas_nao_documentadas', None, 'Não há cenas numeradas para revisar os elos',
              'Separe o roteiro em seções ## CENA 1, ## CENA 2, ...')
    numeros = [c['n'] for c in cenas]
    if len(numeros) != len(set(numeros)):
        aviso('causalidade', 'cena_duplicada', None, 'Número de cena repetido', 'Use números únicos', 'error')
    for i, cena in enumerate(cenas):
        n = cena['n']
        if not preenchido(cena.get('acontecimento')):
            aviso('causalidade', 'acontecimento_ausente', n, 'A cena não documenta uma ação ou acontecimento',
                  'Escreva ACONTECIMENTO: com algo que acontece na tela')
        if not preenchido(cena.get('consequencia')):
            aviso('causalidade', 'consequencia_ausente', n, 'A cena não documenta o que mudou',
                  'Escreva CONSEQUÊNCIA: com uma mudança concreta')
        if i:
            causa = cena.get('causa') if isinstance(cena.get('causa'), dict) else {}
            ref = causa.get('cena')
            if ref != cenas[i-1]['n'] or not preenchido(causa.get('texto')):
                invalida = ref is not None and ref not in numeros[:i]
                aviso('causalidade', 'causa_invalida' if invalida else 'elo_causal_ausente', n,
                      f'Causa não ligada à consequência da cena {cenas[i-1]["n"]}',
                      f'Use CAUSA: CENA {cenas[i-1]["n"]} — explique por que o resultado exige esta cena',
                      'error' if invalida else 'warning')
    conflitos = [c for c in cenas if all(preenchido((c.get('conflito_pessoal') or {}).get(k))
                                         for k in ('texto', 'desejo', 'custo'))]
    if not conflitos:
        aviso('conflito_pessoal', 'conflito_pessoal_ausente', None,
              'Não há desejo pessoal em choque com um custo documentado',
              'Use CONFLITO PESSOAL: personagem | DESEJO: ... | CUSTO: ...')
    falas = [(c['n'], f) for c in cenas for f in c.get('falas', [])]
    for n, fala in falas:
        if norm(fala.get('intencao')) not in INTENCOES or not all(preenchido(fala.get(k)) for k in ('alvo', 'objetivo', 'texto')):
            aviso('dialogo_intencional', 'fala_sem_intencao', n,
                  f'Fala de {fala.get("personagem", "?")} sem intenção, alvo ou objetivo verificável',
                  'Documente INTENÇÃO, ALVO e OBJETIVO no campo FALA')
        if re.search(r'como voce sabe|como todos sabem|como eu ja (?:te )?disse', norm(fala.get('texto'))):
            aviso('dialogo_intencional', 'exposicao_compartilhada', n,
                  'A fala repete informação apresentada como conhecida pelos interlocutores',
                  'Dê à informação uma intenção: cobrança, ameaça, tentativa de convencer ou omissão')
    plantas = {p: -1 for p in pistas_anteriores}
    revelacoes, pagamentos = [], []
    for indice, c in enumerate(cenas):
        for r in c.get('revela', []):
            revelacoes.append((c['n'], r['id']))
            if not preenchido(r.get('texto')):
                aviso('revelacao_preparada', 'revelacao_vazia', c['n'],
                      'Revelação sem descoberta descrita', 'Explique o que o público descobre em REVELA')
            if r['id'] not in plantas or plantas[r['id']] >= indice:
                aviso('revelacao_preparada', 'revelacao_sem_planta', c['n'],
                      f'Revelação {r["id"]!r} sem pista anterior', 'Plante o mesmo identificador em uma cena anterior')
        for p in c.get('paga', []):
            if not any(ident == p['id'] for _, ident in revelacoes) or not preenchido(p.get('texto')):
                aviso('revelacao_preparada', 'pagamento_sem_revelacao', c['n'],
                      f'Pagamento {p["id"]!r} não tem revelação anterior ou consequência descrita',
                      'Associe PAGA ao identificador revelado e descreva o que isso provoca')
            else:
                pagamentos.append(p['id'])
        for p in c.get('planta', []):
            if preenchido(p.get('id')) and preenchido(p.get('texto')):
                plantas.setdefault(p['id'], indice)
    for n, identificador in revelacoes:
        if identificador not in pagamentos:
            aviso('revelacao_preparada', 'revelacao_sem_consequencia', n,
                  f'Revelação {identificador!r} não muda uma ação documentada',
                  'Use PAGA: identificador | consequência concreta da descoberta')
    if not revelacoes:
        aviso('revelacao_preparada', 'revelacao_nao_documentada', None,
              'Não há cadeia de pista, revelação e consequência documentada',
              'Use PLANTA, REVELA e PAGA com o mesmo identificador')
    escolhas = escolhas or {}
    if not final:
        for letra in 'AB':
            op = escolhas.get(letra) or {}
            if not all(preenchido(op.get(k)) for k in ('texto', 'ganha', 'perde', 'motivo')):
                aviso('escolha_dificil', 'escolha_sem_troca', None,
                      f'Opção {letra} sem benefício, perda ou motivo ligado à história',
                      f'Use {letra}) ação | GANHA: ... | PERDE: ... | MOTIVO: ...')
            origem = re.fullmatch(r'CENA\s+(\d+)', str(op.get('origem', '')), re.I)
            if op.get('origem') and (not origem or int(origem[1]) not in numeros):
                aviso('escolha_dificil', 'origem_escolha_invalida', None,
                      f'Opção {letra} aponta uma cena inexistente', 'Use ORIGEM: CENA n com uma cena do episódio', 'error')
            if preenchido(op.get('ganha')) and norm(op.get('ganha')) == norm(op.get('perde')):
                aviso('escolha_dificil', 'troca_contraditoria', None,
                      f'Opção {letra} registra o mesmo benefício e perda', 'Descreva um custo distinto do benefício')
        if all(escolhas.get(k) for k in 'AB'):
            a, b = escolhas['A'], escolhas['B']
            if norm(a.get('texto')) == norm(b.get('texto')) or (
                    a.get('ganha') and a.get('perde') and
                    norm(a.get('ganha')) == norm(b.get('ganha')) and norm(a.get('perde')) == norm(b.get('perde'))):
                aviso('escolha_dificil', 'escolhas_equivalentes', None,
                      'Os caminhos oferecem a mesma ação ou a mesma troca', 'Dê consequências diferentes a cada alternativa')
    resolvidas = {p['id'] for c in cenas for p in c.get('resolve', []) if preenchido(p.get('texto'))}
    abertas = {p['id'] for c in cenas for p in c.get('abre', []) if preenchido(p.get('texto'))}
    if not resolvidas:
        aviso('entrega_episodio', 'episodio_sem_entrega', None, 'Nenhuma pergunta recebe resposta documentada',
              'Use RESOLVE: identificador | resposta ou resultado entregue neste episódio')
    if not final and not (abertas - resolvidas):
        aviso('entrega_episodio', 'episodio_sem_nova_pergunta', None,
              'Não há pergunta nova distinta da pergunta resolvida', 'Use ABRE: outro_identificador | nova pergunta')
    return {'method': 'declaracoes_editoriais_requerem_revisao', 'findings': achados,
            'criteria': {k: ('revisar' if any(a['criterion'] == k for a in achados) else
                            'nao_se_aplica' if ((k == 'dialogo_intencional' and not falas) or (k == 'escolha_dificil' and final))
                            else 'documentado') for k in CRITERIOS},
            'ok': not any(a['severity'] == 'error' for a in achados)}


def avaliar_texto(texto):
    return revisar(*ler_texto(texto))


def formatar_relatorio(relatorio):
    linhas = ['# Revisão dramática', '',
              'Os estados indicam documentação editorial, não aprovação automática da história.', '']
    linhas += [f'- {criterio}: {estado}' for criterio, estado in relatorio.get('criteria', {}).items()]
    for a in relatorio.get('findings', []):
        local = f"Cena {a['scene']}" if a.get('scene') is not None else 'Episódio'
        linhas += ['', f"## {local} — {a['code']}", '', a['message'], '', a['suggestion']]
    return '\n'.join(linhas) + '\n'


def avaliar_plano(plano, memoria=None):
    """Revisa cada ramo isoladamente: uma pista de A não prepara a revelação de B."""
    from .narrativa import ramos
    pistas = [p['id'] for p in (memoria or {}).get('pistas', []) if p.get('publico_sabe')]
    resultados = []
    for ramo, cadeia in ramos(plano).items():
        cenas = []
        for c in cadeia:
            cena = dict(c)
            if isinstance(cena.get('causa'), int):
                cena['causa'] = {'cena': cena['causa'], 'texto': c.get('situacao', '')}
            if 'conflito_pessoal' in cena:
                cena['conflito_pessoal'] = dict(cena['conflito_pessoal'])
                cena['conflito_pessoal'].setdefault('texto', cena['conflito_pessoal'].get('personagem', ''))
            for campo in ('planta', 'revela', 'paga', 'resolve', 'abre'):
                cena[campo] = [p if isinstance(p, dict) else {'id': p, 'texto': c.get('consequencia', '')}
                                for p in c.get(campo, [])]
            cenas.append(cena)
        escolhas = {k: (v if isinstance(v, dict) else partes(v))
                    for k, v in (plano.get('pergunta') or {}).items()}
        resultado = revisar(cenas, escolhas, plano.get('final', False), pistas)
        for achado in resultado['findings']:
            achado['branch'] = ramo
        resultados.append(resultado)
    return {'branches': resultados, 'findings': [a for r in resultados for a in r['findings']]}


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('roteiro')
    parser.add_argument('--markdown', action='store_true')
    args = parser.parse_args()
    resultado = avaliar_texto(Path(args.roteiro).read_text(encoding='utf-8'))
    print(formatar_relatorio(resultado) if args.markdown else json.dumps(resultado, ensure_ascii=False, indent=2))
    raise SystemExit(0 if resultado['ok'] else 1)
