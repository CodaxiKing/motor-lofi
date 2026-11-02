---
name: "serie-lofi-interativa"
description: "Planejar, roteirizar e montar episódios de séries interativas em vídeo vertical (estilo lo-fi, \"escolha o caminho\") com o motor lo-fi do GitHub, a partir das vozes do usuário."
---

# Série lo-fi interativa (v8)

Fluxo completo para séries verticais (9:16) de qualquer gênero (suspense, terror, mistério, comédia, romance, fantasia, policial...) em que o público vota A ou B no fim de cada episódio.
O visual é desenhado e animado por código pelo **motor lo-fi**. Responda sempre em português do Brasil.

## Motor e bíblia: repositório GitHub (nunca peça zip)
- Repositório: https://github.com/CodaxiKing/motor-lofi (branch `main`).
- No início de qualquer etapa: anexe o repositório à sessão com a ferramenta `add_repo` (owner `CodaxiKing`, repo `motor-lofi`, access `push`) e clone com `git clone --depth 1 https://github.com/CodaxiKing/motor-lofi` (timeout generoso). Se o clone já existir, rode `git pull`.
- Cada série vive em `series/<nome-da-serie>/`: `biblia.md` (regras, cor de cada episódio, tabela de episódios com status e votos, resumos), **`personagens.json`** (fichas travadas), **`mundo.json`** (mapa da cidade: lugares, cenários de cada lugar, ligações e o `fim` de cada episódio com lugar, dia/hora e o que cada um carrega), `epNN_roteiro.md`, `epNN.json`.
- **Continuidade:** `personagens.json` é a fonte única do visual de cada personagem e sempre vence o roteiro. Nunca redefina um personagem travado em `characters` do episódio; para mudar o visual de propósito, edite só esse arquivo.
- Ao terminar uma etapa: `git add` dos arquivos da série (e do motor, se mudou), commit com mensagem curta em português terminando com as linhas de atribuição da sessão, `git fetch` + `git pull --rebase` e `git push`. Nunca versione áudios, vídeos ou arquivos temporários.
- **Um episódio só vira "montado" com o `epNN.json` (e o `epNN_roteiro.md`) commitados.** Antes de marcar o status, confira com `git ls-files series/<serie>/`. É desse arquivo que o próximo episódio tira o "Anteriormente em…".
- Se o `epNN.json` do episódio anterior não estiver no repositório, monte o recap com `moments` (ver `SPEC.md`), a partir dos resumos da bíblia, e avise em uma linha. Episódios antigos reconstruídos têm `"legado": true` e servem normalmente de base para o recap (ex.: `dia-zero/ep02.json`; os tempos sugeridos estão na bíblia).
- Se o GitHub falhar, avise em uma linha, entregue os arquivos atualizados (bíblia em texto) e siga com o trabalho.
- Se esta skill ou os comandos forem atualizados, edite o `SKILL.md` em `skills/` e rode `python3 tools/empacotar_skills.py` para regerar os `.zip` (o CI recusa zip desatualizado).

