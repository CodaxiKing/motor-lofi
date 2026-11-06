# Diálogos e animação ilustrada

O motor mantém narração, recortes, puppet e rig original disponíveis. As seis
melhorias abaixo foram integradas ao mesmo renderer.

## 1. Falas por personagem

Cada cena aceita `falas`. Narração é opcional quando há diálogo:

```json
{"personagem":"lucas","texto":"Por que você demorou?",
 "inicio":0.8,"audio":"audio/lucas.wav","intencao":"perguntar"}
```

`inicio` é relativo à cena. `src: [início,fim]` permite usar parte do arquivo.
O compilador considera a duração real do áudio ao distribuir as cenas; não
acelera a voz para fazê-la caber. Episódios continuam com mínimo de 90 segundos.
As demonstrações curtas da biblioteca são testes técnicos.

Na CLI `compilar` e em `tools/studio.py planejar`, caminhos de áudio são relativos
ao arquivo de história. Na API use `pasta_audio`. O resultado registra `voices`,
`clips`, legendas e `dialogue_events`, compatíveis com `lofi.render`.
Sem gravação, a fala fica pendente. `personagem: "narrador"` não move bocas em cena.

## 2. Boca local sincronizada

Lucas e Téo têm formatos M, A, E, O e U no atlas `lucas/bocas_atlas_v1.png`,
calibrados para a pose neutra em `personagem.json.bocas_locais`. Somente a região
da boca muda, antes do puppet e do espelhamento. Repouso usa a boca original.
Olhos, corpo, âncora e altura permanecem estáveis.

O áudio seco de cada fala comanda somente seu personagem; música, ambiente,
eco e falas dos outros não o fazem falar. Há dois caminhos:

```powershell
python -m lofi.sincronia voz.wav cues.json --backend espectro
python -m lofi.sincronia voz.wav cues-rhubarb.json --backend rhubarb
```

O primeiro é local e **aproximado**, sem reconhecimento fonético preciso.
O segundo exige Rhubarb instalado separadamente e não baixa programas.
A fala aceita `mouth_cues_file: "cues.json"` ou `mouth_cues` inline.
As marcações são relativas ao começo da fala, já recortadas conforme `src`.
`cue_format` distingue nossos visemas das letras de Rhubarb. As marcações podem
ser revisadas manualmente. Fora da fala, a boca fica em repouso.

## 3. Atuação e reação

Intenções: `perguntar`, `afirmar`, `negar`, `alertar`, `esconder`, `provocar`.
O compilador acrescenta gestos pequenos ao falante e reação de escuta aos
outros, com atraso. O puppet modifica pins locais; as peças usam ângulos.
Cada pose precisa de seu rig correspondente.

## 4. Preparação e acomodação

Os gestos têm preparação e retorno suaves. `acoes` aceita início/fim, tipo e
keyframes de ângulos. Isso não transforma dois PNGs diferentes em um giro 3D;
ações grandes usam sequências de desenhos completos.

## 5. Movimentos completos

Os atlas de membros separados foram removidos da biblioteca a pedido do autor.
Use os ciclos completos descritos em `QUADROS.md` e `EXPANSAO.md`.
O código genérico de rig permanece para compatibilidade, sem assets de peças
do elenco. As demos que usavam peças agora referenciam quadros completos.

## 6. Auditoria de continuidade

```powershell
python -m lofi.continuidade_animacao episodio.json --out revisao.json
```

A geração ilustrada já executa a auditoria e inclui os achados na qualidade:
saltos de posição, mudanças bruscas de escala, apoio dos pés do rig articulado,
boca aberta durante silêncio, falta de boca calibrada, falas sem áudio e
fechamento quando `seamless_loop: true`. A análise é amostrada, com inspeção
adicional no centro das marcações de boca. `corte_intencional: true` permite
cortes deliberados. Assista ao vídeo para conferir contato, perspectiva e oclusão.

## Demonstrações

- `dialogos_animacao_preview_v1.mp4`: dois falantes, boca local e gestos por pins.

A prévia de diálogos tem áudio. As vozes são trechos de `examples/rafa.mp3` e `examples/roberta.mp3`,
**apenas para teste**, e não definem as vozes finais do elenco. Os JSONs guardam
falas e tempos. Prompts em `animacao6_prompt_*.txt`; áudios derivados em `audio/`.
