---
name: "serie-continuar"
description: "Comando curto para seguir a série lo-fi: /serie-continuar [episódio que terminou] [A ou B] registra o voto e gera o roteiro do próximo episódio sem perguntas."
---

# /serie-continuar

Atalho para avançar a série com uma linha, sem anexar nada. Exemplos:
- `/serie-continuar 2 B` → o episódio 2 terminou e a opção B venceu → gera o roteiro do episódio 3.
- `/serie-continuar B` → usa o último episódio com status "montado" na bíblia.
- `/serie-continuar 2 telhado` → aceita o nome da opção no lugar da letra.
- `/serie-continuar dia-zero 2 B` → quando houver mais de uma série.
- `/serie-continuar 2 B 62%` ou `/serie-continuar 2 B 340x210` → também registra o placar (percentual da vencedora ou votos A x B).
Responda em português do Brasil.

## O que fazer
1. Leia os argumentos: série (opcional), número do episódio que terminou (opcional), a escolha vencedora (A, B ou o nome da opção) e o placar (opcional). O número sempre se refere ao episódio cuja votação fechou; o roteiro gerado é o do seguinte.
2. Anexe o repositório (`add_repo`: CodaxiKing / motor-lofi, access push), clone ou `git pull`, e leia `series/*/biblia.md`. Se houver mais de uma série e o argumento não disser qual, use a que tem episódio "montado" aguardando voto; se ainda houver dúvida, pergunte.
3. Confira a escolha com a pergunta registrada na bíblia para aquele episódio. Se a letra ou o nome não baterem com nenhuma opção, ou se o episódio pedido for o último da série, avise em uma linha e pare. Não faça nenhuma outra pergunta.
4. Registre o voto (e o placar, se veio) na tabela da bíblia e escreva o roteiro do próximo episódio seguindo a skill **serie-lofi-interativa** (seção 2: gancho, "Anteriormente em…", carimbo, 12 cenas ou mais, no mínimo 2 min sem limite máximo com planos de detalhe, ações, luz e clima do motor, consequências das escolhas anteriores, cor do episódio). **Continuidade:** a história segue de onde o episódio anterior parou (`fim` do episódio anterior em `mundo.json`: lugar, dia/hora e o que cada um carrega), anda só por ligações do mapa da cidade, o relógio nunca volta e nunca pula de lugar: cada mudança tem uma linha `LIGAÇÃO:` e, se der, uma cena de passagem (ex.: `entrada_metro` entre a rua e o metrô); cortes para outro lugar são `INSERÇÃO:`; objetos combinam com o lugar (no carro, `radio_carro`; fora de casa, `radio_portatil`). Se faltar um cenário de passagem, crie no motor. Corridas e caminhadas por um trajeto usam PLANO `travelling` (o cenário passa). Enquadramento perto: PLANO médio (1 personagem), conjunto (2 ou mais) ou close; aberto só para situar (no máximo 2 ou 3 por episódio).
5. Se o próximo episódio for o último, escreva o desfecho conforme os finais da bíblia e todas as escolhas registradas, terminando com "FIM" (sem pergunta A/B).
6. Salve `series/<serie>/epNN_roteiro.md` e rode `python3 tests/validar_roteiro.py series/<serie>/epNN_roteiro.md` (`--final` no último): ele também confere o mapa da cidade (`mundo.json`), o relógio e os objetos. Corrija até não haver ERRO. Depois: **revisor de continuidade** (Agent com o roteiro, o fim do episódio anterior e as regras; corrija o que for real), **prévia** (`python3 -m lofi.previa ...`, confira e envie a imagem ao usuário) e `python3 -m lofi.continuidade fechar ...` para gravar como o episódio termina.
7. Entregue **escrito na própria resposta do chat** (não só como arquivo; o arquivo vai junto, mas o usuário lê e copia daqui): roteiro por cena; **narração para o ElevenLabs v3** com um bloco por personagem (nome no título, tags em inglês, dica de voz); versão CapCut; as duas opções finais e o que acontece em cada uma.
8. Marque o episódio como "roteiro" na bíblia, commit e push.
9. Linha final: "Próximo passo: gere um áudio por personagem no ElevenLabs e use /serie-montar com os áudios".

**As falas do ElevenLabs vão na resposta do chat, sempre:** um bloco de código por personagem (nome e dica de voz em cima do bloco, fora dele), só com as falas e as tags em inglês, na ordem do episódio, para o usuário copiar e colar direto. Não basta deixar no arquivo do roteiro.
