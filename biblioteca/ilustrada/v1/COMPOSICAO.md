# Mapeamento de composição

O motor usa os mapas de `catalogo.json.cenarios` e uma pose neutra como
referência de escala por personagem. O cálculo usa a silhueta visível do
PNG, ignorando margens transparentes. A altura desejada vem da zona do cenário;
no abrigo frontal, a referência de 1,70 m ocupa 50% da imagem. Lucas tem
1,45 m e ocupa cerca de 43%, ficando menor que o restante do elenco e que a
porta nessa composição. Quando o grupo não cabe, a escala diminui em conjunto.
Personagens na mesma profundidade ficam proporcionais. `escala_relativa`
permite diferenças físicas intencionais, como adulto/criança.

Cada cenário tem zonas com faixa horizontal, altura física projetada e chão.
A entrada tem `frente` e `porta`; corredor/floresta têm `frente` e `fundo`.
As coordenadas são normalizadas sobre o PNG completo do cenário. O motor
aplica a mesma projeção e recorte do fundo usados na renderização, inclusive
quando a proporção da tela muda. Um chão cortado pelo enquadramento gera aviso.

O cálculo reserva espaço para todas as poses do personagem no episódio,
incluindo caminhada, piscadas e variantes, e conserva ordem e escala nas
trocas de pose. A pintura segue a profundidade: fundo antes do primeiro plano.
No bloqueio automático, o zoom legado e o balanço ficam desligados para
respeitar os limites calculados. A `camera_ilustrada` aplica o enquadramento
cinematográfico depois do bloqueio: inteiro, americano, cintura e close.
Veja `CAMERA.md`. Respiração e movimentos do elenco continuam.

## Uso

Histórias novas do módulo ilustrado já recebem os mapas e o relatório.
Para aplicar aos JSONs do modo imagens com fundos conhecidos:

```powershell
python -m lofi.composicao biblioteca/ilustrada/v1/cena_animada_demo_v1.json biblioteca/ilustrada/v1/cena_mapeada_nova.json
```

A saída deve ser nova e ficar na mesma pasta para preservar os caminhos dos
assets. `--catalogo` aceita uma biblioteca alternativa. Cada ator pode definir
`id`, `zona`, `ordem`, `escala_relativa` e `referencia_escala`. O JSON traz
`composicao_relatorio`, com valores anteriores, ajustes e avisos.

`composicao: "manual"` no bloco `imagens` preserva posições, tamanhos e câmera;
o motor ainda aponta cortes e sobreposição de silhuetas. Use essa opção para
interações precisas com objetos ou enquadramentos deliberados. Os mapas podem
anotar pontos de interação; eles não calculam automaticamente o contato das mãos.

## Verificação

`cena_animada_demo_v2.json` e `cena_animada_preview_v2.gif` mostram o grupo
padronizado. `diagnostico_composicao_v1.png` marca zonas em azul, chão em verde,
eixos dos personagens em amarelo e pontos de interação em rosa.

O método é geométrico, com mapas calibrados manualmente; não identifica sozinho
o chão ou móveis de um cenário novo. Ele detecta cortes, sobreposição excessiva
no mesmo plano, possível oclusão da cabeça e grupos que ficam pequenos demais.
A detecção da cabeça usa a parte superior da silhueta, não reconhecimento facial.
Perspectiva, contato dos pés, pose e interação ainda exigem revisão visual.


## Olhares e entrada pela porta

`orientacao: "centro"` usa `direcao_original: "direita" | "esquerda" | "frente"`.
À esquerda o personagem olha à direita; à direita, à esquerda. A direção é
verificada novamente em cada quadro, após calcular a posição. Uma faixa de
4% ao redor do centro preserva a orientação para evitar oscilações. Para uma
ação específica, use `orientacao: "manual"` e `espelhar` explicitamente.
`direcoes_originais` permite metadados diferentes por pose. A orientação não
é inferida dos pixels: os assets precisam desses metadados.

O mapa de entrada inclui `portais.porta.poligono`, calibrado sobre o cenário
inteiro. O recorte é feito no compositor: os pixels do monstro são limitados
à abertura, respeitando o recorte do fundo e a câmera. Parede, batente e porta
continuam visíveis na frente dele. Não se altera o PNG original do cenário.

O personagem usa `portal: {"nome": "porta", "ate_chao": 0.70}`; a máscara
é liberada quando ele atravessa esse limiar de profundidade. `trajeto` aceita
keyframes para `pos`, `chao` e `altura`, com interpolação contínua. `passo`
e `ciclo_passo` sincronizam o balanço corporal ao ciclo de poses.
A auditoria de trajetórias amostra extremos e 33 instantes; não é uma prova
contínua de colisão. Os limites de cada portal devem ser revisados visualmente.

`cena_animada_demo_v3.json` e `cena_animada_preview_v3.gif` mostram a aproximação
com quatro poses novas do Mímico, salvas em `imagens/mimico/`. Os prompts estão
em `mimico_caminhada_prompts_v1.json`. A caminhada é um teste com quatro desenhos,
com pequenas diferenças entre variantes; não há vídeo generativo ou áudio.
