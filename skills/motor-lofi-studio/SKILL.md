---
name: motor-lofi-studio
description: Orquestra séries de animação 2D vertical de suspense, da história ao roteiro técnico e à revisão, usando o Motor Lo-Fi existente; independente de MCP, ComfyUI e TTS local obrigatório.
---
# Motor Lo-Fi Studio 4.0 — skill principal

## Quando ativar
Pedidos de criação/continuação de série, episódio, direção, atuação, cenários, narração, escolhas A/B, render ou auditoria de qualidade. **É uma skill que usa o motor existente, não um serviço de geração autônomo.**

## Regras essenciais
0. Anexar o repositório à sessão (`add_repo`: owner `CodaxiKing`, repo `motor-lofi`, access `push`) e clonar com `git clone --depth 1 https://github.com/CodaxiKing/motor-lofi` (ou `git pull` se já existir); todos os caminhos abaixo são relativos à raiz desse clone.
1. Ler `README.md`, `SPEC.md`, `CATALOGO.md` e consultar `skills/serie-lofi-interativa/SKILL.md`; chamar as outras skills conforme a etapa.
2. Consultar em `skills/motor-lofi-studio/references/` os arquivos `roteiro.md`, `direcao.md`, `animacao.md`, `audio.md`, `continuidade.md`, `qualidade.md`, `ferramentas.md` e `tiktok.md` apenas quando relevantes.
3. Verificar ambiente com `python tools/studio.py ambiente`; ferramentas externas e MCP são **opcionais**. Não exigir ComfyUI nem voz local.
4. Iniciar série com `python tools/studio.py iniciar series/minha-serie --title 'Minha Série'`; ler a bíblia e **não sobrescrever fichas existentes**.
5. Preparar texto UTF-8 e rodar `python tools/studio.py planejar roteiro.txt series/minha-serie --episode 1 --mode hybrid`.
6. Revisar `.json`, `.assets.json`, `.quality.json`. Verificar que cenas e personagens são válidos. Fazer ajustes manuais no JSON quando necessário.
7. Só usar geração externa de imagem/voz se a ferramenta realmente estiver acessível e autorizada. Nunca declarar gerado o que é apenas manifesto/prompt. Para APIs cobradas, pedir aprovação explícita antes da chamada.
8. Para áudio, criar arquivos reais e mapear `voices`, `clips`, `subs` com tempos aferidos. Sem voz disponível, entregar pacote de produção com pendência explícita.
9. Validar com `python -m lofi.check ...`, pré-visualizar com `python -m lofi.render ... --test 2`, e renderizar MP4 somente em ambiente com dependências; verificar existência, duração e reprodução.
10. Atualizar memória **após aprovação** com `python tools/studio.py confirmar ...`; registrar fatos e ramificações sem inventar acontecimentos.

## Modos
- `automatic`: gerar plano inicial com defaults; validar e sinalizar limites.
- `hybrid`: plano inicial + revisão/ajustes do usuário.
- `professional`: JSON editável com controle manual. Nenhum modo pressupõe geração real de voz/imagem.

## Entrega e integridade
Entregar somente arquivos efetivamente produzidos. Indicar separadamente `planejado`, `gerado`, `validado` e `renderizado`. Nunca chamar o plano JSON de vídeo final. Não incluir credenciais no repositório. Nunca sobrescrever episódio existente sem confirmação. Preferir renderização vertical 9:16 e escolhas A/B quando fizerem sentido.
