# Câmera para a biblioteca ilustrada

O modelo usa a linguagem de câmera do Motor Lo-Fi (`plano`, `alvo`, `push`,
`follow`, `close`, `close_in`, `zoom` e `zoom_k`), adaptada aos PNGs, às alturas
físicas e aos ciclos completos. O mapa primeiro posiciona o elenco no cenário;
a câmera depois transforma cenário, personagens, objetos e máscaras juntos.
Ela não muda a altura física nem reduz cada personagem de forma independente.

## Planos

| Plano | Uso |
| --- | --- |
| `aberto` | Ambiente sem aproximação automática |
| `conjunto` | Elenco selecionado inteiro, com espaço para cabeças e pés |
| `inteiro` / `corpo_inteiro` | Corpo completo do alvo ou grupo selecionado |
| `americano` | Cabeça até a região dos joelhos |
| `medio` / `cintura_para_cima` | Cabeça até a cintura |
| `close` | Rosto e ombros |
| `detalhe` | Região do rosto, com recorte deliberado |
| `auto` | Um personagem parado: médio; movimento amplo: inteiro; grupo: conjunto |

O plano médio foi adaptado para cintura, em vez do corte perto dos joelhos
do rig original. Braços/pernas podem sair do quadro nos planos fechados;
no corpo inteiro o cálculo reserva as poses de todo o ciclo. O modo automático
conserva a decisão durante o plano para não mudar de zoom quando uma ação começa.
Grupos muito largos podem exigir um plano mais aberto para manter os rostos.

## Na história

```json
{
  "cenario": "entrada",
  "camera": {"angulo": "esquerda", "plano": "medio", "alvo": "lucas", "push": 0.4}
}
```

Acrescente os campos normais de ação, personagens e narração/falas da cena.
`alvo` aceita ID, índice ou lista. O compilador resolve índices antes da
ordenação por profundidade. Para diálogo, escolha médio no falante e close
na reação; para corrida, esconderijo e passagem pela porta, prefira inteiro.

O formato anterior `camera: "esquerda"` continua escolhendo o ângulo do cenário.
Também é possível usar `enquadramento: "cintura_para_cima"` junto desse formato.
Sem indicação, a história compilada usa `auto`. O campo antigo `plano` da cena
continua sendo aceito. O ângulo muda a imagem do cenário; o plano muda o recorte.

## No JSON de renderização

```json
{"imagens": {
  "camera_ilustrada": {"plano": "close", "alvo": "clara", "entrada_s": 0.3, "push": 0.3}
}}
```

Use junto da configuração normal de fundo e atores. Um objeto `camera` no
nível do shot também é aceito. `follow` escolhe o ator acompanhado;
`close` escolhe o ator do close, e `close_in` equivale a `entrada_s` nesse caso.
`seguir: false` mantém o foco na posição inicial do personagem.

`zoom` define zoom manual, com `cx`/`cy` normalizados; aceita número, par
início/fim ou keyframes em segundos locais. `zoom_k` multiplica o enquadramento
calculado. Zoom manual e multiplicadores podem provocar cortes intencionais.
O zoom nunca mostra área vazia fora do cenário. `zoom_max` limita a aproximação.
`push` faz a aproximação lenta de 3,5% usada pelo motor; no inteiro é limitado
para preservar cabeça e pés. Os demais efeitos do rig original não são
automaticamente transferidos para PNGs.

## Calibração e continuidade

Cada `personagem.json` guarda `marcos_camera`: cintura, joelhos, ombros,
centro do rosto e largura estimada da cabeça, em frações do corpo visível.
As cinco fichas têm valores iniciais próprios. A câmera usa a pose de referência
e esses marcos estáveis, evitando oscilar com uma mão levantada ou uma piscada.
As máscaras da porta recebem a mesma transformação da câmera.

Legendas/títulos são sobrepostos depois, no renderizador de episódio.
Para close com ciclos de baixa resolução, use retratos de maior definição
quando disponíveis; zoom não cria detalhe novo. O jumpscare tem coreografia
e cortes próprios e continua sem reenquadramento automático.

Prévias: `camera_planos_comparacao_v1.png` e `camera_planos_preview_v1.mp4`.
Não é necessário gerar novas partes do corpo para mudar de plano.


As sombras também recebem a transformação da câmera; veja [SOMBRAS.md](SOMBRAS.md).
