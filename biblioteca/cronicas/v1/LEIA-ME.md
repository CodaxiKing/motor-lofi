# Biblioteca Crônicas

Biblioteca visual independente, baseada na linguagem de câmera e pintura do
vídeo fornecido. A biblioteca ilustrada continua disponível com seu próprio elenco.
O catálogo Crônicas contém **Mara**, personagem original com cabeça redonda,
cabelo preto curto, presilha cobre, jaqueta verde-petróleo e bolsa de lona.

Há treze fundos noturnos e quatro poses transparentes: em pé, apoiada na janela,
deitada no saco de dormir e sentada na laje. Nove composições calibradas combinam
esses assets; dois insertos demonstram telefone e decisão.

Seis ambientes novos são originais: posto de estrada, hospital, mercado saqueado,
metrô, floresta com torre e abrigo com rádio. O padrão preserva pintura, edição
e construção narrativa; os lugares e enquadramentos podem ser diferentes do vídeo.

- [Mara e poses](previas/mara_v1.png)
- [Cenários](previas/fundos_v1.png)
- [Enquadramentos](previas/composicoes_v1.png)
- [Prévia de 22 segundos, sem áudio](previas/direcao_cronicas_v1.mp4)
- [Comparação local com o vídeo](previas/index.html)
- [Análise do roteiro e das câmeras](../../../referencias/video_modelo_v1/ANALISE.md)
- [Estilo](ESTILO.md) e [modelo de roteiro](ROTEIRO.md)
- [Novos ambientes](previas/ambientes_originais_v2.png) e [prévia de 18 s](previas/ambientes_originais_v2.mp4)
- [Padrão de edição e como produzir cenas assim](EDICAO.md)

## Seleção no motor

```powershell
python -m lofi.historias_ilustradas --biblioteca cronicas listar
python -m lofi.historias_ilustradas --biblioteca cronicas validar
```

Em histórias estruturadas, selecione explicitamente:

```json
{
  "biblioteca": "cronicas",
  "producao": {"etapa": "previa_visual"},
  "abertura": {
    "situacao": "Mara está presa no quarto enquanto alguém testa a janela.",
    "premissa": "Ela precisa descobrir de onde vem o ruído antes de abrir a porta."
  }
}
```

Cada cena pode usar `composicao_ref`, como `quarto_janela`, `janela_close` ou
`laje_sentado`. O perfil fornece cenário, câmera e pose compatíveis; substituições
explícitas são preservadas. A primeira narração começa com a situação declarada e
inclui a premissa. O [perfil](perfis/cronicas_situacional_v1.json) é herdado do
catálogo: não é preciso repetir `perfil_direcao`. Cenas livres usam cenário e
`batida_visual`: `estabelecer`, `sustentar`, `detalhe`, `reacao`, `inserto` ou
`decisao`. A câmera explícita prevalece. Sem batida, um novo ambiente recebe plano
aberto; a continuidade no mesmo local recebe aproximação discreta.

```powershell
python tools/studio.py iniciar series/minhas-cronicas --title "Minhas Crônicas" --profile cronicas
python tools/studio.py modo series/minha-serie --render-mode illustrated_library --biblioteca cronicas
python -m lofi.historias_ilustradas --biblioteca cronicas criar producoes/cronicas/meu-rascunho
```

Novas séries com `--profile cronicas` herdam biblioteca e modo ilustrado.
O campo `biblioteca` explícito na história prevalece sobre o padrão da série.
`criar` entrega um exemplo original editável de 120 s; não interpreta briefs
arbitrários. Para outro conflito, escreva a história com a skill e os assets reais.
O [exemplo estruturado](exemplos/a_luz_que_nao_respondeu_v1.json) é um rascunho sem voz.

O HUD padrão mostra **apenas o horário HH:MM**, com `somente_horario: true`.
Missão, recursos, atalhos, dia da semana e marcadores de interação ficam ocultos.
`hora` atualiza o relógio a partir do plano e `interface: false` o esconde.
Telefone, diálogo e escolha são insertos narrativos usados somente quando pedidos
na cena. Arte e interface permanecem separados.

## Estado e reprodução

**Estudo visual**: as quatro poses são estáticas, sem ciclos de corpo ou boca.
A prévia demonstra composição e interface; não é um episódio narrado final.
A compilação e o render exigem `producao.etapa: previa_visual` enquanto o catálogo
estiver nesse estado. `validar` confere consistência dos arquivos disponíveis,
não certifica a cobertura de animações.

O padrão completo continua obrigatório para novas identidades: dez vistas
(oito direções, cima e teto), ações, transições, encaixes de itens e revisão.
O [plano da Mara](imagens/personagens/mara/ficha_animacao_planejada.json) registra
essas pendências separado da ficha ativa. Nenhum caminho nulo é um ciclo pronto.
Monstros futuros ficam em `imagens/monstros/<id>`, com movimentação própria;
itens humanos em `imagens/items`, em todas as vistas. Não há monstros certificados
neste catálogo inicial.

```powershell
python -m lofi.padrao_personagens --base biblioteca/cronicas/v1 auditar
python tools/registrar_biblioteca_cronicas.py
python tools/previa_cronicas.py
python tools/previa_cronicas.py --originais
```

A auditoria completa retorna pendências por projeto. O registrador recalcula
hashes/âncoras e preserva o catálogo ilustrado. O último comando atualiza folhas e
comparações; `--render` cria clipes em `previas/cenas-v1` ou, com `--originais`,
`previas/cenas-originais-v2`. A pasta correspondente deve estar ausente antes
dessa execução. As prévias já estão incluídas neste pacote.

As imagens foram geradas com a ferramenta integrada `image_gen`; prompts completos,
referências e origem estão em [fundos](atlas/geracao_fundos_v1.json) e
[Mara](atlas/geracao_mara_v1.json) e [cenários originais](atlas/geracao_fundos_originais_v2.json).
O estudo anterior à correção da cabeça fica
arquivado no atlas e não é uma pose ativa. Quadros e transcrição do vídeo original
são referências locais, fora dos assets e do Git; a comparação continua exibindo
as novas composições quando esses arquivos locais não estiverem presentes.
