# Animação com desenhos completos

O módulo `lofi.ciclos_quadros` reproduz sequências do personagem inteiro.
Lucas tem oito desenhos por ciclo: andar, correr e levantar o braço.
Os PNGs originais ficam preservados em sua pasta; cada JSON descreve as células
do atlas, a cadência, as âncoras e a sequência de exposição.

Use `animacao: "quadros"` no personagem da história e, por exemplo:

```json
{"animacoes_quadros": [{"acao": "levantar_braco", "inicio": 0, "fim": 6, "modo": "loop"}]}
```

Os nomes disponíveis vêm de `personagem.json.ciclos_quadros` e do inventário.
No arquivo de renderização, cada ação referencia o JSON em `ciclo`.
`loop`, `uma_vez` e `ida_volta` controlam a reprodução. Não sobreponha dois
ciclos de corpo inteiro. A sequência do braço inclui subida, pausa e descida.

Para novos movimentos, gere personagens completos com a mesma câmera,
proporção, roupa e iluminação. Preserve cabeça, quadril e linha do chão.
Meça a escala pela cabeça e pelo corpo em repouso, nunca pela caixa da mão
levantada. Pés no ar usam uma linha de chão virtual para conservar o salto.
Não reposicione o personagem pelo centro da silhueta a cada desenho.
Inspecione joelhos, mãos, contatos e a passagem do último ao primeiro quadro.

Na locomoção com `seguir_travelling`, a distância percorrida pelo cenário
controla a fase dos passos. O campo `deslocamento_corpo_ciclo` calibra a passada.
As demos exportam 24 fps, com oito desenhos únicos por ciclo; a repetição de
exposições não cria desenhos intermediários. Não misture corpos com transparência
para fingir novos quadros. Os ciclos atuais não têm bocas/olhos locais calibrados;
o renderizador evita aplicar os recortes faciais de outras poses.

Prévias: `braco_quadros_preview_v1.mp4` e `locomocao_quadros_preview_v2.mp4`.
Outros modos continuam disponíveis para os assets já calibrados.