## Recursos do motor (use sempre que fizer sentido; detalhes em `SPEC.md`)
Os nomes válidos de cenários, poses, emoções, sons, transições e planos de detalhe estão em **`CATALOGO.md`** (gerado do código). Use só nomes de lá: o validador de roteiro recusa os outros.
- **Guarda-roupa (qualquer gênero):** tons de pele (palido, claro, medio, moreno, escuro, oliva, verde, azul); roupas `shirt`, `tshirt`, `puffer`, `hoodie`, `sweater`, `leather`, `suit`, `trench`, `labcoat`, `scrubs`, `uniform`, `chef`, `dress`, `torn`; manga curta; calça, shorts, saia com meia-calça; cabelos `short`, `long`, `ponytail`, `bun`, `bob`, `curly`, `afro`, `braids`, `pigtails`, `spiky`, `mohawk`, `bald`; barba, bigode, barba por fazer; chapéus `beanie`, `cap`, `helmet`, `hood`, `fedora`, `cowboy`, `tophat`, `crown`, `witch`, `chef`, `headband`, `bandana_hat`; acessórios `sunglasses`, `eyepatch`, `mask`, `earrings`, `bow`, `headphones`, `necklace`, `badge`, `stethoscope`, `tie`, `bowtie`, `bandana`; capa, óculos, cachecol, mochila; `ghost` (translúcido).
- **Personagens prontos:** roberta, rafa, lia, valter, soldado, zumbis (zombie, zombie_corredor, zombie_rastejante, zombie_enfermeiro, zombie_policial) e, para outros gêneros, detetive, cientista, estudante, estudante2, executiva, executivo, medica, policial, roqueiro, vovo, vovo2, crianca, bruxa, rainha, chef, cowboy, fantasma, dj, pirata. Qualquer um pode ser ajustado ou criado em `characters`.
- **Atuação:** boca com formatos de vogal (A, E, O, U, M) lidos da voz, transições de pose com antecipação, troca de emoção com piscada.
- **Gestos pela fala (automáticos com o ator em `idle`):** aponta em "ali/lá/olha/aquele", mão no peito em "eu/meu/minha", acena no "sim", balança a cabeça no "não", cabeça baixa em "desculpa/perdão/sinto". Manual: `gesture` nod/shake/down.
- **Interações:** `hold` (mãos dadas andando), `carried_by` (no colo de alguém, com `pose: carry` em quem carrega), poses `hug`, `push`, `chest`, `hand_r`, `hand_l`, `reach_l`.
- **Eco por ambiente (automático):** voz reverbera em escada, igreja, esgoto e metrô; eco curto em corredor, hospital, escola, mercado e delegacia; abafada no carro. Troque com `acoustic` no plano.
- **Vistas e ações:** frente, costas, lado e **3/4** (`3q`); correr, pular (`jump` + `lift`), esconder (`hide`), abrir porta, tirar mochila, cair (`fallen`), rastejar (`crawl`), tremer (`tremble`).
- **Emoções:** neutral, fear, shock, angry, sad, determined, happy, suspicious, cry, panting.
- **Corpos:** child, old, tall, fat, thin. **Objetos na mão:** radio, flashlight, phone, key, bag.
- **Luz:** breu de verdade (`dark`) iluminado só pela lanterna e por `lights`; sombras projetadas na parede (`wall_shadow`); bloom automático.
- **Cenários (28):** apartamento (ventilador, TV com chiado, cortina ao vento), entrada, corredor, rua, rua_amanhecer (rua de dia/madrugada clara; `time` não tira a lua da `rua`), janela, escada, telhado, ponte, radio (o rádio **de casa**), radio_carro (o rádio **do painel do carro**, com para-brisa e chuva), radio_portatil (rádio de pilha na mão, em qualquer lugar), entrada_metro (calçada com a escada da estação: liga rua ↔ metrô), portao (frente do prédio), beco, viaduto, estacionamento, vagao (metrô por dentro), hospital, mercado, metro, escola, delegacia, posto, floresta, carro, esgoto, igreja. Plano de detalhe `chave` com `"onde": "carro"` vira a ignição. Nuvens e poças animadas nos externos. Novos lugares são criados conforme a história.
- **Travelling (o cenário passa):** `"travelling": 400` no plano faz a rua, mata, túnel, corredor ou ponte rolar atrás de quem anda/corre (de lado; marcas `esq`, `centro`, `dir`, `fundo`, `frente`). `{"dir": "frente"}` = correm na direção da câmera; `{"dir": "fundo"}` = câmera segue por trás. `{"chegada": "carro"}` (ou `porta`, `escada`, `portao`) desacelera e o destino entra no quadro. Use sempre que alguém correr ou caminhar por um trajeto.
- **Clima e hora:** `rain` forte/fraca/nenhuma, `fog`, `snow`, `time` dia/entardecer/amanhecer/madrugada/noite (com transição).
- **Câmera:** enquadramento perto por padrão (`plano`: medio, conjunto, close; aberto só para situar), close no rosto, por cima do ombro, travelling, foco seletivo, paralaxe, câmera na mão (`handheld`), vertigo, câmera lenta (`slowmo`), susto (`scare`), gotas na lente (`lens_drops`).
- **Planos de detalhe:** `type: detail` com maçaneta, olho, celular, chave, relógio. **Partes do corpo:** `"hand": "roberta"` mostra o braço e a mão do personagem certo (rádio, chave, maçaneta, celular; no olho, a pele).
- **Estilo:** `style: "desenho"` (traço de nanquim + papel) e `tint` (cor do episódio).
- **Legendas estilo Reels**, gancho (`hook`), **"Anteriormente em…"** (`type: recap`).

