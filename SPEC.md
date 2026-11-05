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

**Enquadramento perto (padrão)** — `camera.plano`: `aberto` · `conjunto` · `medio` · `close`
- Sem nada escrito, todo plano com personagens se enquadra sozinho: **1 personagem → `medio`** (da cabeça até os joelhos, enchendo o
  quadro, fundo desfocado) e **2 ou mais → `conjunto`** (todos de corpo inteiro, grandes). O personagem é redesenhado no tamanho
  final (traço nítido); só o fundo amplia e desfoca. Há uma aproximação lenta durante o plano (`"push": 0` desliga).
- `"plano": "aberto"` mostra o cenário inteiro: use só para situar um lugar novo ou quando o cenário é a informação (porta abrindo,
  reflexo na geladeira, horda chegando). `"alvo": 1` (ou `[0, 2]`) escolhe quem entra no enquadramento.
- `"plano": "close"` (ou `"close": 0`) = cabeça e ombros enchendo o quadro, em qualquer distância do cenário.
- Closes de objeto (`radio_carro`, `cftv`...), planos de detalhe, `fg` (por cima do ombro) e planos com `zoom`/`follow`/`vertigo`
  ficam como estão. A camada da frente do cenário (balcão, grades) acompanha o zoom.
- Episódio inteiro no enquadramento antigo: `"plano_padrao": "aberto"` no topo do JSON (os episódios já publicados de Dia Zero usam).

**Câmera de cinema** (dentro de `camera`)
- `"close": 0` → close no rosto do ator 0 (zoom automático pelo tamanho do personagem; com `close_zoom` fixo, ou com `plano_padrao: aberto`, 2.9; `close_in` = segundos para entrar). Fundo desfoca, personagem fica nítido.
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
- Som `bell` = sininho da porta da loja (duas batidas metálicas).

**Gancho (primeiros 2 s)**: plano com `"hook": {"text": "ELES ESTÃO\nOUVINDO", "y": 820}` antes do título. O título seguinte com `"transition": "glitch"`.

## Episódios longos (mínimo 2 min, sem máximo)
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
  (macaneta: `turn`, `light` · olho: `pupil`, `look`, `blink_at`, `reflect`, `tear`, `brow` · celular: `text`, `notifs`, `signal`, `type_dur`, `hora`, `chat` = conversa de mensagens: `{"nome", "visto", "destaque", "digita", "digita_dur", "msgs": [{"de": "ele"|"eu", "txt", "t", "type_dur"}]}` · chave: `turn` · relogio: `minutes`).
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
antigo. O verificador passa a tratar as regras de formato atuais (gancho, 12+ cenas, mínimo 2 min) como informação.

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

## Travelling lateral: o cenário passa (`"travelling"`)
Quando os personagens andam ou correm por um caminho (rua, mata, túnel, corredor, ponte), o cenário rola atrás deles em vez de
eles atravessarem um fundo parado:
```json
{"scene": "rua", "travelling": 420, "rain": "forte",
 "actors": [{"char": "roberta", "mark": "dir", "view": "side", "facing": 1, "walk": true, "run": true, "hold": "rafa"},
            {"char": "rafa", "mark": "centro", "view": "side", "facing": 1, "walk": true, "run": true}],
 "crowd": {"count": 7, "area": [-420, 1700, -120, 1780], "dir": 1, "speed": 45}}
```
- Valor = velocidade do chão em px/s (positivo: vão para a direita; negativo: para a esquerda). `{"speed": 300, "frente": true}`
  também passa postes borrados na frente da câmera. ~250 andando, ~400 correndo.
- Camadas com paralaxe geradas por código (`lofi/travelling.py`) e sem emenda visível: céu parado, prédios/árvores ao longe,
  fachadas/paredes no meio, calçada/piso com postes, lixeiras, hidrantes, portas, pilares e luminárias em espaçamento irregular.
- Tema pelo cenário (`TEMA`): cidade (rua, rua_amanhecer, entrada_metro, posto, telhado), mata (floresta), túnel (metro), esgoto,
  ponte e interno (corredor, hospital, escola, delegacia, mercado, igreja, casa, cada um com a cor da parede). Hora, chuva, névoa e
  luz vêm do cenário original (`rain`, `fog`, `time`, `dark` continuam valendo).
- Personagens ficam no lugar: marcas próprias do travelling `esq`, `centro`, `dir`, `fundo`, `frente` (chão de y 1560 a 1900).
  Quem persegue entra com `crowd` (`dir` no mesmo sentido) ou com x/y animado.
- **Chegada:** `{"speed": 400, "chegada": "carro", "para": 1.5, "chegada_x": 760}` desacelera nos últimos `para` segundos e
  o destino (`carro`, `porta`, `escada`, `portao`) entra no quadro e para em `chegada_x`; os personagens param de andar sozinhos.
- **De frente / de costas:** `{"speed": 400, "dir": "frente"}` = eles correm na direção da câmera (`"view": "front"`) e o caminho
  vai ficando para trás; `"dir": "fundo"` = a câmera segue por trás (`"view": "back"`) e o caminho vem. Rua com prédios e postes,
  mata, túnel e corredores em perspectiva.
- Verificador: ERRO para valor inválido ou travelling fora de plano de cenário; AVISO para personagem parado (vai deslizar) ou
  virado contra o movimento.

## Mapa da cidade, objetos e relógio (`series/<serie>/mundo.json`)
```json
{"lugares": {"rua": {"cenarios": ["rua", "rua_amanhecer", "beco", "entrada_metro"]}, "metro": {"cenarios": ["metro", "vagao"]}},
 "ligacoes": [["rua", "metro", "pela escada da estação Sé"]],
 "fim": {"4": {"lugar": "carro", "dia": 5, "hora": "05:20", "inventario": {"roberta": ["radio", "lanterna"]}}}}
```
- O validador de roteiro (via `lofi/continuidade.py`) confere: o episódio começa onde o anterior terminou (`fim`), cada mudança de
  lugar segue uma ligação do mapa (senão mostra a rota: "posto → rua → metro"), o relógio só anda para frente e pulo de mais de 3 h
  precisa de `relogio` ou "O TEMPO PASSA", e objetos usados estão com alguém (`radio_portatil` precisa de "radio", `flashlight`
  de "lanterna"). No roteiro, `PEGA: roberta lanterna` / `LARGA: roberta radio` mudam o inventário.
