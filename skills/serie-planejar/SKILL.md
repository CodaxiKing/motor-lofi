---
name: "serie-planejar"
description: "Comando para criar uma nova série interativa lo-fi: pede os dados num formulário, gera o plano e a capa e salva a bíblia da série no repositório motor-lofi do GitHub."
---

# /serie-planejar

Primeiro passo de uma série nova, sem anexar nada. Siga a skill **serie-lofi-interativa** (seções "Motor e bíblia" e "Planejamento"); as regras abaixo prevalecem.
Responda em português do Brasil.

## Padrões
Duração por episódio 2 a 3 minutos · contador "DIA X · HH:MM" · todas as idades, sem sangue.

## Coletar os dados
1. Se o usuário já escreveu os dados junto com o comando, use-os e pergunte só o que faltar.
2. Senão, faça as perguntas de escolha com AskUserQuestion (uma única chamada):
   - Quantos episódios? (5 (Recomendado) · 3 · 8 · 10)
   - Gênero? (Suspense · Terror · Mistério · Comédia)
   - Duração por episódio? (2–3 min (Recomendado) · 1–2 min · 3–4 min)
   - Estilo do traço? (Desenhado à mão (Recomendado) · Liso)
3. Na mesma resposta, peça em texto livre, numa lista curta: **ideia da história** (obrigatório), protagonista (nome, jeito, roupa marcante, tipo de corpo), cenário/época e elemento fixo na tela (opcionais; o que ficar em branco você decide).
4. Não pergunte nada além disso. Se o usuário não estiver presente, decida e diga o que decidiu.

## Entregar
1. O plano completo da série, com gancho de abertura e cor dominante por episódio.
2. A capa 1080×1920 no estilo do motor (personagens e cenário da série, título, contador "DIA 0").
3. Anexe e clone o repositório (`add_repo`: CodaxiKing / motor-lofi, access push), crie `series/<nome-curto>/biblia.md` no formato de `series/dia-zero/biblia.md` (estilo do traço, cor de cada episódio, fichas com `body`, tabela de episódios com status "planejado", resumos vazios), crie cenários novos no motor se a história precisar, commit e push.
4. Linha final: "Próximo passo: /serie-roteiro".