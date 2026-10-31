# Motor lo-fi · formato do roteiro (episodio.json)

Rodar: `python3 -m lofi.render episodio.json` (teste de quadros: `--test 3 12.5`).
Transcrever vozes: `python3 -m lofi.transcribe roberta.mp3 rafa.mp3` → mostra cada frase com tempo.
Dependências: `pip install --break-system-packages pillow numpy scipy soundfile sherpa-onnx` + ffmpeg.

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
- **Cenários:** apartamento (props: tv), entrada (door 0–1, locks 0–2, dark, under_door_light, feet), corredor (flicker),
  rua, janela (vista de cima), escada (luz de emergência), telhado, ponte, radio (on, level: "auto" = segue a voz).
- **Personagens prontos:** roberta, rafa, lia, valter, zombie, soldado. Novos via `characters`
  (campos: skin, top, top_style [puffer|hoodie|shirt|torn|scrubs|uniform], legs, shoes, hat [beanie|cap|helmet|hood],
  hair [ponytail|bun|short|long], hair_color, scarf, backpack, glasses, infected, scale).
- **Vistas:** front, back, side (+ facing 1/-1). **Poses:** idle, point, reach, pull, knock, phone, hold, scared, hands_up,
  wave, cross, forward, sit, crouch. **Emoções:** neutral, fear, shock, angry, sad, determined, happy, suspicious.
- **Transições:** cut, whip, flash, fade, zoom, glitch, dip. **Efeitos:** peephole, shake, lightning.
- **Sons:** beep, stamp, whoosh, step, shuffle, echo_step, door_open, door_close, lock, bang, knock, glass, impact, thunder,
  no_service, notif, vibe, click, growl, car_alarm, siren, heartbeat(dur), breath(dur), static(dur), crowd(dur).
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
Render: ~10 s de processamento por segundo de vídeo.

## Episódios longos (2–3 min)
- Render em paralelo: `python3 -m lofi.render episodio.json --jobs 2` (≈7 s de processamento por segundo de vídeo; rode em segundo plano).
- Compressão: `"crf": 28` (padrão) deixa ~60–80 MB para 3 min. Use 30 se precisar de arquivo menor.

## Pasta da série (continuidade sem copiar e colar)
Cada série vive dentro do zip em `series/<nome-da-serie>/`:
- `biblia.md` — mapa da série, fichas dos personagens (campos do motor), cenários, regras, tabela de episódios
  (nº, status: planejado/roteiro/montado, pergunta A/B, voto vencedor) e os resumos de cada episódio.
- `epNN_roteiro.md` — roteiro completo do episódio NN (cenas, narração limpa, sons).
- `epNN.json` — roteiro técnico usado na montagem.
Os comandos leem e atualizam esses arquivos e devolvem o zip atualizado.
