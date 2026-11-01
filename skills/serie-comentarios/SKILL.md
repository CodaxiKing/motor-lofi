---
name: "serie-comentarios"
description: "Vídeo curto em que um personagem da série lo-fi lê e responde comentários dos seguidores: recebe os comentários (texto ou print), escreve as respostas no tom do personagem sem spoiler e, com a voz, monta o vídeo com o cartão do comentário na tela."
---

# /serie-comentarios

Vídeo vertical de 30 a 75 s em que um personagem da série responde comentários reais dos seguidores, com o cartão do comentário aparecendo na tela (estilo "Respondendo a @usuario"). Aproveita o engajamento entre um episódio e outro.
Siga a skill **serie-lofi-interativa** (seção "Motor e bíblia") e o `SPEC.md`; as regras abaixo prevalecem. Responda em português do Brasil.

Duas etapas, decididas pelo que vier anexado:
- **Sem áudio** (comentários colados em texto ou em prints) → etapa 1: roteiro.
- **Com áudio** (um arquivo por personagem) → etapa 2: montagem do roteiro de comentários mais recente com status "roteiro".

## Dados (as duas etapas)
1. Anexe o repositório (`add_repo`: CodaxiKing / motor-lofi, access push), clone ou `git pull`, e leia `series/*/biblia.md` e `personagens.json`. Se houver mais de uma série e o pedido não disser qual, use a que tem episódio "montado" mais recente; se ainda houver dúvida, pergunte.
2. Os vídeos de comentários ficam em `series/<serie>/comentarios/`: `cNN_roteiro.md` e `cNN.json` (NN = 01, 02…). A bíblia ganha (ou atualiza) a seção "## Vídeos de comentários" com uma linha por vídeo: nº, depois de qual episódio, comentários respondidos (só o @) e status (roteiro/montado).

## Etapa 1 · Roteiro
1. **Leia os comentários.** Em prints, transcreva o @ e o texto de cada um exatamente como aparecem (emojis podem sair). Se vierem mais de 5, escolha 3 a 5.
2. **Escolha** comentários variados: uma teoria, uma crítica ou bronca a um personagem, uma pergunta, um elogio ou piada. Prefira os mais curtidos e os que rendem resposta boa.
   - **Nunca escolha:** ofensa, preconceito, assédio, comentário sobre a aparência real de alguém, dados pessoais (telefone, endereço, escola) ou comentários que pareçam de criança falando de si. Não os cite nem para recusar.
   - Mostre o @ como o seguidor publicou. Se o usuário pedir, ou se o @ parecer o nome completo de alguém, abrevie (`@ju***`).
3. **Quem responde.** Por padrão, o personagem de quem o comentário fala (bronca na Roberta → Roberta responde); senão a protagonista. Só use personagens que já apareceram nos episódios publicados e estão vivos/presentes no ponto atual da história. Um vídeo pode ter 1 ou 2 personagens.
4. **Respostas no personagem**, como se ele estivesse dentro da história, no dia e no lugar do último episódio publicado:
   - curtas (1 a 3 frases, até ~10 s de fala cada), com a personalidade da bíblia, humor e um pouco de tensão;
   - **zero spoiler:** nunca revele a "verdade" do mistério, os finais, nem o que acontece em episódios não publicados. Teoria certa → desconverse ("Será? Fica de olho no rádio…"); teoria errada → não desminta de um jeito que entregue a resposta;
   - respeite a classificação da série e as regras do universo;
   - se a votação do último episódio estiver aberta, um dos comentários (ou o fechamento) puxa o voto sem dizer qual opção é "a certa".
5. **Estrutura:**
   - **ABERTURA (0–3 s):** personagem em close + texto grande "VOCÊS COMENTARAM…" (gancho), som `notif`.
   - **BLOCO por comentário (7–15 s):** o cartão do comentário entra (`notif`), o personagem reage 0,5–1 s em silêncio (emoção certa: `suspicious` para teoria, `angry` para bronca, `happy` para elogio) e responde. Cenário da série ligado ao comentário ou ao ponto atual da história.
   - **FECHAMENTO (3–6 s):** chamada para a votação aberta ou para o próximo episódio ("Comenta A ou B no episódio 3") e "CONTINUA…".
   - Duração total: 30 a 75 s.
