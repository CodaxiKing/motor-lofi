"""Ciclos de desenhos completos: nenhuma separação ou rotação de membros."""
import json
import math
from functools import lru_cache
from pathlib import Path
from PIL import Image


def validar(ciclo):
    frames=ciclo.get('frames',[])
    if not frames or ciclo.get('tipo') not in ('corpo_inteiro','retrato'):raise ValueError('Ciclo precisa de quadros completos de corpo ou retrato')
    if not 0<ciclo.get('fps_quadros',0)<=60:raise ValueError('Cadência de quadros inválida')
    if not 0<ciclo['referencia']['altura_corpo']<=1:raise ValueError('Referência de corpo inválida')
    for f in frames:
        r=f.get('regiao',[]);a=f.get('ancora',[])
        if len(r)!=4 or not 0<=r[0]<r[2]<=1 or not 0<=r[1]<r[3]<=1:raise ValueError('Região de quadro inválida')
        if len(a)!=2 or not all(math.isfinite(v) and 0<=v<=1 for v in a):raise ValueError('Âncora de quadro inválida')
    return ciclo


@lru_cache(maxsize=64)
def _ler(path,mtime):
    return validar(json.loads(Path(path).read_text(encoding='utf-8')))


def carregar(base,nome):
    raiz=(Path(base)/'imagens').resolve();p=(raiz/nome).resolve()
    if not p.is_relative_to(raiz):raise ValueError('Ciclo fora da biblioteca')
    return _ler(str(p),p.stat().st_mtime_ns)


def ativo(animacoes,t):
    encontrados=[a for a in animacoes or [] if a['inicio']<=t<a['fim']]
    if len(encontrados)>1:raise ValueError('Dois ciclos de corpo inteiro simultâneos')
    return encontrados[0] if encontrados else None


def indice(ciclo,t,modo='loop',velocidade=1):
    n=len(ciclo['frames']);ordem=ciclo.get('ordem',list(range(n)))
    if not ordem or any(not isinstance(i,int) or not 0<=i<n for i in ordem):raise ValueError('Ordem de quadros inválida')
    if not math.isfinite(velocidade) or velocidade<=0:raise ValueError('Velocidade de ciclo inválida')
    k=max(0,int(t*ciclo['fps_quadros']*velocidade))
    if modo=='loop':return ordem[k%len(ordem)]
    if modo=='uma_vez':return ordem[min(len(ordem)-1,k)]
    if modo=='ida_volta':
        ordem=list(range(n))+list(range(n-2,0,-1))
        return ordem[k%len(ordem)]
    raise ValueError('Modo de ciclo inválido')


def quadro(ciclo,atlas,t,modo='loop',velocidade=1):
    i=indice(ciclo,t,modo,velocidade);f=ciclo['frames'][i];w,h=atlas.size
    r=f['regiao'];im=atlas.crop(tuple(round(v*(w if j%2==0 else h)) for j,v in enumerate(r))).convert('RGBA')
    # Escala é comum ao ciclo e não depende da mão elevada nem da pose corrente.
    fator=ciclo['referencia'].get('altura_referencia',.98)/ciclo['referencia']['altura_corpo']
    if ciclo['referencia'].get('altura_celula_px'):
        fator *= im.height/ciclo['referencia']['altura_celula_px']
    return im,f['ancora'],fator,i


def revisar(ciclo,atlas):
    achados=[];w,h=atlas.size;bottoms=[]
    for i,f in enumerate(ciclo['frames']):
        r=f['regiao'];im=atlas.crop(tuple(round(v*(w if j%2==0 else h)) for j,v in enumerate(r))).convert('RGBA')
        a=im.getchannel('A');box=a.point(lambda v:255 if v>30 else 0).getbbox()
        if not box:achados.append({'frame':i,'code':'quadro_vazio'});continue
        if box[0]<=1 or box[1]<=1 or box[2]>=im.width-1 or box[3]>=im.height-1:
            achados.append({'frame':i,'code':'silhueta_na_borda'})
        # Apoio medido só na região dos pés, não pela mão que sobe.
        feet=a.crop((0,round(im.height*.76),im.width,im.height)).point(lambda v:255 if v>30 else 0).getbbox()
        if feet and f.get('apoio',True):bottoms.append((round(im.height*.76)+feet[3])/im.height-f['ancora'][1])
    if bottoms and max(bottoms)-min(bottoms)>.01:achados.append({'code':'apoios_desalinhados'})
    return {'frames':len(ciclo['frames']),'achados':achados,'metodo':'alfa, margens e apoio; articulações requerem revisão visual'}
