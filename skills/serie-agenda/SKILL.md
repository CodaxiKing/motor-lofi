---
name: "serie-agenda"
description: "Comando para gerar a arte de agenda/maratona de uma série lo-fi (1080x1920): data, episódios já no ar, o próximo com horário e chamada para seguir o perfil."
---

# /serie-agenda

Gera a arte de agenda (ou maratona) da série para Stories/feed, no estilo da série, com o motor lo-fi do GitHub. Responda em português do Brasil.
Exemplos: `/serie-agenda` · `/serie-agenda maratona hoje 15h30 19h` · `/serie-agenda dia-zero ep5 18h extra 21h @meuperfil`.

## Passos
1. Anexe o repositório (`add_repo`: CodaxiKing / motor-lofi, access push), clone ou `git pull`; leia `series/*/biblia.md` (se houver mais de uma série e o argumento não disser, use a que tem episódio em andamento).
2. Monte a lista a partir da bíblia: episódios "montado" recentes = `"status": "no_ar"`; o próximo (roteiro/montado ainda não postado) = `"status": "proximo"` com `"hora"`; os seguintes e os extras pendentes com `"hora"`. Horários, data e @perfil vêm dos argumentos; o que faltar, pergunte num cartão (AskUserQuestion), junto com "Título da arte?" (MARATONA · HOJE TEM · O FINAL, conforme o momento) e "Selo?" (TEMPORADA 1 · O FINAL · EP. X). **Escolhas por cartão (padrão):** em cada etapa com opções, mostre um cartão de escolha (AskUserQuestion) em vez de decidir sozinho: até 4 perguntas por cartão, 2 a 4 opções cada, a recomendada primeiro com "(Recomendado)", e o usuário sempre pode digitar outra. Junte num cartão só as decisões da mesma etapa e não pergunte o que os argumentos já responderam. Se o usuário não estiver presente (comando agendado ou sem resposta), siga com as recomendadas e diga quais foram. A data padrão é hoje ("HOJE · SEGUNDA 02/11"). O @perfil fica salvo na bíblia (linha "Perfil:") para as próximas vezes.
3. Escreva `series/<serie>/artes/agenda_<AAAAMMDD>.json`:
   `{"tipo": "agenda", "serie": "<serie>", "cenario": "<cenário marcante da série>", "data": "HOJE · SEGUNDA 02/11", "titulo": "MARATONA" (ou "HOJE TEM"), "selo": "TEMPORADA 1" (ou "O FINAL"), "sub": "3 EPISÓDIOS EM UM DIA", "canto_esq": "<título da série>", "canto_dir": "<contador da série, ex.: DIA 5 · 05:59>", "itens": [{"ep": 4, "titulo": "...", "status": "no_ar"}, {"ep": 5, "titulo": "...", "hora": "18H", "status": "proximo"}, {"rotulo": "EXTRA", "titulo": "...", "hora": "21H"}], "perfil": "@perfil", "chamada": "ATIVA AS NOTIFICAÇÕES E SEGUE"}` (até 4 itens; títulos em caixa alta, curtos).
4. Gere: `python3 -m lofi.artes series/<serie>/artes/agenda_<data>.json series/<serie>/artes/agenda_<data>.png`. Abra a imagem e confira (texto cortado, sobreposição, horário certo); ajuste e gere de novo se precisar.
5. Envie a imagem com uma linha dizendo onde postar (Stories e feed, fixar nos destaques) e faça commit do JSON (sem o PNG) e push.