- `python3 -m lofi.continuidade fechar epNN_roteiro.md` grava o `fim` do episódio; `... rota series/x posto ponte` mostra o caminho.
- O `lofi.check` também recusa relógio do HUD voltando no tempo ou começando antes do fim do episódio anterior.
- Cenários de passagem: `portao` (frente do prédio), `beco`, `viaduto`, `estacionamento`, `vagao` (por dentro).

## Prévia, cache e fim de temporada
- `python3 -m lofi.previa epNN_roteiro.md` → `epNN_previa.png`: um quadro por cena a partir do texto do roteiro (cenário, hora,
  personagens nas marcas, LIGAÇÃO/INSERÇÃO e lugar do mapa), antes de gravar as vozes.
- `python3 -m lofi.render ep.json --jobs 2` guarda cada plano em `series/<serie>/_cache/` e só renderiza de novo os planos que mudaram
  (o plano, o que é global ao vídeo, as vozes, as fichas ou o código do motor). `--sem-cache` renderiza tudo como antes.
- `python3 -m lofi.extras escolhas series/<serie>` → vídeo vertical "vocês escolheram": cada episódio com as duas opções, barras com
  o placar da bíblia (quando houver) e "TEMPORADA 2?" no fim.

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
- O verificador troca as regras de episódio (gancho, título, A/B, 12+ cenas, mínimo 2 min) por: 20–90 s, pelo menos um cartão,
  nenhum cartão vazio e **cartão cobrindo rosto = ERRO**.
- Fontes do cartão: Inter (`font("sans")` e `font("sansb")`, licença OFL em `lofi/fonts/LICENSE-Inter.txt`).

## Cenário generativo e ao pé da letra (`lofi/cenario_gen.py`, `lofi/moveis.py`, `lofi/literal.py`)

**Regra da casa: toda cena é exatamente o que o áudio descreve, no mesmo segundo.** Se a narração diz "você empurra a
caixa de milho", a tela mostra a caixa de milho sendo empurrada; "uma lata... duas... três" mostra uma, duas e três latas.

- **Ambientes prontos** (35, além dos cenários desenhados): `quarto`, `quarto_crianca`, `sala_estar`, `cozinha`, `banheiro`,
  `lavanderia`, `porao`, `sotao`, `cabana`, `velorio`, `corredor_mercado`, `hortifruti`, `farmacia`, `lanchonete`, `escritorio`,
  `biblioteca`, `laboratorio`, `oficina`, `garagem`, `consultorio`, `quarto_hospital`, `sala_espera`, `celeiro`, `quintal`,
  `frente_casa`, `rua_bairro`, `avenida`, `praca`, `parquinho`, `estrada`, `campo`, `cemiterio`, `acampamento`, `praia`,
  `terreno_baldio`. Use como qualquer cenário: `"scene": "cozinha"`. Marcas automáticas: `centro`, `esq`, `dir`, `fundo`,
  `frente` e uma marca na frente de cada móvel (`geladeira`, `fogao`, `cama`...). Folha: `examples/ambientes.jpg`.
- **Descrição no plano** (o cenário é montado para aquela frase): `"cenario": {"base": "cozinha", "luz": "escuro",
  "sem": ["mesa_cozinha"], "mudar": [{"m": "geladeira", "aberta": true}], "mais": [{"m": "cracha", "em": "chao", "x": 0.3, "z": 0.6}]}`
  ou do zero: `{"tipo": "interior", "parede": ["azulejo", [200, 210, 200]], "piso": "xadrez", "luz": "fria", "largura": 400,
  "lateral": {"conteudo": ["milho", "latas"]}, "moveis": [...]}`; externo: `{"tipo": "exterior", "chao": "grama",
  "horizonte": "mata", "hora": "noite", "nevoa": 0.5, "chuva": "fraca", "moveis": [...]}`.
  Móvel: `{"m": nome, "em": "fundo|parede|teto|chao|esq|dir|frente", "x": 0–1, "z": 0–1, "h": cm, "id": "marca"}` + opções do
  desenho (`cor`, `aberta`, `aceso`, `texto`, `conteudo`, `itens`, `quebrada`, `visor`, `hora`...). Lista completa no CATALOGO.md.
  Props do plano: `luz` 0–1, `flicker`, `tv` ("chiado"/"ligada"), `emergencia` 0–1.
- **Close do objeto (inserto da frase):** `"cenario": {"close": "lata", "superficie": "prateleira", "ambiente": "corredor_mercado",
  "opts": {...}}` + `"hand": "leo"`. Props: `n` (quantas cópias; keyframes contam), `desliza`, `treme`, `cai`, `mao` (0–1).
- **Biblioteca de móveis/objetos** (`lofi/moveis.py`, ~135): casa, cozinha, banheiro, comércio, hospital, escritório, oficina,
  objetos pequenos de chão (crachá, cadeado, chave, celular, poça, pegadas...), parede (janela, porta de madeira/metal/vidro/
  vaivém/aço, placa, relógio, quadro de luz...), teto e externos (árvore, poste, carro, casa, prédio, cerca, lápide, fogueira...).
  Cada objeto é desenhado em centímetros e acompanha a escala dos personagens.
- **Conferir e consertar:** `python3 -m lofi.literal series/<serie>/epNN.json` lista cada frase, o que ela cita e se o plano
  mostra. `--aplicar` abre o close do objeto no tempo exato da frase (cortando o plano em volta sem perder as animações),
  conta "duas... três" no mesmo close, põe o estado dito pelo verbo (vidro que explode sai quebrado, porta aberta, luz
  apagada, cadeado que bate treme), o horário dito no visor e o nome no crachá. O `lofi.check` mostra a nota
  ("literal: 89% das frases...") e avisa abaixo de 80% nos episódios narrados.

## Planejamento narrativo, ganchos e experimentos (`lofi/narrativa.py`, `lofi/ganchos.py`, `lofi/experimentos.py`, `lofi/validador_narrativo.py`, `lofi/protecao.py`)

**Ordem de trabalho:** plano → validação → três ganchos → cenas → validador narrativo → montagem → publicação → métricas.

