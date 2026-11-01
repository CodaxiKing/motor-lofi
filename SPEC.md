# Motor lo-fi · formato do roteiro (episodio.json)

Rodar: `python3 -m lofi.render episodio.json` (teste de quadros: `--test 3 12.5`).
Transcrever vozes: `python3 -m lofi.transcribe roberta.mp3 rafa.mp3` → mostra cada frase com tempo.
Dependências obrigatórias: `pip install --break-system-packages pillow numpy scipy` + ffmpeg.
Opcionais: `soundfile` (o motor usa o `scipy` quando ele falta) e `sherpa-onnx` (texto na transcrição; sem ele,
`lofi.transcribe` entrega só os tempos de cada trecho, e as falas são casadas com o roteiro pela ordem).

## Campos principais
```json
{
  "out": "ep3.mp4", "fps": 30, "total": 62.0,
  "voices":   {"roberta": "roberta.mp3", "rafa": "rafa.mp3", "lia": "lia.mp3"},
  "speakers": {"rafa": {"label": "RAFA", "color": [190,240,190]}, "lia": {"label": "RÁDIO", "color": [255,226,120]}},
  "characters": {"dona_cida": {"top": [150,60,90], "top_style": "coat", "hair": "bun", "hair_color": [200,200,200], "glasses": true}},
  "hud": {"place": "APTO 904", "days": [[0, "DIA 3", "07:10"], [40.0, "DIA 4", "21:00"]], "sec_per_min": 8},
  "lightning": [12.3, 40.1],
  "clips": [{"voice": "roberta", "src": [0.0, 6.2], "at": 3.5}, {"voice": "lia", "src": [0, 3.4], "at": 20, "radio": true}],
  "subs":  [{"voice": "roberta", "src": [0.0, 1.9], "text": ["EU DESCI", "PELA ESCADA."]}],
  "shots": [ ... ],
  "sfx":   [{"t": 5.1, "name": "bang", "gain": 1.0}, {"t": 50, "name": "heartbeat", "dur": 8}],
  "music": [{"start": 3.5, "end": 30, "gain": [0.04, 0.1], "tense": 0.6}]
}
```
- `clips.src` = trecho do arquivo de voz (segundos); `at` = onde entra no vídeo. `radio: true` aplica filtro de rádio.
- `subs.src` = tempo da fala no arquivo original; o motor converte para o tempo do vídeo. Máx. 4 palavras por pedaço.
- Ambiente sonoro (chuva, zumbido, eco, vento) é automático por cenário. Trovão é automático para cada `lightning`.

## Planos (`shots`)
Tipos: `scene` (padrão), `title` (abertura com carimbo), `choice` (tela dividida A/B).
```json
{"start": 0, "end": 3.5, "type": "title", "title": "EPISÓDIO 3/5", "subtitle": "DIA ZERO",
 "stamp": {"t": 1.8, "top": "A MAIORIA ESCOLHEU", "word": "TELHADO"}}

{"start": 3.5, "end": 11, "scene": "telhado", "transition": "whip",
 "camera": {"x": [60, -40], "zoom": [1.0, 1.1], "cy": 0.6},
 "shake": [7.2], "effect": "peephole", "props": {"door": [[0,0],[1.2,1]]},
 "overlay": [{"type": "phone", "text": ["SEM", "SERVIÇO"], "t": [6, 8.5]}, {"type": "text", "text": "3 HORAS DEPOIS", "t": [3.5, 5]}],
 "actors": [
   {"char": "roberta", "x": [200, 640], "y": 1650, "view": "side", "facing": 1, "walk": true,
    "emotion": [[0, "fear"], [3.0, "determined"]], "pose": "idle", "look": 0},
   {"char": "rafa", "x": 800, "y": 1700, "view": "front", "emotion": "shock", "pose": "scared", "enter": 2.0}
 ]}

{"start": 55, "end": 62, "type": "choice",
 "a": {"label": "ESCADA", "scene": "escada", "actors": [...], "crop_x": 270},
 "b": {"label": "TELHADO", "scene": "telhado", "actors": [...]},
 "end_card": {"t": 60, "text": "CONTINUA NO EPISÓDIO 4"}}
```
Valores animáveis (x, y, zoom, emoção, pose, view, walk...): número fixo · `[a, b]` (interpola no plano todo) ·
`[[t, valor], ...]` (t em segundos desde o início do plano).

