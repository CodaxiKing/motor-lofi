# Motor lo-fi

Motor de animação para séries interativas em vídeo vertical (9:16), estilo lo-fi, "escolha o caminho".
Personagens expressivos com boca sincronizada, câmera de cinema, legendas palavra por palavra, efeitos e trilha, tudo gerado por código.

## Instalação
```
pip install --break-system-packages pillow numpy scipy soundfile sherpa-onnx
# ffmpeg é necessário
```

## Uso
```
python3 -m lofi.transcribe roberta.mp3 rafa.mp3              # tempos de cada fala
python3 -m lofi.render series/dia-zero/ep03.json --test 2 9   # quadros de teste
python3 -m lofi.check series/dia-zero/ep03.json                 # verificador + folha de revisão
python3 -m lofi.render series/dia-zero/ep03.json --jobs 2     # vídeo final
python3 -m lofi.extras teaser series/dia-zero/ep03.json ep03.mp4   # teaser 15 s
python3 -m lofi.extras capa series/dia-zero/ep03.json              # capa do episódio
```
Formato do roteiro e lista de recursos: [SPEC.md](SPEC.md). Exemplo: `examples/exemplo_roteiro.json`.

## Séries
Cada série fica em `series/<nome>/` com a bíblia (`biblia.md`), os roteiros (`epNN_roteiro.md`) e os roteiros técnicos (`epNN.json`).
Áudios e vídeos não são versionados.
