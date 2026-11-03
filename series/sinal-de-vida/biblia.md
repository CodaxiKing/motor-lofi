# SINAL DE VIDA
10 episódios · Apocalipse zumbi, suspense e terror · Classificação: 14+ (violência leve, sem gore; nenhuma criança na história) · Subúrbio de cidade grande, tempos atuais · Duração por episódio: 3 a 5 min, com subtrama
Formato: com falas
Estilo: imagens
Prompt de estilo: Dark Cinematic Lo-Fi Cartoon 2D, hand-painted digital illustration, mature graphic novel aesthetic, clean slightly textured dark outlines, soft painterly shading with subtle brush textures, muted desaturated colors, cold blue-gray and dusty purple undertones. Perfectly round, smooth, spherical cartoon head; all skin in the same muted off-white grayish porcelain tone with cool-gray and lavender shadows; small black oval eyes, minimalist black eyebrows, small simple mouth; no realistic nose, ears or human facial anatomy; adults 6.5-7 heads tall, children 5-5.5 heads tall. Avoid: Pure white skin, glowing white face, bright white limbs, realistic skin tones, human facial anatomy, realistic nose, photorealistic face, 3D render, Pixar style, anime, manga, chibi, oversized head, short adult legs, flat vector art, plastic skin, overly saturated colors, inconsistent character design
Elemento fixo: contador "DIA X · HH:MM", dias de estoque no `hud.place` (no ep. 1, "6 KM DO MERCADO") e barra "BATERIA DO RÁDIO" · Som assinatura: chiado do rádio da loja (`static`) seguido do bipe do caixa (`beep`) · Capa: gerada quando existirem as imagens dos personagens (PNG fica fora do repositório)
Perfil: @arquivo.zero.0 (TikTok/Instagram; vai nos comentários fixados e nas artes)

## Cor de cada episódio (tint)
- EP 1: azul de TV [80, 130, 220, 0.10] · EP 2: cinza da porta de aço [130, 140, 160, 0.10] · EP 3: âmbar do estoque [230, 165, 60, 0.10] · EP 4: verde do rádio [110, 190, 150, 0.10] · EP 5: vermelho do cofre [210, 60, 50, 0.10] · EP 6: laranja da rua [235, 125, 40, 0.10] · EP 7: azul de câmara fria [120, 190, 225, 0.12] · EP 8: roxo de febre [130, 90, 190, 0.10] · EP 9: vermelho de fogo [225, 80, 40, 0.12] · EP 10: dourado do amanhecer [245, 205, 120, 0.10]

## Resumo
O seu Geraldo é dono de um mercado de bairro. A filha, Bia, cuida das finanças e repõe as prateleiras. O filho, João, faz as entregas e não fala com o pai há um ano. No dia em que o pai liga dizendo "não sai de casa", a família acaba presa dentro do mercado, com o estoque contado, uma dívida escondida e infectados que repetem a última frase que disseram.

## Personagens (motor)
Fichas travadas em `personagens.json` (mesma pasta). Valem para todos os episódios; não redefinir no roteiro. Principais: João, Bia e Geraldo. Apoio: Rubens e Cida. Os demais infectados são figurantes sem nome (`zombie`). Não há crianças na história.
- joao — protagonista, 25 anos, magro, cabelo escuro bagunçado, barba curta, jaqueta grafite com capuz e faixa refletiva, mochila térmica vermelho-escura. Faz as entregas do mercado de moto; mora sozinho numa kitnet a 6 km. Cor: vermelho-escuro.
- bia — a irmã, 29 anos, cuida das finanças e repõe as prateleiras, tranças escuras, colete vermelho apagado do mercado, prancheta e lápis. Cor: azul da camiseta.
- geraldo — o pai, 58 anos, dono do mercado, bigode grisalho, avental verde apagado, molho de chaves na cintura. Cor: verde.
- rubens — chefe da segurança, 48 anos, grandão, careca, uniforme preto, controle da porta de aço na mão. Cor: preto.
- cida — a caixa mais antiga do mercado, 52 anos, coque, colete vermelho, curativo na mão. Sempre pergunta "CPF na nota?". `cida_infectada` é a mesma depois de virar.
- zombie e variações prontas (`zombie_corredor`, `zombie_rastejante`, `zombie_policial`). Chamados de "repetidores".

