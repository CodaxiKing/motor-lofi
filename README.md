# Motor lo-fi · séries interativas em vídeo vertical

Motor de animação para séries curtas no formato **"escolha o caminho"** (Reels, TikTok, Shorts): no fim de cada episódio o público vota **A ou B** e a história segue pelo caminho escolhido.

Tudo é desenhado e animado por código, no estilo lo-fi flat: personagens expressivos com boca sincronizada à voz, câmera de cinema, cenários com luz e clima, legendas palavra por palavra, efeitos sonoros e trilha. Serve para qualquer gênero: suspense, terror, mistério, comédia, romance, fantasia, policial.

![Personagens prontos](examples/guarda_roupa.png)
![Bocas e atuação](examples/atuacao.png)

---

## Como usar no Claude (o jeito fácil)

O repositório vem com **8 skills** (pasta [`skills/`](skills/)) que fazem todo o trabalho por comando. Você não precisa mexer no código.

| Comando | O que você manda | O que recebe |
|---|---|---|
| `/serie-planejar` | A ideia da história | Plano da série, capa, bíblia e personagens travados |
| `/serie-roteiro` | Nada (o voto é escolhido por toque) | Roteiro de 2 min ou mais + narração pronta para o ElevenLabs |
| `/serie-continuar 2 B` | Só o comando (episódio que terminou + opção vencedora) | Voto registrado + roteiro do próximo episódio |
| `/serie-montar` | Um áudio por personagem | Vídeo, teaser de 15 s, capa do TikTok, capa do Instagram e legenda do post |
| `/motor-lofi-studio` | A história (texto) | Série iniciada, roteiro técnico, manifesto de assets e relatório de qualidade (Studio 4.0) |
| `/serie-producao-ia` | Roteiro + perfil visual (voz local ou API, só com autorização) | Episódio preparado, narração e render |
| `/serie-comentarios` | Comentários dos seguidores (texto ou print) e, depois, a voz | Personagem respondendo os comentários, com o cartão do comentário na tela (30–75 s) |

### Ciclo de cada episódio
1. A votação fecha → `/serie-continuar 2 B`
2. Gere as vozes no ElevenLabs (um arquivo por personagem, com o nome do personagem: `roberta.mp3`, `rafa.mp3`)
3. `/serie-montar` com os áudios
4. Poste o vídeo e o teaser e fixe o comentário "Vota aqui: A ou B 👇"

### Instalar em outra conta do Claude
1. Baixe os `.zip` da pasta [`skills/`](skills/) e adicione cada um nas configurações de skills da conta (comece pela `serie-lofi-interativa`).
2. Conecte o GitHub na conta. Se este repositório for privado, a conta conectada precisa ter acesso a ele.
3. Pronto: as duas contas enxergam o mesmo motor e o mesmo progresso das séries.

---


### Novidades: planejamento narrativo, ganchos e experimentos

O projeto inclui três skills complementares para o Claude: `video-script`
(ideias, roteiro e revisão por métricas), `canvas-design` (capas e direção de arte)
e `skill-creator` (melhoria e avaliação das próprias skills). Elas são acionadas
conforme a etapa pela `motor-lofi-studio`, com adaptações ao cânone, ao estilo
lo-fi e ao mínimo de 90 segundos. Os ZIPs instaláveis estão em `skills/`;
consulte [`skills/LEIA-ME.md`](skills/LEIA-ME.md) para instalação e origem.

```bash
python tools/skills_motor.py listar
python tools/skills_motor.py contexto series/visto-amanha --episode 2
python tools/skills_motor.py contexto series/visto-amanha --episode 2 --skill canvas-design
python tools/skills_motor.py evals
```

Esses comandos produzem contexto ou casos de avaliação; a escrita e o design
criativos continuam sendo feitos pelo Claude. Benchmarks que executam o Claude
dependem do runtime correspondente e não são simulados por testes locais.
- **Plano antes das cenas:** cada episódio nasce de uma cadeia causal validada (`python3 -m lofi.narrativa serie series/<serie>`),
  com os dois caminhos do voto, memória da série (o que é fato, suspeita ou segredo até o ep. N) e esqueleto do roteiro.
