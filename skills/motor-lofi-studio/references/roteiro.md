# Roteiro

Use `skills/video-script/SKILL.md` com `references/motor-lofi.md` para o trabalho
criativo. Gere contexto com `python tools/skills_motor.py contexto series/<serie> --episode N`.
O perfil escolhido tem mínimo de 90 s; os dados retornados não são um roteiro pronto.

Defina gancho inicial, progressão de tensão, personagens, conflito, revelação e escolha A/B. Separe fatos narrados de sugestões visuais. Não invente continuidade. Evite frases excessivamente longas para legendas.

## Planejamento, ganchos e validação narrativa (lofi/narrativa.py, lofi/ganchos.py, lofi/validador_narrativo.py)
1. Plano antes das cenas: `series/<serie>/planos/epNN.json` com a cadeia causal e os dois caminhos do voto; `python3 -m lofi.narrativa serie series/<serie>`.
2. Memória da série em `memoria.json`: fato, suspeita ou desconhecido, com o episódio em que pode ser revelado; pendências com prazo.
3. Três ganchos por episódio (`python3 -m lofi.ganchos gerar|escolher`), sempre de cenas comuns aos dois caminhos e sem entregar o que o episódio revela.
4. Experimentos e métricas reais em `experimentos.json` (`python3 -m lofi.experimentos`); sem dados, sem conclusão.
5. Validador narrativo e correção localizada: `python3 -m lofi.validador_narrativo <roteiro> [--corrigir]`.