## Padrão de duração
Episódios de **no mínimo 2 minutos, sem limite máximo** (a história pede o tamanho), com pelo menos 12 cenas de 6 a 14 s e pelo menos 3 momentos de tensão (ou de virada, em comédia e romance) ao longo do episódio.

## 1. Planejamento da série (uma vez por história)
Quando o usuário mandar a ideia, entregue:
1. Título + resumo em 2 linhas (e a capa)
2. Mistério/conflito central e a verdade por trás dele
3. Final com duas variações conforme as escolhas (dizer quais votos levam a cada uma)
4. Por episódio: objetivo, fase (início, complicação, reviravolta, clímax, final), a pergunta A/B, uma ideia de gancho e uma **cor dominante** (vai no `tint`)
5. Ficha visual de cada personagem (vai para `personagens.json`) com os campos do guarda-roupa (skin, top_style, top, inner, sleeves, bottom, skirt, tights, legs, shoes, hair, hair_color, facial, hat, hat_color, acc, glasses, scarf, backpack, cape, body, ghost, scale), partindo de um personagem pronto quando fizer sentido. Cada personagem com uma silhueta e uma cor de destaque únicas; varie tons de pele, corpos e cabelos no elenco.
6. Cenários da biblioteca que serão usados — se precisar de um novo, ele será criado no motor — e o **mapa da cidade** em `mundo.json`: lugares (cada um com seus cenários), as ligações entre eles (por onde se vai de um a outro) e o que cada personagem carrega no começo (formato de `series/dia-zero/mundo.json`)
7. Som assinatura e regras do universo
8. Classificação: "todas as idades" (padrão: sem sangue, sustos sem violência explícita) ou "14+" (violência leve, sem gore). Registre na primeira linha da bíblia e respeite em todos os roteiros.
Salve tudo em `series/<nome>/biblia.md` (formato de `series/dia-zero/biblia.md`), as fichas em `series/<nome>/personagens.json` e o mapa em `series/<nome>/mundo.json` (formatos de `series/dia-zero/`) e faça push.

## 2. Roteiro do episódio
Use a bíblia, a classificação da série e o resultado da votação. Estrutura obrigatória:
- **CENA 0 · GANCHO (0–2 s):** flash-forward do momento mais forte do episódio + frase curta de impacto em caixa alta (máx. 4 palavras por linha). Sem contador.
- **ANTERIORMENTE EM… (4–6 s, a partir do episódio 2):** 3 momentos do episódio anterior com uma frase curta cada.
- **ABERTURA:** "EPISÓDIO X/Y" + carimbo "A MAIORIA ESCOLHEU: ..." (transição glitch).
- **CENAS** (12 ou mais), cada uma com:
  - CENA nº — início s a fim s
  - CENÁRIO + props + clima/hora (ou PLANO DE DETALHE: maçaneta, olho, celular, chave, relógio)
  - PERSONAGENS: quem, posição, vista (frente/costas/lado/3-4), pose, emoção e mudanças durante a fala, se anda/corre/pula, objeto na mão, interação (mãos dadas, abraço, carregar, empurrar)
  - PLANO: médio, conjunto, close ou aberto (ver enquadramento abaixo), por cima do ombro, travelling, foco, câmera na mão, vertigo, câmera lenta; TRANSIÇÃO de entrada
  - LUZ E DETALHES: breu com lanterna, sombra na parede, frio, poeira, horda, relâmpago, susto, gotas na lente
  - NARRAÇÃO com direção de voz entre colchetes; falas de outros personagens separadas
  - LEGENDA em CAIXA ALTA, máx. 4 palavras por pedaço
  - SOM com tempo (nomes do motor: bang, knock, lock, door_open, door_close, step, shuffle, echo_step, glass, impact, thunder, no_service, notif, vibe, click, growl, car_alarm, siren, heartbeat, breath, static, crowd, beep, stamp, whoosh)
