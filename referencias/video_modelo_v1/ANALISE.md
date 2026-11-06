# Análise da referência enviada

Fonte: vídeo local fornecido pelo usuário, 720 × 1280, 30 fps, aproximadamente
2 min 44 s. A identificação e o hash estão em `origem.json`. A análise usa
quadros do próprio arquivo e transcrição local Whisper small. Não há dados de
publicação ou retenção; nenhuma conclusão aqui prevê alcance ou desempenho.

## Abertura e premissa

O vídeo começa com uma situação concreta: um zumbi no portão na primeira noite
do apocalipse. A primeira fala apresenta uma regra contraintuitiva: tentar
espantá-lo é perigoso. O restante da abertura promete uma alternativa ligada ao
som. O plano inicial já mostra o protagonista protegendo a janela.

Depois da antecipação do perigo, a história volta a 22h55 para explicar o
contexto. O prazo de sobrevivência, a dúvida sobre o que o pai sabe e a escolha
entre buscar Helena e procurar o pai estabelecem objetivo, mistério e custo.
O espectador entende o problema antes da escalada, em vez de receber apenas
uma frase vaga de suspense.

Para os próximos roteiros do motor, manter: **situação concreta na primeira
frase; premissa e objetivo/perigo imediatamente depois**. A abertura deve
prometer uma resposta que a própria história consiga mostrar. A história, os
nomes, a regra e o objeto da solução podem mudar a cada episódio.

## Construção dramática observada

| Tempo aproximado | Função narrativa | Imagem predominante |
|---|---|---|
| 0–7 s | Situação, regra de perigo e antecipação da solução | Quarto, costas na janela, aproximação |
| 7–22 s | Recuo temporal, prazo, sinais de ameaça e objetivo | Deitado, parede/pia, vista da cidade |
| 22–41 s | Escolha pessoal e mudança: o barulho chega ao portão | Escolhas na tela, quarto, rosto e janela |
| 41–66 s | Ameaça identificável, tentativa de afastar e escalada | Portão frontal, contraplano da casa, rua e grupo |
| 66–94 s | Alternativas ruins, urgência e lembrança do pai | Escolha com contagem, interiores, diálogo e multidão |
| 94–121 s | Uso de recurso plantado e execução da estratégia | Inventário, telefone/power bank, carga, arremesso e reação |
| 121–143 s | Entrega parcial: distração permite ganhar distância | Rua do alto, laje e mensagem ao pai |
| 143–164 s | Informação nova reabre o conflito pessoal | Telefone, laje, caixa de diálogo e escolha final |

Os intervalos acima são uma leitura editorial aproximada, não uma EDL de cortes
conferida quadro a quadro. `geral.jpg` e `abertura.jpg` permitem conferir a
amostragem. A transcrição automática integral fica em `transcricao_asr.json`;
contém erros de reconhecimento e sobreposição entre janelas. Ela não deve ser
publicada como transcrição literal sem revisão da voz.

## Câmeras e posições

Há câmeras realmente diferentes: dentro do quarto em direção à janela,
posição deitada vista dos pés, inserto da pia, dentro da garagem em direção à
rua, rua em direção à casa e vista alta do bairro. Trocar só o zoom não produz
essas perspectivas. Elas precisam de fundos e poses compatíveis.

O plano geral do quarto coloca janela no centro superior, banco à esquerda,
armário à direita e saco de dormir no primeiro plano. O personagem na janela
está de costas, com mãos erguidas e pés separados; não é uma pose neutra
deslizando pela parede. No plano deitado, cabeça ocupa aproximadamente o terço
superior, com o saco de dormir alongado até perto da borda inferior.

O portão divide o plano perto da metade da altura. Os corpos ficam atrás das
barras quando vistos de dentro. No contraplano, vemos as costas da multidão e
a fachada da casa. A oclusão precisa acompanhar essa troca de lado.

Na laje, o protagonista fica sentado no centro, abaixo do skyline; há bastante
chão vazio no terço inferior para relógio e atalhos. O telefone ocupa um plano
próprio sobre o ambiente desfocado, preservando a leitura das mensagens.

As caixas normalizadas dos atores, momentos de referência e composições estão
em `biblioteca/cronicas/v1/perfis/cronicas_situacional_v1.json`.
São calibrações manuais aproximadas; a identidade e proporção da Mara original
podem produzir diferenças em relação ao personagem do vídeo.

## Movimento, ritmo e acabamento

O vídeo alterna sustentações, microatuação, aproximações e cortes ilustrados.
O movimento não precisa ser contínuo em todos os elementos. As ações amplas
(chegada do grupo, corrida, uso/arremesso do celular) marcam mudanças narrativas.
Há variação de acabamento: os interiores têm pintura e sombra mais texturizadas;
certas ações externas usam contornos mais visíveis, linhas de impacto e efeitos
de borda. Isso não é evidência de um rig 3D nem de interpolação de membros.

Predominam azul/cinza escuro e contraste controlado. A interface amarela e os
indicadores verdes/vermelhos ficam separados da arte. Vinheta escura, luz da
lua, telefone e recortes de detalhe concentram a atenção. Os círculos brancos
que aparecem na abertura e pia são sinais de interação; não devem ser pintados
como objetos do cenário.

## Interface e continuidade

Missão no alto à esquerda; recursos no alto à direita; relógio e atalhos à
esquerda na parte inferior; caixas de diálogo e decisões na região central.
O HUD persiste entre planos e muda com a história. Valores de água, comida,
bicicleta e celular são dados de ficção, não números decorativos aleatórios.
Horário, carga, quantidade de ameaças e disponibilidade de saída precisam de
continuidade. A interface não deve cobrir o rosto nem o objeto que prova a ação.

## Aplicação no motor

1. Abertura estruturada e retirada do texto de gancho fixo alheio à cena.
2. Perfil de composições manuais, com câmera fixa e recortes deliberados.
3. Fundos novos com a geometria das vistas observadas, sem atores ou interface.
4. Poses específicas da Mara para janela, posição deitada e sentado na laje.
5. HUD editável, diálogos, inserto de telefone e decisão como camadas de tela.
6. Prévias comparáveis e registro explícito do que falta para reproduzir o vídeo
   inteiro: multidão certificada, contatos no portão, manipulação de telefone,
   arremesso e novas vozes. Uma pose pronta não certifica todos esses movimentos.

Os frames do vídeo são material de análise; não entram como fundos finais no
catálogo. Os assets novos mantêm arquivos separados e prompts próprios. A marca
d'água do vídeo não é transferida para as novas artes ou para a interface.

## Diretriz atual para Crônicas

A expansão usa ambientes e histórias originais, preservando a linguagem de
edição e a abertura situacional. Os presets que aproximam posições do vídeo são
opcionais. O padrão e a explicação dos processos possíveis de animação estão em
`biblioteca/cronicas/v1/EDICAO.md`. O arquivo analisado não permite confirmar
se o autor usou IA ou atribuir sua produção a uma ferramenta específica.
