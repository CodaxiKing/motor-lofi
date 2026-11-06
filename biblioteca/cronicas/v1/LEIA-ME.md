# Biblioteca Crônicas

Biblioteca visual independente, baseada na linguagem de câmera e pintura do
vídeo fornecido. A biblioteca ilustrada continua disponível com seu próprio elenco.
O catálogo Crônicas contém **Mara**, personagem original com cabeça redonda,
cabelo preto curto, presilha cobre, jaqueta verde-petróleo e bolsa de lona.

Há sete fundos noturnos e quatro poses transparentes: em pé, apoiada na janela,
deitada no saco de dormir e sentada na laje. Nove composições calibradas combinam
esses assets; dois insertos demonstram telefone e decisão.

- [Mara e poses](previas/mara_v1.png)
- [Cenários](previas/fundos_v1.png)
- [Enquadramentos](previas/composicoes_v1.png)
- [Prévia de 22 segundos, sem áudio](previas/direcao_cronicas_v1.mp4)
- [Comparação local com o vídeo](previas/index.html)
- [Análise do roteiro e das câmeras](../../../referencias/video_modelo_v1/ANALISE.md)
- [Estilo](ESTILO.md) e [modelo de roteiro](ROTEIRO.md)

## Seleção no motor

```powershell
python -m lofi.historias_ilustradas --biblioteca cronicas listar
python -m lofi.historias_ilustradas --biblioteca cronicas validar
```

Em histórias estruturadas, selecione explicitamente:

```json
{
  "biblioteca": "cronicas",
  "perfil_direcao": "cronicas_situacional_v1",
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
inclui a premissa. Consulte o [perfil](perfis/cronicas_situacional_v1.json).
O gerador antigo `criar` permanece ligado ao arco do elenco ilustrado; para
Crônicas, escreva uma história estruturada com este elenco e seus assets reais.

A interface `sobrevivencia_compacta` oferece missão, recursos persistentes,
relógio, atalhos, diálogo, cartela, notificação, alerta, telefone e escolha.
`hora`, `status` e `missao` mudam o estado a partir do plano. Neste layout,
`interface: false` esconde o HUD; insertos explicitamente pedidos ainda aparecem.
Arte, interface e sinais de interação permanecem separados.

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
```

A auditoria completa retorna pendências por projeto. O registrador recalcula
hashes/âncoras e preserva o catálogo ilustrado. O último comando atualiza folhas e
comparações; `--render` cria clipes na pasta nova `previas/cenas-v1`, que deve estar
ausente antes dessa execução. As prévias já estão incluídas neste pacote.

As imagens foram geradas com a ferramenta integrada `image_gen`; prompts completos,
referências e origem estão em [fundos](atlas/geracao_fundos_v1.json) e
[Mara](atlas/geracao_mara_v1.json). O estudo anterior à correção da cabeça fica
arquivado no atlas e não é uma pose ativa. Quadros e transcrição do vídeo original
são referências locais, fora dos assets e do Git; a comparação continua exibindo
as novas composições quando esses arquivos locais não estiverem presentes.
