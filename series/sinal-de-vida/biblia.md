# SINAL DE VIDA
10 episódios · Apocalipse zumbi, suspense e terror · Classificação: 14+ (violência leve, sem gore) · Subúrbio de cidade grande e interior do Brasil, tempos atuais · Duração por episódio: 3 a 5 min, com subtrama
Formato: com falas
Estilo: imagens
Prompt de estilo: ilustração digital 2D estilo cartoon lo-fi, traço limpo e grosso, cores chapadas com sombras suaves, proporções de desenho animado (cabeça grande e redonda), iluminação cinematográfica de terror, sem texto, sem marca-d'água, mesmo estilo em todas as imagens da série
Elemento fixo: contador "DIA X · HH:MM", distância até a fazenda no `hud.place` (começa em "480 KM") e barra "BATERIA DO RÁDIO" · Som assinatura: chiado do rádio (`static`) seguido do bipe de chamada (`beep`) · Capa: gerada no planejamento (PNG fica fora do repositório)
Perfil: @arquivo.zero.0 (TikTok/Instagram; vai nos comentários fixados e nas artes)

## Cor de cada episódio (tint)
- EP 1: azul de TV [80, 130, 220, 0.10] · EP 2: âmbar do rádio [230, 165, 60, 0.10] · EP 3: verde de hospital [110, 190, 150, 0.10] · EP 4: vermelho de transmissão [210, 60, 50, 0.10] · EP 5: terra da estrada [190, 130, 80, 0.10] · EP 6: laranja de farol [235, 125, 40, 0.10] · EP 7: azul de câmara fria [120, 190, 225, 0.12] · EP 8: roxo de anoitecer [130, 90, 190, 0.10] · EP 9: vermelho de fogo [225, 80, 40, 0.12] · EP 10: dourado do amanhecer [245, 205, 120, 0.10]

## Resumo
João, entregador de 22 anos, recebe uma ligação do pai: "não sai de casa e liga a TV". Horas depois, a família espalhada pelo interior só consegue se falar por um rádio velho, e a meta é uma só: todo mundo na fazenda do pai. Mas qualquer um pode ouvir o rádio, e os infectados repetem a última frase que disseram.

## Personagens (motor)
Fichas travadas em `personagens.json` (mesma pasta). Valem para todos os episódios; não redefinir no roteiro.
- joao — protagonista, 22 anos, moreno, magro, cabelo crespo curto, jaqueta vermelha de entregador, mochila térmica. Cor: vermelho.
- geraldo — o pai, 58 anos, ex-caminhoneiro, dono da fazenda, bigode grisalho, chapéu de palha, camisa xadrez. Cor: palha.
- cida — a mãe, 54 anos, técnica de enfermagem, separada do Geraldo, mora na cidade do interior com o Téo. Pijama hospitalar verde. Cor: verde.
- bia — a irmã, 27 anos, veterinária em outra cidade, tranças, colete azul. Cor: azul.
- teo — o caçula, 9 anos, boné amarelo, camiseta de time. Cor: amarelo.
- vo_zefa — mãe do Geraldo, 79 anos, baixinha, coque branco, vestido florido roxo, bengala. Cor: roxo.
- nei — tio, irmão do Geraldo, caminhoneiro, gordo, boné e barba. Cor: laranja.
- dandara — cozinheira do restaurante onde João pegava os pedidos, 30 anos, pele negra, black power, dólmã branca e bandana. Cor: branco.
- darcio — Dárcio Leme, 60 anos, dono do Frigorífico Leme e voz da Rádio Esperança, alto e magro, terno bege e fedora. Vilão.
- zombie e variações prontas: `zombie`, `zombie_corredor`, `zombie_rastejante`, `zombie_enfermeiro`, `zombie_policial`. Chamados de "repetidores".

