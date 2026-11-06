# Nitidez da biblioteca ilustrada

O desfoque dos closes vinha principalmente da ampliação de células pequenas dos
atlas. Reamostragem melhora as bordas, mas não recupera os detalhes ausentes.

## Arte disponível

- Lucas, Téo, Clara, Amanhã e Mímico: três retratos transparentes por personagem,
  de 1024 × 1536 pixels: neutro, medo (ameaça para Mímico) e piscando.
- Lucas: caminhada e corrida com oito desenhos completos por ciclo, em PNGs
  individuais de 627 × 627 pixels, preservando os arquivos anteriores.
- Os prompts de geração estão nos arquivos `hd_prompt_*.txt` desta pasta.
  A arte foi criada com ImageGen integrado e registrada por `tools/registrar_arte_hd.py`.

## Seleção automática

O arquivo `imagens/<personagem>/personagem.json` contém `arte_por_plano`.
Cada entrada informa `img`, `rosto` (retângulo normalizado), `cobertura` e
`poses_compativeis`. Close/detalhe consultam `close`; médio consulta `medio`.
Use `expressao: "medo"` no ator para a variante correspondente. Neutros piscam
com a variante de olhos fechados; `piscar_hd: false` desativa essa troca.

O retrato acompanha o centro e a largura do rosto no mundo. A câmera pode ajustar
o enquadramento para cobrir o corte inferior do busto, sem alterar a altura física
do personagem. Se não cobrir a tela, a imagem original permanece.

Corridas, contatos com objetos e falas ativas conservam suas artes e animações.
Os retratos atuais não têm bocas HD calibradas: para diálogo em close, é preciso
criar essa arte compatível. `usar_variantes: false` permite comparar com a fonte antiga.

## Limite de ampliação

Por padrão, a câmera limita a ampliação dos pixels do personagem a 1,25 vez.
O limite abre o enquadramento, preservando as alturas e o foco no mundo. Se a
fonte já for pequena demais na escala base, o relatório sinaliza a insuficiência;
é necessário fornecer uma imagem maior. Isso não garante detalhe nos cenários.

Configuração por cena, dentro de `imagens`:

```json
"qualidade_visual": {"max_ampliacao": 1.25, "limitar_zoom": true}
```

O compositor usa Lanczos com alfa pré-multiplicado para evitar bordas escuras.
Os ciclos aceitam `img` por frame, além de atlas com `regiao`; âncoras, referências
de escala e marcações continuam obrigatórias conforme o ciclo.

## Revisão

```powershell
python -m lofi.qualidade_visual biblioteca/ilustrada/v1/nitidez_demo_v1.json --out biblioteca/ilustrada/v1/nitidez_revisao_v1.json
python tools/preview_nitidez.py
python tools/preview_caminhada.py biblioteca/ilustrada/v1/nitidez_demo_v1.json biblioteca/ilustrada/v1/nitidez_preview_v1.mp4
```

O relatório amostra início, meio e fim das cenas e cortes declarados: não é uma
inspeção de todos os frames. Usa `preview_size` ou, na ausência, `size`; para
avaliar a entrega, configure essa resolução antes da revisão. Informa fonte,
pixels disponíveis, ampliação, zoom pedido/aplicado e motivo de eventual recusa.
A demonstração começa com dois segundos do atlas antigo sem proteção para comparação.