- **FINAL:** pergunta A/B em tela dividida + "CONTINUA NO EPISÓDIO X"; último episódio fecha com "FIM".
**Nomes do motor entre crases** nas linhas CENÁRIO, PERSONAGENS, PLANO, LUZ E DETALHES e SOM (ex.: CENÁRIO: `escada` · SOM: `bang` 32 s). O validador confere cada um. Modelo de formato: `tests/fixtures/roteiro_valido.md`.
**Continuidade (obrigatório):** a história anda sem saltos. Os personagens só aparecem num lugar novo se o roteiro mostrar como chegaram: toda mudança de lugar ganha uma linha `LIGAÇÃO:` (ex.: "saem do posto e descem a escada da estação") e, quando possível, uma cena curta de passagem (`entrada_metro`, `escada`, `corredor`, `rua`, corrida até o carro). Corte para outro lugar sem os personagens irem até lá (a ponte vista de longe, a Lia do outro lado do rádio) é marcado como `INSERÇÃO:` e não muda onde eles estão. Objetos pertencem ao lugar: dentro do carro o rádio é `radio_carro`; na rua/posto/metrô é `radio_portatil`; `radio` só em casa. O tempo também é contínuo: escreva `DIA X · HH:MM` no CENÁRIO; o relógio só anda para frente e pulo de mais de 3 h precisa de `relogio` ou da linha "O TEMPO PASSA". **Mapa da cidade (`mundo.json`):** o episódio começa onde o anterior terminou e só anda por ligações do mapa (posto → rua → metrô, nunca posto → metrô). **Objetos:** use só o que alguém carrega (inventário no `fim` do episódio anterior); pegar ou largar algo vira linha `PEGA: <personagem> <objeto>` / `LARGA: ...` na cena. O validador recusa pulo de lugar sem LIGAÇÃO/INSERÇÃO e objeto fora do lugar; o `lofi.check` recusa o mesmo no JSON (plano com `"insercao": true` é a exceção).
**Enquadramento perto (padrão de todas as séries):** a câmera fica perto dos personagens, como nos vídeos de referência. Escreva no PLANO de cada cena: **médio** (1 personagem, da cabeça aos joelhos, fundo desfocado), **conjunto** (2 ou mais, de corpo inteiro e grandes) ou **close** (rosto e ombros). **Aberto** só para situar um lugar novo ou quando o cenário é a informação (porta abrindo, reflexo, horda); no máximo 2 ou 3 planos abertos por episódio. No JSON isso é automático (`camera.plano`; ver SPEC "Enquadramento perto").
**Modo redes (padrão):** sem cartela de título (a ABERTURA vira o selo "EP X/Y" + carimbo "A MAIORIA ESCOLHEU: ..." sobre a 1ª cena); o gancho de 0–2 s abre já no susto, com o texto em até 4 palavras por linha; escreva uma **PERGUNTA NO MEIO** curta para o público (ex.: "VOCÊ ATENDERIA?"); nas legendas, marque a palavra-chave de cada trecho com `*palavra*`. O motor faz sozinho os cortes a cada 2–3 s, a contagem 3-2-1 antes da escolha e o loop no fim.
Regras de linguagem: plano de detalhe antes de um susto ou revelação; close no rosto em revelações; por cima do ombro em diálogos; câmera na mão em perseguições; corrida ou caminhada por um trajeto = travelling (o cenário passa) e um plano curto de chegada; câmera lenta só no pico; silêncio de 1 s antes dos sustos; pelo menos 1 som por cena. Adapte o tom ao gênero (luz, cor, trilha e ritmo).
**As falas do ElevenLabs vão na resposta do chat, sempre:** um bloco de código por personagem (nome e dica de voz em cima do bloco, fora dele), só com as falas e as tags em inglês, na ordem do episódio, para o usuário copiar e colar direto. Não basta deixar no arquivo do roteiro.
Entregue depois: narração limpa (versão CapCut e versão ElevenLabs v3 com tags em inglês, um bloco por voz), as duas opções e o resumo de 2–3 linhas.
**Episódio extra de curiosidades (padrão, junto com cada roteiro):** além do episódio, escreva um extra curto em `series/<serie>/extraNN_roteiro.md` (NN = episódio depois do qual ele sai). Ele responde uma curiosidade que o público teria sobre a série: o que aconteceu com um personagem que saiu de cena ("O que aconteceu com a Lia?"), a origem de algo, as regras do mundo, o passado de alguém ou o outro lado de uma cena. Regras: 45 a 100 s, 5 a 9 cenas, um narrador em primeira pessoa (de preferência o personagem do tema), mesmo estilo, enquadramento e modo redes (o selo vira "EXTRA"), gancho de 0–2 s, sem votação. Não pode contradizer a bíblia nem entregar o resultado de uma votação aberta; pode revelar o que a história principal deixou no ar se a bíblia permitir. Termina com uma **CHAMADA** (ex.: "A VOTAÇÃO DO EP. 3 CONTINUA ABERTA: COMENTA A OU B"; no fim da temporada, "TEMPORADA 2?"). Valide com `python3 tests/validar_roteiro.py series/<serie>/extraNN_roteiro.md`, registre na tabela "Extras" da bíblia (nº, depois do ep., tema, status) e entregue no chat junto com o roteiro do episódio: resumo das cenas e um bloco do ElevenLabs por personagem. O extra é montado com o mesmo /serie-montar (`"formato": "extra"` no JSON; arquivos `extraNN.json` e áudios em `extraNN/`).
**Antes de entregar:**
1. Salve `epNN_roteiro.md` e rode `python3 tests/validar_roteiro.py series/<serie>/epNN_roteiro.md` (`--final` no último). Ele confere a estrutura, os nomes do motor, o mapa da cidade, o relógio e os objetos. Corrija até não haver ERRO.
2. **Revisor de continuidade:** chame a ferramenta Agent (subagent general-purpose) com um prompt autocontido: o roteiro, o resumo e o `fim` do episódio anterior (de `mundo.json`) e as regras do universo. Peça uma lista objetiva do que não faz sentido na história: lugar ou tempo que pula, objeto que aparece/some, personagem ferido/cansado agindo como se nada fosse, fala que contradiz um episódio anterior, decisão do público ignorada. Corrija o que for real.
3. **Prévia:** `python3 -m lofi.previa series/<serie>/epNN_roteiro.md` gera `epNN_previa.png` (um quadro por cena). Olhe a imagem, corrija o que estiver fora do roteiro e envie-a ao usuário junto com o roteiro, para ele conferir antes de gravar as vozes.
4. `python3 -m lofi.continuidade fechar series/<serie>/epNN_roteiro.md` grava como o episódio termina (lugar, dia/hora, inventário) no `mundo.json`. Depois faça push.

