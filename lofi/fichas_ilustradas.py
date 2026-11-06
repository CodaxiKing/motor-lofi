"""Altura física e rigs pertencem à ficha individual, não às dimensões do PNG."""
import json
import math
from pathlib import Path


def perfil(base, registro, referencia_m=1.70):
    out=dict(registro.get('composicao',{}))
    arquivo=registro.get('arquivo_ficha')
    if not arquivo:return out
    raiz=(Path(base)/'imagens').resolve();p=(raiz/arquivo).resolve()
    if not p.is_relative_to(raiz):raise ValueError('Ficha fora da biblioteca')
    ficha=json.loads(p.read_text(encoding='utf-8'))
    out['transicoes']=ficha.get('transicoes',{})
    altura=ficha.get('altura_m')
    if not isinstance(altura,(int,float)) or not math.isfinite(altura) or not .2<=altura<=5:
        raise ValueError(f'Altura física inválida: {p.name}')
    if not isinstance(referencia_m,(int,float)) or not math.isfinite(referencia_m) or referencia_m<=0:
        raise ValueError('Altura de referência inválida')
    out.update(marcos_camera=ficha.get('marcos_camera',{}), sustos=ficha.get('sustos',{}), ciclos_quadros=ficha.get('ciclos_quadros',{}), preferencia_animacao=ficha.get('preferencia_animacao','puppet'), rig_camadas=ficha.get('rig_camadas'), rigs_camadas=ficha.get('rigs_camadas',{}), altura_m=altura,escala_relativa=altura/referencia_m,
               puppets=ficha.get('puppets',{}), piscadas_locais=ficha.get('piscadas_locais',{}), bocas_locais=ficha.get('bocas_locais',{}),margem_puppet=ficha.get('margem_puppet',.02))
    return out


def enriquecer(catalogo,base):
    for p in catalogo['personagens'].values():
        p['composicao']=perfil(base,p,catalogo.get('escala_referencia_m',1.70))
    return catalogo
