---
name: motor-lofi-ilustrado
description: Criar histórias interativas narradas ou dialogadas usando personagens recortados por pose, puppet ou ciclos de quadros completos e cenários da biblioteca ilustrada do Motor Lo-Fi, ou ampliar essa biblioteca mantendo os outros modos de produção disponíveis.
---

# Histórias com biblioteca ilustrada

Use o checkout do Motor Lo-Fi existente. Este é um modo opcional: não migre o
rig, o modo imagens ou as séries existentes sem pedido do usuário.

## Biblioteca Crônicas separada

Para o estilo Crônicas, leia `biblioteca/cronicas/v1/LEIA-ME.md`, `ESTILO.md`
e `ROTEIRO.md`. Liste com `--biblioteca cronicas listar`; selecione na história
`biblioteca: "cronicas"` e `perfil_direcao: "cronicas_situacional_v1"`.
Use somente o catálogo escolhido. Mara é original, com cabeça redonda, cabelo
preto curto e presilha cobre; preserve o visual aprovado. A biblioteca está em
estudo visual, com sete fundos e quatro poses estáticas. Exige
`producao.etapa: "previa_visual"`; não declare ciclos completos ou produção final.
Seu contrato de animações mantém dez vistas e movimentos próprios para monstros.
Os campos `abertura.situacao` e `abertura.premissa` entram na primeira narração,
explicando imediatamente a situação e o objetivo/perigo. As composições, HUD e
insertos ficam no perfil; confira a prévia e a análise da referência fornecida.

## História original a partir dos assets

1. Rode `python -m lofi.historias_ilustradas listar` e leia
   `biblioteca/ilustrada/v1/catalogo.json`. Identifique elenco, poses, fundos e ligações.
2. Consulte `skills/video-script/SKILL.md` e sua integração `motor-lofi.md` para
   escrever a história solicitada. O catálogo define o que pode aparecer, não o
   enredo inteiro. Preserve as escolhas do usuário, o cânone da série e o mínimo de 90 s.
3. Escreva uma história nova no schema de
   `producoes/ilustradas/a-voz-la-fora-v1/historia.json`: título, perfil, duração,
   narrador quando houver, cenas numeradas e escolhas A/B. Cada cena define cenário, narração ou falas,
   acontecimento, consequência, causa e personagens `{id, pose, pos}`.
   `altura`, `chao` e `espelhar` permitem ajustar o blocking ao fundo.
4. Planeje causa/consequência, conflito pessoal, pista/revelação/pagamento e
   entrega de uma resposta. Cada alternativa tem benefício, perda e motivo.
   O compilador aceita narração e diálogos por personagem; consulte `ANIMACAO.md`
   para falas com áudio e bocas locais; leia QUADROS.md para ações completas.
5. Compile em pasta nova com
   `python -m lofi.historias_ilustradas compilar historia.json producoes/ilustradas/<nome>`.
   Revise roteiro, falas, relatórios e quadros; depois confira o render com as vozes reais.

`python tools/studio.py ilustrado producoes/ilustradas/<nome>` gera um rascunho
pelo arco local de imitação. É um ponto de partida editável, não um LLM nem um
intérprete de ideias arbitrárias. `--ideia` no módulo registra o brief para revisão;
para uma história original, escreva o plano conforme as etapas acima.

## Biblioteca e arte

Leia `biblioteca/ilustrada/v1/FLUIDEZ.md` para calibrar passada e contatos dos pés,
congelar voz antes da atuação e usar camadas independentes de cenário. Prepare a
história com `python -m lofi.atuacao_voz` depois de definir a gravação; use `--previa`
somente para vozes temporárias. Antes do vídeo completo, execute
`python -m lofi.revisao_cenas episodio.json --saida <pasta-nova>` e confira os clipes
com áudio, folhas e relatório por cena. Marque o que não tem marcos/voz final como
pendente; a trava de apoio não recupera uma passada incompatível com o desenho.

Antes de criar qualquer identidade, leia `biblioteca/ilustrada/v1/PADRAO_CRIACAO.md`
e `padrao_criacao.json`. Gere a ficha com `python -m lofi.padrao_personagens novo`.
Complete as dez vistas, ações, transições e revisão antes de registrar como pronta.
Zumbis e skinwalkers usam perfis próprios; monstros ficam em `imagens/monstros/<id>`
e não reutilizam desenhos humanos. Consulte a auditoria para distinguir identidades
legadas de novas criações certificadas. Não declare um modelo nulo como arte pronta.
Para ambientes dark cinematic POV, consulte `biblioteca/ilustrada/v1/PRIMEIRA_PESSOA.md`
e o inventário `primeira_pessoa`; use os fundos existentes antes de gerar variantes.

Para nitidez e closes, leia `biblioteca/ilustrada/v1/NITIDEZ.md`. Consulte
`arte_por_plano` no personagem: o renderer escolhe retratos compatíveis com plano,
pose e expressão e limita a ampliação pelo número de pixels disponíveis.
Não force um retrato neutro sobre corrida, contato ou fala sem boca HD calibrada.
Revise o relatório com `python -m lofi.qualidade_visual spec.json --out nitidez.json`
na resolução final. Para ciclos novos, prefira PNGs completos por quadro ou folhas
com poucas células grandes; ampliar uma célula pequena não recupera detalhes.

Gere assets novos somente quando necessários e autorizados: um PNG transparente
por pose/personagem e fundos separados, sem pessoas ou texto. Use o mesmo personagem
base para as variantes. Preserve as imagens antigas; adicione nomes/versionamentos
novos ao catálogo. Valide com `python -m lofi.historias_ilustradas validar`.
Um recorte de corrida é uma pose, não um ciclo completo de caminhada.

Não substitua poses ausentes por uma figura genérica nem declare animação de boca,
porta ou objeto quando a arte disponível não a representa. Posicione as mãos de
acordo com a geometria do cenário e confira em quadros reais.

## Entrega

O pacote inclui história JSON, roteiro, texto de narração, episódio técnico e
revisão dramática. A biblioteca é referenciada por caminho, sem regerar arte por
episódio. Configure voz, clips e legendas reais antes do render final.
Não declare áudio, vídeo final ou sincronização produzidos pelo plano estático.
Não escreva no episódio publicado da série Visto Amanhã ao criar uma demonstração.

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


Para jumpscare do skinwalker/Mímico saltando em direção à câmera, consulte
`biblioteca/ilustrada/v1/JUMPSCARE.md` e os `sustos` do inventário. A sequência
usa salto frontal e retratos completos; mantenha a expressão aberta no corte
e o foco ancorado no rosto. As escalas de aproximação são cinematográficas,
sem alterar a altura física da ficha.


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