- **Plano antes das cenas** (`series/<serie>/planos/epNN.json`): estado inicial (por voto do episódio anterior), objetivo, conflito,
  obstáculos e a cadeia causal, um passo por cena: `situacao`, `acontecimento`, `reacao`, `consequencia`, `decisao`, `lugar`,
  `cenario`, `dia`/`hora`, `presentes`/`entram`/`saem`, `pega`/`larga`/`usa`, `revela`, `resolve`, `ferimentos`, `narracao` e
  `transicao` (`continuacao`, `deslocamento`, `passagem_tempo`, `perspectiva`, `revelacao`, `montagem`; `passa_tempo: true` quando
  o deslocamento também pula horas). Cena com `"voto": "A"` só existe naquele caminho. Mais `virada`, `consequencias`,
  `pergunta`, `estado_final` e `ponte` (como o próximo abre em cada opção). Último episódio: `"final": true`.
  `python3 -m lofi.narrativa serie series/<serie>` valida todos os planos em cadeia, levando a memória adiante pelos dois caminhos.
  `python3 -m lofi.narrativa esqueleto <plano> A` gera o esqueleto do roteiro no formato de `epNN_roteiro.md`.
- **Memória da série** (`memoria.json`): personagens (estado, ferimentos, relações), fatos com `status` fato/suspeita/desconhecido,
  `publico_sabe` e `revelar_no_ep` (o validador recusa contar antes), mistérios, pendências com `ate_ep`, objetos, locais e o `fim` de
  cada episódio. `python3 -m lofi.narrativa fechar <plano> <voto>` grava o fim.
- **Ganchos** (`ganchos/epNN.json`): três alternativas com estratégias diferentes (lacuna de curiosidade, antecipação, incongruência,
  conflito imediato, mistério contextualizado, identificação, revelação parcial), cada uma tirada de uma cena comum a todos os
  caminhos, com duração estimada (2,4 palavras/s), notas de clareza, relevância, originalidade, continuidade e duração, explicação,
  visual e som sugeridos. Não entram: a pergunta final, frase genérica de clickbait, nem o que o próprio episódio revela.
  `escolher ... A|B|C|auto` troca só o gancho (plano, `ESCOLHIDO`/`FALA DO GANCHO`/`TEXTO` da CENA 0 e o `hook.text` do JSON);
  `gerar ... --regenerar` dá três novas sem tocar no episódio.
- **Experimentos** (`experimentos.json`): variantes, a selecionada, publicações (`publicar`, sem publicar nada de fato) e métricas
  importadas à mão (`importar` CSV/JSON: visualizações, tempo médio, retenção inicial/3 s/5 s, conclusão, replays,
  compartilhamentos, comentários, seguidores). Ausente fica `null`. `comparar` só compara variantes da mesma plataforma, exige
  ≥ 1000 visualizações e ≥ 48 h, lista as diferenças de data, duração e mudanças, e usa teste de duas proporções (p < 0,05) para
  dizer "diferença observada" (associação, não causa). `recomendar` resume só resultados reais; `"recomendacoes": false` desliga.
- **Validador narrativo** (também dentro de `tests/validar_roteiro.py` e do `lofi.check`): gancho desconectado, transição sem
  contexto, salto de tempo, personagem ausente, informação indevida, cena redundante, fala artificial, exposição, consequência
  ignorada, escolha artificial e continuidade audiovisual (luz, cenário gerado e figurino no mesmo lugar). `--corrigir` conserta
  só LIGAÇÃO, O TEMPO PASSA e a referência do gancho, linha a linha, no máximo 3 rodadas.
- **Arquivos travados** (`protegidos.json`): hashes de arquivos e linhas da bíblia que ninguém no motor pode alterar
  (`python3 -m lofi.protecao conferir series/<serie>`). Em O Último Estoque, o ep. 1 e o extra 1 são cânone travado.

## Ritmo, pronúncia, movimento e retenção
- `python3 -m lofi.ritmo roteiro epNN_roteiro.md` estima a voz cena a cena (reticências e `[pause]`/`[long pause]` contam); `medir epNN.json` grava a velocidade real em `ritmo.json`. O validador avisa abaixo de 60% de ocupação.
- `python3 -m lofi.pronuncia epNN_roteiro.md` compara os áudios de `epNN/` com a narração e lista o que conferir de ouvido; ALTA = número.
- `python3 -m lofi.movimento epNN.json` (também no `lofi.check`): parado, deslizando, andando no lugar, sentado sem assento, abraço de longe, postura ou objeto que muda entre planos.
- `python3 -m lofi.retencao importar epNN.json curva.txt tiktok` cruza a curva (`segundo,percentual`) com os planos e grava `retencao.json`; `relatorio series/<serie>` resume, e o `lofi.contexto` leva esse resumo ao próximo roteiro.

## Editor do episódio
`python3 -m lofi.editor preparar epNN.json` gera em `_editor/` a página, a prévia leve com áudio (2 quadros por segundo; só os planos alterados são refeitos), as miniaturas, os dados e uma cópia das vozes. Publique a pasta como artefato com a capacidade `artifact`: legenda, texto do celular, expressão, pose, enquadramento, tempo extra e pedido livre ficam em `edits.json`. O botão "Atualizar prévia" grava `status: previa` e "Gerar vídeo" grava `status: gerar`; depois de salvar, a página dispara a tarefa agendada "Render do editor motor-lofi" (`--tarefa trig_...` e `--url <artefato>` no `preparar`; a capacidade `mcp` declara `Claude Code Remote` com `fire_trigger`). A tarefa baixa as vozes do artefato, aplica as mudanças e publica a prévia nova ou o vídeo final. `python3 -m lofi.editor aplicar epNN.json edits.json` aplica tudo, mantém fala e som em sincronia e devolve os pedidos livres.

## Qualidade
- `python3 -m lofi.check epNN.json` → erros de estrutura e de quadro (legenda no rosto, personagem cortado, cabeça sob o contador)
  + `_revisao.png` com um quadro por plano e por legenda, para um revisor independente aprovar antes do render.
- `python3 tests/validar_roteiro.py epNN_roteiro.md [--final]` → confere gancho, 12+ cenas, mínimo 2 min, A/B, ElevenLabs.
- `tests/evals.json` → casos de teste da skill.

## Extras
- `python3 -m lofi.extras teaser epNN.json epNN.mp4` → teaser de ~15 s para Stories (gancho + 3 melhores momentos + cartela).
- `python3 -m lofi.extras pacote epNN.json epNN.mp4 [tempo]` → **entrega padrão**: corte curto (60–75 s) + capa única para TikTok e Instagram + capa do YouTube.
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
| `hat` | `beanie`, `cap`, `helmet`, `hood`, `fedora`, `cowboy`, `tophat`, `crown`, `witch`, `chef`, `headband`, `bandana_hat`, `capacete_moto` (+ `hat_color`) |
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

