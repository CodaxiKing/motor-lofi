# Canvas Design no Motor Lo-Fi

Aplique esta integração antes dos padrões estéticos genéricos do upstream.
O produto é a série do usuário: preserve o estilo lo-fi/cartoon, a identidade do
elenco, a paleta e o conteúdo solicitado. Não converta a arte em outro gênero
visual para satisfazer exemplos de estética do guia original.

Use `python tools/skills_motor.py contexto series/<serie> --episode N --skill canvas-design`
para ler o brief, as fichas travadas e as referências. O brief não é uma imagem.

## Direção e entrega

- Defina a direção de arte em um `.md`: paleta, tipografia, foco e hierarquia.
  Relacione as escolhas ao conflito do episódio e às referências reais.
- Crie capa, pôster ou prancha estática em PNG ou PDF. Não substitua a animação.
  Formatos do motor: TikTok/Instagram 1080×1920 e YouTube 1280×720. Respeite o
  recorte e as áreas seguras já usadas em `lofi.capas` e `lofi.extras`.
- Consulte as fontes em `canvas-fonts` desta skill; preserve suas licenças.
  Evite downloads adicionais se o conjunto local já atender.
- Preserve geometria, rosto, roupa e acessórios das fichas. Use as folhas em
  `<episodio>.references` ou a referência indicada pelo usuário. Não altere
  `personagens.json` como consequência de produzir uma capa.
- `python -m lofi.capas <episodio.json>` pode fornecer as capas nativas como
  ponto de partida. Revise o arquivo final em tamanho real e em miniatura:
  texto legível, margens, recortes, contraste e ausência de sobreposição.
- Entregue a arte efetivamente produzida e o `.md` de direção. Informe se só o
  brief foi preparado. Serviços de imagem externos não são requisito desta skill.
