---
name: "serie-montar"
description: "Comando para montar o vídeo do episódio de uma série lo-fi interativa: recebe só as vozes, verifica com revisor independente, renderiza e entrega o MP4, teaser, capa e legenda do post."
---

# /serie-montar

Monta o episódio a partir do roteiro salvo no repositório. Siga a skill **serie-lofi-interativa** (seções "Motor e bíblia" e "Montagem") e o `SPEC.md`; as regras abaixo prevalecem.
Responda em português do Brasil.

## Dados
1. Anexos esperados: **só os áudios**, um por personagem (nome do arquivo = personagem; pode conter várias frases). Se faltar algum, diga exatamente qual.
2. Anexe o repositório (`add_repo`: CodaxiKing / motor-lofi, access push), clone ou `git pull`.
3. Leia `series/*/biblia.md` e o roteiro mais recente com status "roteiro" (`epNN_roteiro.md`). Se houver mais de uma série em andamento, use a que tem roteiro pendente; se houver dúvida, pergunte. Sem roteiro salvo, peça o roteiro colado ou rode antes o /serie-continuar.
4. Não faça outras perguntas; tome as decisões de montagem e informe as principais.

## Passos
1. `pip install --break-system-packages pillow numpy scipy` e tente `soundfile sherpa-onnx` (opcionais; se falharem, siga em frente: o Whisper roda com onnxruntime); copie os áudios para `series/<serie>/epNN/` com o nome do personagem (ex.: `roberta.mp3`).
2. Transcreva (`python3 -m lofi.transcribe ...`; na 1ª vez baixa o Whisper do GitHub, ~640 MB, e roda mesmo sem o sherpa-onnx) e case cada frase do roteiro **pelo texto**, nunca pela ordem ou pela duração. Um trecho pode juntar várias falas: se elas vão para cenas diferentes, divida o trecho nas micropausas e transcreva cada pedaço de novo para confirmar. Use os tempos de cada frase nas legendas (uma legenda por frase). Se aparecer "transcrição só com tempos", pare e avise: sem texto o áudio sai fora das cenas. Se faltar uma fala ou o texto divergir muito, avise e siga com o que existe.
3. Escreva `series/<serie>/epNN.json`: vozes com o nome dos personagens, legendas com o texto do roteiro, `series_title`, `episode`, `episodes_total`, `episode_title`, `tint` do episódio (bíblia), plano `recap` apontando para o `epNN.json` anterior (a partir do ep. 2; se ele não estiver no repositório, use `moments` montados a partir do resumo da bíblia) e todos os recursos de câmera, luz e clima que o roteiro pedir. Posicione os personagens com **marcas** do cenário (`"mark": "porta"`, ou `[[0, "fundo"], [3, "frente"]]` para andar; lista no `CATALOGO.md`, seção "Marcas de posição"); use x/y só para ajuste fino (`dx`/`dy`) ou quando nenhuma marca servir. Em cenas que mostram só a mão/braço (rádio, chave, maçaneta, celular, olho), diga de quem é com `"hand": "<personagem>"` (posições no `CATALOGO.md`, seção "Partes do corpo"): sempre o personagem que está agindo ou falando ali. Duração final de 2 a 3 minutos; nunca encha com silêncio parado.
4. **Verificador:** `python3 -m lofi.check series/<serie>/epNN.json` → corrija todos os ERROS (inclusive "fora do chão" e marca inexistente) e os avisos relevantes. Depois **confira o áudio**: `python3 -m lofi.transcribe --conferir series/<serie>/epNN.json` mostra o que é falado em cada cena; compare com o roteiro e corrija qualquer fala na cena errada antes de seguir.
5. **Revisor independente:** chame a ferramenta Agent (subagent general-purpose) com um prompt autocontido: caminho de `series/<serie>/_revisao.png`, o texto do roteiro e o que conferir (rosto coberto pela legenda, personagem cortado/fora do quadro, legenda errada ou fora de hora, cena diferente do roteiro, texto ilegível, contador encobrindo algo). Peça uma lista objetiva de problemas com o tempo de cada um. Corrija, rode o verificador de novo; repita no máximo 2 vezes.
6. Renderize em segundo plano: `python3 -m lofi.render series/<serie>/epNN.json --jobs 2` (≈3,5 s por segundo de vídeo, episódio de 3 min ≈ 10–11 min; avise o tempo estimado antes e mande um aviso curto quando terminar).
7. Confira duração, áudio e tamanho (crf 28 padrão; use 30 se passar de 90 MB).
8. Extras: `python3 -m lofi.extras teaser series/<serie>/epNN.json <mp4>` e `python3 -m lofi.extras capa series/<serie>/epNN.json`.
9. Entregue o MP4, o teaser, a capa e a legenda do post (e uma linha para o teaser).
10. Commit do `epNN.json` e do `epNN_roteiro.md`; só depois atualize a bíblia (resumo de 2–3 linhas, status "montado") e faça novo commit e push (sem áudios, vídeos ou imagens temporárias). Confira com `git ls-files series/<serie>/` que o `epNN.json` está lá.
11. Se for o último episódio, ofereça a compilação da temporada para o YouTube (peça os MP4s e use `python3 -m lofi.extras temporada ...`).
12. Linha final: "Quando a votação fechar: /serie-continuar [episódio] [A ou B]".