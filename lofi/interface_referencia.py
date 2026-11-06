"""HUD compacto e insertos de tela, separados das artes e dimensionados pelo quadro."""
import math
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter


@lru_cache(maxsize=12)
def _vinheta(size,intensidade):
    yy,xx=np.mgrid[-1:1:160j,-1:1:96j]
    mask=np.clip((xx*xx+yy*yy-.35)/1.15,0,1)*255*intensidade
    return Image.fromarray(mask.astype('uint8')).resize(size,Image.Resampling.BICUBIC)


def desenhar(ep,img,shot,t):
    from .interface import _status_now,_clock_now,_mission_now
    cfg=ep.spec.get('interface') or {};W,H=img.size;s=W/720
    intensidade=cfg.get('vinheta',0)
    if not isinstance(intensidade,(int,float)) or not 0<=intensidade<=1:raise ValueError('Vinheta fora de 0..1')
    if intensidade:
        sombra=Image.new('RGBA',img.size,(0,0,0,0));sombra.putalpha(_vinheta(img.size,intensidade))
        img=Image.alpha_composite(img.convert('RGBA'),sombra).convert('RGB')
    accent=tuple(cfg.get('cor',[222,191,83]));ink=(225,228,229);dim=(169,177,181)
    layer=Image.new('RGBA',img.size);d=ImageDraw.Draw(layer);rel=t-shot['start']
    def font(n,bold=False):
        try:return ImageFont.truetype('C:/Windows/Fonts/'+('consolab.ttf' if bold else 'consola.ttf'),max(7,round(n*s)))
        except OSError:return ImageFont.load_default(size=max(7,round(n*s)))
    def xy(x,y):return (round(x*W),round(y*H))
    def box(rect,fill=(8,15,21,190),outline=None,r=7):
        d.rounded_rectangle((*xy(rect[0],rect[1]),*xy(rect[2],rect[3])),radius=max(1,round(r*s)),fill=fill,outline=outline,width=max(1,round(s)))
    def text(x,y,txt,n=14,color=ink,bold=False):d.text(xy(x,y),str(txt),font=font(n,bold),fill=color)
    top=cfg.get('topo',.125);somente_horario=cfg.get('somente_horario',False)
    sinal=shot.get('interacao_visual')
    if sinal and not somente_horario and sinal.get('inicio',0)<=rel<sinal.get('fim',shot['end']-shot['start']):
        cx,cy=xy(*sinal.get('centro',[.5,.35]));periodo=sinal.get('periodo',1.2)
        if periodo<=0:raise ValueError('Período de interação inválido')
        for atraso in (0,.35):
            fase=((rel-sinal.get('inicio',0))/periodo-atraso)%1
            r=max(1,round(W*sinal.get('raio',.13)*fase))
            d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(235,241,245,round((1-fase)*180)),width=max(1,round(2*s)))
    if shot.get('interface') is not False:
        m=_mission_now(ep,t) if not somente_horario else None
        if m:
            box((.09,top,.56,top+.035))
            text(.11,top+.009,m.get('titulo','SOBREVIVA'),12)
            text(.40,top+.008,m.get('prazo',''),15,accent,True)
        for i,(nome,(valor,label)) in enumerate((_status_now(ep,t) if not somente_horario else {}).items()):
            y=top+i*.037
            box((.635,y,.91,y+.032))
            text(.65,y+.008,nome,13)
            cor=(125,206,154) if valor>.5 else accent if valor>.2 else (220,94,105)
            x0,y0=xy(.759,y+.014);x1,y1=xy(.821,y+.019)
            d.rectangle((x0,y0,x1,y1),fill=(150,157,153,140))
            if valor>0:d.rectangle((x0,y0,x0+round((x1-x0)*min(1,max(0,valor))),y1),fill=cor)
            text(.848,y+.007,label if label is not None else f'{round(valor*100)}%',15,cor,True)
        clock=_clock_now(ep,t)
        if clock:
            dia,hora=clock;y=cfg.get('relogio_y',.665)
            if somente_horario:
                box((.09,y,.24,y+.033))
                text(.107,y+.005,hora,24,accent,True)
            else:
                box((.09,y,.295,y+.045))
                text(.158,y+.001,dia,12,dim,True);text(.15,y+.016,hora,24,accent,True)
                cx,cy=xy(.124,y+.027);r=max(3,round(8*s))
                d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=accent,width=max(1,round(2*s)))
                d.line((cx,cy-r*.65,cx,cy,cx+r*.55,cy+r*.3),fill=accent,width=max(1,round(2*s)))
            for i,tipo in enumerate(cfg.get('atalhos',[]) if not somente_horario else []):
                x=.09+i*.103;box((x,y+.057,x+.088,y+.105),outline=accent+(160,),r=12)
                ix,iy=xy(x+.044,y+.081);r=max(4,round(10*s));lw=max(1,round(2*s))
                if tipo=='bike':
                    d.ellipse((ix-r*1.5,iy,ix-r*.1,iy+r*1.4),outline=accent,width=lw)
                    d.ellipse((ix+r*.2,iy,ix+r*1.6,iy+r*1.4),outline=accent,width=lw)
                    d.line((ix-r,iy+r*.7,ix,iy-r*.5,ix+r,iy+r*.7,ix-r,iy+r*.7,ix+r*.25,iy-r*.5),fill=accent,width=lw)
                elif tipo=='objetivo':d.line((ix-r*.5,iy+r,ix-r*.5,iy-r,ix+r,iy-r*.4,ix-r*.5,iy),fill=accent,width=lw)
                elif tipo=='mapa':d.line((ix-r,iy+r,ix-r,iy-r,ix,iy-r*.6,ix+r,iy-r,ix+r,iy+r,ix,iy+r*.6,ix-r,iy+r),fill=accent,width=lw)
                else:d.rounded_rectangle((ix-r*.7,iy-r,ix+r*.7,iy+r),radius=max(1,round(2*s)),outline=accent,width=lw)
    dialogo=shot.get('dialogo')
    if dialogo:
        y=dialogo.get('y',.57);box((.09,y,.82,y+.095),fill=(6,13,18,240),outline=accent)
        box((.25,y-.025,.62,y),fill=accent+(255,))
        text(.264,y-.022,dialogo.get('nome',''),15,(9,15,20),True)
        texto=dialogo.get('texto','')[:max(0,int(rel*dialogo.get('cps',28)))];lines=[];cur=''
        for word in texto.split():
            teste=(cur+' '+word).strip()
            if d.textlength(teste,font=font(19))>W*.68 and cur:lines.append(cur);cur=word
            else:cur=teste
        if cur:lines.append(cur)
        for i,line in enumerate(lines[:3]):text(.115,y+.015+i*.021,line,19)
    if shot.get('cartela'):
        c=shot['cartela'];box((.24,.48,.76,.57),fill=(6,13,18,240),outline=accent)
        text(.28,.502,c.get('titulo',''),18,dim);text(.4,.5,c.get('sub',''),40,accent,True)
    if shot.get('notificacao'):
        n=shot['notificacao'];box((.1,.29,.9,.39),fill=(13,23,29,245),outline=accent)
        text(.125,.301,n.get('app','MENSAGEM'),12,dim)
        text(.125,.322,n.get('titulo',''),18,ink,True)
        text(.125,.353,n.get('texto',''),16)
    if shot.get('alerta'):
        a=shot['alerta'];box((.1,.39,.9,.5),fill=(34,13,20,240),outline=(220,94,105))
        text(.13,.409,a.get('titulo',''),21,(236,149,147),True)
        text(.13,.453,a.get('texto',''),16)
    out=Image.alpha_composite(img.convert('RGBA'),layer).convert('RGB')
    if shot.get('telefone'):
        p=shot['telefone'];out=out.filter(ImageFilter.GaussianBlur(max(1,8*s)));l=Image.new('RGBA',img.size);layer=l;d=ImageDraw.Draw(layer)
        box((.21,.15,.79,.8),fill=(4,10,13,255),outline=(45,56,60),r=38)
        text(.27,.175,p.get('hora','23:05'),16);text(.27,.218,p.get('contato','Contato'),23,ink,True)
        for i,m in enumerate(p.get('mensagens',[])):
            y=.29+i*.12;box((.26,y,.72,y+.085),fill=(24,37,43,255),r=10)
            if m.get('tipo')=='audio':
                text(.28,y+.012,'▶',20,ink)
                for k in range(30):
                    x=.34+k*.011;h=.003+abs(math.sin(k*1.37))*.019
                    d.line((*xy(x,y+.034-h/2),*xy(x,y+.034+h/2)),fill=(129,149,153),width=max(1,round(2*s)))
                text(.34,y+.055,m.get('duracao','0:12')+' · áudio',12,dim)
            else:text(.28,y+.015,m.get('texto','')[:32],15)
        box((.25,.74,.75,.783),fill=(29,44,49,255),r=20);text(.28,.752,'Mensagem',16,dim)
        out=Image.alpha_composite(out.convert('RGBA'),layer).convert('RGB')
    if shot.get('escolha_ref'):
        e=shot['escolha_ref'];l=Image.new('RGBA',img.size,(0,0,0,155));out=Image.alpha_composite(out.convert('RGBA'),l).convert('RGB')
        layer=Image.new('RGBA',img.size);d=ImageDraw.Draw(layer)
        titulo=e.get('titulo','Qual caminho seguir?');words=titulo.split();mid=max(1,len(words)//2)
        for i,line in enumerate((' '.join(words[:mid]),' '.join(words[mid:]))):
            f=font(27,True);d.text((W/2,H*(.39+i*.027)),line.upper(),font=f,fill=ink,anchor='mm')
        opcoes=e.get('opcoes',['A','B'])
        for i,op in enumerate(opcoes[:2]):
            x=.2+i*.32;box((x,.46,x+.28,.502),fill=((47,95,142,240) if i==0 else (51,100,77,240)),outline=accent)
            d.text((W*(x+.14),H*.481),str(op).upper(),font=font(22,True),fill=ink,anchor='mm')
        restante=max(0,math.ceil(shot['end']-t));cx,cy=xy(.5,.54);r=round(16*s)
        d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=accent,width=max(1,round(2*s)))
        d.text((cx,cy),str(restante),font=font(18,True),fill=accent,anchor='mm')
        out=Image.alpha_composite(out.convert('RGBA'),layer).convert('RGB')
    return out