## Personagens (motivação e voz)
| Personagem | DESEJO (o que quer) | MEDO | SEGREDO | JEITO DE FALAR |
|---|---|---|---|---|
| joao | chegar à fazenda e provar que não é o filho que foi embora | chegar tarde e achar a família repetindo frases | não fala com o pai há um ano; saiu de casa depois de uma briga e nunca pediu desculpa | rápido, gíria de entregador ("tá chegando", "deu ruim"), piada quando está com medo |
| geraldo | ver todos os filhos juntos antes que seja tarde | morrer sozinho e sem perdão | transportou as cargas do Frigorífico Leme e sabia que havia algo errado; foi mordido no DIA 3 e não contou | poucas palavras, ordens curtas, termina a chamada com "câmbio, meu filho" |
| cida | tirar o Téo vivo da cidade | ter que escolher entre os pacientes e o filho | guardou uma caixa de remédios que os colegas precisavam | calma de plantão, chama todo mundo de "meu bem", dá instruções numeradas |
| bia | provar que dá conta sem o pai | virar igual a ele | descobriu como os infectados reagem ao som ao sedar um cavalo mordido; escondeu que atirou no próprio noivo infectado | seca e técnica, usa termos de veterinária, fala palavrão pela metade |
| teo | achar o cachorro e reunir a família | ficar sem a mãe | ouve o rádio escondido e sabe de coisas que os adultos acham que ele não sabe | muitas perguntas, repete as frases dos adultos, conta tudo em números |
| vo_zefa | manter a casa de pé e rezar por todos | enterrar outro filho | foi quem escondeu a mordida do Geraldo | fala em ditados, xinga o rádio, chama o Geraldo de "menino" |
| nei | pagar a dívida e salvar a própria pele | morrer devendo | contou ao Dárcio sobre o poço da fazenda em troca de combustível | fala alto, conta causo, chama João de "sobrinho" |
| dandara | achar a filha, que está numa cidade no caminho | ter desistido cedo demais | a filha dela mandou um áudio que ela ainda não teve coragem de ouvir | direta, humor seco, trata tudo como cozinha ("isso aí já passou do ponto") |
| darcio | ser dono do último poço limpo da região e de quem depende dele | perder o controle da cidade que ele comprou | o surto nasceu no frigorífico dele; a TV do DIA 0 mostrava a fábrica | voz de locutor, gentil, chama os ouvintes de "minha gente", repete "aqui ninguém fica sozinho" |

## Pistas
| Pista | Plantada em | Paga em | Status |
|---|---|---|---|
| O pai liga ANTES de a TV dar a notícia | ep. 1 | ep. 7 (ele conhecia a carga) | pendente |
| No fundo da reportagem da TV, um caminhão com o logo Leme | ep. 1 | ep. 7 (o surto nasceu no frigorífico) | pendente |
| Infectados repetem a última frase que disseram | ep. 1 (o vizinho repete "tá servido?") | ep. 8 (a voz no rádio pode não ser de gente viva) | pendente |
| Geraldo passa a usar luva na mão direita ao falar no rádio (descrito pela Zefa) | ep. 4 | ep. 8 (a mordida) | pendente |
| O áudio da filha de Dandara, nunca aberto | ep. 2 | ep. 6 (ela ouve) | pendente |
| Nei sabe o caminho do poço sem nunca ter ido à parte nova da fazenda | ep. 5 | ep. 6 (ele vendeu a informação) | pendente |
| Téo conta "três vozes novas" no rádio | ep. 3 | ep. 8 (o comboio de Dárcio escuta tudo) | pendente |

## Mistério central
Premissa: o reencontro de todo mundo na fazenda do pai. Pergunta que puxa a série: por que o pai sabia antes de todo mundo, e quem está ouvindo a família no rádio?
A verdade: Geraldo transportava carga para o Frigorífico Leme e reconheceu a fábrica na TV; por isso ligou antes da notícia. Ele transformou a fazenda em abrigo (poço, cercas, horta) por culpa. Foi mordido no DIA 3, escondeu e aguenta o que pode para ver os filhos juntos pela última vez. Dárcio escuta a frequência e usa as conversas da família para chegar ao poço. O reencontro acontece nos dois finais; o que muda é quem chega e como.