**Velocidade.** Em 2 núcleos, cerca de 6 a 9 s de processamento por segundo de vídeo com `--jobs 2`; closes pesam mais que planos abertos.
O cache é por plano: legenda, fala, som e pergunta entram só na chave do plano que tocam, e módulos que não desenham (`FORA_DO_CACHE`) não refazem nada.

## Loja de conveniência 24h (`lofi/scenes_loja.py`)
- `loja` — salão com o caixa à esquerda (o balcão fica na frente e tapa da cintura para baixo quem está na marca `caixa`), porta de vidro no fundo, geladeiras à direita, relógio digital e monitor na parede. Props: `relogio` ("03:00"), `vulto` (0–1, silhueta alta na porta), `reflexo` (0–1, vulto no vidro da geladeira), `flicker`, `apagado` (só as geladeiras acesas). Marcas: caixa, balcao, porta, geladeira, centro, frente.
- `deposito` — fundos com caixas, gerador e a porta de aço da câmara fria. Props: `batida` (porta tremendo), `rosto` (rosto e mãos no vidro), `cadeado`, `gerador` (LED verde/vermelho), `luz` (0 = breu). Marcas: porta_camara, frente_porta, gerador, centro, frente.
- `camara_fria` — por dentro, prateleiras de aço, gelo, névoa e lâmpada azul. Props: `flicker`, `tiras` (cortina de tiras na frente). Marcas: fundo, meio, frente.
- `cftv` — close no monitor das câmeras (CAM1 CAIXA, CAM2 CORREDOR, CAM3 BOMBAS, CAM4 CAMARA FRIA). Props: `hora` ("03:00:00"), `vulto` (nº da câmera ou lista), `duplo` (alguém atrás do caixa na CAM1), `ruido` (0–1), `cam` (uma câmera em tela cheia). Mão: `"hand": "davi"` (posições `tela`, `botao`).

## Modo redes (TikTok/Instagram) — padrão nos episódios novos
Ligado sozinho em todo episódio sem `"plano_padrao": "aberto"` (desliga com `"modo_redes": false`). O que ele faz:
- **Sem cartela de título.** Não use plano `title`: o gancho emenda direto na 1ª cena e um selo `EP X/Y` (com o nome da série)
  entra no canto direito por 3,5 s e depois fica discreto. A partir do ep. 2, `"voto": "TELHADO"` no topo do JSON mostra o carimbo
  "A MAIORIA ESCOLHEU" no alto, logo depois do gancho (com som `stamp`). O verificador pede `episode` e, do ep. 2 em diante, `voto`.
- **Gancho falado (padrão).** `"hook": {"fala": "ELES *ESCUTAM*."}`: o motor acha essa fala nas legendas, copia o mesmo trecho de voz para o 1º quadro do
  gancho (a boca de quem fala mexe sozinha; não precisa gravar de novo) e, sem `"text"`, usa a própria fala como texto grande, posto fora dos rostos.
  Também aceita `{"fala": {"voice": "lia", "src": [8.8, 10.0]}}`. Mostre em close o rosto de quem fala; o gancho dura a fala + ~0,5 s.
  O verificador avisa "gancho calado" e o validador de roteiro pede a linha `FALA DO GANCHO:`.
- **Gancho com impacto.** O texto do `hook` aparece palavra por palavra desde o 1º quadro (`"passo": 0.16` s por palavra),
  a câmera entra num "soco" de zoom que assenta em 0,4 s e o motor põe `impact` + `whoosh` no quadro 0.
- **Cortes automáticos.** Planos de 4,8 s ou mais com enquadramento automático (médio/conjunto) são divididos nas pausas da
  fala em trechos de ~2,4–3,8 s, alternando: plano base → close em quem fala → o outro enquadramento (conjunto ↔ médio).
  Não cortam: planos com `zoom`/`close`/`follow`/`vertigo`, `plano: aberto`/`close`, gancho, travelling.
  Desligar: `"camera": {"cortes": false}` no plano ou `"cortes_auto": false` no episódio.
- **Pergunta no meio.** `"pergunta": {"text": "VOCÊ ATENDERIA?"}` (opcional `t`, `dur`) mostra um cartão "COMENTA AQUI
  EMBAIXO" por 3 s no 1º plano de cena depois da metade; sem texto, usa "E VOCÊ, O QUE FARIA?". `"pergunta": false` desliga.
- **Contagem antes da escolha.** Nos 3 s antes da tela A/B: 3… 2… 1 no canto direito com "O QUE VOCÊ FARIA?" e bipes.
- **Loop.** O vídeo não escurece no fim: depois da tela A/B entra meio segundo do gancho, e o último quadro emenda no primeiro.
- **Legendas na área segura.** Faixa em y≈1330 (nunca abaixo de 1400, fora da descrição/música do TikTok), centro um pouco à
  esquerda e largura máxima de 870 px (longe da coluna de botões). A palavra-chave de cada trecho fica 20% maior e em vermelho:
  marque com `*palavra*` no texto da legenda; sem marca, o motor escolhe a palavra mais longa (6 letras ou mais).
- **Corte curto.** `python3 -m lofi.extras corte epNN.json epNN.mp4 [alvo]` gera `epNN_corte.mp4` (60–75 s): gancho, a 1ª cena,
  os planos mais fortes (sustos, closes, detalhes, falas de outros personagens), a última cena, a tela A/B e o loop. Já vem no `pacote`.

## Placar dos comentários (`"type": "placar"`) — padrão a partir do ep. 2
Plano logo depois do "Anteriormente em…": cabeçalho "PLACAR DOS COMENTÁRIOS", total de comentários, cards A/B com a porcentagem
subindo, contagem por rede, os comentários recortados dos prints pulando na tela e "VOCÊS ESCOLHERAM: ...". O carimbo "A MAIORIA
ESCOLHEU" do selo some quando há placar (não repete).
```json
{"start": 7, "end": 12.5, "type": "placar",
 "labels": {"A": "BARULHO", "B": "SILÊNCIO"}, "votes": {"A": 357, "B": 284},
 "platforms": {"TikTok": 357, "YouTube": 184, "Instagram": 100},
 "comments": [{"img": "placar/ep04_c1.png", "vote": "A"}, {"user": "fulano", "text": "B!", "vote": "B"}],
 "winner": "A", "fundo": {"scene": "carro", "rain": "fraca"}}
```
- `comments`: até 5. `img` = recorte do print (preferido; caminho relativo à pasta do roteiro; `w` muda a largura, `x`/`y`/`ang` a posição);
  sem `img`, o comentário é redesenhado com `user` e `text`. `vote` põe a etiqueta da opção no canto.