## Personagens (motivação e voz)
| Personagem | DESEJO (o que quer) | MEDO | SEGREDO | JEITO DE FALAR |
|---|---|---|---|---|
| joao | tirar a irmã de lá e provar que não precisa do pai | que a última frase dele seja uma piada de entregador ("tá chegando") | ainda faz as entregas porque precisa do dinheiro, não por ter perdoado | rápido, gíria de entregador, piada quando está com medo |
| bia | manter todo mundo vivo e fazer as contas fecharem | ficar sozinha com tudo de novo | sabe que o mercado está hipotecado e prometeu ao pai não contar a João | seca e exata, fala em números e prazos, palavrão pela metade |
| geraldo | ter os dois filhos sob o mesmo teto de novo | morrer sem o perdão do filho | hipotecou o mercado para pagar o tratamento da esposa, e o dinheiro não bastou; é mordido no ep. 7 e esconde | poucas palavras, ordens curtas, no rádio termina com "câmbio, meu filho" |
| rubens | ficar com o mercado e o estoque | ficar do lado de fora da porta | é quem emprestou o dinheiro por fora; tem as promissórias e se considera o dono | educado e frio, chama Geraldo de "patrão" com ironia, diz "regra é regra" |
| cida | (antes de virar) se aposentar e ver o neto adulto | ser esquecida | foi mordida por um cliente de manhã e continuou trabalhando para não perder o dia | carinhosa, chama todo mundo de "amor"; "CPF na nota?" |

## Pistas
| Pista | Plantada em | Paga em | Status |
|---|---|---|---|
| O pai liga ANTES de a TV dar a notícia | ep. 1 | ep. 2 (ouviu no rádio PX da loja, dos caminhoneiros que abastecem o mercado) | pendente |
| O curativo na mão da Cida | ep. 1 | ep. 1 (ela vira) e ep. 7 (quanto tempo a mordida leva) | pendente |
| Infectados repetem a última frase que disseram | ep. 1 (vizinho e Cida) | ep. 8 (a voz do pai) | pendente |
| A pasta do banco que a Bia esconde | ep. 1 | ep. 5 (a hipoteca: João estava errado sobre o pai) | pendente |
| Rubens sabe quanto há no cofre sem nunca ter aberto | ep. 3 | ep. 5 (ele tem as promissórias) | pendente |
| Batidas vindas da câmara fria | ep. 3 | ep. 7 (Cida, trancada, escapa) | pendente |
| O pai deixa de dizer "câmbio, meu filho" | ep. 7 | ep. 8 (está piorando) | pendente |
| Mordida do pai demora mais que o normal | ep. 8 | temporada 2 | pendente |
| Voz de mulher lendo nomes no rádio às 21h | ep. 4 | temporada 2 | pendente |

## Mistério central
Pergunta que puxa a série: o que a família esconde dentro do mercado, e quem é a voz que lê nomes no rádio?
A verdade desta temporada: a família não tem nenhuma ligação com a origem do surto, que fica sem explicação. Geraldo soube antes da TV porque escuta o rádio PX da loja. João culpa o pai por não ter vendido o mercado para tratar a mãe, mas ele já tinha hipotecado tudo em segredo. Quem emprestou o resto foi Rubens, que agora quer o mercado e o estoque.