## Regras do universo
1. Os infectados ("repetidores") caçam pelo som e repetem a última frase que disseram; uma voz pedindo socorro pode ser uma isca sem querer · 2. A mordida transforma em até 5 dias, mais depressa quanto mais perto do pescoço; primeiro vêm a febre e a frase que não para de voltar · 3. A rede de celular cai na noite do DIA 0; só resta o rádio PX, sempre às 21h na frequência 19, quando cada um diz o nome: o "sinal de vida" · 4. Todo mundo que tem rádio escuta: falar dá notícia e também entrega a posição · 5. Pouca bateria: cada chamada gasta a barra · 6. Bicicleta é silenciosa e carro atrai horda · 7. Água limpa é a moeda do interior: o poço da fazenda vale mais que comida · 8. 14+: violência leve, sem gore; ataques em corte, sombra e som.

## Finais
- A — SILÊNCIO (voto A no ep. 9, desligar o rádio): com todos na fazenda, João desmonta o rádio. A família vive escondida e segura, mas ninguém mais os encontra e quem chamava pela frequência fica sem resposta. Geraldo se despede antes de virar. Última imagem: a família jantando em silêncio; lá fora, muito baixo, a voz dele repete "não sai de casa, João". "FIM."
- B — SINAL DE VIDA (voto B no ep. 9, manter o rádio): João assume o microfone e passa a chamar outros sobreviventes. A fazenda vira comunidade, e a cada noite mais gente e mais risco chegam. Geraldo se despede no ar. Última imagem: João às 21h dizendo os nomes da família, e dezenas de vozes respondendo, entre elas uma que só repete. "FIM."
- Variações: voto do ep. 3 (Téo chega com a mãe, ou chega depois com a Bia); voto do ep. 4 (Dandara chega à fazenda, ou aparece no comboio de Dárcio); voto do ep. 6 (Nei morre defendendo a porteira, ou abre a porteira para Dárcio); voto do ep. 8 (refugiados lutam ao lado da família, ou a fazenda está sozinha, com mais água e menos gente).

## Escolhas com custo
| Ep. | Opção | GANHA | PERDE |
|---|---|---|---|
| 1 | A) Obedecer ao pai e ficar | abrigo, comida e tempo para conseguir o rádio | perde o último dia com estradas abertas e a bicicleta é roubada |
| 1 | B) Sair agora | ganha distância e a bicicleta | sem comida e sem saber da regra da frequência |
| 2 | A) Responder no rádio | a família sabe que ele está vivo e recebe a rota | todo mundo ouve onde ele está; alguém aparece |
| 2 | B) Ficar calado | continua invisível e poupa bateria | a família o dá como morto e a mãe sai para procurá-lo |
| 3 | A) Cida foge agora com o Téo | mãe e filho juntos | sem os remédios que salvariam alguém na fazenda |
| 3 | B) Cida volta pelos remédios | leva os remédios | Téo fica sozinho, foge e se separa da mãe |
| 4 | A) Ir ao abrigo da Rádio Esperança | comida, banho e informação | João fica na lista de Dárcio; Dandara fica presa lá dentro |
| 4 | B) Seguir a pé | continua livre | sem comida; Dandara o deixa para ir atrás da filha |
| 5 | A) Subir no caminhão do Nei | 200 km em uma noite | barulho e horda atrás; João passa a depender do tio |
| 5 | B) Ir com Bia pela mata | irmãos juntos e em silêncio | perde dois dias; a mãe chega à fazenda sem ajuda |
| 6 | A) Denunciar o Nei no rádio | a família fica sabendo | Dárcio ouve, Nei foge com o caminhão |
| 6 | B) Guardar segredo | mantém caminhão e o tio por perto | o Nei continua passando informações |
| 7 | A) Contar a verdade sobre o pai | a família passa a saber quem ele é | Bia rompe e quase desiste de ir à fazenda |
| 7 | B) Esconder dos outros | mantém todos a caminho | João carrega sozinho, e a mentira estoura no reencontro |
| 8 | A) Abrir a porteira aos refugiados | gente para defender a cerca | a água acaba mais rápido e Dárcio infiltra um homem |
| 8 | B) Fechar a porteira | água e segurança | fica com poucos braços e deixa gente morrer na cerca |
| 9 | A) Desligar o rádio | ninguém mais encontra a fazenda | ninguém mais é salvo por ela |
| 9 | B) Manter o rádio ligado | a fazenda vira esperança para muita gente | Dárcio não será o último a chegar |

