---
name: motor-lofi-studio
description: Orquestra séries de animação 2D vertical de suspense, da história ao roteiro técnico e à revisão, usando o Motor Lo-Fi existente; independente de MCP, ComfyUI e TTS local obrigatório.
---
# Motor Lo-Fi Studio 4.0 — skill principal

Para o tipo Crônicas, selecione `--profile cronicas` ao iniciar a série: isso
persiste biblioteca Crônicas e modo ilustrado. Leia `biblioteca/cronicas/v1/LEIA-ME.md`,
`ROTEIRO.md` e `EDICAO.md`. Preserve a linguagem da referência com histórias e
cenários originais. O catálogo herda direção de câmera, HUD e abertura situacional.
O HUD da Crônicas mantém apenas o horário HH:MM, sem recursos, missão ou atalhos.
As poses atuais são estáticas; use prévia visual enquanto as animações estiverem pendentes.

No modo biblioteca ilustrada, siga também `biblioteca/ilustrada/v1/NITIDEZ.md`.
Use as variantes por enquadramento e revise a ampliação na resolução de entrega
com `python -m lofi.qualidade_visual spec.json --out nitidez.json`. A troca de arte
deve preservar ação, expressão, objetos e fala; solicite arte compatível quando
o relatório indicar que a fonte não tem pixels suficientes.

## Especialidades integradas

Use o checkout existente como raiz de trabalho. As três especialidades estão em
`skills/` e têm ZIPs próprios para o Claude. Se não estiverem instaladas como
skills na sessão, leia seus arquivos no repositório; não bloqueie o trabalho.
As adaptações `references/motor-lofi.md` de cada pacote prevalecem sobre padrões
genéricos para o formato, a duração e a identidade desta série.

| Etapa | Skill | Entrada e saída |
|---|---|---|
| Ideias, roteiro, gancho e análise de publicação | `skills/video-script/SKILL.md` | Contexto da série e métricas reais → roteiro por cena, aberturas e hipóteses |
| Capas, pôsteres e direção de arte estática | `skills/canvas-design/SKILL.md` | Bíblia, elenco e referências → PNG/PDF real e direção de arte `.md` |
| Criar, melhorar ou avaliar skills, quando solicitado | `skills/skill-creator/SKILL.md` | Casos de avaliação → comparação e revisão da skill, com resultados medidos |

Execute `python tools/skills_motor.py listar` para conferir os pacotes.
`python tools/skills_motor.py contexto series/<serie> --episode N` prepara o
brief de roteiro; `--skill canvas-design` prepara o brief visual.
O motor prepara dados e valida arquivos; o Claude usa as skills para o trabalho
criativo. Nunca apresente o brief como roteiro ou imagem já gerados.

O perfil da série/episódio tem mínimo de **90 segundos**, prevalecendo sobre
recomendações antigas de duração. Preserve `personagens.json`, cânone e voto;
revise dramaturgia, encenação, referências, estado físico e áudio antes do render.
Para manter a skill, consulte os casos em `evals/evals.json`. Testes locais não
equivalem a um benchmark comportamental do Claude.

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
- Para histórias com recortes e fundos já gerados, use a especialidade opcional
  `skills/motor-lofi-ilustrado/SKILL.md`. O catálogo fica em `biblioteca/ilustrada/v1/`.
  O comando `python tools/studio.py ilustrado <pasta-nova>` prepara um rascunho;
  os modos abaixo e as séries existentes continuam disponíveis.
- `automatic`: gerar plano inicial com defaults; validar e sinalizar limites.
- `hybrid`: plano inicial + revisão/ajustes do usuário.
- `professional`: JSON editável com controle manual. Nenhum modo pressupõe geração real de voz/imagem.

## Entrega e integridade
Quando o pedido for gerar o vídeo, a entrega padrão é **vídeo em pé + vídeo deitado para o YouTube (`python -m lofi.render ep.json --deitado --jobs 2`) + capas do TikTok, Instagram e YouTube** (`python -m lofi.extras pacote ep.json ep.mp4`). Entregar somente arquivos efetivamente produzidos. Indicar separadamente `planejado`, `gerado`, `validado` e `renderizado`. Nunca chamar o plano JSON de vídeo final. Não incluir credenciais no repositório. Nunca sobrescrever episódio existente sem confirmação. Preferir renderização vertical 9:16 e escolhas A/B quando fizerem sentido.

