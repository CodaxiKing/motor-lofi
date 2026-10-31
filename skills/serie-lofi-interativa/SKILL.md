---
name: "serie-lofi-interativa"
description: "Planejar, roteirizar e montar episódios de séries interativas em vídeo vertical (estilo lo-fi, \"escolha o caminho\") com o motor lo-fi do GitHub, a partir das vozes do usuário."
---

# Série lo-fi interativa (v4)

Fluxo completo para séries verticais (9:16) em que o público vota A ou B no fim de cada episódio.
O visual é desenhado e animado por código pelo **motor lo-fi**. Responda sempre em português do Brasil.

## Motor e bíblia: repositório GitHub (nunca peça zip)
- Repositório: https://github.com/CodaxiKing/motor-lofi (branch `main`).
- No início de qualquer etapa: anexe o repositório à sessão com a ferramenta `add_repo` (owner `CodaxiKing`, repo `motor-lofi`, access `push`) e clone com `git clone --depth 1 https://github.com/CodaxiKing/motor-lofi` (timeout generoso). Se o clone já existir, rode `git pull`.
- Cada série vive em `series/<nome-da-serie>/`: `biblia.md` (mapa, fichas, regras, cor de cada episódio, tabela de episódios com status e votos, resumos), `epNN_roteiro.md`, `epNN.json`.
- Ao terminar uma etapa: `git add` dos arquivos da série (e do motor, se mudou), commit com mensagem curta em português terminando com as linhas de atribuição da sessão, `git fetch` + `git pull --rebase` e `git push`. Nunca versione áudios, vídeos ou arquivos temporários.
- Se o GitHub falhar, avise em uma linha, entregue os arquivos atualizados (bíblia em texto) e siga com o trabalho.

## Recursos do motor (use sempre que fizer sentido; detalhes em `SPEC.md`)
- **Atuação:** boca sincronizada com a voz, gestos ao falar, transições de pose com antecipação, troca de emoção com piscada.
- **Vistas e ações:** frente, costas, lado e **3/4** (`3q`); correr, pular (`jump` + `lift`), esconder (`hide`), abrir porta, tirar mochila, cair (`fallen`), rastejar (`crawl`), tremer (`tremble`).
- **Emoções:** neutral, fear, shock, angry, sad, determined, happy, suspicious, cry, panting.
- **Corpos:** child, old, tall, fat, thin (campo `body` em `characters`). **Objetos na mão:** radio, flashlight, phone, key, bag.
- **Zumbis:** zombie, zombie_corredor, zombie_rastejante, zombie_enfermeiro, zombie_policial; `sniff` = farejando o som.
- **Luz:** breu de verdade (`dark`) iluminado só pela lanterna e por `lights`; sombras projetadas na parede (`wall_shadow`); bloom automático.
- **Cenários (19):** apartamento (ventilador, TV com chiado, cortina ao vento), entrada, corredor, rua, janela, escada, telhado, ponte, radio, hospital, mercado, metro, escola, delegacia, posto, floresta, carro, esgoto, igreja. Nuvens e poças animadas nos externos.
- **Clima e hora:** `rain` forte/fraca/nenhuma, `fog`, `snow`, `time` dia/entardecer/amanhecer/madrugada/noite (com transição).
- **Câmera:** close no rosto, por cima do ombro, travelling, foco seletivo, paralaxe, **câmera na mão** (`handheld`), **vertigo** (`vertigo`), **câmera lenta** (`slowmo`), **susto** (`scare`: tremor + aberração de cor + impacto), **gotas na lente** (`lens_drops`).
- **Planos de detalhe:** `type: detail` com maçaneta girando, olho (pupila dilatando, reflexo), celular, chave, relógio.
- **Estilo:** `style: "desenho"` (traço de nanquim + papel) e `tint` (cor do episódio).
- **Legendas estilo Reels**, gancho (`hook`), **"Anteriormente em…"** (`type: recap` usando cenas do episódio anterior).

## Padrão de duração
Episódios de **2 a 3 minutos**, com 12 a 20 cenas de 6 a 14 s e pelo menos 3 momentos de tensão ao longo do episódio.

## 1. Planejamento da série (uma vez por história)
Quando o usuário mandar a ideia, entregue:
1. Título + resumo em 2 linhas (e a capa)
2. Mistério/conflito central e a verdade por trás dele
3. Final com duas variações conforme as escolhas (dizer quais votos levam a cada uma)
4. Por episódio: objetivo, fase (início, complicação, reviravolta, clímax, final), a pergunta A/B, uma ideia de gancho e uma **cor dominante** (vai no `tint`)
5. Ficha visual de cada personagem com os campos do motor (top, top_style, legs, shoes, hat, hair, hair_color, scarf, backpack, glasses, body, infected, scale) e uma cor de destaque única
6. Cenários da biblioteca que serão usados — se precisar de um novo, ele será criado no motor
7. Som assinatura e regras do universo
Salve tudo em `series/<nome>/biblia.md` (formato de `series/dia-zero/biblia.md`) e faça push.

