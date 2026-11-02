---
name: "serie-aviso"
description: "Comando para gerar a arte de aviso antes de um episódio pesado de uma série lo-fi: tag AVISO, frase de impacto, personagem da série em close e pergunta para o público."
---

# /serie-aviso

Gera a arte de aviso (1080×1920) com um personagem da série desenhado pelo motor lo-fi, para postar antes de um episódio forte. Responda em português do Brasil.
Exemplos: `/serie-aviso` · `/serie-aviso lia chorando "o extra de hoje é pesado"` · `/serie-aviso ep5`.

## Passos
1. Anexe o repositório (`add_repo`: CodaxiKing / motor-lofi, access push), clone ou `git pull`; leia a bíblia e o roteiro do próximo episódio (ou extra) com status "roteiro"/"montado".
2. Escolha (sem perguntar, a não ser que os argumentos digam outra coisa): o personagem central do momento mais forte do episódio, a emoção (`cry`, `fear`, `shock`, `sad`), a pose (`chest`, `scared`, `hands_up`, `idle`) e um cenário do episódio para o fundo. Escreva o título (até 6 palavras, ex.: "O EPISÓDIO DE HOJE É PESADO") e a pergunta (até 7 palavras, ex.: "VOCÊ TÁ PREPARADO PRO QUE VAI VER?"). Nada de spoiler do que acontece.
3. Escreva `series/<serie>/artes/aviso_epNN.json`:
   `{"tipo": "aviso", "serie": "<serie>", "cenario": "<cenário>", "personagem": "<nome>", "emocao": "cry", "pose": "chest", "tag": "AVISO", "titulo": "...", "pergunta": "..."}` (opcionais: `"vista"`, `"escala"` 4.2, `"cabeca_y"` 760, `"cor"`). A roupa vem de `personagens.json` da série.
4. Gere: `python3 -m lofi.artes series/<serie>/artes/aviso_epNN.json series/<serie>/artes/aviso_epNN.png`, abra a imagem e confira (rosto inteiro, título legível, pergunta sem cobrir o rosto).
5. Envie a imagem com uma linha (postar 1–2 h antes do episódio, nos Stories) e uma sugestão de legenda curta; commit do JSON e push.
