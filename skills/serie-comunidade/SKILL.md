---
name: "serie-comunidade"
description: "Comando para gerar as artes de engajamento de uma série lo-fi: meta da comunidade, resultado da meta e ranking de quem mais comentou (menção honrosa), a partir dos dados ou prints do usuário."
---

# /serie-comunidade

Três artes de comunidade (1080×1920, PNG) no estilo da série, geradas pelo motor lo-fi. Responda em português do Brasil.
- `/serie-comunidade meta 1000 salvamentos 18h final-b` → **meta da comunidade** (baú trancado, marcos 0/50/80/100%, prêmio).
- `/serie-comunidade resultado 460` → **resultado da meta** (porcentagem, baú trancado ou aberto, barra de progresso).
- `/serie-comunidade ranking` + prints dos comentários (ou a lista colada) → **ranking / menção honrosa** (top 10 com empates).

## Passos comuns
1. Anexe o repositório (`add_repo`: CodaxiKing / motor-lofi, access push), clone ou `git pull`; leia a bíblia da série (se houver mais de uma, use a que está em andamento).
2. Escreva o JSON em `series/<serie>/artes/<tipo>_<AAAAMMDD>.json`, gere com `python3 -m lofi.artes <json> <png>`, abra a imagem, confira (números certos, nada cortado ou sobreposto) e envie com uma linha dizendo quando postar. Commit do JSON e push. Registre metas e resultados na bíblia (seção "Comunidade").

## Meta
Campos: `{"tipo": "meta", "serie": "<serie>", "titulo": "1.000 SALVAMENTOS", "prazo": "ATÉ AS 18H", "item_nome": "CAIXA DA COMUNIDADE", "trava": "1.000", "prazo_curto": "HOJE 18H", "dentro": "<prêmio curto>", "marcos": [[0, "TRANCADA"], [50, "ACENDE"], [80, "DESTRAVA"], [100, "ABRE"]], "texto": "Se a gente bater, eu libero *o prêmio*.", "texto2": "<chamada para salvar/compartilhar>"}`.
O prêmio deve ser algo que a série pode entregar: final alternativo, extra antecipado, episódio mais cedo, bastidores. Se o usuário não disser o prêmio, mostre um cartão "Prêmio da meta?" com 3 opções tiradas da bíblia (ex.: o final que não venceu, extra antecipado, episódio mais cedo), e "Métrica?" (salvamentos · comentários · compartilhamentos) se ela não veio. **Escolhas por cartão (padrão):** em cada etapa com opções, mostre um cartão de escolha (AskUserQuestion) em vez de decidir sozinho: até 4 perguntas por cartão, 2 a 4 opções cada, a recomendada primeiro com "(Recomendado)", e o usuário sempre pode digitar outra. Junte num cartão só as decisões da mesma etapa e não pergunte o que os argumentos já responderam. Se o usuário não estiver presente (comando agendado ou sem resposta), siga com as recomendadas e diga quais foram. A métrica (salvamentos, comentários, compartilhamentos) e o número vêm dos argumentos.

## Resultado
Campos: `{"tipo": "resultado", "serie": "<serie>", "atual": 460, "meta": 1000, "unidade": "SALVAMENTOS", "verbo": "salvaram"}` (opcional `"texto"`, `"cenario"`). Bateu a meta → "CONSEGUIMOS!" e o baú aberto; senão "NÃO FOI DESSA VEZ". O número atual vem do argumento ou de um print das estatísticas (leia o print).

## Ranking (menção honrosa)
1. Fonte: prints dos comentários (TikTok/Instagram/YouTube, quantos vierem) ou uma lista colada. Nos prints, conte os comentários de cada pessoa (nome e @ como aparecem) somando todos os prints; se o usuário mandar pontos prontos, use os dele. Se não vier nada, peça os prints em uma linha.
2. Campos: `{"tipo": "ranking", "serie": "<serie>", "data": "01/11", "titulo": "OS 10 DE ONTEM", "sub": "QUEM MAIS COMENTOU · DOMINGO, 01/11", "lista": [{"nome": "...", "perfil": "@...", "pontos": 12, "time": "<opção que a pessoa votou, ex.: BARULHO>", "time_letra": "A"}], "top": 10, "texto": "Hoje ainda dá tempo. *Bora pro top 10?*"}`. Empates dividem a posição; 3 ou mais empatados na última posição vão para o quadro "EMPATADOS COM".
3. Use só nomes e @ públicos que aparecem nos comentários; nada de dados pessoais além disso.