6. **Formato do roteiro** (`series/<serie>/comentarios/cNN_roteiro.md`): cabeçalho com série, depois de qual episódio, total; para cada bloco: `BLOCO n — início s a fim s`, `COMENTÁRIO: @usuario · "texto" · curtidas (se houver)`, `CENÁRIO:` (nome do motor entre crases), `PERSONAGENS:` (nomes, vista, pose e emoção do motor entre crases), `PLANO:`, `SOM:`, `FALA (personagem): [tag] texto`, `LEGENDA:` (caixa alta, máx. 4 palavras por pedaço). Use só nomes de `CATALOGO.md` e `personagens.json`.
7. **Entregue:** os comentários escolhidos (e, em uma linha, quantos ficaram de fora, sem citar os recusados), o roteiro por bloco, a **narração para o ElevenLabs v3** com um bloco por personagem (nome no título, tags em inglês, dica de voz) e a legenda do post.
8. Registre na bíblia (status "roteiro"), commit e push. Linha final: "Próximo passo: gere um áudio por personagem no ElevenLabs e use /serie-comentarios com os áudios".

## Etapa 2 · Montagem (com os áudios)
1. Siga a seção "Montagem" da skill **serie-lofi-interativa** e as regras de áudio do /serie-montar: copie as vozes para `series/<serie>/comentarios/cNN/<personagem>.mp3`, transcreva (`python3 -m lofi.transcribe ...`) e case cada fala **pelo texto**, dividindo trechos que juntam respostas de blocos diferentes.
2. Escreva `series/<serie>/comentarios/cNN.json` com `"formato": "comentarios"`, `series_title`, `tint` do último episódio, `style` da série, `voices`, `clips`, `subs` (uma legenda por frase) e `shots`:
   - abertura: plano com `"hook": {"text": "VOCÊS\nCOMENTARAM…"}`;
   - cada bloco: um plano com o cartão em `overlay`: `{"type": "comment", "user": "@usuario", "text": "texto", "likes": 1240, "t": [início, fim], "y": 700}`. O cartão entra 0,3 s antes da reação e sai quando a resposta termina; `y` (centro do cartão) entre 640 e 760, com o personagem abaixo (`y` do ator ≥ 1650, sem close que suba o rosto para a área do cartão);
   - `notif` no `sfx` na entrada de cada cartão; trilha leve (`music` com `tense` baixo);
   - fechamento com `"overlay": [{"type": "text", "text": "COMENTA A OU B", "y": 900}]` (ou "CONTINUA…") e, se fizer sentido, o carimbo do voto.
   - `hud` com o dia/hora do ponto atual da história e `place` "RESPONDENDO".
3. Verificador: `python3 -m lofi.check series/<serie>/comentarios/cNN.json` (ele conhece o formato e acusa cartão cobrindo rosto). Confira o áudio: `python3 -m lofi.transcribe --conferir series/<serie>/comentarios/cNN.json`. Corrija até não haver ERRO e até cada resposta estar no bloco do seu comentário.
4. Revisor independente (ferramenta Agent, subagent general-purpose) com a folha `_revisao.png`, o roteiro e a lista: cartão legível e com o @ certo, cartão sem cobrir rosto, resposta no bloco certo, legenda sem cobrir o cartão, nenhum spoiler na fala ou na tela. Corrija e só então renderize: `python3 -m lofi.render series/<serie>/comentarios/cNN.json --jobs 2` (≈3,5 s por segundo de vídeo; avise o tempo antes).
5. Confira duração, áudio e tamanho. Entregue o MP4 e a legenda do post.
6. Commit do `cNN.json` e do roteiro; atualize a bíblia (status "montado") e faça push. Nunca versione áudios ou vídeos.

## Legenda do post
1 linha de gancho ("A Roberta leu os comentários de vocês… 👀") · 1 frase sobre a melhor resposta · chamada para comentar ("Deixa a sua teoria aqui embaixo, talvez ela responda") · chamada para a votação aberta, se houver · "📺 TÍTULO · Comentários #NN" · 6–8 hashtags.
