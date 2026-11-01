# Motor Lo-Fi 4.0 — Skill Studio (pacote consolidado)

Esta versão mantém **todo o motor e as skills anteriores**, adicionando a skill `skills/motor-lofi-studio/SKILL.md` e a CLI `tools/studio.py`.

## Comece aqui

```bash
python tools/studio.py ambiente
python tools/studio.py iniciar series/arquivo-zero --title "Arquivo Zero"
python tools/studio.py planejar roteiro.txt series/arquivo-zero --episode 1 --mode hybrid
python tools/studio.py revisar series/arquivo-zero/episodios/ep01.json
```

Após revisar e aprovar os fatos da história:

```bash
python tools/studio.py confirmar series/arquivo-zero --episode 1 --fact "O rádio emitiu três batidas" --choice B
```

A skill orquestra as outras skills e **não depende** de MCP, ComfyUI ou instalação local de TTS. A saída automática é um **rascunho técnico JSON** com manifesto e relatório de qualidade, não um MP4 com voz gerada. Para MP4, ainda são necessários assets, áudio e ferramentas de render. Não usar API paga sem aprovação.

## Limites atuais
- Planejamento de enquadramentos e atuação usa heurísticas existentes; não é compreensão cinematográfica completa por LLM.
- Memória da série é mantida em JSON e atualizada explicitamente, sem deduzir fatos automaticamente.
- Relatório estático não substitui inspeção visual ou render completo.
- Imagens e vozes dependem de ferramentas externas opcionais.
- Testes não comprovam renderização de vídeo final.
