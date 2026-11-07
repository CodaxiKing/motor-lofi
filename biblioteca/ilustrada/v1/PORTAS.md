# Portas abertas e fechadas

Cinco variantes estáticas conservam câmera, batentes, móveis e estilo dos fundos
originais. Os PNGs de porta aberta permanecem disponíveis.

| Porta aberta | Porta fechada |
|---|---|
| `entrada` | `entrada_porta_fechada` |
| `entrada_esquerda` | `entrada_esquerda_porta_fechada` |
| `entrada_direita` | `entrada_direita_porta_fechada` |
| `entrada_baixo` | `entrada_baixo_porta_fechada` |
| `pov_abrigo` | `pov_abrigo_porta_fechada` |

Selecione o cenário pelo identificador. Exemplo de campos visuais da cena:

```json
{
  "cenario": "entrada_porta_fechada",
  "camera": "esquerda",
  "personagens": [{"id": "lucas", "pose": "neutro", "pos": 0.3}]
}
```

Acrescente narração, acontecimento e demais campos habituais da história. As
câmeras `frontal`, `esquerda`, `direita` e `baixo` das variantes fechadas apontam
somente para outras vistas fechadas. `variantes_porta` no catálogo relaciona os
dois estados; é metadado de consulta, não um comando automático para abrir a porta.

Os mapas fechados não têm polígono de portal aberto. As maçanetas dos quatro
ângulos foram marcadas de novo, pois saem da folha aberta e vão para o lado do
trinco. Confira mão e contato na cena; o ponto não cria o movimento do braço.
A luz do corredor ou da abertura externa foi retirada dos metadados de luz;
as fontes do próprio ambiente permanecem.

Para mostrar alguém atravessando, volte ao estado aberto antes da travessia.
São dois estados ilustrados: **não há ciclo animado da folha abrindo ou fechando**.

- [Comparação aberta/fechada](previas/portas_abertas_fechadas_v1.png)
- [Revisão](previas/portas_fechadas_revisao_v1.json)
- [Prompts e referências do image_gen integrado](portas_fechadas_geracao_v1.json)

Para registrar novamente metadados e gerar a folha:

```powershell
python tools/registrar_portas_fechadas.py
python -m lofi.historias_ilustradas validar
```