## 3. Montagem (quando chegarem as vozes)
**Placar dos comentários (padrão, a partir do ep. 2):** logo depois do "Anteriormente em…", um plano `"type": "placar"` mostra a votação do episódio anterior: porcentagens de A e B, comentários por rede, os comentários **recortados dos prints** que o usuário mandou e "VOCÊS ESCOLHERAM: ...". Em empate, aparece "EMPATE!" e uma roleta gira e para na opção registrada na bíblia ("DESEMPATE: ..."). Formato e ferramenta de recorte em `SPEC.md` ("Placar dos comentários").
O usuário anexa só os áudios: um por personagem (o nome do arquivo indica o personagem).
1. Clone/atualize o repositório e instale: `pip install --break-system-packages pillow numpy scipy` (obrigatório) e tente `soundfile sherpa-onnx` (opcionais; se falharem, siga: o motor usa o scipy no áudio e roda o Whisper só com onnxruntime).
2. Copie as vozes para `series/<serie>/epNN/` com o nome do personagem e transcreva: `python3 -m lofi.transcribe ...`. Case cada frase do roteiro pelo **texto** transcrito (nunca pela ordem ou duração); um trecho pode juntar várias falas, então divida-o nas micropausas quando elas forem para cenas diferentes e use uma legenda por frase.
3. Escreva `series/<serie>/epNN.json` seguindo `SPEC.md`, posicionando os personagens com **marcas** (`"mark": "porta"`; lista no `CATALOGO.md`, seção "Marcas de posição") em vez de x/y soltos; em rádio e planos de detalhe, `"hand": "<personagem>"` para a mão ter a manga e a pele de quem age (sem redefinir os personagens travados; inclua `series_title`, `episode`, `episodes_total`, `episode_title`, `tint` do episódio e o plano `recap` apontando para `ep(NN-1).json`).
4. **Verificador:** `python3 -m lofi.check series/<serie>/epNN.json`. Corrija todos os ERROS e os avisos relevantes. Confira o áudio com `python3 -m lofi.transcribe --conferir series/<serie>/epNN.json` (fala de cada cena) e corrija falas fora de lugar.
5. **Revisor independente:** use a ferramenta Agent (subagent general-purpose) com um prompt autocontido: o caminho de `_revisao.png`, o roteiro do episódio, as fichas visuais dos personagens e a lista do que conferir (rosto coberto pela legenda, personagem cortado ou fora do quadro, roupa diferente da ficha, legenda errada ou fora de hora, cena que não corresponde ao roteiro, texto ilegível, contador encobrindo algo). Ele não viu a montagem e deve devolver uma lista objetiva de problemas com o tempo de cada um. Corrija, rode o verificador de novo e só então renderize.
6. Renderize em segundo plano com `--jobs 2` (≈3,5 s por segundo de vídeo; episódio de 3 min ≈ 10–11 min na primeira vez). O render guarda cada plano em cache: depois de um ajuste, só os planos alterados são refeitos (1–2 min). Confira duração, áudio e tamanho (crf 28 padrão; 30 se passar de 90 MB).
7. **Extras:** `python3 -m lofi.extras pacote series/<serie>/epNN.json <mp4>` → teaser (15 s), capa do TikTok e capa do Instagram (áreas seguras de cada rede; confira as duas imagens).
8. **Sempre entregue os quatro:** vídeo, teaser, capa do TikTok e capa do Instagram, e a legenda do post; faça commit do `epNN.json`, registre o resumo e o status "montado" na bíblia e faça push (nessa ordem: sem o `epNN.json` no repositório, o status não muda).
9. **Fim de temporada** (último episódio): entregue também o vídeo das escolhas (`python3 -m lofi.extras escolhas series/<serie>`: cada voto do público com o placar da bíblia e "TEMPORADA 2?"), escreva um gancho de 2–3 linhas para a temporada 2 na bíblia e ofereça a compilação para o YouTube (`python3 -m lofi.extras temporada ...`), pedindo os MP4s dos episódios.

