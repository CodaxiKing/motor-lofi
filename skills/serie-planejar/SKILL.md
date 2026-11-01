---
name: "serie-planejar"
description: "Comando para criar uma nova série interativa lo-fi: pede os dados num formulário, gera o plano e a capa e salva a bíblia da série no repositório motor-lofi do GitHub."
---

# /serie-planejar

Primeiro passo de uma série nova, sem anexar nada. Siga a skill **serie-lofi-interativa** (seções "Motor e bíblia" e "Planejamento"); as regras abaixo prevalecem.
Responda em português do Brasil.

## Padrões
Duração por episódio: no mínimo 2 minutos, sem limite máximo · contador "DIA X · HH:MM" · classificação "todas as idades" (sem sangue), a não ser que o usuário peça "14+".

## Coletar os dados
1. Se o usuário já escreveu os dados junto com o comando, use-os e pergunte só o que faltar.
2. Senão, faça as perguntas de escolha com AskUserQuestion (uma única chamada):
   - Quantos episódios? (5 (Recomendado) · 3 · 8 · 10)
   - Gênero? (Suspense/Terror · Mistério/Policial · Comédia/Romance · Fantasia) — o usuário pode digitar outro
   - Duração por episódio? (2–3 min (Recomendado) · 3–4 min · 4 min ou mais); nunca menos de 2 min
   - Estilo do traço? (Desenhado à mão (Recomendado) · Liso)
3. Na mesma resposta, peça em texto livre, numa lista curta: **ideia da história** (obrigatório), protagonista (nome, jeito, roupa marcante, tipo de corpo), cenário/época, elemento fixo na tela e classificação ("todas as idades" ou "14+") (opcionais; o que ficar em branco você decide).
4. Não pergunte nada além disso. Se o usuário não estiver presente, decida e diga o que decidiu.

## Entregar
1. O plano completo da série, com gancho de abertura e cor dominante por episódio.
2. A capa 1080×1920 no estilo do motor (personagens e cenário da série, título, contador "DIA 0").
3. Anexe e clone o repositório (`add_repo`: CodaxiKing / motor-lofi, access push), crie `series/<nome-curto>/biblia.md` no formato de `series/dia-zero/biblia.md` (classificação, estilo do traço, cor de cada episódio, tabela de episódios com status "planejado" e coluna de placar, resumos vazios) e `series/<nome-curto>/personagens.json` com as fichas (campos de `SPEC.md`, incluindo `body`), crie cenários novos no motor se a história precisar, commit e push.
4. Linha final: "Próximo passo: /serie-roteiro".