# Animacao

## Personagem recortado por pose

Para o acabamento ilustrado, use PNGs completos do mesmo personagem em poses
separadas, com alfa real; não divida em cabeça/braços nem substitua por um rig
genérico. A biblioteca inicial está em `series/visto-amanha/lucas_recortes_v1.json`.
Valide com `python -m lofi.recortes validar <biblioteca>`.

No formato `imagens`, `personagens[].poses` troca assets por tempo local,
`ancoras` alinha os pés e `bocas` escolhe a variante de fala da pose correta.
O exemplo `lucas_recortes_demo_v1.json` é teste visual de 12,5 s sem áudio ou
cenário, não um episódio. Para montar uma cena, gere o fundo separadamente.
A aplicação da biblioteca recusa ações, caminhadas e personagens sem recorte
específico. Gere variantes ancoradas na mesma imagem-base e preserve os PNGs
originais, o cânone e os episódios já montados.

Consulte `lofi/rig.py` e `lofi/performance.py` para poses e emoções suportadas. Priorize transições legíveis, reação antes da ação, gestos com propósito e continuidade espacial. Não anuncie rig esquelético inexistente.