- Recortar: `python3 -m lofi.placar recortar print.jpg x0 y0 x1 y1 series/<serie>/placar/ep04_c1.png` (vários prints podem ser usados).
- **Empate** (`votes` iguais): carimbo "EMPATE!", roleta A/B que gira com tiques e para em `winner` ("DESEMPATE: ..."). Duração: 9 s.
  Sem empate: 5,5 s. Sons (`whoosh`, `notif`, `click`, `stamp`) entram sozinhos.

## Episódio extra de curiosidades (`"formato": "extra"`)
Vídeo curto (45–100 s) entre episódios, sem votação: "O que aconteceu com a Lia?", origem de algo, o outro lado de uma cena.
Arquivos `series/<serie>/extraNN_roteiro.md`, `extraNN.json` e vozes em `extraNN/` (NN = episódio depois do qual sai).
O selo mostra "EXTRA"; sem recap, placar, pergunta ou escolha; a chamada final ("A VOTAÇÃO DO EP. 3 CONTINUA ABERTA", "TEMPORADA 2?")
vai num `overlay` de texto. O validador (`tests/validar_roteiro.py`, detecta pelo nome `extra...`) pede gancho, 5+ cenas, título com
EXTRA, CHAMADA e 45–100 s; o `lofi.check` aceita a duração curta.

## Ondas de som na tela (padrão)
Todo efeito sonoro do `sfx` ganha um desenho no lugar de onde vem (`lofi/ondas.py`): `knock` = três arcos saindo da porta + "TOC",
`bang` = estrela de impacto + "BAM!", `door_close` "BLAM", `door_open` "CREC", `glass` cacos + "CRASH", `car_alarm`/`siren` arcos
pulsando, `notif`/`vibe` tremidinhas + "BZZ", `growl` linhas onduladas + "GRRR", `heartbeat` pulso vermelho nas bordas, `beep` "BIP",
`lock` "CLAC". Sem `x`/`y` no efeito, a onda sai da marca `porta` do cenário (sons de porta), do `carro` (alarme) ou do centro.
`{"t": 12, "name": "knock", "x": 690, "y": 1080}` posiciona; `"onda": false` desliga um efeito; `"ondas": false` (episódio ou plano)
desliga tudo; `"ondas": {"texto": false}` tira as onomatopeias; `{"passos": true}` liga os anéis de passos.

## Artes para as redes (`python3 -m lofi.artes dados.json saida.png`)
1080×1920, no estilo da série (personagens travados e cenários do motor). Tipos: `agenda` (maratona/agenda do dia), `aviso`
(antes de episódio pesado, com personagem em close), `meta` (meta da comunidade com baú trancado e marcos), `resultado`
(porcentagem, baú trancado/aberto, barra) e `ranking` (top 10 com empates). Campos de cada tipo nas skills `serie-agenda`,
`serie-aviso` e `serie-comunidade`; exemplos em `series/dia-zero/artes/*.json`.

## Movimento fluido (automático)
- **Passo preso ao chão:** a fase da caminhada vem da distância que o ator percorre (x/y com keyframes ou marcas), então os pés não
  escorregam; no `travelling` vem da velocidade do cenário, e na horda, da velocidade de cada zumbi. Andando sem sair do lugar, usa o tempo.
- **Ciclo novo:** coxa e joelho separados (joelho dobra só no balanço), quadril que sobe e desce duas vezes por ciclo e balança de lado,
  corpo inclinado na corrida, braço oposto à perna com o cotovelo dobrando na ida, objeto na mão com inércia (atrasa e quica).
- **Zumbis:** `zombie` manca (um passo mais demorado), arrasta uma perna, afunda no passo e balança a cabeça; `zombie_corredor` corre
  aos trancos com o corpo para a frente; de frente, os braços ficam soltos e balançam atrasados.
- **Começar e parar:** quando `walk` muda nos keyframes, o passo entra em ~0,2 s e sai em ~0,3 s (sem tranco). Agachar, sentar e pular
  descem/sobem o corpo com suavidade. Personagens são desenhados a 30 quadros por segundo (antes 15).

## Cenários vivos (automático) — `lofi/cenario_vivo.py`
- **Acabamento:** textura leve de papel no fundo de todos os cenários, teto mais escuro nos internos e sombra de contato onde a
  parede reta encontra o chão (entrada, apartamento, depósito, delegacia, loja).
- **Objetos novos:** entrada (capacho, quadro, interruptor, tênis), corredor (extintor, vaso com planta), telhado (ar-condicionado,
  respiro, varal com roupas), rua e rua_amanhecer (sacos de lixo, hidrante, cartaz no poste).
- **Vida por cenário:** mariposas nas lâmpadas, lâmpadas que falham, gotas pingando com respingo, vapor subindo (bueiro, esgoto,
  câmara fria), vaga-lumes na floresta, poeira na luz, papel voando na rua, moscas no lixo do beco, luz vermelha de antena/barreira
  piscando e pássaros no amanhecer. Configuração em `VIDA` (coordenadas do cenário).
- Desligar: `"vida": false` no plano ou no episódio; `"vida": {"vapor": false}` desliga só um efeito.

## Roteiros com contexto e fluxo (padrão)
- `python3 -m lofi.contexto series/<serie> NN` gera `_contexto_epNN.md`: regras, finais, votos, resumos, fim do episódio anterior
  (lugar, hora, inventário, últimas 3 cenas e o que cada opção prometeu), personagens, fios em aberto, mapa e marcas. Leia antes de escrever.
- O roteiro começa por `## ESCALETA` (6–10 batidas). Entrada e saída de personagens: linhas `ENTRA:` e `SAI:`.
- `tests/validar_roteiro.py` confere também o fluxo: personagem que aparece sem `ENTRA:` (ERRO), que some sem `SAI:`, fala acima de
  ~3,3 palavras/s, buraco de tempo entre cenas, gancho que não acontece e falta de ESCALETA (AVISOS).