## Biblioteca
A lista completa e sempre atualizada de cenários, personagens prontos, poses, emoções, vistas, sons, transições,
planos de detalhe e acústicas está em **[CATALOGO.md](CATALOGO.md)**, gerado do código (`python3 -m lofi.catalogo`).
O validador de roteiro usa esse mesmo catálogo, então um nome que não está lá dá erro antes da montagem.
- Novos personagens via `characters` (todos os campos na seção "Guarda-roupa" abaixo).
- Efeitos de plano: `effect: "peephole"`, `shake: [t]`, `lightning` na raiz.
- Legenda: faixa fixa no terço inferior; desvia sozinha do rosto dos personagens.

## Recursos v2 (nativos)
**Fala e atuação**
- Boca sincronizada: automática para todo ator cuja voz tenha o mesmo nome do personagem (ou `"voice": "nome"`). `"lipsync": false` desliga.
- Gestos na fala: cabeça e mão se mexem sozinhas enquanto o personagem fala.
- Transições de pose e emoção: use keyframes de texto (`"pose": [[0,"idle"],[1.2,"point"]]`); a pose muda com antecipação e leve exagero, a emoção troca com piscada e "pop".

**Câmera de cinema** (dentro de `camera`)
- `"close": 0` → close no rosto do ator 0 (`close_zoom` padrão 2.9, `close_in` = segundos para entrar). Fundo desfoca, personagem fica nítido.
- `"follow": 0` → travelling acompanhando o ator 0 (`zoom` padrão 1.3).
- `"focus": 1` → foco no ator 1 (os outros e o fundo desfocam). Aceita keyframes para trocar o foco: `[[0,1],[2.5,0]]`.
- Plano por cima do ombro: ator com `"fg": true, "view": "back", "x": 260, "y": 2380, "scale": 3.4, "blur": 6` (coordenadas de tela) + `focus` em quem fala.

**Legendas estilo Reels**: palavra por palavra com destaque amarelo (padrão). `"word_captions": false` volta ao modo simples.

**Acabamento**
- `"cold": true` no plano (ou `"breath": true` no ator) → bafo de frio.
- Respingos de chuva na cabeça: automáticos em cenários com chuva.
- `"flashlight": 14` no ator (ângulo em graus; true = para onde ele olha) → feixe de lanterna com poeira.
- `"dust": 60` no plano → poeira flutuando.
- `"crowd": {"count": 10, "area": [x0,y0,x1,y1], "dir": 1|-1|0, "speed": 40, "seed": 3}` → horda com andares, velocidades e roupas variadas.
- Novos cenários: `hospital` (flicker), `mercado` (flicker), `metro` (props: `train` 0–1 = farol chegando).

**Gancho (primeiros 2 s)**: plano com `"hook": {"text": "ELES ESTÃO\nOUVINDO", "y": 820}` antes do título. O título seguinte com `"transition": "glitch"`.

## Episódios longos (2–3 min)
- Render em paralelo: `python3 -m lofi.render episodio.json --jobs 2` (rode em segundo plano; velocidade na seção "Velocidade" no fim).
- Compressão: `"crf": 28` (padrão) deixa ~60–80 MB para 3 min. Use 30 se precisar de arquivo menor.

## Pasta da série (continuidade)
Cada série vive no repositório em `series/<nome-da-serie>/`:
- `biblia.md` — mapa da série, regras, cor de cada episódio, tabela de episódios
  (nº, status: planejado/roteiro/montado, pergunta A/B, voto vencedor e placar) e os resumos de cada episódio.
- `personagens.json` — fichas travadas (seção "Personagens travados").
- `epNN_roteiro.md` — roteiro completo do episódio NN (cenas, narração limpa, sons).
- `epNN.json` — roteiro técnico usado na montagem. **Um episódio só fica "montado" com o `epNN.json` versionado**:
  é dele que o próximo episódio tira o "Anteriormente em…".

