# Câmeras e ganchos — o que copiar das referências

Análise de dois vídeos de série interativa (nov/2026):
- **A** — 16:9, 5 min, traço vetorial chapado, narração em CAIXA ALTA palavra por palavra, "O PÚBLICO DECIDE EP. 6".
  87 cortes: **um a cada 3,4 s**.
- **B** — 9:16, 2 min 26, terror em 2ª pessoa ("Você se abaixa lentamente…"), escolha marcada com um selo **B**.
  28 cortes: **um a cada 5 s**, mas com planos longos de 12–17 s no clímax (câmera lenta, quase parada).

O motor já faz quase tudo; a tabela diz qual campo usar. "FALTA" = ainda não existe.

## 1. Abertura (0–8 s)

| O que eles fazem | Onde | No motor |
|---|---|---|
| Quadro 0 preto com a frase da escolha do público ("Você decidiu permanecer escondido") | B 0,0 s | `hook` com `"fala"`; texto = a decisão, não a pergunta |
| Plano de situação de **meio segundo** (fachada do prédio à noite) antes do personagem | B 0,5 s | plano `aberto` de 0,5 s, sem fala |
| Selo da escolha (B) no canto + borda acesa durante o resumo | B 1–2 s, volta no fim | `"escolhida": "B"` no topo + `voto` (carimbo) |
| "VOCÊS DECIDIRAM": miniaturas dos episódios anteriores com carimbo da opção vencedora | A 3–5 s | `placar` / `recap` — a faixa de miniaturas com carimbo **FALTA** |
| Resumo do que já aconteceu em **sépia** | A 5–8 s | `recap` (já sai em sépia) ou `"lembranca": true` |

**Regra:** antes de 3 s o espectador já sabe (1) o que o público escolheu e (2) quem está em perigo.

## 2. Repertório de câmera

Na ordem em que mais aparecem:

1. **Médio de lado, corpo até o joelho**, personagem andando ou agachado: é o plano de base dos dois. `plano` automático `medio`.
2. **Close frontal com o olho arregalado**, câmera um pouco abaixo do rosto, objeto querido no quadro (o gato): é a reação. `"plano": "close"`.
3. **Contraplano do perigo sem mostrar o perigo**: câmera **no chão**, por baixo da porta, só os pés e duas sombras compridas
   (B 7–19 s, alternando com o close de reação a cada 1–2 s). É o plano que mais segura a atenção nos dois vídeos.
   No motor: `"type": "pes"` (`sapato`, `descalco` ou `garra`; `x` animado faz andar, com passos no som).
4. **POV pelo olho mágico** (círculo, tudo distorcido): B 23–25 s. `"effect": "peephole"`. Entrada boa: de costas para a porta
   (`view: back`), e o círculo **aparece por cima** do plano de costas antes do corte.
5. **Insertos de mão e objeto**: mão passando pela fresta do portão, garrafas caindo, bilhete no bolso (A 25–33 s, 192 s).
   `detail` (`macaneta`, `chave`, `celular`) e `partes` (mão/braço). Use 1 inserto a cada ~20 s de narração.
6. **Pés / chão**: quem chega é mostrado pelos pés (A 31 s, B 13 s). `"type": "pes"`, como no item 3.
7. **Plano de cima (plongée)**: a horda cercando o poste vista de cima (A 81–83 s). Para mostrar **cerco e número**. **FALTA**
   (cenário visto de cima); dá para fazer com `crowd` em fundo liso.
8. **Silhueta contra a janela** e revelação em 3 tempos: silhueta → corpo inteiro no escuro → close com olhos acesos
   (B 48 s → 77 s → 81 s). Use `dark` + `lights` e `light: silhouette`; o close final com `scare`.
9. **Quadro dentro do quadro**: o monstro visto pelo vão da porta, laterais pretas (B 77 s, 101 s). `fg` com a porta, ou
   `darken` nas laterais.
10. **Personagem cortado pelo quadro**: só tronco e o gato, cabeça fora (B 72–77 s) — o gato vira o protagonista do plano.
    `camera.alvo` no objeto/animal com `zoom` alto.
11. **Dois atores na escada, lanterna em diagonal** e campo/contracampo em closes (B 120–131 s). `flashlight` + `focus`
    alternando + cortes automáticos do modo redes.
12. **Tela dividida com ação simultânea**: um no poste, o outro no chão (A 79 s). Hoje só a `choice` divide a tela;
    divisão no meio do episódio **FALTA**.
13. **Mapa/rota em linhas de luz** (B 31–35 s): planta do prédio em arame com o caminho acendendo. `"type": "plano"` (mente.py).

**Ritmo:** corte a cada 2–4 s na conversa e na fuga; **plano longo e lento (10–17 s) só no encontro com o perigo**,
com aproximação mínima e sem trilha. O contraste é o que assusta.

## 3. Ganchos que prendem

- **Regras do mundo em cartela** ("REGRA 2: ELES NÃO SABEM SUBIR", A 76 s): uma regra nova por episódio, sempre testada logo
  depois. **FALTA** a cartela; hoje dá com `overlay` `text`.
- **Palavra-chave colorida na legenda** (vermelho = perigo, amarelo = nome/lugar). Já existe: `*palavra*`.
- **Frase cortada no corte**: a legenda termina com vírgula e o plano muda ("segurando seu gato, / e olha por baixo da porta.").
  Escreva a narração em pedaços de 3–5 palavras e corte o plano junto.
- **Pergunta antes da escolha com o balão de comentário** ("RESPONDE AQUI / NOS COMENTÁRIOS", A 293 s). `pergunta` + contagem.
- **Chamada final dupla**: "envie este vídeo para um amigo **e comente B**" com o selo da escolha na tela (B 144 s).
  A letra pedida é sempre a da opção mais arriscada.
- **Cartela final de série**: "O PÚBLICO DECIDE · EP. 6 · quem decide o episódio é você" (A 294 s). `end_card` da `choice`.
- **Animal em perigo**: o gato está em quase todo plano de B; quando ele foge dos braços (72 s) é o ponto de virada.
  Dê ao protagonista algo pequeno para proteger.

## 4. Visual

Nenhum dos dois usa névoa, granulado ou brilho nos personagens: traço limpo, luz do lugar e escuro. O único filtro é a
**sépia nas lembranças**. Por isso o padrão do motor agora é `"efeitos": "nenhum"` e a sépia fica só em
`"lembranca": true` e no `recap` (ver SPEC, "Intensidade dos efeitos").

## 5. O que falta no motor (em ordem de impacto)

Já feitos: pés por baixo da porta (`"type": "pes"`) e selo da escolha (`"escolhida"`).

1. Faixa **"VOCÊS DECIDIRAM"** com as miniaturas dos episódios e o carimbo da opção.
2. Cartela de **REGRA N**.
3. **Tela dividida** no meio do episódio.
4. **Plano de cima** (cerco).
