# Motor Lo-Fi 3.0 — atualização incremental verificável

Este pacote inclui o projeto original e todas as atualizações anteriores, além de:

- `lofi/performance.py`: planejador de atuação (gestos, caminhada, corrida, emoções), aproveitando poses do rig existente.
- `lofi/autodirect.py`: injeta planos de atuação nos personagens do JSON técnico.
- `lofi/asset_plan.py`: gera manifesto de cenários/personagens para uso com geradores externos.
- `tools/produzir.py`: CLI offline que compila história e manifesto em uma etapa.
- `tests/test_pipeline3.py`: testes de regressão dos recursos adicionados.

## Uso

```bash
python3 tools/produzir.py exemplos/roteiro.txt saida/ep01.json --profile horror_illustrated
python3 -m lofi.render saida/ep01.json --test 2
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/smoke.py
```

Os arquivos JSON são editáveis manualmente. O manifesto é uma lista de prompts, **não imagens geradas**. O motor não gera voz, imagens por IA ou MP4 final a partir de texto sem fornecer recursos de áudio. Não inclui interface web, rig de malha/deformação nem publicação automática no TikTok. O teste `--test` produz quadros de pré-visualização, não um vídeo final. A integração com provedores externos depende de configuração e credenciais.
