# Biblioteca ilustrada v1

Modo opcional do Motor Lo-Fi: 5 identidades, recortes, ciclos completos e 15 fundos/ângulos.
Lucas mantém as cinco poses iniciais e ganha perfil, costas e uma pose de corrida.
Clara e Téo têm poses de atenção e medo. Lucas de Amanhã tem uma pose de ameaça
encapuzada. O Mímico tem poses de presença e chamado; é uma criatura ficcional
inspirada em skinwalker. Os ambientes originais são entrada, corredor e floresta.
O catálogo também inclui ângulos do abrigo e oito ambientes dark cinematic em
[primeira pessoa](PRIMEIRA_PESSOA.md).

Novas criações seguem o [padrão do motor](PADRAO_CRIACAO.md): dez vistas,
repertório obrigatório, transições e coreografias próprias para monstros.
Os modelos e o validador ficam salvos no repositório para uso em outro computador.

Os PNGs em `imagens/` são arte real gerada com image_gen. O catálogo registra
dimensões, âncoras dos pés e hashes dos recortes. `prompts.md` guarda os prompts
usados. As cinco primeiras poses de Lucas foram reaproveitadas sem alterar as originais.

Use `python -m lofi.historias_ilustradas listar` para consultar o inventário e
`python -m lofi.historias_ilustradas validar` para verificar arquivos e transparência.
`python tools/studio.py ilustrado producoes/ilustradas/<nome-novo>` cria um
rascunho independente usando o arco de imitação. Para histórias originais, use
a skill `motor-lofi-ilustrado`, escreva o plano e compile com o mesmo módulo.

Os assets não impõem mudanças às séries existentes. Usar a aparência de alguém
em outra história não transporta automaticamente sua biografia ou os segredos
de Visto Amanhã. Consulte o cânone ao continuar uma série.

Uma pose não é um ciclo completo: corrida, piscadas, movimento de boca e contato
com objetos precisam dos recortes específicos correspondentes. Não há áudio ou
sincronização gerados pela biblioteca. No rascunho, escolha e revise o enquadramento,
os pés e a posição de cada personagem antes de gravar a narração.


A biblioteca guarda os recortes em `biblioteca/ilustrada/v1/imagens/<personagem>/`:
`lucas`, `clara`, `teo`, `amanha` e `mimico`. O catálogo aponta para cada pose.
São 15 poses, mais 4 microposes: piscadas neutras de Lucas, Clara e Téo,
e uma inclinação de cabeça de Lucas. Os fundos continuam em `imagens/`.

Escolha uma vez por série:
```
python tools/studio.py modo series/<serie> --render-mode illustrated_library
python tools/studio.py planejar historia.json series/<serie> --episode 1
```
A skill lê a escolha persistida. `--render-mode rig` no episódio permite usar
o modo anterior; o comando `modo` muda o padrão da série. A biblioteca usa
respiração e balanço discretos. Só poses com variante compatível piscam.


O módulo também aceita diálogos, bocas locais sincronizadas e ações com peças
articuladas. Consulte `ANIMACAO.md`. As demonstrações MP4 têm vozes de teste
reaproveitadas dos exemplos; as vozes finais ainda precisam ser gravadas.


Animação por desenhos completos: Lucas possui ciclos de andar, correr e levantar
o braço, com oito desenhos por ação. Consulte [QUADROS.md](QUADROS.md) para gerar e alinhar novos ciclos.


Câmeras, movimentos do elenco e criaturas e objetos: [EXPANSAO.md](EXPANSAO.md).


Câmera cinematográfica da biblioteca: corpo inteiro, americano, cintura e close.
Veja [CAMERA.md](CAMERA.md). O mapa organiza o elenco antes de aplicar o enquadramento.


Sombras de contato e silhueta seguem as luzes calibradas do cenário.
Veja [SOMBRAS.md](SOMBRAS.md) para luzes, piso, movimento e saltos.


Contato com objetos, ligações de movimento e câmera narrativa: [DIRECAO_INTERACOES.md](DIRECAO_INTERACOES.md).
