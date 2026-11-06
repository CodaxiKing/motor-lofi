# Video Script no Motor Lo-Fi

Esta adaptação acrescenta o contexto do motor às instruções upstream. A série,
o gênero e as decisões explícitas do usuário orientam o trabalho. O texto pode
ser ficção: referências factuais externas só são necessárias para afirmações reais.

Na raiz do projeto, use `python tools/skills_motor.py contexto series/<serie> --episode N`.
Esse comando lê a bíblia, o elenco, o plano e as métricas existentes sem alterá-los.
O JSON retornado é o brief da etapa; não é roteiro escrito por um modelo.
Não crie `~/.video-script/profile.md` como requisito: a pasta da série é o perfil.
Se não houver métricas, proponha hipóteses e mantenha a evidência como insuficiente.
Não peça vídeos anteriores como condição para começar uma série nova.

Para séries do tipo Crônicas, use a biblioteca `cronicas` e leia seus
`ROTEIRO.md` e `EDICAO.md`. A abertura explica a situação concreta e a premissa
nas primeiras frases; desenvolver preparação, escalada, resposta e escolha com
custo. A edição acompanha informação, reação e detalhe. Cenários e conflitos
devem poder ser originais, preservando a linguagem do vídeo sem copiar sua trama.

## Contrato do roteiro

- Português do Brasil, formato da bíblia e perfil de duração escolhido, com mínimo de 90 s.
  Não encurte para o padrão de vídeos curtos do upstream nem alongue com silêncio.
- Preserve cânone e voto. Ofereça três aberturas coerentes, cada uma com frase,
  segunda frase, primeiro quadro, ação, legenda e som. A nota editorial não prevê views.
- Cada cena registra tempo, fala, imagem e mudança dramática. Use os seis critérios
  de `lofi.dramaturgia`: causa/consequência, conflito pessoal, intenção, preparação,
  escolha com custo e entrega. Em finais, não force outra votação ou suspense.
- Use `PERSONAGENS`, `SUJEITO`, `DESTINATÁRIO`, `CENÁRIO` e `MARCA` quando necessários.
  Gere fala por personagem ou uma única narração conforme a bíblia.
- Entregue `epNN_roteiro.md` e as alternativas, sem sobrescrever episódios travados.
  Para a forma completa das anotações, consulte `examples/roteiro_dramatico.md`.

Valide com `python -m lofi.dramaturgia <roteiro> --markdown` e
`python tests/validar_roteiro.py <roteiro> --perfil <perfil>`.
Consulte `lofi.experimentos` para registrar versões e publicações; não publique
nem altere a memória da série como efeito de uma revisão de texto.

O upstream pode sugerir agentes separados; essa é uma opção quando disponível
e autorizada. Revisão sequencial continua válida. Não exija Remotion, animated-video
ou video-edit para roteirizar com o Motor Lo-Fi.