## 2. Roteiro do episódio
Use a bíblia e o resultado da votação. Estrutura obrigatória:
- **CENA 0 · GANCHO (0–2 s):** flash-forward do momento mais tenso do episódio + frase curta de impacto em caixa alta (máx. 4 palavras por linha). Sem contador.
- **ANTERIORMENTE EM… (4–6 s, a partir do episódio 2):** 3 momentos do episódio anterior com uma frase curta cada.
- **ABERTURA:** "EPISÓDIO X/Y" + carimbo "A MAIORIA ESCOLHEU: ..." (transição glitch).
- **CENAS** (12 a 20), cada uma com:
  - CENA nº — início s a fim s
  - CENÁRIO + props + clima/hora (ou PLANO DE DETALHE: maçaneta, olho, celular, chave, relógio)
  - PERSONAGENS: quem, posição, vista (frente/costas/lado/3-4), pose, emoção e mudanças durante a fala, se anda/corre/pula
  - PLANO: aberto, close, por cima do ombro, travelling, foco, câmera na mão, vertigo, câmera lenta; TRANSIÇÃO de entrada
  - LUZ E DETALHES: breu com lanterna, sombra na parede, frio, poeira, horda, relâmpago, susto, gotas na lente
  - NARRAÇÃO com direção de voz entre colchetes; falas de outros personagens separadas
  - LEGENDA em CAIXA ALTA, máx. 4 palavras por pedaço
  - SOM com tempo (nomes do motor: bang, knock, lock, door_open, door_close, step, shuffle, echo_step, glass, impact, thunder, no_service, notif, vibe, click, growl, car_alarm, siren, heartbeat, breath, static, crowd, beep, stamp, whoosh)
- **FINAL:** pergunta A/B em tela dividida + "CONTINUA NO EPISÓDIO X"; último episódio fecha com "FIM".
Regras de linguagem: plano de detalhe antes de um susto; close no rosto em revelações; por cima do ombro em diálogos; câmera na mão em perseguições; câmera lenta só no pico; silêncio de 1 s antes dos sustos; pelo menos 1 som por cena.
Entregue depois: narração limpa (versão CapCut e versão ElevenLabs v3 com tags em inglês, um bloco por voz), as duas opções e o resumo de 2–3 linhas.
**Antes de entregar:** salve `epNN_roteiro.md` e rode `python3 tests/validar_roteiro.py series/<serie>/epNN_roteiro.md` (`--final` no último). Corrija até não haver ERRO. Depois faça push.

## 3. Montagem (quando chegarem as vozes)
O usuário anexa só os áudios: um por personagem (o nome do arquivo indica o personagem).
1. Clone/atualize o repositório e instale: `pip install --break-system-packages pillow numpy scipy soundfile sherpa-onnx`.
2. Copie as vozes para `series/<serie>/epNN/` com o nome do personagem e transcreva: `python3 -m lofi.transcribe ...`. Mapeie cada frase do roteiro aos tempos.
3. Escreva `series/<serie>/epNN.json` seguindo `SPEC.md` (inclua `series_title`, `episode`, `episodes_total`, `episode_title`, `tint` do episódio e o plano `recap` apontando para `ep(NN-1).json`).
4. **Verificador:** `python3 -m lofi.check series/<serie>/epNN.json`. Corrija todos os ERROS e os avisos relevantes.
5. **Revisor independente:** use a ferramenta Agent (subagent general-purpose) com um prompt autocontido: o caminho de `_revisao.png`, o roteiro do episódio e a lista do que conferir (rosto coberto pela legenda, personagem cortado ou fora do quadro, legenda errada ou fora de hora, cena que não corresponde ao roteiro, texto ilegível, contador encobrindo algo). Ele não viu a montagem e deve devolver uma lista objetiva de problemas com o tempo de cada um. Corrija, rode o verificador de novo e só então renderize.
6. Renderize em segundo plano com `--jobs 2` (≈10 s por segundo de vídeo). Confira duração, áudio e tamanho (crf 28 padrão; 30 se passar de 90 MB).
7. **Extras:** `python3 -m lofi.extras teaser ...` (15 s para Stories) e `python3 -m lofi.extras capa ...`.
8. Envie o MP4, o teaser, a capa e a legenda do post; registre o resumo e o status "montado" na bíblia e faça push.
9. No último episódio, ofereça a compilação da temporada para o YouTube (`python3 -m lofi.extras temporada ...`), pedindo os MP4s dos episódios.

## 4. Legenda do post
Gancho de 1 linha com o dia · resumo em 2–3 frases citando a escolha do público · as duas opções com 🅰️ e 🅱️ · "Comenta A ou B. A maioria decide o próximo episódio." · "📺 TÍTULO · Episódio X/Y" · 8–10 hashtags. Sugira fixar um comentário "Vota aqui: A ou B 👇". Para o teaser: 1 linha + "Episódio X no perfil".

## Testes da skill
`tests/evals.json` tem casos de teste (roteiro do meio, roteiro final, voto inválido, planejamento, montagem). Ao alterar esta skill ou os comandos, rode esses casos (skill skill-creator) e confira que continuam passando.

## Dicas de qualidade
- Personagem principal sempre com a mesma cor de destaque; infectados em cinza com olhos brilhando.
- Paralaxe em planos longos, zoom lento em momentos tensos, relâmpago e tremor só nos picos.
- Transição whip para mudança de lugar, flash para susto, glitch saindo do gancho.
- Se a história pedir um lugar que não existe, crie uma nova classe em `lofi/scenes.py` no mesmo padrão (camadas fundo/meio/frente, chão em perspectiva, luz, tratamento de cor, clima), registre em `REGISTRY`, teste e faça push. Personagens novos entram pelo campo `characters` do roteiro.