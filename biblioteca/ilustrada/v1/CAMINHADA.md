# Prévia de caminhada do Lucas

Teste visual curto, separado dos episódios e do catálogo estável de poses.
Quatro recortes originais com transparência estão em `imagens/lucas/`:
contato A, passagem A, contato B e passagem B. O manifesto
`lucas_caminhada_v1.json` registra arquivos, canvas, âncoras e hashes.
Os prompts estão em `caminhada_prompts_v1.json`.

O motor existente alterna `poses` por tempo e aplica `andar: [de, até]`.
Não há deformação das imagens nem geração de quadros por IA no renderer.
O GIF tem 2,4 segundos, 48 quadros e três repetições do ciclo de 0,8 s.

Para reproduzir a prévia:

```powershell
python tools/preview_caminhada.py biblioteca/ilustrada/v1/lucas_caminhada_demo_v1.json biblioteca/ilustrada/v1/lucas_caminhada_preview_v1.gif
```

É um primeiro teste com quatro poses: há mudanças de textura e de silhueta
entre gerações, e o contato dos pés ainda precisa de refinamento. Para uma
caminhada final mais suave, ampliar para oito poses, conferir a posição do
quadril e ajustar o deslocamento à distância real da passada. Não confundir
os 20 quadros por segundo do GIF com 20 desenhos diferentes por segundo.
