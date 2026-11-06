# Cenários dark cinematic em primeira pessoa

Oito fundos opacos novos, pintados no estilo da biblioteca, com câmera à altura
dos olhos, elementos próximos das bordas e profundidade: rua em quarentena,
hospital, abrigo, trilha macabra, metrô, esgoto, igreja e escadaria de emergência.
Estão em `imagens/cenarios/primeira_pessoa/`. Nenhum contém o corpo do observador,
mãos, monstros ou texto; esses elementos podem ser compostos separadamente.

- [Galeria renderizada](previas/primeira_pessoa_v1.png).
- [Prompts completos e origem das imagens](atlas/primeira_pessoa_v1/geracao.json).
- [Spec de revisão com os oito fundos](primeira_pessoa_demo_v1.json).

Os identificadores são `pov_rua_quarentena`, `pov_hospital`, `pov_abrigo`,
`pov_floresta`, `pov_metro`, `pov_esgoto`, `pov_igreja` e `pov_escadaria`.
Escolha um deles em `cenario` na história. O inventário lista esses ambientes
em `primeira_pessoa`; o compilador preserva `perspectiva: primeira_pessoa`.
O POV vem do desenho do fundo; não é uma câmera 3D navegável.

Uma cena só com o ponto de vista usa `personagens: []`. Quando outra pessoa ou
criatura estiver visível, adicione apenas esse ator e calibre seu blocking para
a perspectiva do local. Não desenhe o próprio observador inteiro diante da lente.
As ligações de montagem do pacote são genéricas; confira a continuidade da série.
Os fundos têm polígonos de piso e projeções de luz próprios, calibrados sobre as
ilustrações no manifesto. Não reutilizam mapas de portas de outros ambientes.
Luz e névoa são estáticas na ilustração; não são efeitos animados independentes.

Para conferir o registro e gerar novamente a galeria, sem regerar as artes:

```bash
python tools/registrar_cenarios_pov.py biblioteca/ilustrada/v1/atlas/primeira_pessoa_v1/geracao.json
python -m lofi.historias_ilustradas validar
```