## Intensidade dos efeitos
`"efeitos"` no topo do episódio controla névoa (`fog` do plano e do cenário), brilho (bloom), granulado, vinheta, partículas
(poeira `dust`, vapor, vaga-lumes, moscas) e o desfoque dos bonecos (fora de foco e bafo de frio):
- `"nenhum"` (padrão): tela limpa e bonecos nítidos, sem filtro nenhum. Luz, cor do lugar (`grade`), lanterna e escuro continuam.
- `"leve"`: névoa a 20%, brilho e vinheta suaves, granulado pela metade, partículas a 40% (padrão dos episódios `legado`).
- `"normal"`: como era antes.
- Ajuste fino sobre o `"nenhum"`: `{"fog": 0.3, "bloom": 0.2, "grain": 0.5, "vig": 0.7, "part": 0.5, "desfoque": 1}` (0 a 1).
Sustos (`scare`), relâmpago, chuva, gotas na lente, `tint`, `reticula` e `glitch` são do plano e não mudam.

**Lembrança** — o único lugar com visual de filme: `"lembranca": true` no plano aplica sépia, vinheta e granulado cheios
(flashback, "o que aconteceu antes", alguém se lembrando). O `recap` já sai assim; `"lembranca": false` desliga.

## Contraplano pelos pés (`"type": "pes"`)
A câmera no chão, por baixo da porta: só os pés de quem está do outro lado, com a luz do corredor vazando pela fresta e as
sombras das pernas vindo na direção da câmera.
```json
{"start": 12, "end": 14.5, "type": "pes", "x": [[0, -160], [2.2, 470]], "pes": "sapato", "luz": [210, 176, 120]}
```
- `x` (animável, px da tela em pé): quando muda, os pés andam com passo alternado e o som `step` sai sozinho; parados, mudam o peso.
- `pes`: `sapato` (gente), `descalco`, `garra` (dedos longos com unha: a criatura). `facing` 1/-1 quando parado.
- `luz` = cor do corredor; `"piscar": true` = lâmpada falhando; `handheld` (padrão 4) = tremor da câmera; `cor` = cor das pernas.
- Use alternando com o close de reação de quem está escondido, 1–2 s cada. Sem HUD; legenda normal. Na versão deitada vem do vídeo em pé.

## Selo da escolha (`"escolhida": "A" | "B"`)
No topo do episódio (do ep. 2 em diante, modo redes): um selo redondo com a letra que o público escolheu fica ao lado do selo
`EP X/Y` o episódio todo, e nos 3,5 s depois do gancho a tela ganha uma borda acesa na cor da opção (A creme, B vermelho,
as mesmas da tela de escolha). Combina com `voto` (o carimbo com a palavra).

## Contagem automática dos votos
`python3 -m lofi.votos contar series/<serie> NN print1.jpg print2_insta.jpg ... [--recortar] [--a "sinônimos"] [--b "sinônimos"]`
lê os prints (Tesseract, português), agrupa os comentários (nome → texto → rodapé "Há 7h · Responder"), relê cada texto ampliado
(pega votos de uma letra só), identifica A/B pela letra ("a", "B", "vou de A", "letra b") ou pelas palavras da opção na bíblia,
conta um voto por pessoa (somando os prints), separa por rede (nome do arquivo, `caminho:Rede` ou pelo print), ignora o criador e
os selos ("Primeiro comentário", "Fixado"). `--recortar` salva até 5 comentários em `placar/epNN_cN.png`. Sempre gera
`placar/epNN_conferencia.png` para conferir (verde = A, laranja = B, cinza = não contou) e imprime o plano `placar`.
Comentário com A e B ao mesmo tempo fica como dúvida e não conta.

## Poses sentadas
**Moto:** `"pose": "sit", "assento": "moto"` senta o personagem numa moto (de lado, com rodas girando quando há `walk`/`run` ou `travelling`; de frente/costas, versão estreita). Combine com `"travelling"` para pilotar. Guarda-roupa: chapéu `capacete_moto` e `"bag_termica": true` (a `backpack` vira a mochila cúbica de entregador).
`"pose": "sit"` senta num banco desenhado junto (`"assento": "banco"` padrão, `"caixa"`, `"cadeira"` ou `"nenhum"` quando o cenário
já tem onde sentar); de frente, as coxas vêm na direção da câmera e os joelhos aparecem. `"pose": "chao"` = sentado no chão com as
pernas esticadas (a marca `chao_porta` usa essa). Sentado nunca anda, mesmo com `walk` ligado.

## Pensamento e plano (lofi/mente.py)
**Pensamento** — o que o personagem lembra, imagina ou teme, num balão de pensamento:
`{"type": "pensamento", "quem": "lia", "emotion": "sad", "estilo": "memoria" | "imaginacao" | "medo", "texto": "E SE...?" (opcional),
"fundo": {...cena atual, fica escura e desfocada...}, "cena": {...plano de cena normal dentro do balão: scene, actors, props...}}`.
O personagem fica em close embaixo, as bolinhas sobem da cabeça e o balão cresce em 0,4 s. Lembrança = sépia; imaginação = azulada;
medo = vermelha e tremendo (com batimento). O balão se centraliza em quem está dentro dele, e quem está na lembrança não mexe a boca.
Rótulo no canto do balão (LEMBRANÇA / E SE... / MEDO; `"rotulo": false` tira). Som `whoosh` automático; legenda sobe para 1440.

**Plano** — a estratégia desenhada à mão:
`{"type": "plano", "titulo": "O PLANO", "fundo": "papel" | "quadro" | "mapa", "lugares": [{"id", "nome", "x", "y", "icone"}],
"setas": [{"de", "para", "t", "dur", "cor", "tracejado"}], "passos": [{"t", "texto"}], "fichas": [{"char", "caminho": [ids], "t": [t0, t1], "dx"}],
"perigos": [{"x", "y", "t", "texto"}]}` (tempos relativos ao plano). Ícones: casa, predio, hospital, loja, ponte, carro, porta,
estrela, caveira, radio. As setas se desenham, os passos entram numerados, as cabecinhas dos personagens andam pelo caminho e cada
perigo ganha um X vermelho (com `click`/`impact` automáticos). Sem contador na tela.

