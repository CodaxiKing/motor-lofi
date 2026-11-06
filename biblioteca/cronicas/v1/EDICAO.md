# Padrão de edição Crônicas

O estilo do vídeo orienta a linguagem de montagem. Cenários, história e câmeras
podem ser originais. Não há obrigação de recriar a casa, posições ou geometria
da referência em todo episódio.

## O que a referência permite observar

Na abertura, uma pose junto à janela é sustentada e aproximada. A sequência
seguinte alterna posição deitada, detalhes da pia e cidade. Mais adiante entram
contraplanos, ações rápidas, telefone, diálogos e decisões. A montagem acompanha
a informação e a voz; nem todo corpo está em movimento contínuo.

Isso é compatível com animação limitada e composição de ilustrações: fundo,
personagem, objetos, luz/névoa e interface tratados separadamente. Há trechos de
ação que podem ter usado desenhos sucessivos, deformação de recortes ou clipes
gerados. A análise do MP4 **não identifica o processo usado pelo autor**.
Nem o acabamento pintado nem pequenas variações entre poses provam uso de IA.
Também não é possível confirmar a ferramenta da voz pelo áudio isoladamente.

## Como produzir esse resultado

1. Escrever situação e premissa nas primeiras frases; plantar pista e recurso,
   escalar o conflito, entregar uma resposta e terminar com uma escolha custosa.
2. Finalizar a narração e marcar ação, pausa, reação, detalhe e decisão no áudio.
3. Criar fundos próprios e poses consistentes do personagem em arquivos separados.
4. Sustentar planos e usar mudanças suaves de escala/posição. Cortar ao revelar
   informação, mudar o ponto de vista ou mostrar uma consequência.
5. Animar só o necessário: olhos, respiração, mão, luz ou ação de corpo com quadros
   compatíveis. Corrida e contato precisam de arte real, apoios e transições.
6. Sobrepor interface, mensagens, escolhas e efeitos sonoros; revisar cada cena
   e depois a mixagem do episódio completo.

Editores de composição permitem animar posição, escala e opacidade por keyframes,
como descreve a [documentação do After Effects](https://helpx.adobe.com/ae_en/after-effects/desktop/animate-in-after-effects/animation-basics/animation-basics.html).
Uma alternativa para ações curtas é imagem-para-vídeo: fornecer uma ilustração
e descrever movimento de personagem/câmera, como no
[guia oficial do Runway](https://help.runwayml.com/hc/en-us/articles/48324313115155-Image-to-Video-Prompting-Guide).
São meios possíveis de produção, sem atribuição dessas ferramentas ao autor.
Clipes gerados ainda exigem conferir identidade, mãos, chão e continuidade.

## Padrão implementado no motor

Selecionar `biblioteca: cronicas` herda o perfil do catálogo. Novas séries com
estilo `cronicas` selecionam essa biblioteca. Câmeras explícitas são preservadas;
composições copiadas da geometria do vídeo são apenas presets opcionais.

| Batida visual | Comportamento inicial |
|---|---|
| `estabelecer` | Plano aberto fixo para situar o ambiente |
| `sustentar` | Aproximação discreta de 1 a 1,035 durante o plano |
| `detalhe` | Recorte com aproximação suave; ajustar `cx`/`cy` para a pista |
| `reacao` | Close no ator; sem ator, detalhe do ambiente |
| `inserto` | Base fixa para telefone ou diálogo |
| `decisao` | Base fixa para escolha |

As batidas são decisões editoriais na história, não uma interpretação automática
do significado da voz. A auditoria confere presença textual de situação/premissa;
a clareza criativa continua sendo revisada. Valores do HUD devem ser atualizados
pela história, sem reiniciar recursos entre cortes.

Os cenários desta biblioteca foram feitos aqui com `image_gen`. A edição da
prévia é do motor Python/FFmpeg, com câmera interpolada e interface em camadas.
Não foram gerados clipes por IA nem animações completas da Mara nesta entrega.
