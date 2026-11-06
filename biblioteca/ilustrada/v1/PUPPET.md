# Alturas físicas e animação por pins

Cada pasta de personagem contém `personagem.json`. `altura_m` é a autoridade
para a altura física; o tamanho do PNG serve apenas para medir o desenho visível.
Alturas atuais: Lucas 1,45 m (protagonista menor), Téo 1,60 m, Clara 1,75 m, Amanhã 1,70 m e Mímico
2,10 m. A referência do cenário é `catalogo.json.escala_referencia_m = 1.70`.
A razão física é aplicada antes de ajustar o grupo ao enquadramento. Se o grupo
não cabe, o motor reduz todos juntos, preservando as diferenças e a perspectiva.

O planejamento lê novamente as fichas. Um episódio já compilado guarda os
valores usados; recompile/remapeie após editar as alturas. `escala_override`
permite uma exceção explícita ao remapear; não altere alturas para esconder
problemas de enquadramento. Um cenário manual ou uma trajetória de altura
explicitamente desenhada continua sob controle do autor.

## Puppet local v1

O renderer suporta deformação de recortes por pontos de controle, com campo
suave TPS inverso e malha de quadriláteros. Não implementa o algoritmo proprietário
do After Effects. Usa NumPy e Pillow já presentes no motor.

Os rigs de Lucas e Téo estão em `imagens/<id>/puppet_neutro_v1.json`.
`personagem.json.puppets` associa cada PNG compatível ao rig correto.
Somente pose neutra e sua variante de piscada estão calibradas nesta versão.
Outras poses continuam renderizando normalmente; nunca se reutiliza um rig
incompatível silenciosamente. O renderer aplica a deformação antes de espelhar
o personagem e antes do recorte do portal.

Cada pin define `pos: [x,y]` normalizada no canvas e pode usar:

- `fixo: true`: conserva quadril, joelhos e apoios dos pés.
- `amplitude: [dx,dy]`, `periodo` e `fase`: movimento periódico contínuo.
- `keys: [[tempo,[dx,dy]], ...]`: deslocamentos com interpolação suave.
- `loop_s`: repetição dos keyframes, que devem ter início/fim compatíveis.

`grupos_rigidos` move um conjunto de pins por rotação comum, usado para reduzir
a distorção da cabeça. É uma aproximação por restrições de pontos, não uma
garantia de rigidez de cada pixel. O rosto permanece desenhado no próprio PNG.
Amplitude máxima aceita: 8% do canvas por eixo; rotação: 12 graus. Prefira gestos
pequenos para não esticar o desenho. Bordas do canvas ficam ancoradas.

Com puppet ativo, a respiração e o balanço global do recorte são substituídos
pela deformação local, mantendo os apoios estáveis. A câmera e os portais
continuam funcionando. A malha é calculada na resolução do sprite que será
exibido, evitando deformar o PNG inteiro em resolução original a cada quadro.

## Prévia e limites

`puppet_alturas_demo_v1.json` e `puppet_alturas_preview_v1.gif` mostram Lucas
e Téo com suas alturas e movimentos contínuos a 24 fps. O Mímico aparece na
porta com escala física própria. `diagnostico_puppet_lucas_v1.png` mostra os
pins: verdes fixos, amarelos móveis. A prévia não contém áudio.

```powershell
python tools/preview_caminhada.py biblioteca/ilustrada/v1/puppet_alturas_demo_v1.json biblioteca/ilustrada/v1/puppet_alturas_preview_v1.gif
```

Os pins são editados em JSON nesta versão; ainda não há editor visual de arrastar.
Uma imagem única não revela partes escondidas do corpo. Caminhadas com cruzamento
das pernas, giro de corpo e gestos grandes precisam de poses próprias ou membros
separados em camadas, com rig e ordem de oclusão revisados. A deformação suave
complementa esses assets; não cria automaticamente todos os quadros intermediários.


## Correção das piscadas e do loop

`personagem.json.piscadas_locais` associa cada pose às regiões dos olhos.
O compositor traz as pálpebras da variante fechada para essas regiões e mantém
o canvas, a âncora, o corpo e o rig da pose original. Assim a piscada não desloca
o personagem inteiro. As regiões usam coordenadas normalizadas `destino` e,
quando necessário, `origem`. A configuração atual está calibrada para Lucas e Téo.

`puppet_alturas_demo_v2.json` e `puppet_alturas_preview_v2.gif` corrigem a prévia:
os movimentos dos rigs têm ciclo comum de quatro segundos e o GIF dura oito.
O primeiro quadro e o quadro no instante final foram comparados e coincidem.
Os testes verificam que piscar não modifica os pixels do corpo nem a sua âncora.


A sincronização de diálogos está documentada em `ANIMACAO.md`; movimentos
grandes usam os desenhos completos de `QUADROS.md`.


Atualização: o elenco usa quadros completos para movimentos grandes; os atlas
de membros separados foram retirados. Consulte `EXPANSAO.md`. Pins locais
continuam disponíveis nas poses originais calibradas.