## Recursos v3
**Personagens**
- Vista `"view": "3q"` (meio perfil; use `facing` 1/-1).
- Poses novas: `jump` (use com `"lift": [[t, px]]` para subir), `hide` (agachado protegendo a cabeça), `open_door`, `remove_bag`, `fallen` (deitado; gira sozinho), `crawl` (rastejando; gira sozinho). `"rot": graus` gira qualquer pose.
- Correr: `"walk": true, "run": true`. Tremer de medo: `"tremble": 0–1`.
- Emoções novas: `cry` (lágrimas escorrendo), `panting` (ofegante: ombros e boca no ritmo).
- Corpos: em `characters`, `"body": "child" | "old" | "tall" | "fat" | "thin"`.
- Objetos na mão: `"prop": "radio" | "flashlight" | "phone" | "key" | "bag"` (combine com `pose: hold/phone/reach/remove_bag`).
- Zumbis: `zombie`, `zombie_corredor` (use run), `zombie_rastejante` (use pose crawl), `zombie_enfermeiro`, `zombie_policial`; `"sniff": true` = farejando o som.

**Luz**
- `"dark": 0–1` no plano → breu; só a lanterna (`flashlight` no ator) e `"lights": [[x, y, raio]]` iluminam. Personagens ficam levemente visíveis.
- `"wall_shadow": {"light": [x, y], "alpha": 0.5}` → sombra projetada na parede atrás dos personagens.

**Cenários vivos e clima**
- apartamento: ventilador girando (`fan`), `"tv": "static"` (chiado), `"wind": 0–1` (cortina balançando).
- Nuvens se movendo e poças com ondinhas nos externos.
- No plano: `"rain": "forte" | "normal" | "fraca" | "nenhuma"`, `"fog": 0–1`, `"snow": 0–1`, `"time": "dia" | "entardecer" | "amanhecer" | "madrugada" | "noite"` (aceita keyframes, transição suave).
- Novos lugares: `escola`, `delegacia` (sirene), `posto`, `floresta`, `carro` (limpador animado), `esgoto`, `igreja`.
- `rua_amanhecer`: a mesma rua de madrugada clareando (céu claro, sem lua, garoa fina). Use quando a cena precisar ser de dia: o `time` só muda a cor e não tira a lua da `rua`.

**Câmera e pós**
- Plano de detalhe: `{"type": "detail", "subject": "macaneta|olho|celular|chave|relogio", "params": {...}}`
  (macaneta: `turn`, `light` · olho: `pupil`, `look`, `blink_at`, `reflect`, `tear`, `brow` · celular: `text`, `notifs`, `signal`, `type_dur` · chave: `turn` · relogio: `minutes`).
- `camera.handheld: px` (câmera na mão) · `camera.vertigo: [1.0, 1.3]` (dolly zoom) · `"slowmo": 0.4` (câmera lenta) ·
  `"scare": [t]` (susto: tremor + aberração de cor + impacto) · `"lens_drops": true` (gotas na lente) · brilho nas luzes automático (`"bloom": false` desliga).
- Estilo: `"style": "desenho"` (traço de nanquim + papel) e `"tint": [r, g, b, força]` (cor do episódio; também por plano).

**Anteriormente em…**: `{"type": "recap", "from": "ep02.json", "times": [12, 40, 75], "label": "ANTERIORMENTE EM DIA ZERO", "lines": ["...", "...", "..."]}`
(usa as cenas do episódio anterior direto do roteiro técnico; 4–6 s).
Se o `epNN.json` anterior não estiver no repositório, descreva os momentos no próprio plano com `moments`
(um por frase, mesmos campos de um plano de cena):
`"moments": [{"scene": "entrada", "actors": [{"char": "roberta", "x": 540, "y": 1650, "view": "back", "emotion": "fear"}]}, ...]`.
Sem arquivo e sem `moments`, o verificador dá ERRO (o render mostra só as frases sobre chiado de TV).

**Episódio legado**: `"legado": true` na raiz marca um roteiro técnico reconstruído de um episódio publicado num formato
antigo. O verificador passa a tratar as regras de formato atuais (gancho, 12–20 cenas, 2–3 min) como informação.