## Regras do universo
1. Os infectados ("repetidores") caçam pelo som e repetem a última frase que disseram; uma voz conhecida pode ser só um deles · 2. A mordida transforma de horas a alguns dias, mais depressa quanto mais perto do pescoço; primeiro vêm a febre e uma frase que não para de voltar · 3. A rede de celular cai na tarde do DIA 0; resta o rádio de entrega da loja, de alcance curto, e o rádio PX do escritório · 4. Todos os rádios escutam: falar dá notícia e também entrega quem fala; às 21h, uma voz de mulher lê nomes · 5. A porta de aço, o bipe do caixa e o gerador fazem barulho, e barulho chama horda · 6. O estoque é a contagem regressiva: Bia sabe quantos dias restam · 7. 14+: violência leve, sem gore; ataques em corte, sombra e som; sem crianças.

## Finais
Nos dois, a temporada fecha o conflito com Rubens e a família se perdoa, mas a história fica aberta para a temporada 2.
- A — SILÊNCIO (voto A no ep. 9, queimar o mercado): João e Bia põem fogo no mercado com a horda dentro, e o pai fica para trás segurando a porta. Da loja não sobra nada, e o corpo de Geraldo nunca aparece. Última imagem: os irmãos numa laje, às 21h, e o rádio de entrega chia: "câmbio, meu filho". Ele sobreviveu ou é só um repetidor? "CONTINUA NA TEMPORADA 2."
- B — SINAL DE VIDA (voto B no ep. 9, segurar a porta): a família resiste e o mercado vira abrigo, com João chamando sobreviventes pelo rádio. Geraldo, antes de virar, sai sozinho de madrugada para os filhos não verem. Última imagem: João às 21h, várias vozes responde, e uma delas diz: "câmbio, meu filho". "CONTINUA NA TEMPORADA 2."
- Variações: voto do ep. 1 (João chega ao mercado inteiro ou ferido); voto do ep. 3 (Rubens controla o estoque, ou a família tem reserva escondida); voto do ep. 5 (Rubens morre fora da porta, ou trai por dentro); voto do ep. 7 (João sabe da mordida a tempo, ou descobre pela voz).

## Ganchos para a temporada 2
- Geraldo está vivo? A mordida dele não evoluiu no tempo normal, e ninguém explica por quê.
- Às 21h, uma mulher lê nomes pelo rádio, e os nomes da família entram na lista. Quem é ela e como sabe?
- A origem do surto continua sem explicação e sem ligação com a família.

## Escolhas com custo
| Ep. | Opção | GANHA | PERDE |
|---|---|---|---|
| 1 | A) Obedecer ao pai e ficar | comida, luz do dia e uma rota mais segura | a irmã fica a noite inteira sem ele, e ele perde a kitnet sem dormir |
| 1 | B) Sair agora | chega ainda de madrugada e com a moto | sai sem comida, atrai a horda até o mercado e chega ferido |
| 2 | A) Trancar a Cida na câmara fria | Bia mantém a amiga "viva" e a família não mata ninguém | perde a câmara e a carne, e algo fica batendo lá dentro |
| 2 | B) Acabar com a Cida | câmara livre e comida para semanas | Bia não perdoa João, e o barulho chama a horda |
| 3 | A) Dividir o estoque com o Rubens | paz e a ajuda dele na porta | ele passa a ter as chaves |
| 3 | B) Esconder parte do estoque | reserva da família | se ele descobrir, vira guerra |
| 4 | A) Responder à voz no rádio | descobre que há gente lá fora | entrega que estão no mercado |
| 4 | B) Ficar calado | continuam invisíveis | ninguém sabe que eles existem |
| 5 | A) Expulsar o Rubens | o mercado volta para a família | ele fica lá fora, sabendo de cada entrada |
| 5 | B) Fazer um trato com o Rubens | a porta continua protegida | João assina a dívida e fica nas mãos dele |
| 6 | A) Ir de moto à farmácia | volta rápido com o remédio | o motor traz a horda até a porta |
| 6 | B) Ir a pé, em silêncio | não atrai ninguém | demora, e o pai piora |
| 7 | A) Bia conta da mordida | João e Bia se preparam juntos | quebra a promessa, e o pai para de falar com ela |
| 7 | B) Bia guarda o segredo | atende ao pedido do pai | carrega sozinha, e João descobre pela voz |
| 8 | A) Amarrar o pai | todos seguros | ele ouve os filhos decidindo isso, lúcido |
| 8 | B) Dar mais um dia a ele | a família fica junta | ele pode virar a qualquer hora, com a chave |
| 9 | A) Queimar o mercado | a horda morre com ele | perdem tudo, e o pai fica lá dentro |
| 9 | B) Segurar a porta | o mercado vira abrigo e a família fica junta | a horda continua, e muita gente vai chegar atrás de comida |

