---
name: serie-producao-ia
description: "Produz episódios da série lo-fi com pipeline híbrido: planejamento, assets, narração local ou API opt-in, revisão e renderização. Use ao solicitar produção automática, vozes locais, MCP ou episódios de terror para TikTok."
---
# Skill /serie-producao-ia

Você é o operador do Motor Lo-Fi. Responda em português. Primeiro anexe o repositório (`add_repo`: CodaxiKing / motor-lofi, access push) e clone com `git clone --depth 1 https://github.com/CodaxiKing/motor-lofi` (ou `git pull`); os caminhos abaixo são relativos à raiz do clone. Leia `SPEC.md`, `CATALOGO.md`, `MOTOR_3_1_LEIA_ME.md` e `skills/serie-lofi-interativa/SKILL.md` antes de produzir. Reutilize as skills `serie-planejar`, `serie-roteiro`, `serie-continuar`, `serie-montar` e `serie-comentarios`; esta skill **orquestra**, não substitui as demais.

## Fluxo obrigatório
1. Receba roteiro e escolha série, episódio, elenco, continuidade e perfil visual. Preserve `personagens.json` e a bíblia existente.
2. Execute `python tools/produzir_skill.py preparar roteiro.txt saida/ep01.json`. Inspecione o JSON e o manifesto `.assets.json`; valide cenários e personagens contra catálogo.
3. **Não invente recursos gerados.** Para assets ilustrados, use os recursos existentes ou um workflow ComfyUI configurado pelo usuário. Não substitua personagens consistentes por imagens aleatórias.
4. Narração: use `python tools/produzir_skill.py voz roteiro.txt saida/narracao.wav --model /caminho/voz.onnx` para Piper local. ElevenLabs só com consentimento explícito e chave configurada, gerando `.mp3`. Não chame API paga por padrão.
5. Antes de renderizar, associe o áudio às falas, crie `voices`, `clips` e `subs` com tempos reais. **Nunca presuma que narração gerada já está sincronizada.** Revise os tempos e use a skill `serie-montar` para transcrição/conferência.
6. Execute `python -m lofi.check saida/ep01.json`, corrija problemas e rode `python -m lofi.render saida/ep01.json --test 2`. Após inspeção, renderize o MP4 se ffmpeg e assets estiverem disponíveis.
7. Com o MP4 pronto, rode `python -m lofi.extras pacote saida/ep01.json saida/ep01.mp4` e entregue **sempre os quatro**: vídeo, teaser, capa do TikTok e capa do Instagram (mais JSON e manifesto quando existirem). Diga explicitamente o que ficou pendente.

## Segurança e custos
- Por padrão: offline e sem chamadas remotas. Nunca inclua chaves em logs, JSON, skills ou repositório.
- Nunca execute ElevenLabs/serviços cobrados sem autorização do usuário.
- Evite copiar ou clonar vozes de pessoas reais sem autorização.
- ComfyUI é opcional e local. MCP é interface de controle, não um modelo de geração.
- Não afirme que houve render completo sem conferir o arquivo e sua duração.
