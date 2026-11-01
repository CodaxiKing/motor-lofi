---
name: "serie-roteiro"
description: "Comando para gerar o roteiro do próximo episódio de uma série lo-fi interativa a partir da bíblia no GitHub, perguntando o voto por toque, já com a narração para o ElevenLabs."
---

# /serie-roteiro

Gera o roteiro do próximo episódio sem anexar nada nem colar mapa. Siga a skill **serie-lofi-interativa** (seções "Motor e bíblia" e "Roteiro"); as regras abaixo prevalecem. Para quem já sabe o voto, o atalho é /serie-continuar.
Responda em português do Brasil.

## Dados
1. Anexe e clone o repositório (`add_repo`: CodaxiKing / motor-lofi, access push) ou `git pull`; leia `series/*/biblia.md`. Se houver mais de uma série, pergunte qual (AskUserQuestion).
2. Episódio: o primeiro da tabela com status "planejado".
3. Pergunte o voto com AskUserQuestion usando as duas opções do episódio anterior registradas na bíblia. Se o usuário já disse o voto, não pergunte. No episódio 1 não há voto. Se o usuário informar o placar (ex.: 62% ou 340x210), registre também.

## Regras
- No mínimo 2 minutos, sem limite máximo; 12 cenas ou mais, de 6 a 14 s, pelo menos 3 momentos de tensão.
- Estrutura: gancho (0–2 s) → "Anteriormente em…" (a partir do ep. 2) → abertura com carimbo do voto → consequência da escolha → algo novo e estranho → plano de detalhe + susto → revelação com close → escalada → pergunta A/B → "CONTINUA NO EPISÓDIO X". Último episódio: desfecho conforme os finais e escolhas, "FIM".
- Use os recursos do motor: vista 3/4, ações (correr, pular, esconder, abrir porta, cair), breu com lanterna, sombras na parede, clima e hora, câmera na mão, vertigo, câmera lenta, cor do episódio.
- **Enquadramento perto:** cada cena diz no PLANO se é médio (1 personagem), conjunto (2 ou mais) ou close; aberto só para situar um lugar ou mostrar algo do cenário (no máximo 2 ou 3 por episódio).
- **Movimento:** quando alguém anda ou corre por um trajeto, escreva PLANO: `travelling` (o cenário passa: postes, prédios, portas) e uma cena curta de chegada.
- **Continuidade:** começa onde o episódio anterior terminou (`mundo.json`) e só anda por ligações do mapa da cidade; relógio só para frente; objetos só se alguém carrega (`PEGA:`/`LARGA:`). Sem pulos de lugar. Toda mudança de lugar tem `LIGAÇÃO:` (como eles chegam lá) e, se der, uma cena de passagem; corte para outro lugar sem os personagens é `INSERÇÃO:`. Objetos combinam com o lugar: `radio` só em casa, `radio_carro` no carro, `radio_portatil` fora; `chave` com `"onde": "carro"` é a ignição. Se faltar um cenário de passagem, crie no motor.
- Mantenha as consequências das escolhas anteriores registradas na bíblia e respeite a classificação da série.
- Use só nomes de cenário, som, pose, emoção e personagem que estão em `CATALOGO.md` ou em `personagens.json`.

## Entregar
Tudo **escrito na própria resposta do chat** (não só como arquivo anexado): o usuário lê e copia direto daqui. A narração vai em blocos de código, um por personagem, prontos para colar no ElevenLabs.
1. Roteiro completo por cena.
2. Narração para o ElevenLabs v3: um bloco por personagem (nome no título), tags em inglês, dica de voz; versão CapCut. **As falas do ElevenLabs vão na resposta do chat, sempre:** um bloco de código por personagem (nome e dica de voz em cima do bloco, fora dele), só com as falas e as tags em inglês, na ordem do episódio, para o usuário copiar e colar direto. Não basta deixar no arquivo do roteiro.
3. As duas opções finais e o que acontece em cada uma.
4. Salve `series/<serie>/epNN_roteiro.md`, rode `python3 tests/validar_roteiro.py` (`--final` no último) e corrija até não haver ERRO; rode o revisor de continuidade (Agent) e a prévia (`python3 -m lofi.previa ...`, envie a imagem) e grave o fim com `python3 -m lofi.continuidade fechar ...`; registre o voto e o status "roteiro" na bíblia, commit e push.
5. Linha final: "Próximo passo: gere um áudio por personagem no ElevenLabs e use /serie-montar com os áudios".