No roteiro: `PENSAMENTO: \`lia\` · lembrança · no balão: ...` ou `O PLANO: passos ... · setas ... · perigos ...` (a cena não muda o
lugar de ninguém). O validador avisa se o episódio não tiver nenhuma das duas.

## Chamada para seguir na escolha
A tela de escolha A/B mostra no alto (abaixo da área dos botões das redes) o selo "SIGA PARA ACOMPANHAR AS HISTÓRIAS", que entra
0,5 s depois do começo da escolha e fica até o fim. Troque o texto com `"seguir": "..."` no plano `choice` ou no topo do episódio;
`"seguir": false` tira.

## Pausa para seguir (padrão, antes da escolha)
Plano `{"start": 110, "end": 113, "type": "pausa"}` logo antes da escolha: congela o último quadro do plano anterior, escurece, mostra o
sinal de pausa e "SIGA PARA NÃO PERDER O PRÓXIMO EPISÓDIO", com impacto e batimento. A contagem 3, 2, 1 corre por cima. Troque a frase com
`"texto": "LINHA 1\nLINHA 2"`. O verificador avisa quando falta. Não muda o som da fala: nenhum clipe pode cair dentro da pausa.

## Capa única
`python3 -m lofi.capas epNN.json --unica` gera `epNN_capa.png` (1080×1920), a mesma imagem para TikTok e Instagram: o texto fica no recorte
4:5 do Instagram, acima da descrição do TikTok e fora da coluna de botões. `pacote` já entrega essa capa e a do YouTube.

## Formato 100% narrado
`"narrado": true` no topo do episódio: só o narrador fala (uma voz, ex.: `"voices": {"narrador": "ep03/narrador.mp3"}`); ninguém mexe
a boca nem faz gesto de fala (um ator pode ligar com `"lipsync": true`, ex.: uma TV), e a voz sai limpa, sem o eco do lugar (rádio
continua com `"radio": true`). O `lofi.check` recusa mais de uma voz. No roteiro, a linha `Formato: 100% narrado (...)` da bíblia
(ou do cabeçalho) liga as regras do validador: fala de personagem é ERRO, toda cena tem NARRAÇÃO, até ~2,6 palavras/s, ElevenLabs
com um bloco só. O dossiê de contexto (`lofi.contexto`) ganha a seção "FORMATO 100% NARRADO".

## Estilo visual: lofi ou vetor
`"style"` no topo do episódio: `"desenho"` (lo-fi com traço de nanquim e papel), ausente (lo-fi liso) ou `"vetor"`.
No vetor os personagens não têm contorno; cada parte do corpo ganha uma faixa de sombra do lado oposto à luz e um brilho fino do
lado da luz (borda dura, sem degradê); camisas, uniformes e jalecos ganham bolsos com lapela e botões, calças ganham cinto com fivela,
as mãos ganham polegar e as mangas ficam um tom mais escuras que o tronco. Traços do rosto (sobrancelhas) continuam. As fichas de
`personagens.json` valem igual nos dois estilos. A bíblia registra na linha `Estilo: lofi-desenho | lofi-liso | vetor`.

## Boca pelo Rhubarb (padrão)
A boca segue a voz com o [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync) (`lofi/rhubarb.py`, modo fonético, funciona em português). Na primeira vez o motor baixa o Rhubarb do GitHub (~90 MB, em `~/.cache/motor-lofi`); o resultado de cada voz fica em `_cache/rhubarb_*.json`.
Formatos de boca: repouso, M/B/P (lábios fechados), dentes (S/T/I), aberta (E), bem aberta (A), redonda (O), biquinho (U), F/V (dente no lábio) e L (língua).
`"boca": "espectro"` no episódio volta ao cálculo antigo; sem internet ou sem o Rhubarb, o motor usa o antigo sozinho. Teste: `python3 -m lofi.rhubarb voz.mp3`.

## Biblioteca de poses (`lofi/poses.json`)
No estilo do OpenMontage: a arte é do rig e as poses moram num arquivo de dados. Cada pose diz para onde vai cada mão (alvos: queixo, boca, olhos, rosto, testa, topo, nuca, ouvido, peito, coracao, barriga, cintura, ombro_oposto, juntas, frente, frente_baixo, lado, lado_baixo, lado_alto, acima) e o braço é calculado sozinho (IK de dois ossos), em todas as vistas.
Poses: pensativo, desespero, mao_na_boca, silencio, ouvir, cocar_nuca, cocar_cabeca, maos_na_cintura, dar_de_ombros, pedir_calma, chamar, acenar, comemorar, proteger_rosto, abracar_se, implorar, explicar, apontar_cima, punho, segurar_barriga, espiar_longe. Use como qualquer pose: `"pose": "pensativo"` ou `[[0, "idle"], [2, "desespero"]]`.
**Gestos pela fala (automático):** com o ator parado em `idle`, frases da legenda disparam a pose da biblioteca (campo `palavras`: "calma" → pedir_calma, "não sei" → dar_de_ombros, "por favor" → implorar, "shh" → silencio...), com entrada suave e emoção sugerida; a pose dura até ~1,4 s depois da palavra. Uma pose escrita no JSON sempre vence.
Pose nova: acrescente uma entrada em `poses.json` (`maos`, `dx`/`dy`, `cotovelo`, `anim`, `frente`, `dedo`, `cabeca`, `gesto`, `emocao`, `palavras`) e rode `python3 -m lofi.catalogo --md CATALOGO.md`.

## Tamanho dos personagens
Os personagens saem 18% maiores em relação ao cenário (`"escala_personagens": 1.18`, padrão; `1.0` = tamanho antigo; episódios `"legado"` ficam como eram). No plano **conjunto** o maior personagem ocupa ~60% da altura e quem está mais ao fundo não afasta mais a câmera. A legenda procura um vão entre as cabeças quando elas estão em alturas diferentes.
Roupas: de lado, sobretudo e jaleco viram um painel fechado (sem a abertura da frente), gravata, lapela, colar e estetoscópio somem, o distintivo vai para o peito e a ponta do cachecol cai na frente; sentado, a barra do casaco fica no colo; o cachecol é desenhado antes dos braços (mão no queixo passa por cima dele).

