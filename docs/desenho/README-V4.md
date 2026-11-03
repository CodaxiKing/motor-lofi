# Visual Asset Library V4 — motor-lofi

## Entrega

Esta versão **não** é um motor de animação facial por IA. Ela acrescenta ao V3:

- **Facial timeline:** troca de expressão/olhar por keyframes e leitura de mouth cues Rhubarb JSON/TSV. Para animação labial, forneça imagens transparentes das bocas e um arquivo de cues; não há geração automática de boca a partir de uma única imagem.
- **Living environments:** flutuação e balanço de objetos por camada, pulsação de iluminação, névoa, flicker, parallax, câmera e keyframes já existentes.
- **Storyboard planner:** lista requisitos explícitos de imagens do episódio, busca na biblioteca e gera prompts para as faltantes.
- **Auto rig:** mantém heurística da V3; não há detector de pose por IA nem ARAP.

## Instalação em checkout local

```bash
python install_into_motor.py /caminho/para/motor-lofi
python -m unittest discover -s tests -v
```

O instalador preserva o renderizador procedural e habilita o modo `visual_mode: DESENHO` apenas em planos com `image_scene`. Faz backup do `render.py` na primeira instalação. **Faça commit ou backup antes de instalar.**

## Storyboard e prompts

```bash
PYTHONPATH=. python -m lofi.storyboard_planner examples/episode-v4.json /caminho/para/biblioteca --out image-plan.json
```

No episódio, `shots[].image_requirements` lista imagens necessárias com `kind`, `subject`, `style`, `pose`, `view`, `emotion`, etc. O planejador não deduz automaticamente requisitos a partir de roteiro em linguagem natural; essa etapa deve ser feita pela Skill/Claude.

## Expressões e boca

Em `layers[].character.state`, use `expression_keys: [[0, "neutral"], [1.2, "fear"]]`, `gaze_keys: [[0,"center"],[1.5,"left"]]` e `mouth_cues_file: "mouth.json"`. As `parts` devem ter `variants` correspondentes. O arquivo Rhubarb JSON contém `mouthCues` com `start`, `end`, `value`. Os tempos são relativos ao início do plano. Para evitar distorções, prepare as camadas com coordenadas consistentes.

## Limitações verificáveis

- Não foi executado um episódio completo no repositório original nesta sessão.
- A integração ao Claude Code Skill ainda exige configuração específica da Skill existente.
- A detecção de articulações é heurística e requer revisão manual.
- Animação facial é baseada em sprites, não em deformação neural de rosto.
- O renderizador de imagens continua usando Pillow e pode ser lento em 1080×1920 sem cache.
- GitHub: escrita bloqueada pela integração (403); não houve push.
