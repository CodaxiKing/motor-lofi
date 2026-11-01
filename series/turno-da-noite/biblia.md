# TURNO DA NOITE — AS REGRAS DA LUA 24H
5 episódios · Suspense/Terror (estilo creepypasta narrada, em primeira pessoa) · Classificação: todas as idades (sem sangue, sustos sem violência explícita) · Posto de rodovia, tempos atuais · Duração por episódio: 2 a 3 min
Elemento fixo: contador "DIA X · HH:MM" com o lugar "LUA 24H" · Som assinatura: o sininho da porta (`bell`), que às 3h17 toca sem ninguém entrar · Estilo do traço: desenho

## Cor de cada episódio (tint)
- EP 1: verde fluorescente [120, 200, 150, 0.10] · EP 2: azul do monitor [80, 130, 200, 0.12] · EP 3: sépia de 1996 [210, 160, 90, 0.12] · EP 4: vermelho [200, 60, 60, 0.14] · EP 5: rosa amanhecer [240, 160, 130, 0.12]

## Resumo
Bia, 19 anos, assume o turno da noite na Conveniência Lua 24H, num posto à beira da rodovia, uma semana depois de o antigo atendente sumir. Embaixo da registradora ela encontra um bilhete com as regras do turno, e cada regra que ela quebra (ou segue) muda quem sai vivo de lá ao amanhecer.

## Narração (estilo creepypasta)
A Bia narra em primeira pessoa, no passado, como quem conta a história anos depois ("Eu tinha dezenove anos quando aceitei o turno da noite."). Voz baixa, calma, com pausas antes dos sustos. As regras do bilhete são lidas na voz do Nestor (gravada, mais grave e cansada). Toda abertura de episódio começa com uma regra.

## Personagens (motor)
Fichas travadas em `personagens.json` (mesma pasta). Valem para todos os episódios; não redefinir no roteiro.
- bia — protagonista e narradora, atendente nova. Silhueta: cabelo afro + boné. Cor: vermelho da loja (boné e camisa).
- nestor — antigo atendente que sumiu; escreveu as regras. Velho, careca, bigode branco, óculos. Cor: vermelho desbotado.
- caio — motoboy que toma café ali toda madrugada; aliado. Alto, capacete e baú amarelos. Cor: amarelo.
- dona_cida — senhora que compra leite às 2h toda noite; não aparece na câmera. Coque grisalho, saia, cachecol lilás. Cor: lilás.
- cliente — o Cliente das 3h17: alto, magro, sobretudo, chapéu e óculos escuros; nunca aparece na câmera. Silhueta preta e comprida (scale 1.14).

## As regras do bilhete (letra do Nestor)
1. Nunca atenda ninguém às 3h17. Se o sininho tocar às 3h17, olhe o monitor antes de olhar a porta.
2. Se alguém não aparecer na câmera, não aceite o dinheiro dele. Nem o troco.
3. A Dona Cida compra leite às 2h. Venda. Não pergunte de onde ela vem.
4. A câmara fria fica trancada. Se alguém bater lá de dentro, não abra. *(letra diferente: escrita pelo Cliente)*
5. Se o relógio da parede parar, apague as luzes e fique atrás do balcão até ele voltar a andar.
6. Antes das 6h, nunca saia pela porta da frente.
7. *(pedaço rasgado: "Se ele souber o seu nome…")*

## Mistério central e a verdade
Na madrugada de 1º de novembro de 1996, um ônibus sumiu no nevoeiro na curva do viaduto, logo depois de parar no Posto Lua. Os passageiros nunca chegaram. Desde então, quem não aparece na câmera é daquela noite: a Dona Cida é uma das passageiras, presa na última parada, comprando o leite que ia levar pro neto.
O Cliente das 3h17 é o "cobrador" daquela viagem: ele precisa que alguém da loja aceite o dinheiro dele. Quem aceita "paga a passagem" e passa a pertencer à noite de 1996. O Nestor aceitou um troco dele há uma semana e está preso na câmara fria, que às 3h17 vira o bagageiro do ônibus. A regra 4 não é do Nestor: o Cliente a escreveu no bilhete para que ninguém o solte.
Para soltar alguém, é preciso devolver o dinheiro na mão do Cliente às 3h17, com o relógio parado, sem dizer o próprio nome.

## Finais
- A — O TROCO (voto A no ep. 4): Bia devolve a moeda na mão do Cliente. O relógio volta a andar, o Nestor sai da câmara fria e o sininho toca pela última vez. Às 6h, a Dona Cida paga o leite com uma moeda atual e vai embora: os passageiros foram liberados. Bia fica com o emprego, e a última cena mostra um bilhete novo embaixo da registradora, na letra dela.
- B — A PORTA DA FRENTE (voto B no ep. 4): Bia foge com o Nestor pela porta da frente antes das 6h. Eles saem no nevoeiro e veem o ônibus de 1996 parado no pátio, de faróis acesos. O Nestor entra no lugar dela para que ela possa correr até a rodovia. Às 6h, a loja está fechada, coberta de poeira, como se estivesse abandonada há 30 anos. Última fala: "Eu nunca mais passei por aquele posto. Mas às 3h17, o meu celular ainda toca um sininho."
- Ep. 1 (A ATENDER): o Cliente fala o nome dela ("Até amanhã, Bia"): no final ele pode chamá-la pelo nome, e ela precisa cobrir o crachá. (B ESCONDER): ele deixa uma moeda de 1996 no balcão: é essa moeda que ela devolve no final A.
- Ep. 2 (A ABRIR): a Bia vê o Nestor por um segundo dentro do bagageiro do ônibus e fecha a porta. Ela tem prova; o Nestor confia nela. (B NÃO ABRIR): o Nestor passa a falar com ela só pelas batidas (3 = sim, 1 = não).
- Ep. 3 (A CONTAR AO CAIO): no final o Caio segura a lanterna e vigia o relógio; o Caio aparece na câmera, então ele é a prova de que a Bia ainda está "do lado de cá". (B SOZINHA): no final ela fica sem ajuda e sem luz.

