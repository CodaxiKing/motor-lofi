# Biblioteca ilustrada v1

Modo opcional do Motor Lo-Fi: 5 identidades, 15 recortes por pose e 3 fundos.
Lucas mantém as cinco poses iniciais e ganha perfil, costas e uma pose de corrida.
Clara e Téo têm poses de atenção e medo. Lucas de Amanhã tem uma pose de ameaça
encapuzada. O Mímico tem poses de presença e chamado; é uma criatura ficcional
inspirada em skinwalker. Os ambientes são entrada, corredor e floresta.

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
