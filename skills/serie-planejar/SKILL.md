---
name: "serie-planejar"
description: "Comando para criar uma nova série interativa lo-fi: pede os dados num formulário, gera o plano e a capa e salva a bíblia da série no repositório motor-lofi do GitHub."
---

# /serie-planejar

Primeiro passo de uma série nova, sem anexar nada. Siga a skill **serie-lofi-interativa** (seções "Motor e bíblia" e "Planejamento"); as regras abaixo prevalecem.
Responda em português do Brasil.

## Padrões
Mapa da cidade em `mundo.json` (lugares, cenários de cada lugar, ligações e o que cada um carrega no início; formato de `series/dia-zero/mundo.json`) · duração por episódio: 3 a 5 minutos (no mínimo 2, sem limite máximo), com subtrama · contador "DIA X · HH:MM" · classificação "todas as idades" (sem sangue), a não ser que o usuário peça "14+".

## Coletar os dados
1. Se o usuário já escreveu os dados junto com o comando, use-os e pergunte só o que faltar.
2. Senão, faça as perguntas de escolha com AskUserQuestion (uma única chamada):
   - Quantos episódios? (5 (Recomendado) · 3 · 8 · 10)
   - Gênero? (Suspense/Terror · Mistério/Policial · Comédia/Romance · Fantasia) — o usuário pode digitar outro
   - Formato das vozes? (Com falas dos personagens (Recomendado) · 100% narrado: um narrador conta tudo, sem falas dos personagens)
   - Estilo visual? (Lo-fi desenhado à mão (Recomendado) · Lo-fi liso · Vetor sombreado: sem contorno, sombra em duas tons, roupa com bolsos e cinto · Imagens geradas no ChatGPT: você gera fundos e personagens pelos prompts que eu mando)
3. Na mesma resposta, peça em texto livre, numa lista curta: **ideia da história** (obrigatório), protagonista (nome, jeito, roupa marcante, tipo de corpo), cenário/época, elemento fixo na tela, classificação ("todas as idades" ou "14+"), duração se não for 3–5 min e, no formato 100% narrado, quem narra (um narrador de fora, em 3ª pessoa, ou o protagonista, em 1ª pessoa) (opcionais; o que ficar em branco você decide).
4. **Escolhas por cartão (padrão):** em cada etapa com opções, mostre um cartão de escolha (AskUserQuestion) em vez de decidir sozinho: até 4 perguntas por cartão, 2 a 4 opções cada, a recomendada primeiro com "(Recomendado)", e o usuário sempre pode digitar outra. Junte num cartão só as decisões da mesma etapa e não pergunte o que os argumentos já responderam. Se o usuário não estiver presente (comando agendado ou sem resposta), siga com as recomendadas e diga quais foram.
5. **Cartão 2 (depois das respostas):** se o formato for 100% narrado, "Quem narra?" (Narrador de fora, 3ª pessoa (Recomendado) · O protagonista, 1ª pessoa) e "Duração por episódio?" (3–5 min, com subtrama (Recomendado) · 2–3 min, simples · 5 min ou mais).
6. **Cartão 3 (com o plano rascunhado, antes de salvar):** "Título da série?" (3 títulos que você propõe) e "Final principal?" (2–3 ideias de verdade por trás do mistério), cada opção com uma linha de descrição; e "Gancho do ep. 1?" (3 perguntas sem resposta). Salve com o que foi escolhido.

## Entregar
1. O plano completo da série, com gancho de abertura e cor dominante por episódio.
2. A capa 1080×1920 no estilo do motor (personagens e cenário da série, título, contador "DIA 0").
3. Anexe e clone o repositório (`add_repo`: CodaxiKing / motor-lofi, access push), crie `series/<nome-curto>/biblia.md` no formato de `series/dia-zero/biblia.md` (classificação, linha `Formato: com falas` ou `Formato: 100% narrado (narrador em 3ª pessoa | <protagonista> em 1ª pessoa)`, estilo visual (linha `Estilo: lofi-desenho | lofi-liso | vetor | imagens`; no JSON vira `"style": "desenho"`, nada, `"style": "vetor"` ou planos com `"imagens"`; no estilo imagens, escreva também `Prompt de estilo: ...` na bíblia (padrão: o `ESTILO_PADRAO` de `lofi/imagens.py`, Dark Cinematic Lo-Fi Cartoon, em inglês, que segue o `MASTER_STYLE` obrigatório; só mude se o usuário pedir) e, em cada ficha do `personagens.json`, os campos em inglês `"aparencia"` (rosto, idade, cabelo, roupa e cores, em uma frase), `"ref_personagem"` (lista: frase de quem é e os traços) e `"ref_roupa"` (lista de peças); criatura também pode ganhar `"ref_negativo"`, rode `python3 -m lofi.imagens referencias series/<nome>` e entregue no chat um bloco por personagem com o prompt da **ficha de referência** (frente, 3/4 e costas, sempre no modelo padrão; rode também `python3 -m lofi.imagens folhas series/<nome>` e entregue as folhas do elenco) para o usuário gerar primeiro e anexar nas próximas imagens), cor de cada episódio, tabela de episódios com status "planejado" e coluna de placar, resumos vazios) e `series/<nome-curto>/personagens.json` com as fichas (campos de `SPEC.md`, incluindo `body`), inclua na bíblia as tabelas `## Personagens (motivação e voz)` (DESEJO, MEDO, SEGREDO e JEITO DE FALAR de cada personagem importante, inclusive o vilão) e `## Pistas` (pistas que levam às revelações e aos finais, com o episódio em que são plantadas e pagas), e faça cada pergunta A/B custar algo dos dois lados (GANHA/PERDE). Crie cenários novos no motor se a história precisar, commit e push.
4. Linha final: "Próximo passo: /serie-roteiro".