# Catálogo do motor

Gerado por `python3 -m lofi.catalogo --md CATALOGO.md` a partir do código. Não edite à mão.

**Cenários** (32): `apartamento`, `beco`, `camara_fria`, `carro`, `cftv`, `corredor`, `delegacia`, `deposito`, `entrada`, `entrada_metro`, `escada`, `escola`, `esgoto`, `estacionamento`, `floresta`, `hospital`, `igreja`, `janela`, `loja`, `mercado`, `metro`, `ponte`, `portao`, `posto`, `radio`, `radio_carro`, `radio_portatil`, `rua`, `rua_amanhecer`, `telhado`, `vagao`, `viaduto`

**Personagens prontos** (29): `bruxa`, `chef`, `cientista`, `cowboy`, `crianca`, `detetive`, `dj`, `estudante`, `estudante2`, `executiva`, `executivo`, `fantasma`, `lia`, `medica`, `pirata`, `policial`, `rafa`, `rainha`, `roberta`, `roqueiro`, `soldado`, `valter`, `vovo`, `vovo2`, `zombie`, `zombie_corredor`, `zombie_enfermeiro`, `zombie_policial`, `zombie_rastejante`

**Poses** (29): `carry`, `chest`, `crawl`, `cross`, `crouch`, `fallen`, `forward`, `hand_l`, `hand_r`, `hands_up`, `hide`, `hold`, `hug`, `idle`, `jump`, `knock`, `knock2`, `open_door`, `phone`, `point`, `pull`, `push`, `reach`, `reach_l`, `remove_bag`, `run`, `scared`, `sit`, `wave`

**Emoções** (10): `angry`, `cry`, `determined`, `fear`, `happy`, `neutral`, `panting`, `sad`, `shock`, `suspicious`

**Vistas** (4): `front`, `back`, `side`, `3q`

**Planos de detalhe (`subject`)** (5): `celular`, `chave`, `macaneta`, `olho`, `relogio`

**Sons (`sfx.name`)** (26): `bang`, `beep`, `bell`, `breath`, `car_alarm`, `click`, `crowd`, `door_close`, `door_open`, `echo_step`, `glass`, `growl`, `heartbeat`, `impact`, `knock`, `lock`, `no_service`, `notif`, `shuffle`, `siren`, `stamp`, `static`, `step`, `thunder`, `vibe`, `whoosh`

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
- **entrada_metro:** `calcada_esq` (na calçada, à esquerda), `frente` (na calçada, perto da câmera), `escada_topo` (no primeiro degrau, perto da câmera (prestes a descer ou acabando de subir)), `escada_baixo` (lá embaixo na escada, entrando na estação (pequeno, longe)), `longe` (lá no fundo da calçada)
- **radio_carro:** 
- **radio_portatil:** 
- **portao:** `portao` (no portão, saindo ou entrando no prédio), `calcada_esq`, `calcada_dir`, `frente` (na calçada, perto da câmera)
- **beco:** `fundo` (no fim do beco (pequeno)), `meio`, `frente`, `lixeira` (escondido atrás da lixeira)
- **viaduto:** `longe` (lá no fim do viaduto, perto da ponte), `meio`, `frente`, `mureta` (junto à mureta, olhando a cidade)
- **estacionamento:** `fundo`, `meio`, `frente`, `pilar` (escondido atrás do pilar)
- **vagao:** `porta` (na porta do fundo), `meio`, `frente`, `banco_esq` (perto do banco da esquerda), `banco_dir`
- **travelling (qualquer cenário com "travelling"):** `esq` (atrás na corrida (quem persegue/segue)), `centro`, `dir` (à frente na corrida), `fundo` (junto à parede/fachada), `frente` (na beira da calçada, perto da câmera)
- **loja:** `caixa` (atrás do balcão do caixa (o balcão tapa da cintura para baixo)), `balcao` (cliente na frente do balcão, à direita dele), `porta` (entrando pela porta de vidro (pequeno, no fundo)), `geladeira` (na frente das geladeiras, à direita), `centro`, `frente` (perto da câmera)
- **deposito:** `porta_camara` (colado na porta da câmara fria, de costas), `frente_porta` (de frente, diante da porta da câmara fria), `gerador` (ao lado do gerador), `centro`, `frente`
- **camara_fria:** `fundo` (lá no fundo, perto da porta), `meio`, `frente`
- **cftv:** 

## Travelling lateral (o cenário passa)

No plano: `"travelling": 320` (px/s; positivo = eles vão para a direita) ou `{"speed": 320, "frente": true}`. Os personagens ficam no lugar correndo/andando (`walk`, `run`, `facing` no sentido do movimento) e o cenário rola: cidade (rua, rua_amanhecer, entrada_metro, posto, telhado), mata (floresta), túnel (metro), esgoto, ponte e interno (corredor, hospital, escola, delegacia, mercado, igreja, casa). Use as marcas de travelling acima.


## Partes do corpo (mão e braço do personagem)

Em rádio e planos de detalhe, `"hand": "roberta"` desenha o braço com a manga e a pele da ficha do personagem; `{"of": "rafa", "at": "antena"}` escolhe a posição; `false` tira a mão. No `olho`, a pele em volta é a do personagem.

- **radio:** `dial` (girando o dial (padrão)), `antena` (segurando a antena), `botao` (apertando o botão de ligar), `repouso` (mão parada na mesa, ao lado do rádio)
- **radio_carro:** `dial` (girando a sintonia do rádio do carro (padrão)), `volume` (no botão de volume (braço vindo da esquerda: motorista))
- **radio_portatil:** `segurando` (segurando o rádio por baixo (padrão)), `dial` (girando a sintonia)
- **chave:** `girando` (segurando a cabeça da chave, acompanha o giro (padrão))
- **macaneta:** `girando` (na ponta da maçaneta, acompanha o giro (padrão))
- **celular:** `segurando` (segurando o celular pela borda (padrão)), `dedo` (dedo tocando a tela)
- **cftv:** `tela` (dedo apontando a tela do monitor (padrão)), `botao` (apertando o botão do monitor)
