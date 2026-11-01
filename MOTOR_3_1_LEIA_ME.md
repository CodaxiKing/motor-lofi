# Motor Lo-Fi 3.1 — Skill de produção híbrida

Esta entrega adiciona uma **skill operacional**, um CLI de preparação, adaptadores opcionais de TTS e ComfyUI, e um servidor MCP opcional. Mantém o motor original e suas seis skills.

## Requisitos
- Para preparar episódio: dependências do projeto original (Pillow, NumPy, SciPy, ffmpeg para render).
- Para voz local: executável `piper` no PATH e modelo `.onnx` apropriado, baixado pelo usuário. A qualidade em português depende da voz instalada.
- Para voz ElevenLabs: variável de ambiente `ELEVENLABS_API_KEY` e voice ID, com custo conforme conta/plano.
- Para MCP: `pip install mcp`; execute `python -m lofi.mcp_server` e configure um cliente MCP com transporte stdio.
- Para ComfyUI: servidor local e workflow exportado em formato API JSON com marcador `__PROMPT__`.

## Exemplos
```bash
python tools/produzir_skill.py preparar examples/automatico/roteiro.txt examples/automatico/ep01.json
python tools/produzir_skill.py status examples/automatico/roteiro.txt examples/automatico/ep01.json
python tools/produzir_skill.py voz examples/automatico/roteiro.txt saida/narracao.wav --model /modelos/pt_BR.onnx
# Somente após autorização de cobrança:
python tools/produzir_skill.py voz examples/automatico/roteiro.txt saida/narracao.mp3 --provider elevenlabs --voice VOICE_ID
python -m lofi.mcp_server
python -m unittest discover -s tests -p 'test_skill31.py' -v
```

## Limites importantes
- O compilador produz JSON/manifesto; **não cria assets por IA automaticamente**.
- O adaptador ComfyUI somente **enfileira** um workflow; consultar resultado, baixar e vincular imagens requer integração adicional.
- O TTS gera arquivo de áudio, mas não configura `clips` e `subs` automaticamente; precisa de alinhamento temporal para lip-sync correto.
- MCP é opcional, não precisa de API paga para preparar episódios.
- Não há garantia de renderização completa sem ffmpeg, assets e vozes disponíveis.
