"""Contrato de produção para novas identidades, sem promover rascunhos a arte pronta."""
import argparse
import copy
import hashlib
import json
import math
import re
from pathlib import Path

from PIL import Image

BASE = Path(__file__).resolve().parents[1] / 'biblioteca/ilustrada/v1'


def carregar(base=BASE):
    return json.loads((Path(base) / 'padrao_criacao.json').read_text(encoding='utf-8'))


def requisitos(padrao, tipo):
    if tipo not in ('humano', 'zumbi', 'skinwalker', 'monstro'):
        raise ValueError('Tipo deve ser humano, zumbi, skinwalker ou monstro')
    return dict(padrao['acoes_comuns'], **padrao['acoes_humanos' if tipo == 'humano' else 'acoes_monstros'])


def modelo(identidade, tipo, padrao=None):
    if not re.fullmatch(r'[a-z][a-z0-9_]*', identidade):
        raise ValueError('Use identificador minúsculo com letras, números e sublinhado')
    p = padrao or carregar()
    acoes = requisitos(p, tipo)
    pasta = ('personagens' if tipo == 'humano' else 'monstros') + '/' + identidade
    return {
        'version': 2, 'padrao_criacao': p['version'], 'id': identidade, 'nome': identidade,
        'tipo_movimento': tipo, 'estado_producao': 'rascunho', 'altura_m': None,
        'preferencia_animacao': 'quadros', 'pasta_assets': pasta,
        'perfil_movimento': copy.deepcopy(p['perfis_monstros'].get(tipo, {})),
        'ciclos_direcionais': {angulo: {acao: None for acao in acoes} for angulo in p['angulos']},
        'transicoes_direcionais': {angulo: {t: {'ciclo': None, 'duracao': .5} for t in p['transicoes']} for angulo in p['angulos']},
        'encaixes_items': {angulo: {'frames': []} for angulo in p['angulos']} if tipo == 'humano' else {},
        'items_obrigatorios': p['items'] if tipo == 'humano' else [],
        'items_direcionais': {item: {a: {'img': None, 'ancora': [.5, .5]} for a in p['angulos']} for item in p['items']} if tipo == 'humano' else {},
        'revisao_visual': {nome: False for nome in p['qualidade']['revisao']},
        'notas': 'Preencher com PNGs e ciclos reais. Nenhum caminho nulo representa animação pronta.',
    }


def _arquivo(base, nome):
    raiz = (Path(base) / 'imagens').resolve()
    if not isinstance(nome, str) or not nome or '\\' in nome:
        raise ValueError('Caminho de asset ausente ou inválido')
    p = (raiz / nome).resolve()
    if not p.is_relative_to(raiz):
        raise ValueError('Asset fora da biblioteca')
    return p