## Desempates (roleta do placar)
Ep. 1: B · Ep. 2: A · Ep. 3: A · Ep. 4: A · Ep. 5: B · Ep. 6: A · Ep. 7: A · Ep. 8: A · Ep. 9: B

## Episódios
| Nº | Dia | Fase | Status | Pergunta | Voto | Placar |
|---|---|---|---|---|---|---|
| 1 | 0 | início | planejado | A) Obedecer e ficar · B) Sair agora | | |
| 2 | 1 | complicação | planejado | A) Responder no rádio · B) Ficar calado | | |
| 3 | 2 | complicação | planejado | A) Fugir com o Téo · B) Voltar pelos remédios | | |
| 4 | 3 | complicação | planejado | A) Ir ao abrigo · B) Seguir a pé | | |
| 5 | 4 | virada | planejado | A) Caminhão do Nei · B) Mata com a Bia | | |
| 6 | 5 | reviravolta | planejado | A) Denunciar o Nei · B) Guardar segredo | | |
| 7 | 6 | reviravolta | planejado | A) Contar a verdade · B) Esconder | | |
| 8 | 7 | escalada | planejado | A) Abrir a porteira · B) Fechar a porteira | | |
| 9 | 8 | clímax | planejado | A) Desligar o rádio · B) Manter o rádio | | |
| 10 | 9 | final | planejado | — | | |

