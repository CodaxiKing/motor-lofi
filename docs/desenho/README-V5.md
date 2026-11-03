# Visual Asset Library V5

## Novidades
- `lofi/advanced_rig.py`: detector opcional MediaPipe Tasks PoseLandmarker com modelo `.task` fornecido pelo usuário; fallback heurístico explícito. Deformação por triângulos com `scipy.spatial.Delaunay` e Pillow (piecewise affine; **não ARAP**).
- `lofi/lipsync_pipeline.py`: execução opcional do Rhubarb instalado localmente, leitura de cues e alinhamento de recortes de voz.
- `lofi/episode_export.py`: renderização de episódios `DESENHO` diretamente para MP4 via FFmpeg, incluindo áudio único opcional; independente do renderizador original.
- `skill/SKILL.md`: fluxo operacional Claude Skill, com bíblia visual, busca de assets, prompts, validação e render.
- Corrigidas repetições de efeitos e importações em módulos da V4.

## Instalação
```bash
python install_into_motor.py /caminho/para/motor-lofi
cd /caminho/para/motor-lofi
python -m lofi.episode_export /caminho/para/episodio.json
```
A Skill pode ser copiada para `.claude/skills/motor-lofi-desenho/SKILL.md` no checkout.

## Dependências
Obrigatórias: Pillow, NumPy, SciPy e FFmpeg (motor original). Opcionais: `mediapipe` e arquivo de modelo `pose_landmarker.task` para detecção por IA; Rhubarb executável para gerar mouth cues. Não há downloads automáticos nem chamadas pagas.

## Observações
O exportador independente renderiza as cenas ilustradas, mas não replica todos os efeitos, legendas e mixagem do motor original. A integração com o `Episode.scene_frame` é opt-in e requer testes no checkout real. A deformação triangulada não preserva volume/rigidez como ARAP. Rig gerado automaticamente exige revisão humana.