## Escolha persistente e movimentos

Leia `serie.json.render_mode` antes de planejar. Ausência significa `rig`.
Quando o usuário escolher personagens recortados, salve uma vez com
`python tools/studio.py modo series/<serie> --render-mode illustrated_library`.
Para voltar: `--render-mode rig`. Não confunda este campo com paleta visual
nem com `--mode hybrid`. Cada episódio pode sobrescrever `--render-mode`.
No modo ilustrado, escreva `historia.json` estruturada e execute
`python tools/studio.py planejar historia.json series/<serie> --episode N`.
A criação e revisão de histórias continua sendo trabalho criativo da skill.

O renderer aplica `respirar` e `balanco_corpo` com intensidade configurável
(0 desliga). `piscadas` mapeia cada imagem à sua variante de olhos fechados;
não use uma pose neutra para piscar durante outra ação. `olhares` permite uma
transição suave para uma variante de cabeça inclinada no mesmo canvas.
A biblioteca inclui piscadas neutras de Lucas, Téo e Clara e uma inclinação
de Lucas. São variantes completas: não há rig facial nem movimento livre
de cabeça independente. Não animar boca pela narração em off.


## Composição e proporção do elenco

No modo ilustrado, use os mapas de `catalogo.json.cenarios` para chão,
profundidade e espaço disponível. Leia `biblioteca/ilustrada/v1/COMPOSICAO.md`.
A composição automática padroniza a altura visível por referência neutra,
reserva espaço para todas as poses e produz `composicao_relatorio`.
Personagens da mesma profundidade usam escala física consistente; diferenças
intencionais usam `escala_relativa`. Para colocar alguém na porta ou distante,
defina `zona` explicitamente. Não reduza um único personagem para fazê-lo caber.
Revise avisos e uma imagem de diagnóstico antes do vídeo. Mapas de novos fundos
precisam de calibração; o motor não reconhece perspectiva ou móveis sozinho.
Interações precisas podem usar `composicao: "manual"`, mantendo a auditoria.
O mapeamento também se aplica a JSONs existentes com `python -m lofi.composicao`.


### Orientação e portais

Verifique a orientação em toda cena ilustrada: quem está à esquerda deve
olhar à direita e quem está à direita deve olhar à esquerda. Use `orientacao:
"centro"` com a direção original do asset; não suponha que todos os PNGs têm
a mesma orientação. Exceções narrativas usam `orientacao: "manual"` explicitamente.
Para chegar de outro ambiente, use os portais calibrados do mapa e `trajeto`
com escala e chão variando por profundidade. O recorte da porta deve esconder
o corpo atrás de parede/batente até o cruzamento do limiar. Não simule caminhada
apenas deslizando a pose neutra: consulte os ciclos reais do catálogo.
Revise começo, meio, cruzamento da porta e final, incluindo os olhares do elenco.


### Altura individual e puppet

A altura física vem de `biblioteca/ilustrada/v1/imagens/<id>/personagem.json`,
campo `altura_m`. Preserve as diferenças entre pessoas; não padronize todos
para a mesma altura visível. A composição aplica profundidade e reduz o grupo
junto se necessário. Leia `biblioteca/ilustrada/v1/PUPPET.md` antes de animar.
Rigs por pins ficam associados ao PNG em `personagem.json.puppets`.
Use-os para movimentos locais contínuos de cabeça, ombros e mãos. Não aplique
um rig de pose neutra a outra pose sem calibrar os pins. O primeiro protótipo
usa arquivos JSON e malha; não oferece o editor visual completo do After Effects.
Caminhadas e gestos usam preferencialmente ciclos de desenhos completos disponíveis na ficha.


### Diálogos, atuação e rig articulado

