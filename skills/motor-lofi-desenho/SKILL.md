---
name: motor-lofi-desenho
description: Planejar e renderizar séries ilustradas com assets reutilizáveis no motor-lofi.
---
# Motor-lofi · modo DESENHO

## Quando usar
Quando o usuário pedir um episódio de série ilustrada, storyboard, prompts de imagens ou animação com personagens e cenários em PNG.

## Procedimento obrigatório
1. Ler `SPEC.md` do checkout e verificar se `lofi/drawing_mode.py` está instalado. Não alterar episódios vetoriais.
2. Criar bíblia visual com estilo, proporções, paleta, continuidade de roupas e cenário. Registrar identificadores consistentes de personagens.
3. Dividir o roteiro em shots com `start`, `end`, `image_scene`, câmera, efeitos e movimentos.
4. Consultar `VisualAssetLibrary` e `storyboard_planner.plan_episode` antes de pedir imagens novas.
5. Para imagens faltantes, produzir prompts específicos de imagem, incluindo referência de estilo, enquadramento, transparência para cutouts e lista de variantes faciais. O Claude **não deve fingir que gerou as imagens**.
6. Usar camadas quando personagens, objetos ou iluminação precisam mover-se separadamente. Usar imagem inteira quando apenas câmera e efeitos são necessários.
7. Para face, separar olhos, pupilas, sobrancelhas e bocas A-H. `mouth_cues_file` recebe JSON do Rhubarb; alinhar tempos do áudio ao plano. Não inventar lipsync a partir do texto.
8. Para corpo, executar `python -m lofi.auto_rig personagem.png`; se houver modelo MediaPipe local, usar `lofi.advanced_rig.detect_pose`. Revisar pontos manualmente. Deformação disponível é piecewise affine, **não ARAP**.
9. Validar um quadro no início/meio/fim do shot; renderizar com `python -m lofi.render episodio.json --test 3 0` ou `python -m lofi.episode_export episodio.json` (modo independente).
10. Checar imagem cortada, transparência, continuidade, timing, legendas, áudio, qualidade e proporção antes de exportar o episódio.

## Contrato JSON mínimo
```json
{"visual_mode":"DESENHO","fps":24,"size":[1080,1920],"total":3,"shots":[{"start":0,"end":3,"image_scene":{"layers":[{"path":"fundo.png","z":0}],"camera":{"zoom":[1,1.08]},"effects":[{"type":"flicker","rate":2,"strength":0.2}]}}]}
```

## Limites
Sem imagens de entrada, produzir plano e prompts, não vídeo final. Não assumir que a integração GitHub permite push. A inferência automática do rig depende de um modelo local opcional; sem ele é heurística.