## Desempates (roleta do placar)
Ep. 1: B · Ep. 2: A · Ep. 3: B · Ep. 4: A · Ep. 5: A · Ep. 6: B · Ep. 7: A · Ep. 8: B · Ep. 9: A

## Episódios
| Nº | Dia | Fase | Status | Pergunta | Voto | Placar |
|---|---|---|---|---|---|---|
| 1 | 0 | início | roteiro | A) Obedecer e ficar · B) Sair agora | | |
| 2 | 1 | complicação | planejado | A) Trancar a Cida · B) Acabar com a Cida | | |
| 3 | 3 | complicação | planejado | A) Dividir o estoque · B) Esconder parte | | |
| 4 | 5 | complicação | planejado | A) Responder à voz · B) Ficar calado | | |
| 5 | 6 | virada | planejado | A) Expulsar o Rubens · B) Fazer um trato | | |
| 6 | 8 | complicação | planejado | A) De moto · B) A pé | | |
| 7 | 9 | reviravolta | planejado | A) Bia conta · B) Bia guarda segredo | | |
| 8 | 11 | escalada | planejado | A) Amarrar o pai · B) Dar mais um dia | | |
| 9 | 12 | clímax | planejado | A) Queimar o mercado · B) Segurar a porta | | |
| 10 | 13 | final | planejado | — | | |

## Plano por episódio
- **EP 1 · DIA 0 · "NÃO SAI DE CASA"** (início, azul) — O pai liga depois de um ano: "Não sai de casa. Liga a TV." No mercado, Cida trabalha com um curativo na mão e Rubens baixa a porta com ordem do Geraldo. O vizinho de João bate repetindo "tá servido?". A tentativa de sair falha. Pelo rádio da loja, Bia sussurra que Cida virou e fala da pasta do banco. Gancho: "CPF NA NOTA?". Pergunta: A) OBEDECER E FICAR · B) SAIR AGORA.
- **EP 2 · DIA 1 · "PORTA DE AÇO"** (complicação, cinza) — João chega e Rubens não quer abrir: regra é regra. Dentro, pai e filho se encontram depois de um ano, com Cida solta entre as prateleiras. Gancho: Geraldo e João frente a frente ("UM ANO, / PAI"). Pergunta: A) TRANCAR A CIDA · B) ACABAR COM A CIDA.
- **EP 3 · DIA 3 · "ESTOQUE"** (complicação, âmbar) — Bia conta: 19 dias. Rubens quer as chaves. Batidas vêm da câmara. Gancho: a prancheta com o número caindo ("DEZENOVE / DIAS"). Pergunta: A) DIVIDIR · B) ESCONDER.
- **EP 4 · DIA 5 · "21 HORAS"** (complicação, verde) — O PX do escritório volta e uma mulher lê nomes de sobreviventes. Rubens quer pedir ajuda; Geraldo não deixa. Gancho: a voz lendo uma lista ("QUEM / ESTÁ LENDO?"). Pergunta: A) RESPONDER · B) FICAR CALADO.
- **EP 5 · DIA 6 · "A PASTA"** (virada, vermelho) — João abre o cofre: a hipoteca e as promissórias em nome de Rubens. Tudo o que ele achava do pai vira ao contrário, e Rubens tira a máscara: "o mercado é meu". Gancho: João lendo a pasta ("VOCÊ / HIPOTECOU?"). Pergunta: A) EXPULSAR · B) FAZER UM TRATO.
- **EP 6 · DIA 8 · "ÚLTIMA ENTREGA"** (complicação, laranja) — O coração de Geraldo falha, e João faz a entrega mais perigosa da vida: o remédio da farmácia da esquina. Na rua, um entregador virado chama pelo nome de um pedido. Gancho: ("JOÃO, / SEU PEDIDO"). Pergunta: A) DE MOTO · B) A PÉ.
- **EP 7 · DIA 9 · "CÂMARA FRIA"** (reviravolta, azul) — Cida escapa, e Geraldo é mordido salvando a Bia. Ele faz a filha prometer silêncio. Gancho: a mão dele sob o curativo ("NÃO CONTA / PRA ELE"). Pergunta: A) BIA CONTA · B) BIA GUARDA SEGREDO.
- **EP 8 · DIA 11 · "REPETIDOR"** (escalada, roxo) — A febre sobe e, na madrugada, Geraldo repete a frase do começo. A horda se junta na porta, e Rubens faz o último movimento. Gancho: ("NÃO SAI / DE CASA"). Pergunta: A) AMARRAR O PAI · B) DAR MAIS UM DIA.
- **EP 9 · DIA 12 · "ÚLTIMA HORA"** (clímax, fogo) — A porta de aço cede. João e o pai enfim se falam, com a pasta na mão, e Rubens cai. Só há dois jeitos de sair dessa. Gancho: pai e filho ("ME PERDOA, / PAI"). Pergunta: A) QUEIMAR O MERCADO · B) SEGURAR A PORTA.
- **EP 10 · DIA 13 · "SINAL DE VIDA"** (final, dourado) — A despedida de Geraldo e a primeira noite depois, conforme os votos. Gancho: ("CÂMBIO, / MEU FILHO"). Fecha com "CONTINUA NA TEMPORADA 2".

