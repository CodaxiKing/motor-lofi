# DIA ZERO — O COMEÇO DO FIM
5 episódios · Suspense · Classificação: todas as idades (sem sangue) · Cidade, tempos atuais · Duração por episódio: 2 a 3 min
Elemento fixo: contador "DIA X · HH:MM" · Som assinatura: bipe duplo de alerta de emergência · Estilo do traço: desenho

## Cor de cada episódio (tint)
- EP 1: azul frio [90, 120, 200, 0.10] · EP 2: cinza chuvoso [140, 150, 170, 0.10] · EP 3: azul profundo [70, 90, 190, 0.12] · EP 4: vermelho [200, 70, 60, 0.12] · EP 5: laranja amanhecer [240, 150, 90, 0.12]

## Resumo
Roberta acorda numa cidade em silêncio, com o celular cheio de alertas e uma voz no rádio repetindo um único aviso. Ela tem 5 dias para chegar à ponte antes que a cidade seja fechada, e cada escolha muda quem vai com ela.

## Personagens (motor)
Fichas travadas em `personagens.json` (mesma pasta). Elas valem para todos os episódios; não redefinir no roteiro.
- roberta — protagonista (pronta no motor). Cor: laranja (cachecol).
- rafa — garoto do 12º andar (pronto). Cor: verde.
- lia — irmã de Roberta, enfermeira; voz do rádio (pronta).
- valter / zombie — infectados.

## Mistério central
O rádio repete: "Cheguem à ponte antes do Dia 5. Três batidas." Quem transmite é Lia. Ela descobriu que os infectados não enxergam e seguem o som, e que o exército fecha a ponte às 6h do Dia 5. "Três batidas" é o código dos sobreviventes.

## Finais
- A — O BARULHO (voto A no ep. 4): alarme de carro atrai a horda; grupo atravessa; Roberta passa às 5h59. DIA 6.
- B — O SILÊNCIO (voto B no ep. 4): portão trava antes de Roberta; ela fica e assume o rádio: "Dia 6. Agora sou eu quem transmite."
- Ep. 1 (ESPIAR) → Rafa desconfiado; hesita no momento decisivo, a não ser que Roberta recupere a confiança dele.
- Ep. 3: buscar Lia → Lia no final; ir direto → Lia só pelo rádio.
- Ep. 3 (roteiro): Roberta segurou Rafa no pulo entre os prédios → a confiança dele começa a voltar.
- Ep. 4 (voto BARULHO): final A. No ep. 5 o alarme puxa a horda, a Roberta cai na ponte e o Rafa volta para puxá-la (devolve o pulo do telhado); atravessam às 5h59. Do outro lado, ela chama a Lia e ouve três batidas no chiado (esperança sem confirmação, gancho para uma 2ª temporada). Fecha no DIA 6.
- Ep. 3 (voto PONTE): Lia fica só pelo rádio; no ep. 4 ela se despede ("o hospital caiu") e Roberta promete atravessar. Rafa passa a confiar nela: no ep. 4 é ele quem tem a ideia do alarme e diz "eu confio em você" → no final ele não hesita.

## Regras do universo
1. Infectados são cegos e seguem qualquer som · 2. Lentos de dia, rápidos à noite · 3. Sobreviventes: 3 batidas ritmadas · 4. Sem celular desde o Dia 2; só rádio · 5. Ponte fecha às 6h do Dia 5 · 6. Sem cura nesta temporada · 7. Sem sangue

## Episódios
| Nº | Dia | Fase | Status | Pergunta | Voto | Placar |
|---|---|---|---|---|---|---|
| 1 | 1 | início | montado | A) Abrir · B) Espiar | ESPIAR | — |
| 2 | 2 | complicação | montado | A) Escada · B) Telhado | TELHADO | |
| 3 | 3 | reviravolta | montado | A) Buscar Lia no hospital · B) Ir direto pra ponte | PONTE | |
| 4 | 4 | clímax | montado | A) Fazer barulho · B) Esperar em silêncio | BARULHO (A) | 1×1 no TikTok (empate; roleta: BARULHO) |
| 5 | 5 | final | montado | — (final A — O BARULHO) | — | — |

