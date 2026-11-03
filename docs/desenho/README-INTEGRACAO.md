# Visual Asset Library — implementação inicial

**Escopo:** biblioteca de imagens externas, busca por metadados, deduplicação por SHA-256, prompts para assets ausentes, composição de planos em camadas. Não substitui o rig vetorial e não altera o renderizador existente.

## Instalação

Copie `lofi/visual_assets.py` e `lofi/visual_compositor.py` para a pasta `lofi/` do repositório, e `tests/test_visual_assets.py` para `tests/`. Dependência de composição: Pillow (já usada no motor).

## Exemplos

```bash
python3 -m lofi.visual_assets --library asset-library import ./rafa.png --kind character --name Rafael --style cartoon --subject rafael --view front --pose sitting
python3 -m lofi.visual_assets --library asset-library search --kind character --subject rafael
python3 -m lofi.visual_assets --library asset-library plan requests.json
python3 -m unittest discover -s tests -p 'test_visual_assets.py'
```

`requests.json`:

```json
[
  {"kind":"character", "subject":"rafael", "style":"cartoon", "view":"front", "pose":"sitting", "description":"Rafael sentado no sofá", "transparent":true},
  {"kind":"environment", "subject":"apartamento", "style":"cartoon", "description":"Sala noturna sem personagens"}
]
```

Composição programática:

```python
from lofi.visual_compositor import compose_shot
compose_shot((1080, 1920), [
  {'path': 'apartamento.png', 'x': 0, 'y': 0},
  {'path': 'rafa.png', 'x': 350, 'y': 700, 'scale': 1.2},
], 'preview.png')
```

## Limites e próximos passos

- A biblioteca **não está ligada automaticamente** ao `lofi.render.Episode`: ainda é preciso adaptar o carregamento e composição de planos do motor.
- `compose_shot` gera quadros estáticos; não inclui timeline, câmera, lip sync ou articulações.
- `FULL_SCENE`, `LAYERED_SCENE` e `HYBRID_SCENE` são modos de organização, não três renderizadores independentes.
- Os metadados são informados pelo usuário; ainda não há reconhecimento automático de pose/expressão nem verificação semântica de consistência.
- Imagens são deduplicadas por conteúdo: mesmo arquivo importado com outros metadados aponta para o registro original.
- O índice SQLite deve ser versionado com cuidado; recomenda-se excluir `asset-library/` do Git e fazer backup dos originais.
- Próxima etapa: adaptar o schema dos shots, integrar com `lofi.render`, adicionar controles de keyframes e uma Skill Claude que use o planejador.

## Novos módulos — animação de imagens (novembro de 2026)

Os três módulos abaixo são **implementações iniciais executáveis e independentes**. Ainda **não estão conectados automaticamente ao `lofi.render.Episode`** e não devem ser descritos como integração completa do motor.

### 1. Image Scene Animator — `lofi/image_scene_animator.py`

Gera frames PNG com camadas, keyframes de posição/escala/opacidade, câmera (pan e zoom), parallax, respiração simples e efeitos `flicker`, `fog`, `vignette`.

```bash
python3 -m lofi.image_scene_animator examples/scene.json ./frames --fps 12
# Para produzir MP4, com ffmpeg instalado:
ffmpeg -y -framerate 12 -i frames/frame_%06d.png -c:v libx264 -pix_fmt yuv420p episodio.mp4
```

A cena de exemplo usa imagens `background.png` e `actor.png` relativas ao arquivo JSON; substitua pelos seus assets. O compositor não cria imagens ausentes.

### 2. Character Motion Engine — `lofi/character_motion.py`

Composição de partes transparentes, variação discreta de posição, rotação, respiração, balanço de cabeça, sprites de olhos e boca. As bocas podem ser alimentadas por cues temporais (`mouth_cues`), mas **não há reconhecimento automático de fonemas**. O personagem precisa ter partes recortadas e variantes de expressões fornecidas.

### 3. Auto Rig Generator — `lofi/auto_rig.py`

Estimativa heurística de 13 landmarks de um humanoide ereto, baseada na silhueta transparente, com correções manuais e visualização. **Não detecta articulações com IA, não recorta partes e não anima automaticamente o esqueleto.** Este módulo prepara metadados de rig para futura integração e requer revisão manual.

```bash
python3 -m lofi.auto_rig personagem.png --out rig.json --preview rig-preview.png
# Opcional: --overrides correcoes.json
```

### Testes

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

### Limitações e integração futura

- Os módulos são uma fundação funcional, não uma solução de produção final.
- Integrar a timeline de imagens ao renderizador principal, áudio, biblioteca e especificação de episódios requer alterações adicionais.
- Rig estimado é apenas uma aproximação geométrica; modelos de pose/segmentação e deformação ARAP ainda não foram integrados.
- Movimento de cabeça por sprite não reconstrói vistas ocultas, e o módulo facial não implementa malha facial 3D.
- Efeitos são simples, determinísticos e CPU/Pillow; performance em 1080×1920 exige otimização e cache.
- O projeto AnimatedDrawings não foi incorporado nem vendorizado neste pacote.

## Integração opt-in com motor-lofi (V3)

A V3 inclui `lofi/drawing_mode.py` e `install_into_motor.py`. O instalador copia os módulos e injeta um **hook apenas em `Episode.scene_frame`**, criando backup `lofi/render.py.bak`. O comportamento vetorial continua padrão para episódios sem `visual_mode: DESENHO`. **Não execute o instalador em um checkout com alterações não salvas sem revisar o diff.**

```bash
python install_into_motor.py /caminho/para/motor-lofi
```

No `episodio.json`, mantenha os campos obrigatórios existentes e adicione:

```json
{
  "visual_mode": "DESENHO",
  "shots": [{
    "start": 0, "end": 3, "type": "scene",
    "image_scene": {
      "layers": [
        {"path": "imagens/apartamento.png", "x": 0, "y": 0, "z": 0},
        {"path": "imagens/rafael.png", "x": 200, "y": 500, "z": 2,
         "motion": {"breathing": true, "amplitude": 3}}
      ],
      "camera": {"zoom": [1, 1.08], "x": [0, 12]},
      "effects": [{"type": "flicker", "rate": 2.2, "strength": 0.1}]
    }
  }]
}
```

O `image_scene` também aceita o caminho relativo para um arquivo JSON com as camadas. Para rosto em camadas, cada layer pode conter `character: {parts: [...], state: {size: [w,h], mouth_cues: [...]}}`; as partes são sprites PNG transparentes com variantes de olhos, boca, sobrancelhas e pupilas. Os estados faciais são baseados em imagens preparadas, não em geração automática de novos rostos. A biblioteca de assets pode ser consultada pela CLI de `lofi.visual_assets`; os planos ainda precisam referenciar caminhos de imagens explícitos.

### Limitações honestas

- A integração do hook foi desenvolvida contra a assinatura de `scene_frame` consultada no GitHub, mas **não foi testada dentro do checkout completo do motor**, apenas com testes unitários isolados.
- `auto_rig.py` ainda é uma **heurística de silhueta** com revisão manual obrigatória, não uma implementação de AnimatedDrawings nem detector de pose por IA.
- Não há ARAP, recorte automático de membros, reconhecimento facial robusto, lip-sync extraído do áudio nem interface visual de edição. As bocas podem ser acionadas por cues temporais externos.
- `image_scene` substitui a renderização procedural daquele plano; o restante do pipeline de `Episode.frame` (legendas, etc.) depende do código original.
- A imagem de cenário precisa ter dimensões suficientes para cobrir o quadro; não há geração automática de regiões ocultas.
