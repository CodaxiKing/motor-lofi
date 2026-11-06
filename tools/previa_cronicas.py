"""Gera folhas, comparação local e vídeo de composição da Biblioteca Crônicas."""
import argparse
import copy
import html
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image,ImageDraw,ImageFont
from lofi.historias_ilustradas import carregar,arquivo
from lofi.imagens import quadro
from lofi.interface import desenhar_previa
from lofi.sincronia import ffmpeg

BASE=Path(__file__).resolve().parents[1]/'biblioteca/cronicas/v1'


def salvar(path,doc):path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def preparar(render=False):
    cat=carregar(BASE/'catalogo.json')
    perfil=json.loads((BASE/'perfis/cronicas_situacional_v1.json').read_text(encoding='utf-8'))
    out=BASE/'previas';out.mkdir(exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
    for nome,assets in [('fundos',list(cat['cenarios'].values())),('mara',list(cat['personagens']['mara']['poses'].values()))]:
        cols=4;w,h=240,426;sheet=Image.new('RGB',(cols*w,((len(assets)+cols-1)//cols)*(h+28)),'#111721');d=ImageDraw.Draw(sheet)
        for i,a in enumerate(assets):
            im=Image.open(arquivo(BASE/'catalogo.json',a['img'])).convert('RGBA')
            if nome=='mara':
                im=im.crop(im.getchannel('A').getbbox());im.thumbnail((w-20,h-12),Image.Resampling.LANCZOS)
            else:im=im.resize((w,h),Image.Resampling.LANCZOS)
            x,y=i%cols*w,i//cols*(h+28);sheet.paste(im,(x+(w-im.width)//2,y+28+(h-im.height)//2),im)
            d.text((x+6,y+6),a.get('descricao',nome)[:31],font=font,fill='#e2c779')
        sheet.save(out/f'{nome}_v1.png')
    shots=[];ordem=[]
    for chave,preset in perfil['composicoes'].items():
        pessoas=[]
        if preset.get('ator'):
            a=copy.deepcopy(preset['ator']);pose=cat['personagens']['mara']['poses'][a.pop('pose')]
            a.update(img=pose['img'],ancora=pose['ancora'],referencia_escala=pose['img'],altura_m=1.68,sombra={'intensidade':.4})
            pessoas=[a]
        inicio=len(shots)*2
        cfg={'pasta_biblioteca':'..','fundo':cat['cenarios'][preset['cenario']]['img'],
             'personagens':pessoas,'composicao':'manual','camera_ilustrada':preset['camera'],
             'qualidade_visual':False,'aproximar':0,'balanco':0}
        shot={'start':inicio,'end':inicio+2,'scene':preset['cenario'],'imagens':cfg,'composicao_ref':chave}
        for campo in ('interface','interacao_visual'):
            if campo in preset:shot[campo]=copy.deepcopy(preset[campo])
        shots.append(shot);ordem.append((chave,preset))
    base_laje=next(s for s in shots if s['composicao_ref']=='laje_sentado')
    for chave,extra in [('telefone',{'telefone':{'hora':'23:05','contato':'Irmã','mensagens':[{'tipo':'audio','duracao':'0:11'},{'tipo':'texto','texto':'Estou no prédio da esquina.'}]}}),
                        ('escolha',{'escolha_ref':{'titulo':'Buscar a irmã ou esperar o rádio?','opcoes':['IR ATÉ LÁ','ESPERAR']}})]:
        shot=copy.deepcopy(base_laje);inicio=len(shots)*2;shot.update(start=inicio,end=inicio+2,composicao_ref=chave,**extra)
        shots.append(shot);ordem.append((chave,{'referencia_s':133 if chave=='telefone' else 161,'descricao':'Interface editável sobre a cena da Mara'}))
    spec={'fps':24,'preview_size':[270,480],'total':shots[-1]['end'],'loop':False,'narrado':True,
          'biblioteca':'cronicas','biblioteca_estado':'estudo_visual','producao':{'etapa':'previa_visual'},
          'sem_audio_intencional':True,'interface':perfil['interface'],'shots':shots,
          'nota':'Estudo de enquadramento sem áudio e sem animações de corpo certificadas.'}
    salvar(out/'direcao_demo_v1.json',spec)
    cols=3;sheet=Image.new('RGB',(cols*270,((len(shots)+cols-1)//cols)*508),'#0e141e');draw=ImageDraw.Draw(sheet)
    comparacoes=[]
    for i,(shot,(chave,preset)) in enumerate(zip(shots,ordem)):
        t=shot['start']+1.2
        im=desenhar_previa(spec,out,quadro(shot,t,out,(270,480)),shot,t)
        im.save(out/f'comp_{chave}.png')
        x,y=i%cols*270,i//cols*508;sheet.paste(im,(x,y+28));draw.text((x+6,y+6),chave,font=font,fill='#dfc16e')
        comparacoes.append({'composicao':chave,'referencia_s':preset['referencia_s'],'imagem':f'comp_{chave}.png',
                            'caixa_referencia':preset.get('caixa'),'caixa_mara':preset.get('caixa_resultante'),
                            'nota':preset['descricao']})
    sheet.save(out/'composicoes_v1.png');salvar(out/'comparacao.json',comparacoes)
    cards=[]
    for c in comparacoes:
        ref=f'../../../../referencias/video_modelo_v1/quadros/{c["referencia_s"]:06.2f}.jpg'
        cards.append(f'<article><h2>{html.escape(c["composicao"])}</h2><div class="par"><figure><img src="{ref}" alt="Quadro da referência local"><figcaption>Vídeo: {c["referencia_s"]:.2f}s</figcaption></figure><figure><img src="{c["imagem"]}" alt="Composição Crônicas"><figcaption>Mara e assets próprios</figcaption></figure></div><p>{html.escape(c["nota"])}</p></article>')
    pagina='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Biblioteca Crônicas</title><style>body{background:#10151d;color:#e1e4e7;font:16px system-ui;margin:28px}a{color:#e2c779}article{display:inline-block;vertical-align:top;max-width:570px;margin:18px}.par{display:flex}figure{margin:6px}img{max-width:260px;width:100%}video{max-width:360px;width:100%}</style><h1>Biblioteca Crônicas</h1><p>Personagem original Mara, cabeça redonda. Catálogo e estilo separados. Estudo visual: poses estáticas, sem voz; não certifica animações.</p><video controls preload="metadata" src="direcao_cronicas_v1.mp4"></video><p><a href="mara_v1.png">Mara</a> · <a href="fundos_v1.png">Fundos</a> · <a href="comparacao.json">Medidas</a></p><p>Os quadros originais são referências locais de análise. Para vê-los em outro computador, extraia novamente o vídeo fornecido.</p>'+''.join(cards)+'</html>'
    (out/'index.html').write_text(pagina,encoding='utf-8')
    if render:
        from lofi.revisao_cenas import revisar
        pasta=out/'cenas-v1';revisar(spec,out,pasta,max_segundos=3,size=(270,480))
        lista=out/'concat.txt'
        lista.write_text('\n'.join("file 'cenas-v1/"+f'cena_{i:03d}.mp4'+"'" for i in range(1,len(shots)+1))+'\n',encoding='utf-8')
        subprocess.run([ffmpeg(),'-v','error','-y','-f','concat','-safe','0','-i',str(lista),'-c','copy','-movflags','+faststart',str(out/'direcao_cronicas_v1.mp4')],check=True)
    print(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--render',action='store_true');args=p.parse_args();preparar(args.render)