## Cenários
Estilo imagens: cada fundo é gerado no ChatGPT. A linha `CENÁRIO` usa o nome do motor mais próximo e a linha `IMAGENS` dá o fundo real. Fundos principais: `kitnet_joao`, `kitnet_porta`, `corredor_vila`, `escada_vila`, `laje_vila`, `portao_vila`, `mercado_caixas`, `mercado_corredor`, `mercado_estoque`, `mercado_camara_fria`, `mercado_escritorio`, `mercado_porta_aco`, `rua_suburbio`, `farmacia_esquina`.

## Extras planejados
1. Ep. 1: por que João foi embora? · 2. Ep. 2: quem era a Cida · 3. Ep. 3: como Bia faz as contas · 4. Ep. 4: quem é Rubens · 5. Ep. 5: a última conversa com a mãe · 6. Ep. 6: o entregador virado · 7. Ep. 7: o que o Geraldo sabia · 8. Ep. 8: de quem é a voz · 9. Ep. 9: o que há no cofre.

## Extras
| Nº | Depois do ep. | Tema | Status |
|---|---|---|---|
| 1 | 1 | Por que João foi embora? | roteiro |

## Resumos
- EP 1: Depois de um ano sem falar com o filho, Geraldo liga para João: "Não sai de casa. Liga a TV." João vê o vizinho virar um repetidor, e o plano de ir de moto até o mercado falha. À noite, pelo rádio da loja, Bia sussurra que a caixa Cida virou e fala de uma pasta do banco sobre a mãe. O pai a corta e manda João ficar.
- EP 2:
- EP 3:
- EP 4:
- EP 5:
- EP 6:
- EP 7:
- EP 8:
- EP 9:
- EP 10:

## Vídeos de comentários
| Nº | Depois do ep. | Comentários respondidos | Status |
|---|---|---|---|

## Continuidade (onde eles estão)
- Início do ep. 1: João de folga na kitnet, DIA 0, 14:10, com o celular, as chaves da moto, a mochila e o rádio de entrega da loja. Geraldo, Bia, Rubens e Cida no mercado, a 6 km.
