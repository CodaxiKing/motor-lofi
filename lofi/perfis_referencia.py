"""Direção por referência: roteiro situacional e composições explícitas, sem trocar identidades."""
import copy
import json
import re
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]/'biblioteca/ilustrada/v1'


def carregar(nome,base=BASE):
    if not isinstance(nome,str) or not re.fullmatch(r'[a-z0-9_]+',nome):
        raise ValueError('Perfil de direção inválido')
    return json.loads((Path(base)/'perfis'/(nome+'.json')).read_text(encoding='utf-8'))


def aplicar(historia,base=BASE):
    nome=historia.get('perfil_direcao')
    if not nome:return historia
    perfil=carregar(nome,base);out=copy.deepcopy(historia)
    out.setdefault('interface',copy.deepcopy(perfil.get('interface',{})))
    for cena in out['cenas']:
        chave=cena.get('composicao_ref')
        if not chave:continue
        if chave not in perfil['composicoes']:raise ValueError('Composição de referência ausente: '+chave)
        preset=perfil['composicoes'][chave]
        cena.setdefault('cenario',preset['cenario'])
        cena.setdefault('composicao','manual')
        cena.setdefault('camera',copy.deepcopy(preset['camera']))
        cena.setdefault('direcao_narrativa',False)
        cena.setdefault('qualidade_visual',False)  # composição calibrada; revisão de pixels é etapa separada
        if 'personagens' not in cena:
            cena['personagens']=[copy.deepcopy(preset['ator'])] if preset.get('ator') else []
        if 'interface' not in cena and preset.get('interface') is False:cena['interface']=False
        if preset.get('interacao_visual'):cena.setdefault('interacao_visual',copy.deepcopy(preset['interacao_visual']))
    return out


def auditar_abertura(historia):
    abertura=historia.get('abertura',{})
    problemas=[]
    for campo in ('situacao','premissa'):
        if not isinstance(abertura.get(campo),str) or not abertura[campo].strip():
            problemas.append('Abertura sem '+campo)
    texto=' '.join(c.get('narracao','')+' '+' '.join(f.get('texto','') for f in c.get('falas',[])) for c in historia.get('cenas',[])[:1]).strip()
    if not problemas:
        if not texto.startswith(abertura['situacao'].strip()):problemas.append('Primeira frase precisa apresentar a situação declarada')
        if abertura['premissa'].strip() not in texto:problemas.append('Primeira cena precisa explicar a premissa declarada')
    if problemas and historia.get('producao',{}).get('etapa')=='final':raise ValueError('; '.join(problemas))
    return {'ok':not problemas,'pendencias':problemas,'metodo':'Situação e premissa declaradas; revisão criativa ainda necessária.'}