## Por episódio
| Nº | Fase | Objetivo | Gancho (cena 0) | Pergunta A/B | Cor |
|---|---|---|---|---|---|
| 1 | início | A primeira noite: Bia acha o bilhete, conhece o Caio e a Dona Cida (que não aparece no monitor). Às 3h17 o sininho toca. | Monitor mostrando a porta vazia, enquanto na porta há um homem alto de chapéu: "ELE NÃO APARECE NA CÂMERA" | A) Atender o cliente · B) Seguir a regra e se esconder atrás do balcão | verde fluorescente |
| 2 | complicação | O Cliente espera no balcão; o relógio para (regra 5), as luzes apagam. No estoque, a Bia acha o celular do Nestor com um último vídeo. Batidas na câmara fria: "Bia… sou eu, o Nestor." | Mão batendo de dentro, porta da câmara fria com gelo: "ALGUÉM BATE LÁ DENTRO" | A) Abrir a câmara fria · B) Obedecer a regra 4 | azul do monitor |
| 3 | reviravolta | A Bia percebe que a regra 4 tem outra letra. Na segunda noite, a Dona Cida conta do ônibus de 1996 e do "cobrador". | Bilhete em close, a regra 4 tremendo: "ESSA LETRA NÃO É DELE" | A) Contar tudo pro Caio · B) Resolver sozinha | sépia de 1996 |
| 4 | clímax | Terceira noite: o plano para soltar o Nestor. Às 3h17 o relógio para, o Cliente entra e sabe tudo. | Relógio parado em 3:17 e o sininho: "O RELÓGIO PAROU" | A) Devolver o dinheiro na mão dele · B) Fugir pela porta da frente antes das 6h | vermelho |
| 5 | final | Final A ou B conforme o voto do ep. 4. | Porta da câmara fria se abrindo em câmera lenta: "QUEM SAI DAQUI?" | — | rosa amanhecer |

## Cenários e mapa (`mundo.json`)
- `loja` (novo no motor): a loja por dentro: balcão do caixa com registradora e monitor das câmeras (com chiado), geladeiras de vidro, gôndola e a porta de vidro com sininho. Marcas: balcao, caixa, porta, geladeira, fundo, meio, frente.
- `estoque` (novo no motor): prateleiras de caixas, lâmpada que balança e a porta da câmara fria no fundo. Marcas: camara, meio, frente, prateleira_esq, prateleira_dir.
- `posto` (pátio com as bombas), `beco` (fundos do posto), `rua`/`rua_amanhecer`/`viaduto` (a rodovia e a curva do viaduto).
- Planos de detalhe: `relogio` (o relógio da parede), `celular` (o vídeo do Nestor), `macaneta` (a porta da câmara fria), `olho`.
- Ligações: loja ↔ estoque (porta de vaivém) · loja ↔ pátio (porta de vidro, sininho) · estoque ↔ fundos (porta de serviço) · fundos ↔ pátio (pela lateral) · pátio ↔ rodovia (saída do posto).
- Começo: Bia na loja, DIA 1 · 22:00, com o bilhete, a lanterna e o celular; o Caio com a mochila (baú).
- Tempo: a série vai do DIA 1 · 22:00 ao amanhecer do DIA 4. Cada madrugada vira o dia seguinte no contador (3h17 da primeira noite = DIA 2 · 03:17).

## Regras do universo
1. Quem não aparece no monitor das câmeras é da noite de 1996 · 2. Aceitar dinheiro (ou troco) de quem não aparece prende você naquela noite · 3. O Cliente só entra às 3h17 e só pode tocar no que é dado a ele · 4. Com o relógio parado, nada lá dentro muda de lugar até ele voltar a andar · 5. Saber o seu nome dá poder a ele: o crachá é perigoso · 6. A loja é segura até as 6h, desde que ninguém saia pela porta da frente · 7. Sem sangue; os sumiços são silenciosos (a pessoa some no nevoeiro ou numa luz)

## Episódios
| Nº | Dia | Fase | Status | Pergunta | Voto | Placar |
|---|---|---|---|---|---|---|
| 1 | 1–2 | início | planejado | A) Atender o cliente · B) Seguir a regra e se esconder | | |
| 2 | 2 | complicação | planejado | A) Abrir a câmara fria · B) Obedecer a regra 4 | | |
| 3 | 2–3 | reviravolta | planejado | A) Contar tudo pro Caio · B) Resolver sozinha | | |
| 4 | 3–4 | clímax | planejado | A) Devolver o dinheiro na mão dele · B) Fugir pela porta da frente | | |
| 5 | 4 | final | planejado | — | | |

## Resumos
- EP 1:
- EP 2:
- EP 3:
- EP 4:
- EP 5:

## Vídeos de comentários
| Nº | Depois do ep. | Comentários respondidos | Status |
|---|---|---|---|

## Continuidade (onde eles estão)
- Começo da série: Bia sozinha atrás do balcão da Lua 24H, DIA 1 · 22:00. O bilhete estava colado embaixo da registradora.
