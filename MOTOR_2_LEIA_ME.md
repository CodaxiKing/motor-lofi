# Motor Lo-Fi 2 — pacote integrado e testável

Este ZIP contém o projeto original e melhorias opcionais de produção. **Não inclui IA generativa embutida**,
editor visual, rig avançado ou geração autônoma de episódios. A direção automática atual sugere planos,
mas não transforma texto livre em um roteiro técnico completo.

## Implementado
- Perfis de cor (`visual_profile`) aplicados pelo renderizador: `lofi_classic`, `cartoon_dark`, `horror_illustrated`, `cinematic_cartoon`.
- Importação de PNG/WEBP em camadas por plano com posição, escala, transparência, movimento e profundidade.
- Sugestões de planos baseadas em texto: `python3 tools/diretor.py roteiro.txt sugestoes.json`.
- Validação extra de continuidade: `python3 tools/validar_continuidade.py episodio.json`.
- Pré-visualização de quadros: `python3 tools/preview_2.py episodio.json 2 7 12`.
- Testes unitários e os testes originais de fumaça.

## Exemplo de plano com ilustração em camadas
No JSON do episódio, adicione ao plano desejado:
```json
"layers": [
  {"path": "assets/cenario.png", "x": 0, "y": 0, "scale": 1, "opacity": 1, "depth": 0.15},
  {"path": "assets/neblina.png", "x": 0, "y": 0, "opacity": 0.5, "depth": 0.8, "motion_x": 30}
]
```
Os arquivos são relativos à pasta do JSON. As camadas são compostas sobre a cena desenhada **antes** das legendas e overlays.
Para que o fundo substitua totalmente o desenho original, use uma imagem opaca no tamanho 1080×1920.

Na raiz do JSON, opcionalmente:
```json
"visual_profile": "cartoon_dark",
"visual_overrides": {"contrast": 1.2, "brightness": 0.92}
```

## Instalação e testes
```bash
pip install pillow numpy scipy
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/smoke.py
python3 tools/preview_2.py examples/demo4/demo4.json 2
```
Para gerar vídeo completo, instale `ffmpeg` e siga o README original.

## Atualizar a main
Faça backup da main. Extraia este ZIP, substitua os arquivos do repositório pelos arquivos extraídos,
execute os testes e só então faça commit. O ChatGPT não publicou alterações no GitHub.

## Atualização incremental: diretor 2.1

O módulo `lofi/director.py` agora fornece sugestões de duração por plano,
intensidade dramática, movimento de câmera, transição e indicação de som.
O comando `python3 tools/diretor.py roteiro.txt shotlist.json` continua funcionando.
A saída é uma **shotlist editorial** e não um JSON de episódio diretamente
compatível com `lofi.render`. O renderizador original continua inalterado.

## Motor 2.2 — Direção automática offline

Converta uma história (uma frase ou parágrafo por linha) em planos editáveis:

```bash
python tools/gerar_episodio.py examples/historia_automatica.txt examples/ep_automatico.json --profile cartoon_dark
python -m lofi.render examples/ep_automatico.json --test 0 1
```

O compilador usa regras determinísticas para sugerir cenários, duração, câmera e emoção. O JSON é compatível com o renderizador, mas **não gera voz, trilha, imagens ou assets por IA**. Para produção profissional, edite `shots`, `actors`, `camera`, `clips`, `voices` e `subs` no JSON resultante, fornecendo os arquivos de áudio necessários. Sem narração, o vídeo não terá voz. Para validar: `python -m unittest discover -s tests -p 'test_*.py'`.

O recurso de direção é heurístico, não um modelo de linguagem. Recomenda-se revisão humana de cada episódio antes da publicação.
