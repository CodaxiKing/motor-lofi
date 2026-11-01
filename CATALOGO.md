# Catálogo do motor

Gerado por `python3 -m lofi.catalogo --md CATALOGO.md` a partir do código. Não edite à mão.

**Cenários** (20): `apartamento`, `carro`, `corredor`, `delegacia`, `entrada`, `escada`, `escola`, `esgoto`, `floresta`, `hospital`, `igreja`, `janela`, `mercado`, `metro`, `ponte`, `posto`, `radio`, `rua`, `rua_amanhecer`, `telhado`

**Personagens prontos** (29): `bruxa`, `chef`, `cientista`, `cowboy`, `crianca`, `detetive`, `dj`, `estudante`, `estudante2`, `executiva`, `executivo`, `fantasma`, `lia`, `medica`, `pirata`, `policial`, `rafa`, `rainha`, `roberta`, `roqueiro`, `soldado`, `valter`, `vovo`, `vovo2`, `zombie`, `zombie_corredor`, `zombie_enfermeiro`, `zombie_policial`, `zombie_rastejante`

**Poses** (29): `carry`, `chest`, `crawl`, `cross`, `crouch`, `fallen`, `forward`, `hand_l`, `hand_r`, `hands_up`, `hide`, `hold`, `hug`, `idle`, `jump`, `knock`, `knock2`, `open_door`, `phone`, `point`, `pull`, `push`, `reach`, `reach_l`, `remove_bag`, `run`, `scared`, `sit`, `wave`

**Emoções** (10): `angry`, `cry`, `determined`, `fear`, `happy`, `neutral`, `panting`, `sad`, `shock`, `suspicious`

**Vistas** (4): `front`, `back`, `side`, `3q`

**Planos de detalhe (`subject`)** (5): `celular`, `chave`, `macaneta`, `olho`, `relogio`

**Sons (`sfx.name`)** (25): `bang`, `beep`, `breath`, `car_alarm`, `click`, `crowd`, `door_close`, `door_open`, `echo_step`, `glass`, `growl`, `heartbeat`, `impact`, `knock`, `lock`, `no_service`, `notif`, `shuffle`, `siren`, `stamp`, `static`, `step`, `thunder`, `vibe`, `whoosh`

**Sons que aceitam `dur`** (4): `breath`, `crowd`, `heartbeat`, `static`

**Transições** (7): `cut`, `whip`, `flash`, `fade`, `zoom`, `glitch`, `dip`

**Acústicas** (5): `abafado`, `aberto`, `grande`, `media`, `sala`

**Objetos na mão (`prop`)** (5): `radio`, `flashlight`, `phone`, `key`, `bag`

**Corpos (`body`)** (5): `child`, `old`, `tall`, `fat`, `thin`

**Clima:** `rain` = `forte`, `normal`, `fraca`, `nenhuma` · `time` = `dia`, `entardecer`, `amanhecer`, `madrugada`, `noite` · `fog` e `snow` de 0 a 1

## Marcas de posição por cenário

Use no ator: `"mark": "porta"` (ou `[[0, "fundo"], [3, "frente"]]` para andar entre marcas). Imagem com todas: [`examples/mapa_cenarios.png`](examples/mapa_cenarios.png).

- **apartamento:** `centro` (no meio do tapete), `tapete_esq`, `tapete_dir`, `janela` (em frente à janela, mais longe da câmera), `abajur` (ao lado do abajur, à esquerda), `sofa` (na frente do sofá (use pose sit para sentar))
- **entrada:** `porta` (colada na porta, de costas (espiar, trancar, bater)), `frente_porta` (de frente para a câmera, diante da porta), `lado_esq` (perto do cabideiro), `lado_dir`, `chao_porta` (sentada no chão encostada na parede)
- **corredor:** `fundo` (no fim do corredor (bem pequeno)), `meio`, `frente`, `frente_esq`, `frente_dir`, `olho_magico` (visto pelo olho mágico (effect peephole): dentro do círculo), `olho_magico_fundo` (atrás de quem está no olho mágico)
- **rua:** `centro`, `calcada_esq`, `calcada_dir`, `longe` (lá no fundo da rua (pequeno)), `longe_esq`, `longe_dir`, `carro` (ao lado do carro estacionado, à esquerda)
- **janela:** `rua_longe` (na rua, vista de cima (minúsculo)), `rua_perto` (na rua, vista de cima), `na_janela` (quem olha pela janela, de costas, em primeiro plano), `na_janela_dir`
- **escada:** `degrau_baixo`, `degrau_meio`, `degrau_alto`, `patamar` (no patamar, de frente)
- **telhado:** `centro`, `parapeito_esq` (na beirada esquerda), `parapeito_dir` (na beirada direita), `fundo` (longe, perto da caixa d'água)
- **ponte:** `barreira` (na barreira do exército, lá no fundo), `meio`, `frente_esq`, `frente_dir`
- **radio:** `mesa_esq` (cenário de objeto: o rádio é o destaque; personagem pequeno no canto), `mesa_dir`
- **hospital:** `fundo`, `meio`, `frente`, `maca` (ao lado da maca, à direita)
- **mercado:** `fundo`, `meio`, `frente_esq`, `frente_dir`
- **metro:** `plataforma`, `plataforma_longe`, `beira` (na beira da plataforma, perto da faixa amarela)
- **escola:** `fundo`, `meio`, `frente`, `armario_esq` (encostado nos armários da esquerda), `armario_dir`
- **delegacia:** `mesa` (na frente da mesa, à esquerda), `cela` (na frente das grades), `centro`
- **posto:** `bomba_esq` (ao lado da bomba da esquerda), `bomba_dir`, `frente`, `frente_esq`, `frente_dir`
- **floresta:** `trilha`, `longe`, `arvore` (ao lado do tronco grande)
- **carro:** `motorista` (dirigindo, de costas para a câmera, atrás do volante), `carona` (banco do passageiro, de costas)
- **esgoto:** `fundo`, `meio`, `frente`
- **igreja:** `altar` (no altar, lá no fundo), `corredor`, `frente`, `banco_esq`, `banco_dir`
- **rua_amanhecer:** `centro`, `calcada_esq`, `calcada_dir`, `longe` (lá no fundo da rua (pequeno)), `longe_esq`, `longe_dir`, `carro` (ao lado do carro estacionado, à esquerda)

## Partes do corpo (mão e braço do personagem)

Em rádio e planos de detalhe, `"hand": "roberta"` desenha o braço com a manga e a pele da ficha do personagem; `{"of": "rafa", "at": "antena"}` escolhe a posição; `false` tira a mão. No `olho`, a pele em volta é a do personagem.

- **radio:** `dial` (girando o dial (padrão)), `antena` (segurando a antena), `botao` (apertando o botão de ligar), `repouso` (mão parada na mesa, ao lado do rádio)
- **chave:** `girando` (segurando a cabeça da chave, acompanha o giro (padrão))
- **macaneta:** `girando` (na ponta da maçaneta, acompanha o giro (padrão))
- **celular:** `segurando` (segurando o celular pela borda (padrão)), `dedo` (dedo tocando a tela)
