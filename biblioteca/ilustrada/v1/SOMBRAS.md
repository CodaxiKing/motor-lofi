# Sombras de contato e projeção

O compositor cria sombras para todos os personagens e criaturas por padrão.
São efeitos do motor; os PNGs e os desenhos originais permanecem intactos.
Há contato sob cada pé apoiado e uma projeção suave da silhueta para cada luz.
As sombras são pintadas no chão antes dos corpos e dos objetos de primeiro plano.
Câmera, profundidade, escala física e máscaras de porta compartilham a mesma
transformação. O polígono do piso impede que a projeção escureça a parede.

As luzes dos cenários atuais ficam em `catalogo.json.cenarios.<id>.iluminacao`.
O compilador copia essa configuração para o episódio; JSONs existentes da
biblioteca também podem usar o catálogo durante a renderização. Uma cena pode
substituir a configuração pelo campo `iluminacao`.

```json
{
  "ambiente": 0.25,
  "espaco": "cenario",
  "piso": [[0,0.72],[1,0.72],[1,1],[0,1]],
  "luzes": [{
    "tipo": "pontual", "posicao": [0.6,0.89], "altura_m": 3.2,
    "intensidade": 0.9, "suavidade": 0.65
  }]
}
```

`posicao` é a projeção da fonte no piso, não a posição desenhada da lâmpada
no teto. `altura_m` define a altura física da fonte. A direção e o comprimento
resultam da posição relativa entre fonte e personagem. Uma fonte alta gera
sombras menores; várias fontes distribuem a projeção. A luz ambiente reduz
o contraste, e `suavidade` varia entre 0 e 1.

Para luar ou fonte distante, use `tipo: "direcional"`, `direcao: [dx,dy]`
(sentido em que a sombra se alonga) e `comprimento` em alturas do personagem.
Por padrão, posições e piso pertencem ao PNG do cenário e acompanham o
travelling. `espaco: "tela"` usa o mundo do enquadramento antes do zoom.
As luzes aceitam `trajeto` com keyframes de `x`, `y`, `intensidade`,
`altura_m`, `suavidade` e `comprimento`, em segundos locais da cena.

## Movimento e saltos

A silhueta vem do desenho inteiro ativo; a referência física vem da ficha.
Agachar reduz a altura efetiva da projeção. Durante voo, o contato desaparece
e a sombra no chão fica mais difusa, fraca e deslocada conforme a luz.
`elevacao` no ator, em frações da altura da tela, levanta o corpo preservando
o chão e aceita keyframes. Para ciclos com solo virtual, a distância visível
entre os pés e essa linha também informa a suspensão.

Um ator pode usar `sombra: {"intensidade": 0.8}` ou desativar com `sombra: false`.
`sombras: false` desativa a cena. Coreografias com âncora no rosto, como o
jumpscare, precisam de `sombra.chao` e podem usar `sombra.elevacao` para sua
projeção específica. Retratos sem pés não recebem sombra artificial no chão.
O salto do skinwalker já tem esses dados; seu close continua sem sombra.

As luzes são calibradas em metadados, não detectadas automaticamente nos
pixels. Ao gerar outro ângulo, calibre novamente a projeção da fonte e o piso.
O cálculo é uma aproximação de chão plano; não projeta sombras sobre móveis
ou outros personagens e não repinta a iluminação já desenhada na arte.
Em fundos externos sem configuração, o motor usa uma luz padrão ajustável.

Comparação: `sombras_comparacao_v1.png`. Prévia: `sombras_preview_v1.mp4`,
sem áudio, com mudança de luz, caminhada e o jumpscare do skinwalker ao final.
