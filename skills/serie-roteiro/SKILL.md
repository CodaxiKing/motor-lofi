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
- 2 a 3 minutos, 12 a 20 cenas de 6 a 14 s, pelo menos 3 momentos de tensão.
- Estrutura: gancho (0–2 s) → "Anteriormente em…" (a partir do ep. 2) → abertura com carimbo do voto → consequência da escolha → algo novo e estranho → plano de detalhe + susto → revelação com close → escalada → pergunta A/B → "CONTINUA NO EPISÓDIO X". Último episódio: desfecho conforme os finais e escolhas, "FIM".
- Use os recursos do motor: vista 3/4, ações (correr, pular, esconder, abrir porta, cair), breu com lanterna, sombras na parede, clima e hora, câmera na mão, vertigo, câmera lenta, cor do episódio.
- Mantenha as consequências das escolhas anteriores registradas na bíblia e respeite a classificação da série.
- Use só nomes de cenário, som, pose, emoção e personagem que estão em `CATALOGO.md` ou em `personagens.json`.

## Entregar
1. Roteiro completo por cena.
2. Narração para o ElevenLabs v3: um bloco por personagem (nome no título), tags em inglês, dica de voz; versão CapCut.
3. As duas opções finais e o que acontece em cada uma.
4. Salve `series/<serie>/epNN_roteiro.md`, rode `python3 tests/validar_roteiro.py` (`--final` no último) e corrija até não haver ERRO; registre o voto e o status "roteiro" na bíblia, commit e push.
5. Linha final: "Próximo passo: gere um áudio por personagem no ElevenLabs e use /serie-montar com os áudios".