## Mapa dos cenários: marcas de posição e chão
Cada cenário tem em `lofi/mapa.py` a **área de chão** (onde os pés podem ficar) e **marcas nomeadas**. Prefira marcas a x/y soltos:
```json
{"char": "roberta", "mark": "porta"}                          // x, y e padrões da marca (ex.: porta = de costas)
{"char": "rafa", "mark": [[0, "fundo"], [3.5, "frente"]], "walk": true}   // anda de uma marca até a outra
{"char": "lia", "mark": "sofa", "dx": -60}                     // deslocado 60 px para a esquerda
```
- x/y escritos no ator vencem a marca; vista, pose, escala, `fg` e `blur` da marca só entram se o ator não definir.
- Lista de marcas: seção "Marcas de posição por cenário" do [CATALOGO.md](CATALOGO.md). Imagem com a personagem em cada marca:
  [`examples/mapa_cenarios.png`](examples/mapa_cenarios.png) (`python3 -m lofi.mapa`; só um cenário: `python3 -m lofi.mapa escada`).
- O verificador dá **ERRO** para marca que não existe no cenário e para personagem **fora do chão** (flutuando ou dentro da
  parede), conferindo início, meio e fim de cada plano. Exceções: `fg` (primeiro plano), `carried_by`, horda e `"livre": true`
  (de propósito, ex.: fantasma voando). Quem entra ou sai pela lateral (x fora da tela) não é acusado.
- Cenário novo precisa entrar no `MAPA` (o teste de fumaça falha se faltar ou se uma marca cair fora do chão).

## Partes do corpo: mão e braço do personagem
Quando a cena mostra só uma parte do corpo (a mão no rádio, girando a chave, na maçaneta, no celular), diga **de quem** é:
```json
{"scene": "radio", "hand": "rafa"}                                   // braço com a manga verde e a pele do Rafa, no dial
{"scene": "radio", "hand": {"of": "lia", "at": "antena"}}            // posição nomeada
{"type": "detail", "subject": "chave", "hand": "roberta"}           // a mão acompanha a cabeça da chave girando
{"type": "detail", "subject": "celular", "hand": {"of": "roberta", "at": "dedo"}}
{"type": "detail", "subject": "olho", "hand": "rafa"}                // pele em volta do olho = pele do Rafa
"hand": false                                                        // sem mão
```
- Manga, punho e pele vêm da ficha (`personagens.json` ou personagem pronto); manga curta mostra o antebraço.
- Posições por cenário: seção "Partes do corpo" do [CATALOGO.md](CATALOGO.md) (`lofi/partes.py`).
- A legenda desvia sozinha do braço e do objeto em destaque (rádio, tela do celular, fechadura, olho).
- Verificador: ERRO para mão de personagem desconhecido ou posição inexistente; AVISO quando o rádio ou a chave mostram
  a mão genérica (sem `hand`).

## Continuidade de lugar e objetos
A história não pode pular de lugar. `lofi/mapa.py` agrupa os cenários em lugares (`LUGAR`: `apartamento`/`entrada`/`radio`/`janela` = casa;
`carro`/`radio_carro` = carro; `rua`/`rua_amanhecer`/`entrada_metro` = rua; os demais são o próprio lugar).
- **Roteiro:** toda cena que muda de lugar precisa de uma linha `LIGAÇÃO:` (como eles chegam lá; de preferência com uma cena de passagem,
  ex.: `entrada_metro` entre a rua e o `metro`). Corte para outro lugar sem os personagens (a ponte vista de longe, quem fala do outro
  lado do rádio) é `INSERÇÃO:` e não muda onde eles estão. O `tests/validar_roteiro.py` dá ERRO nos dois casos.
- **Objetos do lugar** (`OBJETO_DO_LUGAR`): `radio` é o rádio de casa; no carro use `radio_carro` (painel, para-brisa com chuva);
  fora de casa, `radio_portatil` (rádio de pilha na mão). `{"type": "detail", "subject": "chave", "params": {"onde": "carro"}}` desenha a ignição.
- **JSON:** o `lofi.check` dá ERRO quando o plano usa um objeto de outro lugar que o da cena anterior; um plano com `"insercao": true` é isento.