- **Três aberturas por episódio** (`python3 -m lofi.ganchos gerar|escolher`): estratégias diferentes, duração estimada, notas
  explicáveis, e a troca do gancho sem mexer no resto do roteiro.
- **Experimentos com métricas reais** (`python3 -m lofi.experimentos`): importação manual do painel das redes, comparação justa
  (mesma plataforma, amostra e tempo mínimos) e recomendações que dizem quando ainda não há evidência.
- **Validador narrativo** com correção localizada e **arquivos travados** (`protegidos.json`) para episódios que não podem mudar.

### Novidades: cenário generativo, ao pé da letra
- **Toda cena é o que o áudio diz:** `python3 -m lofi.literal series/<serie>/epNN.json` confere cada frase da narração
  contra o que aparece na tela e, com `--aplicar`, abre o close do objeto citado no segundo exato ("uma lata... duas...
  três" vira 1, 2 e 3 latas na prateleira; "o vidro explode" mostra o vidro quebrado).
- **Cenário generativo:** cenários montados por descrição (paredes, piso, luz e móveis) com **35 ambientes novos**
  (cozinha, quarto, banheiro, porão, sótão, velório, farmácia, hortifrúti, cemitério, estrada, acampamento, praia...)
  e **~135 móveis e objetos**. Veja [`examples/ambientes.jpg`](examples/ambientes.jpg) e o [SPEC.md](SPEC.md).

### Novidades: continuidade e produção
- **Mapa da cidade** (`series/<serie>/mundo.json`): o roteiro só anda por caminhos que existem, começa onde o episódio anterior
  parou, o relógio nunca volta e os objetos só aparecem se alguém carrega (`python3 -m lofi.continuidade ...`).
- **Travelling:** o cenário passa de lado, de frente ou por trás, com chegada automática ao destino.
- **Prévia do roteiro** antes de gravar: `python3 -m lofi.previa series/<serie>/epNN_roteiro.md`.
- **Render com cache:** ajustes refazem só os planos alterados.
- **Fim de temporada:** `python3 -m lofi.extras escolhas series/<serie>` (todas as escolhas do público).

## Continuidade: os personagens não mudam

Cada série tem uma pasta própria em `series/<nome-da-serie>/`:

| Arquivo | Para que serve |
|---|---|
| `biblia.md` | Mapa da série: mistério, finais, regras, cor de cada episódio, tabela de episódios (status e votos) e resumos |
| `personagens.json` | **Fichas travadas** de roupa, cabelo, pele e acessórios de cada personagem |
| `epNN_roteiro.md` | Roteiro completo do episódio NN |
| `epNN.json` | Roteiro técnico usado na montagem |

O `personagens.json` **sempre vence**: se um roteiro tentar redefinir um personagem, o motor ignora e usa a ficha travada, e o verificador avisa. Para mudar o visual de alguém de propósito (ex.: troca de roupa numa nova temporada), edite só esse arquivo.

Séries no repositório: [`series/dia-zero`](series/dia-zero/) (apocalipse zumbi, 5 episódios).

---

## O que o motor faz

**Personagens**
- 4 vistas (frente, costas, lado e **3/4**) e ações: andar, correr, pular, esconder, abrir porta, cair, rastejar, tremer
- 10 emoções com sobrancelhas, olhos e boca: neutro, medo, choque, raiva, tristeza, determinação, alegria, desconfiança, choro (com lágrimas) e ofegante
- Boca sincronizada com a voz **em formatos de vogal** (A, E, O, U, M), piscar, respiração, cabelo e cachecol balançando
- **Gestos automáticos pela fala**: aponta quando diz "ali", mão no peito em "eu", acena no "sim", balança a cabeça no "não", cabeça baixa em "desculpa"
- **Interações**: mãos dadas andando, carregar alguém no colo, abraço, empurrão
- Corpos: criança, idoso, alto, gordo, magro · objetos na mão: rádio, lanterna, celular, chave, mochila
- **Guarda-roupa** completo: 8 tons de pele, 14 tipos de roupa, saia/shorts/calça, 12 cabelos, barba e bigode, 12 chapéus, 12 acessórios, capa e modo fantasma
- **29 personagens prontos**: Roberta, Rafa, Lia, zumbis variados, soldado, detetive, cientista, estudantes, executivos, médica, policial, roqueiro, avós, criança, bruxa, rainha, chef, cowboy, fantasma, DJ, pirata

**Cenários (74, sendo 35 gerados por descrição)** — apartamento, entrada, corredor, rua, rua de madrugada, vista da janela, escada, telhado, ponte, rádio, hospital, mercado, metrô, escola, delegacia, posto de gasolina, floresta, interior de carro, esgoto, igreja
- Camadas em paralaxe, desfoque de fundo, névoa, chuva forte ou fraca, neve, nuvens, poças com ondinhas, hora do dia
- Detalhes vivos: ventilador girando, TV com chiado, cortina ao vento, sirene, limpador de para-brisa, velas

**Luz e câmera**
- Breu de verdade iluminado só pela lanterna, sombras projetadas na parede, relâmpagos, brilho nas luzes
- Close no rosto, plano por cima do ombro, travelling, foco seletivo, câmera na mão, vertigo, câmera lenta, tremor nos sustos
- Planos de detalhe: maçaneta girando, olho (pupila dilatando), celular, chave, relógio
- Transições: corte, whip, flash, fade, zoom, glitch · traço "desenhado à mão" e cor por episódio

**Narrativa e acabamento**
- Gancho de 2 s antes do título, "Anteriormente em…" com cenas do episódio anterior, carimbo "A MAIORIA ESCOLHEU", tela dividida A/B
- Legendas estilo Reels (palavra por palavra, destaque amarelo) que desviam do rosto dos personagens
- 25 efeitos sonoros sintetizados, ambiente automático por cenário e trilha de suspense
- **Eco por ambiente**: a voz reverbera na escada e na igreja, fica abafada dentro do carro

**Qualidade**
- Partes do corpo do personagem certo: quando a cena mostra só a mão (rádio, chave, maçaneta, celular), a manga e a pele são as da ficha de quem age, e a legenda desvia do braço
- Mapa de cada cenário com chão e marcas de posição (porta, sofá, parapeito…): os personagens são posicionados por nome e o verificador acusa quem fica flutuando ou dentro da parede ([`examples/mapa_cenarios.png`](examples/mapa_cenarios.png))
- Validador de roteiro (gancho, 12+ cenas, mínimo 2 min, A/B) e verificador de montagem (legenda no rosto, personagem cortado, ficha desrespeitada)
- Folha de revisão para um revisor independente aprovar antes do render
- Casos de teste das skills em [`tests/evals.json`](tests/evals.json)

**Extras automáticos** (`python3 -m lofi.extras pacote`): teaser de 15 s para Stories, capa do TikTok e capa do Instagram de cada episódio (texto dentro da área segura de cada rede) e compilação da temporada em 16:9 para o YouTube, com capítulos.

---

## Uso direto pelo terminal

### Perfis de duração para experimentar formatos

O validador aceita perfis editoriais (não são limites das redes):

| Perfil | Duração | Mínimo de cenas |
|---|---|---|
| `curto` | 90–120 s | 9 |
| `medio` | 120–180 s | 12 |
| `longo` | 180–300 s | 18 |
| `tradicional` | 90 s ou mais | 12 |

Use `python tests/validar_roteiro.py serie/ep01_roteiro.md --perfil curto`,
ou adicione `Perfil de duração: curto` ao roteiro ou à `biblia.md` da série.
A prioridade é: argumento do terminal, roteiro, bíblia, padrão `tradicional`.
Sem configuração, usa-se o perfil `tradicional`. Todos os perfis exigem pelo menos 90 segundos. Os novos perfis dispensam
os avisos de complexidade de episódios tradicionais (18 cenas, subtramas e quatro lugares);
as demais verificações de qualidade continuam ativas.

Nos novos perfis, escreva os tempos no formato `## CENA 1 — 0 s a 10 s`.
A duração é o último fim de cena, incluindo o tempo inicial reservado ao gancho e à abertura.
Tempos mencionados em falas e efeitos sonoros não contam como duração do vídeo.
O perfil valida o planejamento; ele não corta nem acelera automaticamente o vídeo.

### Encenação e identidade dos personagens

#### Modo opcional de histórias ilustradas

O módulo `lofi.historias_ilustradas` usa `biblioteca/ilustrada/v1/catalogo.json`
para montar histórias com personagens e cenários já produzidos. Ele coexiste
com o rig, o modo imagens e os recortes individuais. Nada migra automaticamente.

```bash
python -m lofi.historias_ilustradas listar
python -m lofi.historias_ilustradas validar
python tools/studio.py ilustrado producoes/ilustradas/minha-historia --apoio clara --vilao mimico
python -m lofi.historias_ilustradas compilar historia.json producoes/ilustradas/outra-historia
```

A biblioteca contém Lucas, Clara, Téo, Lucas de Amanhã e o Mímico (criatura
ficcional inspirada em skinwalker), além de entrada, corredor e floresta.
O inventário mostra as poses realmente disponíveis; o compilador recusa poses,
personagens e cenários ausentes e transições sem ligação no mapa da biblioteca.
As novas artes foram geradas com `image_gen`, preservando o alfa dos recortes;
os prompts e a origem ficam junto do catálogo.

`criar`/`studio ilustrado` usa um arco local de imitação e gera um rascunho editável.
`--ideia` registra um brief, não o interpreta semanticamente. A skill
`motor-lofi-ilustrado` usa o catálogo e `video-script` para escrever planos originais;
`compilar` monta esses planos. O exemplo independente está em
`producoes/ilustradas/a-voz-la-fora-v1/`, sem alterar o cânone de Visto Amanhã.

Cada produção inclui `historia.json`, `roteiro.md`, `narracao.txt`, `episodio.json`,
`qualidade.json` e `dramaturgia.md`. A duração mínima é 90 s; narração gravada,
alinhamento e legendas são etapas posteriores. A arte é reutilizada por referência,
não baixada nem gerada novamente para cada episódio. Se mover o projeto, mantenha
a relação entre a pasta de produções e a biblioteca, ou recompile o plano.

#### Personagem ilustrado recortado por pose

O primeiro pacote visual de Lucas, baseado na referência fornecida pelo usuário,
fica em `series/visto-amanha/lucas_recortes_v1.json`: cinco PNGs transparentes em
`imagens/`, sem substituir fichas ou episódios publicados. As poses são parado/atento,
celular, falando, medo e alcançar maçaneta. Os prompts usados estão em
`lucas_recortes_prompts_v1.md`; cada variante usa a mesma imagem-base para reduzir deriva.

```bash
python -m lofi.recortes validar series/visto-amanha/lucas_recortes_v1.json
python -m lofi.render series/visto-amanha/lucas_recortes_demo_v1.json --test 1 4 6 9 11
```

A demonstração é um teste visual de 12,5 s, sem áudio ou cenário, não um episódio.
No modo `imagens`, `personagens[].poses` aceita `[[segundo_local, nome_imagem], ...]`.
As âncoras por imagem alinham os pés sem modificar os PNGs; `bocas` mapeia a
variante de fala adequada a cada pose. Uma pose parada não é ciclo de caminhada.

Para aplicar os recortes a uma cópia de um episódio técnico, registre os fundos
ilustrados em `fundos` na biblioteca e execute
`python -m lofi.recortes aplicar episodio.json biblioteca.json saida.json`.
A saída deve ficar ao lado da biblioteca, preservando os caminhos de `imagens/`.
O comando recusa personagens, movimentos ou ações sem arte correspondente.

A geração agora prepara participantes, sujeito, alvo, ação e estado físico antes
da composição de câmera. Nomes de personagens conhecidos, aliases e nomes simples
em ações ou falas são reconhecidos. Pronomes usam antecedentes compatíveis; uma
ambiguidade gera aviso e impede aplicar a ação física sem sujeito definido.
Nos roteiros estruturados, use `PERSONAGENS: lia, rafa`, `SUJEITO: lia`,
`DESTINATÁRIO: rafa`, `CENÁRIO: entrada` e `MARCA: porta` para direção explícita.

As marcas do ambiente posicionam o elenco no chão; caminhadas usam trajetos,
ações com objetos têm antecipação, contato e reação, e os ouvintes olham para
quem fala. Abraços e empurrões entre participantes recebem aproximação e reação.
Portas, objetos nas mãos, entregas e objetos abandonados persistem entre planos.
Os objetos suportados são chave, mochila, lanterna, celular e rádio. O estado
atual representa uma unidade por tipo; múltiplos objetos iguais exigem direção
manual. A resolução linguística é baseada em regras, não compreensão geral:
revise frases com várias ações e use sujeitos explícitos nos casos complexos.

Um `elenco.json` opcional define identidade, relações e movimento:

```json
{
  "lia": {
    "nome": "Lia", "genero": "feminino", "aliases": ["doutora"],
    "relacoes": {"irma": "ana"}, "movimento": "contido",
    "visual": {"body": "tall", "face_shape": "square", "head_scale": 0.98}
  },
  "ana": {"nome": "Ana", "genero": "feminino", "movimento": "energico"}
}
```

Movimentos disponíveis: `equilibrado`, `contido`, `energico`, `cauteloso`.
Eles alteram postura, ritmo, respiração, balanço e atraso de reação. Identidades
novas são estáveis por nome; presets existentes são preservados e a aparência
de `personagens.json` sempre vence. Cabeça, tronco e formato de rosto podem ser
personalizados além do guarda-roupa e dos corpos já existentes.

Na geração por arquivo, `elenco.json` é procurado ao lado do roteiro;
`--cast elenco.json` seleciona outro arquivo. No Studio, fica na pasta da série.
Cada personagem recebe uma folha de referência local com quatro vistas e cinco
expressões, na pasta `<episodio>.references`. `referencia` no elenco aponta para
uma imagem existente que deve ser preservada. O manifesto registra essa referência,
a identidade e os requisitos por plano para geração externa; não chama APIs de
imagem automaticamente. As folhas produzidas localmente usam o próprio rig.

```bash
python -m lofi.personagens criar elenco.json ana bruno
python -m lofi.personagens folha elenco.json ana ana_referencia.png
python tools/gerar_episodio.py historia.md episodio.json --cast elenco.json --duration-profile curto --duration 90
```

O estado físico final fica em `<episodio>.state.json`. Para outra produção por
arquivo, passe `--state episodio.state.json`. No Studio, o estado só entra na
continuidade ao executar `confirmar`, junto da revisão explícita do episódio.

### Critérios dramáticos no planejamento

O planejamento, o validador narrativo e o Studio compartilham a revisão de:
causa/consequência, conflito pessoal, intenção das falas, revelações preparadas,
escolhas com custo e entrega de uma resposta com abertura de outra pergunta.
O relatório aponta o critério, a cena, a linha do cabeçalho e uma sugestão localizada.
Ao gerar por arquivo ou pelo Studio, também é salvo `<episodio>.dramaturgia.md`.

Veja o contrato completo em [`examples/roteiro_dramatico.md`](examples/roteiro_dramatico.md).
As cenas usam `ACONTECIMENTO`, `CONSEQUÊNCIA` e `CAUSA: CENA n — justificativa`;
`CONFLITO PESSOAL` registra personagem, desejo e custo. `FALA` registra falante,
alvo, intenção, objetivo e texto dito. `PLANTA`, `REVELA` e `PAGA` usam o mesmo
identificador em ordem; `RESOLVE` e `ABRE` registram perguntas diferentes.
Cada opção A/B registra `GANHA`, `PERDE`, `MOTIVO` e, opcionalmente, `ORIGEM: CENA n`.

```bash
python -m lofi.dramaturgia examples/roteiro_dramatico.md --markdown
```

Os campos documentam decisões do autor; não comprovam a qualidade literária por
contagem de palavras. Informações ausentes geram avisos, referências impossíveis
geram erros e episódios finais (`ENCERRAMENTO: final` ou `FIM` em linha própria)
dispensam novo suspense e votação, mas ainda precisam entregar uma resposta.
Roteiros antigos continuam legíveis e recebem pendências do que não documentam.
As anotações não viram falas ou planos na compilação de roteiros estruturados.

Nos planos JSON, `causa` pode ser um número de cena ou `{cena, texto}`;
`conflito_pessoal` contém `personagem`, `desejo` e `custo`;
`falas` contém objetos com `personagem`, `texto`, `alvo`, `intencao` e `objetivo`.
As listas `planta`, `revela`, `paga`, `resolve` e `abre` aceitam `{id, texto}`
(identificadores antigos continuam aceitos). Cada ramo A/B é revisado isoladamente.
O fechamento explícito do plano guarda as pistas em `memoria.pistas` para episódios
futuros; o Studio continua sem alterar a memória durante a geração de rascunhos.

### Produção integrada, narrativa, atuação e aberturas

Studio e os comandos `gerar_episodio.py`, `produzir.py` e `produzir_skill.py preparar`
aceitam `--duration-profile curto|medio|longo|tradicional`, `--duration` e
`--opening A|B|C`. `--profile` continua sendo o estilo visual.
Na geração por arquivo, a prioridade é argumento, linha no texto, bíblia e tradicional.
No Studio, o padrão de `serie.json` também pode definir o perfil; o texto do episódio
vence esse padrão. A duração escolhida é registrada no JSON e no plano de áudio;
a revisão e o verificador pré-render usam as mesmas faixas.

```bash
python tools/studio.py iniciar series/minha-serie --title "Minha série" --duration-profile curto
python tools/studio.py planejar historia.txt series/minha-serie --duration 90 --opening A
python tools/studio.py abertura series/minha-serie/episodios/ep01.json series/minha-serie/episodios/ep01_b.json --opening B
python tools/studio.py revisar series/minha-serie/episodios/ep01_b.json
```

O compilador separa frases em planos, identifica evidências de objetivo, obstáculo,
virada e consequência, e aponta lacunas e escolhas sem custo no relatório.
Isso é uma análise por regras, que exige revisão editorial; não inventa acontecimentos
nem garante qualidade narrativa. Escreva as alternativas em linhas `A) ...` e `B) ...`,
incluindo os riscos. Quando há espaço na cena final, elas viram uma tela de votação.

A atuação aplica deslocamento a quem anda/corre, poses para abrir portas e empurrar,
reações de medo/tristeza/raiva e objetos suportados nas ações de pegar/segurar.
A biblioteca continua limitada às ações e aos objetos existentes no rig.

Cada episódio inclui `opening_variants`: três alternativas com texto, primeiro quadro,
ação, legenda, som e plano técnico. A troca ocupa os três segundos iniciais e preserva
o corpo após essa janela e a duração total. As imagens vêm do próprio episódio;
revise as alternativas para evitar antecipar uma revelação. A exportação cria outro
JSON no mesmo diretório e recusa sobrescrita. Gere/revise a abertura antes de sincronizar
as vozes: as variantes não sintetizam nem realinham áudio existente.

O Studio salva `.openings.json`, manifesto e relatório de qualidade, e registra as
variantes em `experimentos.json`. O comando existente `python -m lofi.experimentos publicar`
registra a publicação feita fora do motor, incluindo uma cópia completa da variante;
edições posteriores não alteram essa cópia. Texto insuficiente para sustentar a duração
gera aviso de revisão: o motor não produz falas novas para preencher o tempo.
`compile_story` sem perfil permanece disponível como utilitário de baixo nível para
prévias e testes curtos; os produtores por arquivo adotam os perfis de episódio.

```bash
pip install --break-system-packages pillow numpy scipy          # obrigatório, + ffmpeg
pip install --break-system-packages soundfile sherpa-onnx       # opcional (sem eles: scipy no áudio e transcrição só com tempos)

python3 -m lofi.transcribe roberta.mp3 rafa.mp3                # tempo de cada fala (baixa o Whisper na 1ª vez)
python3 tests/validar_roteiro.py series/dia-zero/ep03_roteiro.md   # confere o roteiro
python3 -m lofi.check  series/dia-zero/ep03.json               # verificador + folha _revisao.png
python3 -m lofi.render series/dia-zero/ep03.json --test 2 9    # quadros de teste
python3 -m lofi.render series/dia-zero/ep03.json --jobs 2      # vídeo final (~3,5 s por s de vídeo: episódio de 3 min ≈ 10–11 min)
python3 -m lofi.extras teaser series/dia-zero/ep03.json ep03.mp4
python3 -m lofi.extras pacote series/dia-zero/ep03.json ep03.mp4   # teaser + capa TikTok + capa Instagram
python3 -m lofi.extras capa   series/dia-zero/ep03.json
python3 -m lofi.extras temporada temporada.mp4 "DIA ZERO" ep1.mp4 ep2.mp4 ep3.mp4
```

O formato completo do roteiro técnico (planos, câmera, atores, guarda-roupa, sons) está em **[SPEC.md](SPEC.md)**; a lista de todos os nomes aceitos pelo motor está em **[CATALOGO.md](CATALOGO.md)**, gerada do código. Exemplos: [`examples/exemplo_roteiro.json`](examples/exemplo_roteiro.json) e [`examples/demo3/demo3.json`](examples/demo3/demo3.json).

## Estrutura

```
lofi/          código do motor
  rig.py         personagens (poses, emoções, guarda-roupa)
  scenes.py      cenários
  cenario_gen.py cenário generativo (ambientes por descrição e closes de objeto)
  moveis.py      biblioteca de móveis e objetos
  literal.py     confere/conserta: cada frase da narração com a sua imagem
  narrativa.py   plano da história, memória da série e continuidade entre cenas e episódios
  ganchos.py     três aberturas por episódio, avaliação e troca do gancho
  experimentos.py variantes publicadas, métricas reais, comparação e recomendações
  validador_narrativo.py  revisão da história com correção localizada
  protecao.py    arquivos travados (cânone que o motor não pode alterar)
  render.py      montagem do vídeo a partir do roteiro
  fx.py          chuva, luz, câmera, transições, estilo
  particles.py   poeira, lanterna, bafo de frio, hordas
  detail.py      planos de detalhe
  audio.py       efeitos sonoros e mixagem
  text.py        contador e legendas
  check.py       verificador de montagem
  extras.py      teaser, capa e temporada
  transcribe.py  transcrição das vozes
  catalogo.py    lista de nomes aceitos (gera o CATALOGO.md)
  mapa.py        chão e marcas de posição de cada cenário
  partes.py      mão e braço do personagem em closes de objeto
  wavio.py       leitura/escrita de áudio sem dependências extras
series/        uma pasta por série (bíblia, personagens travados, roteiros)
skills/        as 5 skills do Claude (SKILL.md + .zip gerado)
tools/         empacotar_skills.py (gera os .zip das skills)
.github/       CI: confere zips, catálogo, validador e verificador a cada push
tests/         validador de roteiro e casos de teste
examples/      roteiros de exemplo e imagens
```

Áudios e vídeos não são versionados.


A biblioteca guarda os recortes em `biblioteca/ilustrada/v1/imagens/<personagem>/`:
`lucas`, `clara`, `teo`, `amanha` e `mimico`. O catálogo aponta para cada pose.
São 15 poses, mais 4 microposes: piscadas neutras de Lucas, Clara e Téo,
e uma inclinação de cabeça de Lucas. Os fundos continuam em `imagens/`.

Escolha uma vez por série:
```
python tools/studio.py modo series/<serie> --render-mode illustrated_library
python tools/studio.py planejar historia.json series/<serie> --episode 1
```
A skill lê a escolha persistida. `--render-mode rig` no episódio permite usar
o modo anterior; o comando `modo` muda o padrão da série. A biblioteca usa
respiração e balanço discretos. Só poses com variante compatível piscam.
