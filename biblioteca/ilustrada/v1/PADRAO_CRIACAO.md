# Padrão de criação de personagens e monstros

O contrato executável do motor está em [padrao_criacao.json](padrao_criacao.json).
Novas identidades registradas no catálogo precisam passar por ele. O validador
recusa ficha incompleta, quadro repetido usado como desenho novo, imagem de outra
identidade, vista ausente, resolução insuficiente e revisão visual pendente.
O mínimo de desenhos é um piso de produção; a fluidez precisa de revisão em vídeo.

## Vistas e animações obrigatórias

As dez vistas são `frente`, `frente_direita`, `direita`, `costas_direita`,
`costas`, `costas_esquerda`, `esquerda`, `frente_esquerda`, `cima` e `baixo`.
`cima` olha de cima para baixo; `baixo` olha de baixo para cima, em direção ao teto.
Cada vista possui seus próprios arquivos e sua própria perspectiva desenhada.

| Grupo | Ações por vista | Mínimo de desenhos por ação |
|---|---|---|
| Todos | parado, andar, correr, agachar, levantar, pular | 8 |
| Todos | levantar_braco, interagir, reagir_medo, reagir_dano | 8 |
| Humanos | segurar_item | 8 |
| Monstros | espreitar, rastejar, atacar, avancar | 16 |
| Todos | parado→andar, andar→parado, andar→correr, correr→andar, correr→parado | 4 por ligação |

Agachar e levantar podem compartilhar desenhos em ordem inversa, com JSONs de ação
distintos. Esconder-se usa a postura baixa com um oclusor calibrado; não apaga o ator.
Pulo inclui preparação, impulso, voo e aterrissagem. Marque `apoio: false` no voo,
preserve a linha de chão virtual e calibre a elevação para a sombra.

Os PNGs têm corpo completo e transparência. A referência ereta deve ter ao menos
600 pixels de altura. Para closes e entrega em alta resolução, siga também
[NITIDEZ.md](NITIDEZ.md). Escala vem de `altura_m`, não da caixa da pose.
Inspecione silhueta, apoio, escala, loop, anatomia e encaixes antes de marcar a
respectiva revisão como aprovada. O validador lê essa declaração; não substitui
a avaliação visual do autor.

## Identidade dos monstros

Novos monstros ficam em `imagens/monstros/<id>/`; novos humanos em
`imagens/personagens/<id>/`. Os arquivos antigos conservam seus caminhos.
Cada JSON de ciclo declara `identidade`, `angulo` e `acao`, além do schema de
[QUADROS.md](QUADROS.md). Seus PNGs e atlas pertencem à mesma identidade.
Andar e correr também precisam de `deslocamento_corpo_ciclo`, `contatos_solo`
e marcos dos pés por quadro. Consulte [FLUIDEZ.md](FLUIDEZ.md) para o fluxo
de calibração, voz de referência, camadas e revisão por cena.

Zumbis têm pés arrastados, tronco caído, assimetria, arrancadas cambaleantes e
queda pesada. Skinwalkers têm corrida baixa, contorções, rastejo assimétrico e
bote predatório. As descrições completas ficam em `perfil_movimento` no modelo.
Um monstro novo precisa descrever a anatomia, apoios e cadência das quatro ações
exclusivas. Não reutilize o corpo humano nem só altere a velocidade do ciclo humano.

## Itens e atuação

Humanos precisam da pose `segurar_item`, com ponto `mao: [x,y]` normalizado em cada
quadro e ângulo. `items_direcionais` registra PNG e âncora dos objetos compartilhados
em `imagens/items/`: lanterna, estojo médico, rádio e chave inglesa. Inclua as vistas
de cima e para o teto. Objetos ficam separados dos corpos. Monstros não recebem
esses encaixes. Este contrato certifica os assets e pontos de encaixe; a composição
de cada interação ainda deve ser preparada e revisada na cena.

Piscar, mudar o olhar, falar e expressões de rosto exigem artes locais compatíveis
com a pose, ângulo e retrato. Para diálogo, use `bocas_locais` e áudio conforme
[ANIMACAO.md](ANIMACAO.md). Não aplique a boca frontal sobre perfil/costas nem
declare lipsync por existir um ciclo de corpo. Narração em off não aciona boca.

## Preparar, validar e integrar

Há modelos persistidos em `modelos/humano.json`, `zumbi.json`, `skinwalker.json` e
`monstro.json`. São rascunhos com campos nulos, não personagens prontos.

```bash
python -m lofi.padrao_personagens novo nina --tipo humano --saida biblioteca/ilustrada/v1/imagens/personagens/nina/personagem.json
python -m lofi.padrao_personagens novo zumbi_operario --tipo zumbi --saida biblioteca/ilustrada/v1/imagens/monstros/zumbi_operario/personagem.json
python -m lofi.padrao_personagens validar biblioteca/ilustrada/v1/imagens/monstros/zumbi_operario/personagem.json
python -m lofi.padrao_personagens auditar
python -m lofi.historias_ilustradas validar
```

Depois de produzir a arte real, preencher a ficha e aprovar as revisões, mude
`estado_producao` para `pronto`. No catálogo, registre `arquivo_ficha`, o `tipo`
(`humano` ou `criatura`), `padrao_criacao: 1` e ao menos a pose neutra transparente.
O compilador seleciona `ciclos_direcionais` e `transicoes_direcionais` pelo campo
`angulo` do ator. Novas identidades direcionais usam quadros completos; sem uma
ação explícita, usam `parado` na vista escolhida. Use `animacoes_quadros` para ações
isoladas e `movimentos` para a sequência com ligações.

```json
{"id":"nina","pose":"neutro","angulo":"costas_direita","animacao":"quadros",
 "animacoes_quadros":[{"acao":"correr","inicio":0,"fim":3,"modo":"loop"}]}
```

As cinco identidades deste checkout (Lucas, Clara, Téo, Amanhã e Mímico) são
legadas. Seus ciclos e retratos continuam disponíveis. A auditoria não afirma que
tenham todas as dez vistas. Para certificar uma delas, complete a ficha nova e
registre `padrao_criacao: 1` na entrada do catálogo, removendo a isenção legada.