## Vídeo de comentários (`"formato": "comentarios"`)
Usado pela skill `serie-comentarios`: um personagem responde comentários dos seguidores. Arquivos em `series/<serie>/comentarios/cNN.json`
(o motor acha o `personagens.json` da série na pasta acima).
- Cartão de comentário estilo app, desenhado por cima de todos os filtros:
  `{"type": "comment", "user": "@usuario", "text": "texto do comentário", "likes": 1240, "t": [início, fim], "y": 700, "label": "Respondendo a"}`
  (`y` = centro do cartão, nunca acima do contador; texto quebra sozinho até 6 linhas; emojis são removidos; `likes` opcional, 1240 vira "1,2 mil").
- O verificador troca as regras de episódio (gancho, título, A/B, 12–20 cenas, 2–3 min) por: 20–90 s, pelo menos um cartão,
  nenhum cartão vazio e **cartão cobrindo rosto = ERRO**.
- Fontes do cartão: Inter (`font("sans")` e `font("sansb")`, licença OFL em `lofi/fonts/LICENSE-Inter.txt`).

## Qualidade
- `python3 -m lofi.check epNN.json` → erros de estrutura e de quadro (legenda no rosto, personagem cortado, cabeça sob o contador)
  + `_revisao.png` com um quadro por plano e por legenda, para um revisor independente aprovar antes do render.
- `python3 tests/validar_roteiro.py epNN_roteiro.md [--final]` → confere gancho, 12–20 cenas, A/B, ElevenLabs.
- `tests/evals.json` → casos de teste da skill.

## Extras
- `python3 -m lofi.extras teaser epNN.json epNN.mp4` → teaser de ~15 s para Stories (gancho + 3 melhores momentos + cartela).
- `python3 -m lofi.extras pacote epNN.json epNN.mp4 [tempo]` → **entrega padrão**: teaser + capa do TikTok + capa do Instagram.
- `python3 -m lofi.extras capa epNN.json [tempo] [--tiktok|--instagram] [--guias]` → `epNN_capa_tiktok.png` e `epNN_capa_instagram.png`
  (1080×1920; usam `series_title`, `episode`, `episodes_total`, `episode_title`). Texto dentro da área segura de cada rede:
  TikTok evita o topo (~200 px), a base (~480 px, legenda e música) e a coluna direita (~150 px, botões); Instagram mantém
  tudo no recorte 3:4 do grid do perfil (y 240–1680) e no 4:5 do feed. O quadro escolhido tem todos os rostos inteiros,
  sem legenda e sem contador. `--guias` desenha as áreas seguras (só para conferir).
- `python3 -m lofi.extras temporada saida.mp4 "TÍTULO" ep1.mp4 ep2.mp4 ...` → compilação 16:9 para o YouTube + capítulos.

## Guarda-roupa (v4)
Todos os campos vão em `characters` no roteiro (ou na ficha da bíblia). Cores em `[r, g, b]`.

| Campo | Opções |
|---|---|
| `skin` | `palido`, `claro`, `medio`, `moreno`, `escuro`, `oliva`, `verde`, `azul` ou `[r, g, b]` |
| `top_style` | `shirt`, `tshirt`, `puffer`, `hoodie`, `sweater`, `leather`, `suit` (com gravata), `trench` (sobretudo), `labcoat` (jaleco), `scrubs`, `uniform`, `chef`, `dress` (vestido), `torn` |
| `top`, `inner`, `tie` | cor da roupa, da camisa por baixo do casaco/jaleco, da gravata |
| `sleeves` | `long`, `short` |
| `bottom` | `pants`, `shorts`, `skirt` (com `skirt` = cor e `tights` = meia-calça) |
| `legs`, `shoes` | cor da calça/shorts e do sapato |
| `hair` | `short`, `long`, `ponytail`, `bun`, `bob`, `curly`, `afro`, `braids`, `pigtails`, `spiky`, `mohawk`, `bald` (+ `hair_color`) |
| `facial` | `beard`, `mustache`, `stubble` (+ `facial_color`) |
| `hat` | `beanie`, `cap`, `helmet`, `hood`, `fedora`, `cowboy`, `tophat`, `crown`, `witch`, `chef`, `headband`, `bandana_hat` (+ `hat_color`) |
| `acc` (lista) | `sunglasses`, `eyepatch`, `mask`, `earrings`, `bow`, `headphones`, `necklace`, `badge`, `stethoscope`, `tie`, `bowtie`, `bandana` |
| outros | `glasses`, `scarf` (cor), `backpack` (cor), `cape` (cor, balança), `body`, `ghost: true` (translúcido), `scale` |