Leia `biblioteca/ilustrada/v1/ANIMACAO.md`. Cenas ilustradas aceitam `falas`
com personagem, texto, áudio, tempo e intenção; não force o modo narrado quando
há diálogo. O narrador não aciona bocas. Use somente bocas locais calibradas
para a pose e preserve âncora/corpo. A análise espectral é aproximada;
marcações revisadas ou Rhubarb instalado podem melhorar a sincronização.
Sem áudio, registre fala pendente e não declare lipsync pronto.
Os atlas de membros separados foram retirados; use ciclos completos do elenco.
Use somente ações registradas na ficha do personagem. Gestos têm preparação,
acomodação e reações de escuta. Revise `animation_review`, a boca no silêncio,
o apoio dos pés, mudanças de escala e o loop. Renderize e assista à prévia
com áudio antes de declarar o diálogo final. As vozes das demos são temporárias.


### Preferência por quadros completos

Leia `biblioteca/ilustrada/v1/QUADROS.md`. Para caminhar, correr ou levantar
o braço, consulte `ciclos_quadros` no inventário e use `animacao: "quadros"`
com `animacoes_quadros`. Prefira desenhos completos aos novos recortes de membros.
Lucas tem oito desenhos por ação. Preserve escala pela cabeça/corpo e âncora
do chão; a mão elevada não deve reduzir o personagem. Com cenário móvel, use
`seguir_travelling`. Revise os apoios e o fechamento do ciclo. Não aplique
bocas ou olhos de outra pose sobre estes atlas sem calibração facial específica.


Para trocar o ângulo do mesmo cenário ou esconder alguém com objetos, leia
`biblioteca/ilustrada/v1/EXPANSAO.md`. Consulte `cameras`, `objetos`, `grupos`
e `ciclos_quadros` do inventário. Selecione `camera` na cena e objetos em
`frente`. Agachar/abaixar e se esconder usam `uma_vez` para manter a posição
final; levantar reproduz os desenhos na ordem inversa. Não use o mapa de porta
de um ângulo em outro. Cada criatura usa seus próprios desenhos e movimentos,
sem substituir o corpo por frames humanos. Preserve a altura física individual.


### Câmera da biblioteca ilustrada

Leia `biblioteca/ilustrada/v1/CAMERA.md` ao montar enquadramentos. O mapa
primeiro posiciona os atores; `camera_ilustrada` depois aplica o plano. Use
`camera: {"angulo":"esquerda", "plano":"medio", "alvo":"lucas"}` na história.
`medio` é cintura para cima; `inteiro` conserva cabeça e pés; `americano` vai
até joelhos; `close` mostra rosto/ombros. Para andar, correr, levantar o braço
e esconder-se, prefira inteiro; para falas, médio; para reações, close.
A altura física permanece na ficha e os marcos anatômicos são individuais.
`auto` mantém grupo em conjunto e ações amplas em inteiro, sem mudar o zoom
a cada pose. Não aplique a câmera automática sobre a coreografia do jumpscare.


### Sombras e iluminação da biblioteca

Leia `biblioteca/ilustrada/v1/SOMBRAS.md`. Todos os atores recebem sombra
de contato e projeção de silhueta conforme `iluminacao` do cenário. Ao criar
ou trocar o ângulo de um cenário, calibre luzes e polígono do piso; a posição
da fonte é sua projeção no chão e a altura é física. Preserve sombras sob
os pés e atrás de corpos/objetos. Saltos perdem contato e suavizam a projeção;
retratos sem pés não ganham sombra. Confira câmera, porta e travelling na
prévia. Não confunda os metadados com detecção automática da luz na imagem.


### Contato, ligações e direção por narrativa

Leia `biblioteca/ilustrada/v1/DIRECAO_INTERACOES.md`. Consulte `transicoes`
e `ciclos_quadros` nas fichas. Use `movimentos` para parado/andar/correr/parar;
o motor insere desenhos reais de ligação. Para alcançar objetos, use o ciclo
`interagir` com marco `palma_d` e ponto do cenário calibrado. Faça o trajeto
terminar no bloqueio do contato; não deslize os pés para corrigir um braço.
Use `oclusores` para passar atrás e à frente de móveis. Planeje `batidas`
para ação, fala, reação, descoberta e preparação do susto. Os cortes não
reiniciam o relógio da animação. Confira contato, apoios, fases, oclusão e
closes em uma prévia. Reutilize a biblioteca; gere arte nova apenas quando
o movimento ou enquadramento necessário não estiver disponível.
