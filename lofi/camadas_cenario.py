"""Camadas raster independentes, névoa e luz procedural, preservando as artes-fonte."""
import math
import numpy as np
from PIL import Image


def validar(camadas):
    ids = set()
    for c in camadas:
        if not c.get('id') or c['id'] in ids: raise ValueError('Camada precisa de ID único')
        ids.add(c['id'])
        if c.get('tipo') not in ('imagem', 'nevoa', 'luz'): raise ValueError('Tipo de camada inválido')
        if c.get('plano', 'fundo') not in ('fundo', 'frente'): raise ValueError('Plano de camada inválido')
        for k, default in (('opacidade',1), ('profundidade',.5), ('velocidade',.02)):
            v = c.get(k, default)
            if not isinstance(v,(int,float)) or not math.isfinite(v): raise ValueError('Parâmetro de camada inválido: '+k)
        if not 0 <= c.get('opacidade',1) <= 1: raise ValueError('Opacidade fora de 0..1')
        if c['tipo'] == 'imagem' and not c.get('img'): raise ValueError('Camada sem imagem')
    return camadas


def gerar(camadas, t, size, carregar, travelling=None):
    validar(camadas)
    if not camadas:return []
    W, H = size
    yy, xx = np.mgrid[0:160,0:96].astype(float)
    xx /= 95; yy /= 159
    saida = []
    for c in camadas:
        profundidade = c.get('profundidade',.5)
        x = c.get('x',.5)*W; y = c.get('y',.5)*H
        distancia=0
        if travelling:
            from .travelling import estado
            distancia=estado(travelling,t)[0]
            if c['tipo']!='nevoa':x-=distancia*H*profundidade
        tipo = c['tipo']; alpha = c.get('opacidade',1)
        if tipo == 'imagem':
            im = carregar(c['img']).copy()
            escala = c.get('altura',1)*H/im.height
        else:
            cor = c.get('cor',[135,155,170])
            if len(cor) != 3 or any(not 0<=v<=255 for v in cor): raise ValueError('Cor de camada inválida')
            if tipo == 'nevoa':
                a,b = c.get('faixa',[.5,1])
                if not 0<=a<b<=1: raise ValueError('Faixa de névoa inválida')
                v = c.get('velocidade',.02)*t
                x_nevoa=xx+distancia*H/W*profundidade
                ruido = (.52+.16*np.sin(2*math.pi*(x_nevoa*1.3-v+yy*.8))
                         +.12*np.cos(2*math.pi*(x_nevoa*2.4+v*.7-yy*1.4)))
                mask = ruido*np.clip((yy-a)/max(.001,b-a),0,1)
            else:
                rx,ry = c.get('raio',[.3,.25])
                if rx<=0 or ry<=0: raise ValueError('Raio de luz inválido')
                mask = np.exp(-3*(((xx-.5)/rx)**2+((yy-.5)/ry)**2))
                mask *= 1-c.get('pulsar',0)*(.5+.5*math.sin(t*c.get('frequencia',1.3)))
            pixels = np.empty((160,96,4),dtype=np.uint8)
            pixels[:,:,:3] = cor
            pixels[:,:,3] = np.clip(mask*255,0,255).astype(np.uint8)
            im = Image.fromarray(pixels).resize((W,H),Image.Resampling.BICUBIC)
            escala = 1
        im.putalpha(im.getchannel('A').point(lambda a:round(a*alpha)))
        x -= im.width*escala/2; y -= im.height*escala/2
        saida.append((im,x,y,escala,profundidade,None,{'cenario':True,'plano_camada':c.get('plano','fundo')}))
    return saida
