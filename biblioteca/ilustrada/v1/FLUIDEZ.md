# Fluidez e revisão por cena

O fluxo ilustrado tem quatro recursos integrados: passada por distância,
atuação preparada a partir da voz, camadas de cenário e revisão curta com áudio.
Os desenhos existentes são preservados. Nenhuma dessas funções cria desenhos
intermediários ou substitui a revisão visual da anatomia.

## Passada, apoios e transições

`deslocamento_corpo_ciclo` mede o avanço de um ciclo completo em alturas do corpo.
O motor integra a trajetória de `pos`/`chao`, a altura em perspectiva e a distância
do travelling. Assim, acelerar, frear ou mudar o trajeto muda a cadência dos
desenhos. Quando o trajeto para, a fase para. `sincronizar_passada: false` permite
um ciclo intencionalmente no lugar. O resultado é determinístico ao buscar um
instante ou renderizar quadros fora de ordem.

Para travar a sola durante o contato, o ciclo precisa de `contatos_solo` e um
marco normalizado em cada desenho. A trava é automática em ciclos calibrados com
deslocamento; `travar_apoios: false` permite desligá-la, e `true` exige os marcos.
Exemplo de metadados no ciclo:

```json
{"contatos_solo":[{"inicio":0.125,"fim":0.625,"marco":"pe_solo"},
                   {"inicio":0.625,"fim":1.125,"marco":"pe_solo"}]}
```

Os números são frações do ciclo; `fim` pode ultrapassar 1 para um contato que
cruza a emenda. O renderer compensa apenas a raiz do desenho, sem esticar membros.
O marco fica preso no mundo mesmo com espelhamento. O voo fica livre de trava.
Se a correção ultrapassar `limite_correcao_apoio` (padrão 0.08 altura de tela), o
motor pede recalibração em vez de deformar o corpo. Use a trava somente em ciclos
de locomoção calibrados. A primeira referência conferida está em
`imagens/lucas/hd/andar_apoios_v2.json`, usada pela ficha do Lucas e pela demo;
o arquivo anterior permanece.
Os outros ciclos continuam disponíveis e a auditoria informa os marcos ausentes.
Novas criações do padrão precisam dessa calibração em andar e correr.

As ligações em `transicoes` aceitam `fase_origem` e `fase_destino` entre 0 e 1.
Quando a ponte informa seu período de origem, o ciclo anterior termina na fase
calibrada mesmo sob velocidade variável. O ciclo seguinte começa na fase de
destino. A ponte continua sendo uma sequência desenhada, sem dissolver corpos.
Mudanças de anatomia ou apoio entre ponte e ciclo requerem conferência visual.

## Voz antes da atuação

Escreva `falas` com o arquivo de voz e `audio_final: true` quando aquela gravação
for a referência final. Depois prepare uma cópia da história:

```bash
python -m lofi.atuacao_voz historia.json --saida historia_atuacao.json
python -m lofi.historias_ilustradas compilar historia_atuacao.json producoes/minha-historia
```

O preparo lê o recorte real de cada áudio, registra hash/duração e detecta janelas
de voz e pausas. Gestos usam essas janelas, a boca fecha nas pausas e piscadas
compatíveis podem ocorrer nelas. Bocas/cues revisados existentes são conservados;
na ausência deles, os visemas são estimados acusticamente, sem promessa de
alinhamento fonético exato. Olhares e gestos visíveis dependem das variantes e
puppets calibrados para aquela pose; não se inventa um rosto para um ciclo sem boca.

Trocar o arquivo ou seu recorte depois do preparo invalida a sincronização na
compilação, revisão e render. Prepare novamente para atualizar a atuação.
`--previa` permite vozes temporárias, identificadas como teste no relatório;
não certifica essas gravações para a etapa final. Falas sem áudio não recebem
gestos fabricados por uma duração estimada. Narração em off continua sem boca.

## Cenários em camadas

Uma cena ou entrada do catálogo pode ter `camadas_cenario`. Cada camada usa
`id`, `tipo` (`imagem`, `nevoa`, `luz`), `plano` (`fundo`, `frente`),
`profundidade` e `opacidade`. A profundidade controla paralaxe no balanço e
travelling; a ordem determina se o ator fica na frente ou atrás da camada.
As sombras continuam entre o fundo e os corpos.
O cenário `floresta` já registra essas camadas no catálogo.

```json
{"camadas_cenario":[
  {"id":"bruma","tipo":"nevoa","plano":"fundo","faixa":[0.5,1],
   "opacidade":0.15,"velocidade":0.03,"profundidade":0.4},
  {"id":"arvore","tipo":"imagem","img":"objetos/arvore_v2","plano":"frente",
   "x":1.5,"y":0.5,"altura":1.05,"profundidade":1.4},
  {"id":"luar","tipo":"luz","plano":"fundo","cor":[150,185,220],
   "opacidade":0.12,"raio":[0.4,0.45],"pulsar":0.08}
]}
```

Névoa e luz são overlays animados independentes e determinísticos; o fundo opaco
mantém sua pintura original. A luz adicional é um halo visual: a projeção das
sombras dos atores continua vindo de `iluminacao`, que deve ser calibrada de forma
coerente. Separar uma árvore que já esteja pintada no fundo exige arte própria;
o motor não segmenta automaticamente uma imagem única em planos 3D.

## Revisar antes do vídeo completo

```bash
python -m lofi.revisao_cenas episodio.json --saida producoes/revisoes/meu-teste --cenas 1 2 --max-segundos 8
```

A pasta nova contém um MP4 por cena, a faixa seca de voz usada, folhas de quadros,
`index.html` com players e `relatorio.json`. O comando conserva os tempos do
episódio ao extrair o áudio e renderiza pelo compositor real. O relatório reúne
apoios calibrados/ausentes, contatos, enquadramento, sombras, continuidade e voz
final/temporária. Clipes limitados são marcados como parciais. `ok_tecnico` não é
aprovação visual; assista aos pés, mãos, cortes e atuação antes da exportação.

As prévias usam voz seca; música, ambiente e efeitos precisam ser conferidos
novamente na mixagem completa. A resolução de prévia também não certifica nitidez
em 1080p: rode a análise visual com a resolução de entrega.

Demonstração reproduzível:

```bash
python tools/preview_fluidez.py
python -m lofi.revisao_cenas biblioteca/ilustrada/v1/fluidez_demo_v1.json --saida producoes/revisoes/nova-previa --largura 270
```

O exemplo usa a caminhada calibrada do Lucas, planos independentes da floresta
e a voz de teste existente. São duas cenas de quatro segundos. Não é um novo
episódio de Visto Amanhã nem uma gravação final.

[Abrir prévias e relatório gerados](../../../producoes/revisoes/fluidez-v2/index.html).
