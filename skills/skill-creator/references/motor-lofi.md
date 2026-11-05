# Skill Creator no Motor Lo-Fi

Use para criar, revisar ou avaliar skills do projeto, quando isso for solicitado.
Não execute otimizações de descrição ou benchmarks durante toda produção de episódio.
O escopo padrão é `skills/` deste checkout; preserve licenças e `UPSTREAM.json`.

## Avaliações compatíveis

`python tools/skills_motor.py evals --skill-name serie-lofi-interativa` converte
`tests/evals.json` para o schema `evals/evals.json` deste pacote. O resultado
contém prompts e expectativas, não pontuações nem execuções já realizadas.
Use `skills/motor-lofi-studio/evals/evals.json` para os casos de integração.

Compare baseline e mudança com os mesmos prompts, cânone e arquivos de entrada,
em uma pasta temporária isolada. Não use episódios protegidos como saída.
Verifique invariantes com as ferramentas reais do motor: duração mínima de 90 s,
nomes aceitos, continuidade, preservação de fichas e existência dos arquivos.
Julgue diálogo, ritmo e direção visual qualitativamente; passar no validador não
comprova qualidade artística ou aumento de visualizações.

Os scripts upstream de trigger/otimização usam o executável `claude` e um
ambiente compatível. Verifique a disponibilidade antes de executá-los. Sem esse
runtime, valide os pacotes e execute avaliações manuais no Claude; marque o
benchmark comportamental como não executado. Não fabrique tempos, custos ou notas.
Não troque automaticamente para outro provedor nem invoque uma API paga.

Ao terminar, rode `python tools/empacotar_skills.py` e
`python tools/empacotar_skills.py --checar`. Preserve o formato dos ZIPs do Claude
e reempacote somente os pacotes cujo conteúdo mudou. Se houver agente independente
disponível e autorizado, use-o para revisão; caso contrário, faça revisão sequencial.