> Eps. 1 e 2 foram publicados na versão antiga do motor (~1 min cada). Os roteiros e os `epNN.json` desta pasta foram
> reconstruídos a partir dos vídeos publicados (marcados como `legado`). Para o "Anteriormente em…" do ep. 3, use
> `"from": "ep02.json", "times": [7, 25, 37]` (Rafa no olho mágico · Rafa e Roberta no apartamento · rua cheia no Dia 2).

## Resumos
- EP 1: Roberta acordou no Dia 1 com 37 alertas pedindo silêncio. No corredor, o vizinho seu Válter virou a cabeça, com olhos brancos, quando um copo caiu. No rádio, uma voz feminina que Roberta acha familiar disse: "Cheguem à ponte antes do Dia 5. Três batidas." Às 23h40, alguém bateu 3 vezes na porta.
- EP 2: Roberta espiou e viu Rafa, do 12º andar, com seu Válter vindo atrás. Ela abriu no último segundo; Rafa entrou desconfiado por ela ter demorado. Rafa provou que os infectados seguem o som. No Dia 2, o celular ficou sem sinal e a rua amanheceu cheia de infectados. O rádio repetiu: "A ponte, antes do Dia 5."
- EP 3: Roberta e Rafa pularam para o prédio vizinho; ela o segurou no pulo e a confiança dele começou a voltar. No Dia 3, um caco de vidro atraiu a horda e os dois se esconderam num posto, onde o rádio chamou Roberta pelo nome: era Lia, a irmã dela, no Hospital Central. Com a ponte fechando em dois dias, ela precisa escolher entre buscar a irmã ou correr para a ponte.
- EP 5: Roberta disparou o alarme do carro e a horda correu para o lado errado. Ela e o Rafa subiram o viaduto até a ponte; quando ela caiu, foi o Rafa quem voltou e a puxou. Atravessaram às 5h59, com o portão batendo atrás deles. Do outro lado, ela chamou a Lia pelo rádio e ouviu três batidas no chiado. Dia 6.
- EP 4: Roberta desligou o rádio para não voltar pela irmã e desceu com o Rafa pela estação Sé, na mesma rua do posto, e esperou o dia passar na plataforma. À noite subiram pela mesma escada, a um quarteirão da ponte; o megafone do exército acordou a horda e os dois correram para um carro parado na rua, que foi cercado. Pelo rádio do carro, a Lia disse que o hospital caiu e pediu que ela atravessasse; Roberta prometeu. O Rafa teve a ideia do alarme do carro e disse que confia nela: fazer barulho ou esperar o dia, com a ponte fechando às seis.

## Extras (curiosidades)
| Nº | Depois do ep. | Tema | Status |
|---|---|---|---|
| 05 | 5 | O que aconteceu com a Lia? (as três batidas eram dela; continua presa no hospital) | montado |

## Vídeos de comentários
| Nº | Depois do ep. | Comentários respondidos | Status |
|---|---|---|---|

## Continuidade (onde eles estão)
- Fim do ep. 4: Roberta e Rafa dentro de um carro parado na rua da estação Sé, a um quarteirão da ponte, cercados pela horda, ao amanhecer do dia 5. O rádio que ela usa agora é o do carro (o rádio de casa ficou no apartamento). O ep. 5 começa dentro desse carro.
- Fim do ep. 5 (roteiro): Roberta e Rafa do lado de dentro da barreira da ponte, DIA 6 · 06:00, com o rádio de pilha ligado. Portão fechado; a horda ficou do outro lado.

## Temporada 2 (gancho)
As três batidas eram da Lia: ela está viva, presa na sala do rádio do Hospital Central, com os infectados do outro lado da porta (revelado no extra 05). Do lado seguro da ponte, Roberta e Rafa sabem que alguém respondeu. A temporada 2 começa com Roberta voltando para buscar a irmã, agora transmitindo ela mesma no rádio.
