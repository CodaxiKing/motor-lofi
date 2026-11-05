# Skills da série lo-fi interativa

Skills usadas com o motor. Para usar em outra conta do Claude, adicione cada uma nas configurações de skills
da conta (envie o arquivo `.zip` de cada pasta ou o `SKILL.md`).

| Skill | Para que serve |
|---|---|
| `serie-lofi-interativa` | Manual base: estilo, recursos do motor e formato do roteiro (instale primeiro) |
| `serie-planejar` | `/serie-planejar` — cria uma série nova e a bíblia |
| `serie-roteiro` | `/serie-roteiro` — roteiro do próximo episódio, voto por toque |
| `serie-continuar` | `/serie-continuar 2 B` — registra o voto e gera o próximo roteiro |
| `serie-montar` | `/serie-montar` + áudios — monta o vídeo, teaser, capa e legenda |
| `motor-lofi-studio` | Skill principal do Studio 4.0: orquestra as outras, da história ao roteiro técnico e à revisão (`tools/studio.py`) |
| `serie-producao-ia` | Produção híbrida: planejamento automático, assets, narração local (Piper) ou ElevenLabs só com autorização, revisão e render |
| `serie-comentarios` | `/serie-comentarios` + comentários (texto ou print) → roteiro de respostas; com os áudios → vídeo |
| `video-script` | Ideias, aberturas, roteiro e revisão com métricas reais; adaptada ao mínimo de 90 s e ao cânone da série |
| `canvas-design` | Capas, pôsteres e direção de arte estática, preservando o estilo e as referências do elenco |
| `motor-lofi-ilustrado` | Histórias narradas com personagens recortados por pose, fundos reutilizáveis e elenco da biblioteca ilustrada |
| `skill-creator` | Criar, revisar e avaliar skills do motor, separando testes locais de avaliação comportamental |

As três especialidades têm ZIPs próprios. Instale-as junto de `motor-lofi-studio`
e `serie-lofi-interativa`. Elas não são plugins de renderização: o Claude segue
suas instruções e usa os comandos existentes do motor. Na sessão atual, o checkout
permite ler os arquivos diretamente; a descoberta como skill depende da instalação
na conta do Claude. Em Codex, a instalação local não altera as skills globais.

`python tools/skills_motor.py listar` mostra os caminhos. `contexto` exporta o
brief de roteiro/arte; `evals` adapta os casos existentes para o schema do
skill-creator. Veja a referência `references/motor-lofi.md` de cada pacote.
Os arquivos `UPSTREAM.json` registram repositório, commit e adaptações locais.
Licenças, scripts, referências e fontes originais estão dentro de cada pacote.
Para atualizar as cópias, compare primeiro com o commit registrado e preserve as
adaptações; não substitua as pastas indiscriminadamente.

## Requisitos na outra conta
- Acesso a este repositório no GitHub (`CodaxiKing/motor-lofi`): conecte o GitHub na outra conta. Se o repositório for privado,
  a conta conectada precisa ter permissão nele (convide-a como colaboradora ou deixe o repositório público).
- As skills apontam para `https://github.com/CodaxiKing/motor-lofi`. Se você copiar o repositório para outro lugar,
  troque esse endereço dentro dos arquivos `SKILL.md`.
