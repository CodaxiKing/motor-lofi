# Interação, ligações de movimento e câmera narrativa

Os cinco personagens têm 32 desenhos completos novos por pessoa/criatura:
oito para começar a andar, oito para acelerar, oito para frear e oito para
alcançar um objeto. Os originais e os atlas importados ficam nas pastas
individuais. Prompts do imagegen integrado em `ligacoes_prompt_<id>_v1.txt`.

## 1. Pontos de contato e objetos

`mapa_composicao.interacoes` ou `pontos_interacao` nomeiam pontos normalizados
do PNG do cenário. Cada desenho de interação tem marcos calibrados na mão,
palma e rosto. Um ator aceita:

```json
{"interacoes": [{"alvo":"macaneta", "marco":"palma_d", "inicio":0,
  "fim":3, "modo":"posicionar"}]}
```

Use junto do ciclo `interagir`, em `uma_vez`. `posicionar` bloqueia a raiz
pela posição da mão no desenho final: o braço desenhado alcança o objeto
enquanto a escala permanece constante. Escolha a zona/profundidade antes e
termine o trajeto de aproximação nesse bloqueio para evitar um salto de posição.
O centro da palma serve para segurar; `mao_d` marca a ponta da mão.

`modo: "contato"` trava o marco atual e mantém a linha dos pés. Se a altura
do alvo e a do chão forem incompatíveis, o motor pede ajuste da pose/bloqueio;
não estica o braço nem faz o personagem flutuar. O contato é geométrico sobre
desenhos completos, sem simulação de dedos ou abertura automática da porta.

`seguir_piso` escolhe uma linha em `mapa_composicao.pisos`, com pontos `[x,y]`
do cenário. A altura do chão interpola linearmente com a posição do ator.
Isso acompanha um piso inclinado em 2D; escadas precisam de poses específicas.

Objetos em `oclusores` são pintados por profundidade junto com os atores:

```json
{"oclusores":[{"objeto":"armario_baixo","x":0.54,"y":0.735,"altura":0.25,"chao":0.86}]}
```

Esse é o formato da história. O compilador resolve `objeto` para o PNG;
no JSON de renderização use `img`. `chao` define a base do objeto e `y`
seu centro. O ator fica atrás quando seu chão está mais distante e à frente
quando atravessa a base do objeto. `frente` continua sendo oclusão fixa.

## 2. Transições com desenhos reais

Use `movimentos` em vez de agendar manualmente os ciclos:

```json
{"movimentos":[
  {"acao":"parado","inicio":0,"fim":1},
  {"acao":"andar","inicio":1,"fim":3},
  {"acao":"correr","inicio":3,"fim":5},
  {"acao":"parado","inicio":5,"fim":7}
]}
```

A ficha individual registra `transicoes`. A ligação ocupa os primeiros 0,5 s
do novo estado, sem aumentar a duração nem sobrepor corpos. Depois começa o
ciclo normal. A fase do ciclo anterior é ajustada à saída quando há cadência
calibrada. A parada de caminhada reaproveita os desenhos de início na ordem
inversa; a freada de corrida tem desenhos próprios.

Não combine `movimentos` e `animacoes_quadros` no mesmo ator. As ligações
inexistentes ou intervalos curtos demais geram erro, em vez de uma dissolução
entre duas silhuetas. A velocidade do trajeto ainda deve corresponder à passada;
o modo travelling pode controlar a fase pela distância percorrida.

## 5. Câmera por batidas do roteiro

Uma cena pode declarar `batidas`, em segundos locais:

```json
{"batidas":[
  {"tipo":"acao","inicio":0,"fim":2},
  {"tipo":"fala","alvo":"lucas","inicio":2,"fim":4},
  {"tipo":"reacao","alvo":"teo","inicio":4,"fim":5.5},
  {"tipo":"pre_susto","inicio":5.5,"fim":7},
  {"tipo":"susto","inicio":7,"fim":8}
]}
```

Ação/interação: inteiro. Fala: cintura. Reação/descoberta: close.
Preparação do susto: conjunto. Susto: aberto para conservar a coreografia
própria. O planejador usa informações declaradas, não palavras-chave da narração.
Batidas sobrepostas têm prioridade explícita; segmentos iguais são unidos.
Batidas menores que 0,35 s são rejeitadas. Revise a cadência dos cortes.

Sem batidas, falas com tempos conhecidos podem gerar planos médios no falante;
revelações estruturadas podem terminar em close. Uma câmera explícita continua
valendo quando não há batidas. `direcao_narrativa: false` desativa o planejamento.
O resultado é `camera_ilustrada.cortes`, com motivo e alvos auditáveis.
Os cortes usam seu relógio local para aproximação, sem reiniciar movimento,
interação, fala ou sombra dos atores. Closes seguem o rosto calibrado do desenho.

Prévia integrada: `interacao_direcao_preview_v1.mp4`, sem áudio, com passagem
atrás/à frente do móvel, início/aceleração/freada, mão na maçaneta, câmera de
reação e preparação para o jumpscare. A resolução dos desenhos de ciclo limita
o detalhe de closes; para publicação, prefira poses/retratos de alta definição.
