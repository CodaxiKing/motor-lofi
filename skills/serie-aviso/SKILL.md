---
name: "serie-aviso"
description: "Comando para gerar a arte de aviso antes de um episódio pesado de uma série lo-fi: tag AVISO, frase de impacto, personagem da série em close e pergunta para o público."
---

# /serie-aviso

Gera a arte de aviso (1080×1920) com um personagem da série desenhado pelo motor lo-fi, para postar antes de um episódio forte. Responda em português do Brasil.
Exemplos: `/serie-aviso` · `/serie-aviso O que aconteceu com a Lia? 15:00` · `/serie-aviso lia chorando "o extra de hoje é pesado"` · `/serie-aviso ep5`.
**Texto do usuário manda:** se os argumentos trazem uma frase, ela é o título da arte, exatamente como veio (em caixa alta), e **não entra nenhum outro texto** (sem pergunta e sem frase inventada). Um horário nos argumentos (ex.: `15:00`) vira a tag `AVISO · HOJE 15H`.

## Passos
1. Anexe o repositório (`add_repo`: CodaxiKing / motor-lofi, access push), clone ou `git pull`; leia a bíblia e o roteiro do próximo episódio (ou extra) com status "roteiro"/"montado".
2. **Escolhas por cartão (padrão):** em cada etapa com opções, mostre um cartão de escolha (AskUserQuestion) em vez de decidir sozinho: até 4 perguntas por cartão, 2 a 4 opções cada, a recomendada primeiro com "(Recomendado)", e o usuário sempre pode digitar outra. Junte num cartão só as decisões da mesma etapa e não pergunte o que os argumentos já responderam. Se o usuário não estiver presente (comando agendado ou sem resposta), siga com as recomendadas e diga quais foram. Cartão do aviso: "Personagem?" (2–3 do momento mais forte, o central recomendado), "Emoção?" (`cry`, `fear`, `shock`, `sad`, a que combina recomendada), "Fundo?" (2–3 cenários do episódio) e, só sem frase do usuário, "Título?" (3 opções de até 6 palavras). Recomendações: o personagem central do momento mais forte do episódio, a emoção (`cry`, `fear`, `shock`, `sad`), a pose (`chest`, `scared`, `hands_up`, `idle`) e um cenário do episódio para o fundo. Só quando o usuário não mandar frase: escreva o título (até 6 palavras, ex.: "O EPISÓDIO DE HOJE É PESADO") e a pergunta (até 7 palavras, ex.: "VOCÊ TÁ PREPARADO PRO QUE VAI VER?"). Nada de spoiler do que acontece.
3. Escreva `series/<serie>/artes/aviso_epNN.json`:
   `{"tipo": "aviso", "serie": "<serie>", "cenario": "<cenário>", "personagem": "<nome>", "emocao": "cry", "pose": "chest", "tag": "AVISO", "titulo": "...", "pergunta": "..."}` (com frase do usuário: `"titulo": "<frase dele>"` e `"pergunta": ""`; opcionais: `"vista"`, `"escala"` 4.2, `"cabeca_y"` 840, `"cor"`). A roupa vem de `personagens.json` da série.
4. Gere: `python3 -m lofi.artes series/<serie>/artes/aviso_epNN.json series/<serie>/artes/aviso_epNN.png`, abra a imagem e confira (rosto inteiro, título legível, pergunta sem cobrir o rosto).
5. Envie a imagem com uma linha (postar 1–2 h antes do episódio, nos Stories) e uma sugestão de legenda curta; commit do JSON e push.