## Plano por episódio
- **EP 1 · DIA 0 · "NÃO SAI DE CASA"** (início, azul de TV) — João faz entregas no subúrbio quando o pai, com quem não fala há um ano, liga: "Não sai de casa. Liga a TV." A reportagem mostra um surto no interior, com um caminhão Leme ao fundo. O vizinho morde um colega no corredor e repete "tá servido?". A rede cai. Gancho: a voz do pai ao telefone e João diante da TV ("NÃO SAI / DE CASA"). PENSAMENTO: a briga com o pai. Pergunta: A) OBEDECER E FICAR · B) SAIR AGORA.
- **EP 2 · DIA 1 · "FREQUÊNCIA 19"** (complicação, âmbar) — Num posto, João e Dandara acham um rádio PX. Às 21h ouve o pai chamando um a um; Bia, Cida e Téo dizem o nome e a Zefa manda todos para a fazenda. Falta só ele. Gancho: o pai chamando "João, responde" ("ME RESPONDE, / MEU FILHO"). O PLANO: a rota dos 480 km. Pergunta: A) RESPONDER · B) FICAR CALADO.
- **EP 3 · DIA 2 · "PLANTÃO"** (complicação, verde) — A história vai à Cida e ao Téo no hospital do interior, com João ouvindo pelo rádio de dentro de um vagão. Pacientes repetem frases no corredor; Téo conta "três vozes novas" no rádio. Gancho: os doentes repetindo o nome de Cida ("TÉO, / CADÊ VOCÊ?"). Pergunta: A) FUGIR COM O TÉO · B) VOLTAR PELOS REMÉDIOS.
- **EP 4 · DIA 3 · "RÁDIO ESPERANÇA"** (complicação, vermelho) — Uma voz gentil oferece abrigo no Frigorífico Leme. Dandara quer ir; João desconfia. Zefa comenta no rádio que Geraldo agora fala de luva. Gancho: "aqui ninguém fica sozinho" sobre uma fila de gente sumindo portão adentro. Pergunta: A) IR AO ABRIGO · B) SEGUIR A PÉ.
- **EP 5 · DIA 4 · "BIA"** (virada, terra) — Bia, numa clínica veterinária, descobre como o som guia os infectados e encontra João no meio de um cerco. Tio Nei aparece de caminhão, sabendo demais sobre o poço. Primeira conversa dos irmãos, cheia de rancor. Gancho: o caminhão iluminando a horda ("SOBE AGORA, / SOBRINHO!"). Pergunta: A) CAMINHÃO DO NEI · B) MATA COM A BIA.
- **EP 6 · DIA 5 · "DÍVIDA"** (reviravolta, laranja) — Dandara ouve o áudio da filha. João pega Nei falando com Dárcio no rádio: ele vendeu o poço. Gancho: a voz de Dárcio, gentil, saindo do rádio do caminhão ("OBRIGADO, / SEU NEI"). Pergunta: A) DENUNCIAR · B) GUARDAR SEGREDO.
- **EP 7 · DIA 6 · "A CARGA"** (reviravolta, azul) — Para buscar combustível, entram no frigorífico. João acha as notas de carga com a assinatura do pai e a câmara onde tudo começou. Dárcio aparece. Revelação: o pai sabia. Gancho: a assinatura na nota ("MEU PAI / SABIA?"). Pergunta: A) CONTAR A VERDADE · B) ESCONDER.
- **EP 8 · DIA 7 · "A PORTEIRA"** (escalada, roxo) — Cida chega à fazenda e vê a mão do Geraldo. A Zefa confessa. O rádio começa a repetir frases, e João não sabe mais se fala com o pai. Refugiados chegam, e atrás deles o comboio. Gancho: pela frequência, a voz do pai sem parar ("NÃO SAI / DE CASA"). Pergunta: A) ABRIR A PORTEIRA · B) FECHAR A PORTEIRA.
- **EP 9 · DIA 8 · "ÚLTIMO QUILÔMETRO"** (clímax, fogo) — O reencontro acontece debaixo do cerco: João chega, a família está inteira pela primeira vez, e pai e filho enfim se falam. Dárcio ataca o poço; João usa o rádio e a voz do próprio Dárcio para jogar a horda sobre o comboio. Gancho: João e o pai frente a frente ("CHEGUEI, / PAI"). Pergunta: A) DESLIGAR O RÁDIO · B) MANTER O RÁDIO.
- **EP 10 · DIA 9 · "SINAL DE VIDA"** (final, dourado) — Geraldo se despede e a família decide o que vem depois, conforme os votos. Finais A e B acima. Gancho: a última chamada de Geraldo às 21h ("CÂMBIO, / MEU FILHO"). Fecha com "FIM".

## Cenários
Estilo imagens: cada fundo é gerado no ChatGPT. A linha `CENÁRIO` usa o nome do motor mais próximo e a linha `IMAGENS` dá o fundo real. Fundos principais: `quarto_joao`, `corredor_vila`, `rua_suburbio`, `posto_abandonado`, `vagao_de_carga`, `hospital_interior`, `estrada_interior`, `clinica_veterinaria`, `cabine_caminhao`, `frigorifico_patio`, `camara_fria_leme`, `fazenda_porteira`, `fazenda_cozinha_radio`, `fazenda_poco`.

## Extras planejados
1. Ep. 1: o que aconteceu com o vizinho? · 2. Ep. 2: por que João saiu de casa · 3. Ep. 3: o primeiro paciente da Cida · 4. Ep. 4: quem é Dárcio Leme · 5. Ep. 5: o que a Bia fez com o noivo · 6. Ep. 6: o áudio da filha de Dandara · 7. Ep. 7: a última viagem do Geraldo · 8. Ep. 8: o que a Zefa viu · 9. Ep. 9: como o Téo ouvia o rádio.

## Extras
| Nº | Depois do ep. | Tema | Status |
|---|---|---|---|

## Resumos
- EP 1:
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
- Início do ep. 1: João faz entregas no subúrbio, DIA 0, à tarde, com a mochila térmica e o celular. Geraldo e Zefa na fazenda; Cida e Téo na cidade do interior; Bia em outra cidade.