## 4. Legenda do post
Gancho de 1 linha com o dia · resumo em 2–3 frases citando a escolha do público · as duas opções com 🅰️ e 🅱️ · "Comenta A ou B. A maioria decide o próximo episódio." · "📺 TÍTULO · Episódio X/Y" · 8–10 hashtags do gênero. Sugira fixar um comentário "Vota aqui: A ou B 👇". Para o teaser: 1 linha + "Episódio X no perfil".

## Testes da skill
`tests/evals.json` tem casos de teste (roteiro do meio, roteiro final, voto inválido, planejamento, montagem). Ao alterar esta skill ou os comandos, rode esses casos (skill skill-creator) e confira que continuam passando.

## Dicas de qualidade
- Personagem principal sempre com a mesma roupa e cor de destaque em todos os episódios (`personagens.json` é a fonte única); vilões e criaturas com silhueta bem diferente.
- Escreva falas que aproveitem os gestos automáticos ("ali", "eu", "não") e use interações nos momentos emocionais (mãos dadas na fuga, abraço no reencontro, carregar o ferido).
- Paralaxe em planos longos, zoom lento em momentos tensos, relâmpago e tremor só nos picos.
- Transição whip para mudança de lugar, flash para susto, glitch saindo do gancho.
- Se a história pedir um lugar ou uma peça de roupa que não existe, crie no motor (`lofi/scenes.py` ou `lofi/rig.py`) no mesmo padrão; cenário novo também ganha chão e marcas em `lofi/mapa.py` (confira com `python3 -m lofi.mapa <cenario>`) e entra em `LUGAR` (e em `OBJETO_DO_LUGAR`, se for um objeto de um lugar). Teste com uma folha de referência, documente no `SPEC.md` e faça push.