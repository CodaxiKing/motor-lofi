---
name: motor-lofi-ilustrado
description: Criar histórias interativas narradas e planos usando personagens recortados por pose e cenários da biblioteca ilustrada do Motor Lo-Fi, ou ampliar essa biblioteca mantendo os outros modos de produção disponíveis.
---

# Histórias com biblioteca ilustrada

Use o checkout do Motor Lo-Fi existente. Este é um modo opcional: não migre o
rig, o modo imagens ou as séries existentes sem pedido do usuário.

## História original a partir dos assets

1. Rode `python -m lofi.historias_ilustradas listar` e leia
   `biblioteca/ilustrada/v1/catalogo.json`. Identifique elenco, poses, fundos e ligações.
2. Consulte `skills/video-script/SKILL.md` e sua integração `motor-lofi.md` para
   escrever a história solicitada. O catálogo define o que pode aparecer, não o
   enredo inteiro. Preserve as escolhas do usuário, o cânone da série e o mínimo de 90 s.
3. Escreva uma história nova no schema de
   `producoes/ilustradas/a-voz-la-fora-v1/historia.json`: título, perfil, duração,
   narrador, cenas numeradas e escolhas A/B. Cada cena define cenário, narração,
   acontecimento, consequência, causa e personagens `{id, pose, pos}`.
   `altura`, `chao` e `espelhar` permitem ajustar o blocking ao fundo.
4. Planeje causa/consequência, conflito pessoal, pista/revelação/pagamento e
   entrega de uma resposta. Cada alternativa tem benefício, perda e motivo.
   Este compilador é interativo e narrado; use os fluxos existentes quando o
   formato pedido não couber nesse contrato.
5. Compile em pasta nova com
   `python -m lofi.historias_ilustradas compilar historia.json producoes/ilustradas/<nome>`.
   Revise roteiro, narração, relatório e quadros do render antes de gravar a voz.

`python tools/studio.py ilustrado producoes/ilustradas/<nome>` gera um rascunho
pelo arco local de imitação. É um ponto de partida editável, não um LLM nem um
intérprete de ideias arbitrárias. `--ideia` no módulo registra o brief para revisão;
para uma história original, escreva o plano conforme as etapas acima.

## Biblioteca e arte

Gere assets novos somente quando necessários e autorizados: um PNG transparente
por pose/personagem e fundos separados, sem pessoas ou texto. Use o mesmo personagem
base para as variantes. Preserve as imagens antigas; adicione nomes/versionamentos
novos ao catálogo. Valide com `python -m lofi.historias_ilustradas validar`.
Um recorte de corrida é uma pose, não um ciclo completo de caminhada.

Não substitua poses ausentes por uma figura genérica nem declare animação de boca,
porta ou objeto quando a arte disponível não a representa. Posicione as mãos de
acordo com a geometria do cenário e confira em quadros reais.

## Entrega

O pacote inclui história JSON, roteiro, texto de narração, episódio técnico e
revisão dramática. A biblioteca é referenciada por caminho, sem regerar arte por
episódio. Configure voz, clips e legendas reais antes do render final.
Não declare áudio, vídeo final ou sincronização produzidos pelo plano estático.
Não escreva no episódio publicado da série Visto Amanhã ao criar uma demonstração.

## Escolha persistente e movimentos

Leia `serie.json.render_mode` antes de planejar. Ausência significa `rig`.
Quando o usuário escolher personagens recortados, salve uma vez com
`python tools/studio.py modo series/<serie> --render-mode illustrated_library`.
Para voltar: `--render-mode rig`. Não confunda este campo com paleta visual
nem com `--mode hybrid`. Cada episódio pode sobrescrever `--render-mode`.
No modo ilustrado, escreva `historia.json` estruturada e execute
`python tools/studio.py planejar historia.json series/<serie> --episode N`.
A criação e revisão de histórias continua sendo trabalho criativo da skill.

O renderer aplica `respirar` e `balanco_corpo` com intensidade configurável
(0 desliga). `piscadas` mapeia cada imagem à sua variante de olhos fechados;
não use uma pose neutra para piscar durante outra ação. `olhares` permite uma
transição suave para uma variante de cabeça inclinada no mesmo canvas.
A biblioteca inclui piscadas neutras de Lucas, Téo e Clara e uma inclinação
de Lucas. São variantes completas: não há rig facial nem movimento livre
de cabeça independente. Não animar boca pela narração em off.