def validar_ficha(ficha, base=BASE, padrao=None):
    from .ciclos_quadros import carregar as ler_ciclo, arquivos, imagem_frame
    p = padrao or carregar(base)
    erros = []
    tipo = ficha.get('tipo_movimento')
    try:
        acoes = requisitos(p, tipo)
    except ValueError as exc:
        return [str(exc)]
    if ficha.get('padrao_criacao') != p['version']:
        erros.append('Versão do padrão de criação ausente ou incompatível')
    if ficha.get('estado_producao') != 'pronto':
        erros.append('Ficha ainda é rascunho')
    altura = ficha.get('altura_m')
    if isinstance(altura, bool) or not isinstance(altura, (int, float)) or not math.isfinite(altura) or not .2 <= altura <= 5:
        erros.append('Altura física não calibrada')
    if ficha.get('preferencia_animacao') != 'quadros':
        erros.append('Novas identidades devem usar quadros completos')
    identidade = ficha.get('id', '')
    prefixo = ('personagens' if tipo == 'humano' else 'monstros') + '/' + identidade + '/'
    revisao = ficha.get('revisao_visual', {})
    for campo in p['qualidade']['revisao']:
        if revisao.get(campo) is not True:
            erros.append('Revisão visual pendente: ' + campo)
    if tipo != 'humano':
        for acao in p['acoes_monstros']:
            if not ficha.get('perfil_movimento', {}).get(acao, '').strip():
                erros.append('Coreografia própria não descrita: ' + acao)
        if ficha.get('encaixes_items') or ficha.get('items_obrigatorios') or ficha.get('items_direcionais'):
            erros.append('Monstros não usam o banco modular humano de itens')
    else:
        for item in p['items']:
            if item not in ficha.get('items_obrigatorios', []):
                erros.append('Item modular obrigatório ausente: ' + item)
            for angulo in p['angulos']:
                try:
                    objeto = ficha.get('items_direcionais', {}).get(item, {}).get(angulo, {})
                    nome = objeto.get('img')
                    if not isinstance(nome, str) or not nome.startswith('items/'):
                        raise ValueError('Item deve estar na pasta items')
                    ancora = objeto.get('ancora', [])
                    if len(ancora) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 1 for v in ancora):
                        raise ValueError('Âncora de item inválida')
                    with Image.open(_arquivo(base, nome + '.png')) as im:
                        if 'A' not in im.getbands() or im.getchannel('A').getextrema()[0] == 255 or not im.getchannel('A').getbbox():
                            raise ValueError('Item precisa de PNG visível e transparente')
                except (ValueError, OSError, TypeError) as exc:
                    erros.append(f'{item}/{angulo}: {exc}')

    def conferir(nome, minimo, etiqueta, acao, angulo):
        try:
            if not isinstance(nome, str) or not nome.startswith(prefixo):
                raise ValueError('Ciclo deve pertencer à própria identidade em ' + prefixo)
            c = ler_ciclo(base, nome)
            if c.get('tipo') != 'corpo_inteiro':
                raise ValueError('Movimento precisa do corpo inteiro')
            if acao in ('andar','correr') and (not c.get('deslocamento_corpo_ciclo') or not c.get('contatos_solo')):
                raise ValueError('Locomoção exige passada e contatos_solo calibrados')
            if c.get('identidade') != identidade or c.get('angulo') != angulo or c.get('acao') != acao:
                raise ValueError('Identidade, ângulo ou ação do ciclo não correspondem à ficha')
            if len(c['frames']) < minimo:
                raise ValueError(f'Precisa de pelo menos {minimo} desenhos')
            for img in arquivos(c):
                if not img.startswith(prefixo):
                    raise ValueError('Imagem emprestada de outra identidade')
                with Image.open(_arquivo(base, img + '.png')) as im:
                    if 'A' not in im.getbands() or im.getchannel('A').getextrema()[0] == 255:
                        raise ValueError('PNG precisa de transparência real')
            desenhos = set()
            for i in range(len(c['frames'])):
                im = imagem_frame(c, i, base=base)
                desenhos.add(hashlib.sha256(im.tobytes()).digest())
                box = im.getchannel('A').getbbox()
                if not box:
                    raise ValueError('Quadro vazio')
                # A altura é a referência ereta comum ao ciclo, não a silhueta agachada.
                pixels = c['referencia'].get('altura_celula_px', im.height) * c['referencia']['altura_corpo']
                if pixels < p['qualidade']['min_altura_corpo_px']:
                    raise ValueError('Resolução do corpo abaixo do padrão')
            if len(desenhos) < minimo:
                raise ValueError('Exposições repetidas não contam como novos desenhos')
            return c
        except (ValueError, KeyError, OSError, TypeError) as exc:
            erros.append(f'{etiqueta}: {exc}')

    for angulo in p['angulos']:
        ciclos = ficha.get('ciclos_direcionais', {}).get(angulo, {})
        for acao, regra in acoes.items():
            c = conferir(ciclos.get(acao), regra['min_quadros'], angulo + '/' + acao, acao, angulo)
            if c and tipo == 'humano' and acao == 'segurar_item':
                encaixes = ficha.get('encaixes_items', {}).get(angulo, {}).get('frames', [])
                if len(encaixes) != len(c['frames']) or any(
                    len(f.get('mao', [])) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 1 for v in f['mao'])
                    for f in encaixes
                ):
                    erros.append(angulo + ': encaixe da mão ausente por quadro de segurar_item')
        for transicao in p['transicoes']:
            t = ficha.get('transicoes_direcionais', {}).get(angulo, {}).get(transicao, {})
            conferir(t.get('ciclo'), p['min_quadros_transicao'], angulo + '/' + transicao, transicao, angulo)
            duracao = t.get('duracao')
            if not isinstance(duracao, (int, float)) or not math.isfinite(duracao) or duracao <= 0:
                erros.append(angulo + '/' + transicao + ': duração inválida')
    return erros


def auditar_catalogo(catalogo, base=BASE):
    p = carregar(base)
    resultado = {}
    for identidade, registro in catalogo.get('personagens', {}).items():
        nome = registro.get('arquivo_ficha')
        if identidade in p['legados'] and not registro.get('padrao_criacao'):
            resultado[identidade] = {'estado': 'legado', 'notas': 'Compatível com produções existentes; cobertura direcional ainda não certificada.'}
            continue
        try:
            ficha = json.loads(_arquivo(base, nome).read_text(encoding='utf-8'))
            erros = validar_ficha(ficha, base, p)
            if ficha.get('id') != identidade:
                erros.append('ID da ficha difere do catálogo')
            if registro.get('tipo') != ('humano' if ficha.get('tipo_movimento') == 'humano' else 'criatura'):
                erros.append('Tipo do catálogo difere da ficha')
        except (ValueError, OSError, TypeError) as exc:
            erros = [str(exc)]
        resultado[identidade] = {'estado': 'pendente' if erros else 'pronto', 'erros': erros}
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=BASE,help='Pasta da biblioteca a auditar ou validar')
    sub = parser.add_subparsers(dest='comando', required=True)
    novo = sub.add_parser('novo')
    novo.add_argument('id')
    novo.add_argument('--tipo', choices=('humano', 'zumbi', 'skinwalker', 'monstro'), required=True)
    novo.add_argument('--saida', type=Path, required=True)
    val = sub.add_parser('validar')
    val.add_argument('ficha', type=Path)
    sub.add_parser('auditar')
    args = parser.parse_args()
    if args.comando == 'novo':
        dados = modelo(args.id, args.tipo,carregar(args.base))
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        with args.saida.open('x', encoding='utf-8') as f:
            f.write(json.dumps(dados, ensure_ascii=False, indent=2) + '\n')
        print(args.saida)
    elif args.comando == 'validar':
        erros = validar_ficha(json.loads(args.ficha.read_text(encoding='utf-8')),args.base)
        print(json.dumps(erros, ensure_ascii=False, indent=2))
        return bool(erros)
    else:
        cat = json.loads((args.base / 'catalogo.json').read_text(encoding='utf-8'))
        relatorio = auditar_catalogo(cat,args.base)
        print(json.dumps(relatorio, ensure_ascii=False, indent=2))
        return any(r['estado'] == 'pendente' for r in relatorio.values())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