Personagens prontos além da série zumbi: `detetive`, `cientista`, `estudante`, `estudante2`, `executiva`, `executivo`, `medica`,
`policial`, `roqueiro`, `vovo`, `vovo2`, `crianca`, `bruxa`, `rainha`, `chef`, `cowboy`, `fantasma`, `dj`, `pirata`.
Para variar um pronto: `"characters": {"detetive": {"skin": "escuro", "hat_color": [30, 30, 30]}}`.
Para criar um novo: `"characters": {"marina": {"top_style": "leather", "top": [120, 30, 40], "hair": "braids", "skin": "moreno", "acc": ["earrings"]}}`
e use `"char": "marina"` nos atores.

## Personagens travados da série
`series/<serie>/personagens.json` guarda a ficha de cada personagem da série (mesmos campos do guarda-roupa).
O motor carrega esse arquivo sozinho (da pasta do roteiro ou da pasta acima) e ele **sempre vence** o campo `characters`
do roteiro e o `custom` dos atores. O verificador avisa quando um roteiro tenta redefinir um personagem travado e quando
a série não tem `personagens.json`. Chaves que começam com `_` são comentários.

## Atuação e som (v5)

**Eco por ambiente (automático).** Cada fala recebe a acústica do cenário do plano em que ela começa:

| Acústica | Cenários | Efeito |
|---|---|---|
| `grande` | escada, igreja, esgoto, metrô | reverberação longa |
| `media` | corredor, hospital, escola, mercado, delegacia | eco curto |
| `sala` | apartamento, entrada, rádio | ambiente leve |
| `abafado` | carro | voz fechada, sem agudos |
| `aberto` | rua, telhado, ponte, floresta… | seca |

Para trocar: `"acoustic": "grande"` no plano ou no clipe (`null` desliga só ali). `"acoustics": false` na raiz desliga tudo.
A boca segue a voz seca, então o eco não deixa o personagem "falando" depois da frase.

**Boca com vogais (automático).** O motor lê o espectro de cada voz e escolhe o formato da boca quadro a quadro:
A (aberta), E (larga, com dentes), O (redonda), U (biquinho), M (lábios fechados) e repouso. Os limites se ajustam a cada voz.

**Gestos ligados à fala (automático).** Quando o ator está em `idle` e a palavra da legenda é dita:

| Palavras | Gesto |
|---|---|
| ali, lá, olha, aquele, aquela, aquilo, veja | aponta |
| eu, meu, minha, mim, comigo, juro | mão no peito |
| sim, isso, claro, certo | acena com a cabeça |
| não, nunca, jamais, nada | balança a cabeça |
| desculpa, perdão, sinto, morreu, sozinha | cabeça baixa e rosto triste |

Desligar: `"gestures": false` no ator ou na raiz. Gesto manual: `"gesture": "nod" | "shake" | "down"` (aceita keyframes).

**Interações entre personagens**

| Campo / pose | O que faz |
|---|---|
| `"hold": "rafa"` | os dois andam de mãos dadas (poses e mãos unidas automáticas) |
| `"carried_by": "rafa"` | o ator vai no colo de Rafa (posição, rotação e sombra automáticas); use `"pose": "carry"` em quem carrega |
| `"pose": "hug"` | abraço — ponha os dois em `view: "3q"`, virados um para o outro, a ~140 px |
| `"pose": "push"` | empurrar |
| `"pose": "chest"` / `"hand_r"` / `"hand_l"` / `"reach_l"` | mão no peito, mão estendida para a direita/esquerda |

Exemplo completo: [`examples/demo4/demo4.json`](examples/demo4/demo4.json).

**Velocidade.** ~3,5 s de processamento por segundo de vídeo com `--jobs 2` (episódio de 3 min ≈ 10–11 min).
Esse é o único valor de referência; os números de versões antigas (7 s, 10 s) não valem mais.
