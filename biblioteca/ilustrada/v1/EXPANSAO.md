# Elenco completo, câmeras e esconderijos

Cada personagem mantém seus próprios desenhos e ciclos em `imagens/<id>`.
O inventário separa `personagens` e `criaturas`; o Mímico tem ciclos próprios,
incluindo espreitar e avançar. A altura continua vindo de `personagem.json`.
Cada ação comum tem oito desenhos; espreitar e avançar do Mímico usam dezesseis
desenhos cada, a 12 exposições por segundo. As folhas originais desses dois
ciclos ficam preservadas junto dos atlas importados. A importação identifica
os corpos completos conectados e os empacota com margem, conservando a escala
por pixel e evitando cortar uma cauda de casaco que cruza uma célula nominal.
Os atlas de membros separados foram retirados. O código genérico de rig
permanece compatível com outros projetos, sem peças do elenco nesta biblioteca.

`agachar`/`abaixar` descem até a posição baixa. `levantar` usa os mesmos desenhos
na ordem inversa. Use `modo: "uma_vez"` para segurar a posição final, evitando
reiniciar em pé a cada segundo. `se_esconder` usa a descida e requer um objeto
de primeiro plano: a silhueta é encoberta pelo alfa do objeto, não apagada.

Exemplo de campos em uma cena da história:

```json
{
  "cenario": "entrada",
  "camera": "esquerda",
  "frente": [{"objeto": "bau", "x": 0.5, "y": 0.74, "altura": 0.4}],
  "personagens": [{
    "id": "clara", "pose": "neutro", "pos": 0.5,
    "animacao": "quadros",
    "animacoes_quadros": [{"acao": "se_esconder", "inicio": 0, "fim": 3, "modo": "uma_vez"}]
  }]
}
```

Acrescente os campos narrativos normais da cena. Câmeras: `esquerda`, `direita`
e `baixo`; a câmera original continua sendo o padrão. São novas imagens do
mesmo ambiente, com mapas próprios. Não reutilize o polígono da porta frontal
em outro ângulo. Para passar pelo batente, calibre sua abertura nesse ângulo.

Objetos: baú, armário baixo, batente e árvore. `altura` dimensiona o objeto
em relação à tela; `x`/`y` indicam seu centro. Ajuste à perspectiva e à altura
física do personagem e confira se o objeto cobre a posição agachada inteira.
Um objeto em `frente` encobre os atores anteriores; cenas com atores à frente
e atrás do mesmo objeto requerem planos separados ou máscara específica.

Os prompts usados pelo gerador integrado ficam em `expansao_prompt_*.txt`.
Prévias: `expansao_elenco_preview_v2.mp4` (quatro pessoas),
`expansao_esconder_preview_v2.mp4` (três câmeras e esconderijos) e
`expansao_criatura_preview_v2.mp4` (plano mais aberto para os braços do Mímico).
São testes visuais sem falas. O relatório `expansao_revisao_v2.json` confere
alfa, margens e apoios; a revisão visual complementa essas medidas.


Salto frontal com rosto na tela: [JUMPSCARE.md](JUMPSCARE.md).
