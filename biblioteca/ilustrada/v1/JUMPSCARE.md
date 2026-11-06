# Skinwalker saltando para a câmera

`jumpscare_skinwalker_preview_v1.mp4` é uma prévia de 3,6 segundos a 30 fps,
com preparação, salto frontal, rosto cobrindo a tela e corte final para preto.
Inclui um efeito sonoro sintético original, sem falas.

A ficha do Mímico registra `sustos.jumpscare` e dois ciclos: `jumpscare_salto`
(16 desenhos completos de corpo) e `jumpscare_rosto` (8 retratos completos).
O inventário também lista os sustos disponíveis. Os retratos são quadros de
cabeça e ombros desenhados juntos; não são membros separados.
As exposições do close começam com a boca aberta para manter a expressão
do último desenho do salto. O tipo `retrato` usa o mesmo leitor de quadros.

Para reutilizar, copie os dois primeiros planos de
`jumpscare_skinwalker_demo_v1.json`, ajuste o tempo absoluto dos planos e o
fundo. A trajetória e os tempos de animação dentro de cada plano são locais.
Os campos `ancora` dos ciclos acompanham o rosto, e `chao` nesta coreografia
é a posição vertical desse foco. A aproximação usa escala acima de 1 e cortes
de corpo deliberados; não aplique o reenquadramento automático de caminhada.
Não altere a altura física da ficha para reproduzir esse efeito de perspectiva.

O arquivo de áudio está em `audio/jumpscare_skinwalker_v1.wav`; a demo guarda
o clip na timeline. O vídeo tem áudio e há um corte deliberado para o retrato
de maior definição no impacto. Não há flashes intermitentes.

Arte criada com imagegen integrado. Prompts em `jumpscare_prompt_salto_v1.txt`
e `jumpscare_prompt_rosto_v1.txt`; atlas e metadados em `imagens/mimico/`.