## Versão deitada para o YouTube (16:9)
`python3 -m lofi.render epNN.json --deitado --jobs 2` → `epNN_youtube.mp4` (1920×1080), depois do vídeo em pé (ele é usado nas telas de texto).
- Os cenários são desenhados com 420 px a mais de cada lado (o mundo de projeto continua 1080×1920; `core.XO`); o que muda no
  quadro (TV, luzes, portas, vida do cenário) vem do centro e as laterais acompanham a luz geral.
- A câmera recorta uma janela 16:9: aberto mostra a faixa do chão e das cabeças (`camera.cy` força outra altura), médio,
  conjunto e close usam as mesmas regras com a tela larga. Legenda embaixo no centro (em cima, se cobrir um rosto),
  contador menor no canto, selo e cartões no alto.
- Telas de texto e planos de detalhe (placar, recap, escolha, pensamento, plano, detalhe, título) vêm do vídeo em pé, no centro,
  com o próprio quadro desfocado nas laterais.
- Cache próprio em `_cache_deitado/`. Teste quadros com `--deitado --test 5 12.5`.

## Capas (`lofi/capas.py`)
`python3 -m lofi.capas epNN.json` → `epNN_capa_tiktok.png`, `epNN_capa_instagram.png` (1080×1920) e `epNN_capa_youtube.png` (1280×720);
o `pacote` já gera as três (e o corte curto; o teaser saiu da entrega padrão). Protagonista = quem mais fala, desenhado grande com
contorno branco; ameaça = zumbi/criatura que mais aparece, escura com brilho vermelho atrás; fundo = cenário do gancho (sem pessoas),
desfocado na cor do episódio; frase = texto do gancho. Ajustes: `"capa": {"quem", "emocao", "pose", "vista", "frase", "ameaca": false, "tempo"}`.

## Roteiro com camadas (padrão)
3 a 5 min, 18+ cenas, ESCALETA de 10–14 batidas em ATO 1/2/3 com VIRADA DO MEIO, `## SUBTRAMA` marcada em 2+ cenas (`SUBTRAMA:`),
`CONFLITO:`, `SEQUÊNCIA:` de ação de 30 s+, 2+ PENSAMENTO/O PLANO e 4+ lugares. O validador avisa o que faltar (COMPLEXIDADE);
`Complexidade: simples` na bíblia (ou `--simples`) desliga.

## Modo DESENHO: cenas feitas de imagens prontas (visual-asset-library v5)
Opcional, por episódio: `"visual_mode": "DESENHO"` + `"image_scene"` no plano troca o desenho por código daquele plano por imagens
PNG em camadas (fundo, personagem recortado, objetos), com câmera (zoom/pan), respiração, balanço, flicker, névoa e vinheta.
Não confundir com `"style": "desenho"` (o lo-fi com traço de nanquim). Planos sem `image_scene` continuam iguais.
Módulos: `visual_assets` (biblioteca de imagens com busca e prompts das que faltam), `visual_compositor`, `image_scene_animator`,
`character_motion` e `facial_timeline` (rosto em sprites: olhos, boca por cues do Rhubarb, expressões por tempo), `auto_rig` e
`advanced_rig` (pontos do esqueleto por silhueta ou MediaPipe opcional; deformação por triângulos, não ARAP), `lipsync_pipeline`,
`storyboard_planner`, `episode_export` (exporta só cenas DESENHO, sem legendas nem mixagem do motor) e `drawing_mode` (a ponte com
`Episode.scene_frame`). Funciona em pé e deitado. Documentação completa e limites em `docs/desenho/`; skill em `skills/motor-lofi-desenho/`.

## Estilo "imagens" (imagens geradas no ChatGPT) — `lofi/imagens.py`
Bíblia: `Estilo: imagens` e `Prompt de estilo: ...`; fichas com `"aparencia"`. Roteiro: linha `IMAGENS:` em cada cena
(fundo `lugar` · `<personagem>_<vista>_<emoção>[_<pose>]` · `obj_<nome>`). `python3 -m lofi.imagens prompts epNN_roteiro.md` →
`epNN_imagens.md` só com as imagens que faltam em `series/<serie>/imagens/`; `referencias <serie>` → fichas de referência (frente, 3/4 e costas) no modelo padrão `MODELO_REFERENCIA`, com os campos `ref_personagem`, `ref_roupa` e, se preciso, `ref_negativo`, sempre com o `MASTER_STYLE`; `folhas <serie>` → `imagens_folhas.md`, com o elenco inteiro em 4 folhas (cada personagem numa linha, 8 posições);
`importar <serie> arquivo.png nome` tira fundo liso e sobras; `faltam epNN.json` confere.
Plano: `"imagens": {"fundo", "personagens": [{"img", "pos": "esq|centro|dir|0–1", "altura", "fala": voz, "espelhar", "chao"}],
"objetos": [{"img", "x", "y", "altura"}], "plano": "aberto|medio|close", "alvo", "aproximar", "fundo_y", "efeitos": ["flicker", "escuro"]}`.
Quem tem `fala` balança com a voz; todos respiram; a câmera aproxima devagar e balança de leve com paralaxe (fundo 0,3 ·
personagens 1 · `frente` 1,4). Recursos vindos do addon "motor-lofi-v4": piscar (`<img>_piscando.png` troca por 0,12 s a cada ~3,6 s;
`"piscar": "<outro nome>"` ou `false`), `"andar": ["esq", "dir"]` (atravessa a cena com passo), objetos `"flutuar"`/`"pulsar"`,
camada `"frente"` (primeiro plano) e **barras de recurso** no contador (vale para qualquer estilo):
`"hud": {..., "barras": [{"label": "BATERIA DO RÁDIO", "value": [[0, 0.6], [90, 0.1]], "color": [110, 180, 230]}]}` (abaixo de 25% pisca em vermelho). Funciona em pé e deitado, com legendas, HUD,
gancho falado, placar e escolha do motor. O `lofi.check` acusa imagem faltando. As imagens de `series/<serie>/imagens/` vão para o repositório (commit) para serem reaproveitadas nos próximos episódios.

## Portais e caçadores (`lofi/scenes_fenda.py`)
Cenários `fenda` (props `aberta`, `cor`, `pulso`), `masmorra` (`portal`, `cor`, `luz`), `associacao` (`rank`: "E"…"S" ou "0", `erro`) e `trono` (`olhos`, `ocupado`, `cor`). Marcas no `CATALOGO.md`. Objeto na mão novo: `"prop": "adaga"`.
