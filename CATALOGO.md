# Catálogo do motor

Gerado por `python3 -m lofi.catalogo --md CATALOGO.md` a partir do código. Não edite à mão.

**Cenários** (74): `acampamento`, `apartamento`, `associacao`, `avenida`, `banheiro`, `beco`, `biblioteca`, `cabana`, `camara_fria`, `campo`, `carro`, `celeiro`, `cemiterio`, `cftv`, `consultorio`, `corredor`, `corredor_mercado`, `cozinha`, `delegacia`, `deposito`, `entrada`, `entrada_metro`, `escada`, `escola`, `escritorio`, `esgoto`, `estacionamento`, `estrada`, `farmacia`, `fenda`, `floresta`, `frente_casa`, `garagem`, `hortifruti`, `hospital`, `igreja`, `janela`, `laboratorio`, `lanchonete`, `lavanderia`, `loja`, `masmorra`, `mercado`, `metro`, `mezanino`, `oficina`, `parquinho`, `ponte`, `porao`, `portao`, `posto`, `praca`, `praia`, `quadra`, `quarto`, `quarto_crianca`, `quarto_hospital`, `quintal`, `radio`, `radio_carro`, `radio_portatil`, `rua`, `rua_amanhecer`, `rua_bairro`, `sala_aula`, `sala_espera`, `sala_estar`, `sotao`, `telhado`, `terreno_baldio`, `trono`, `vagao`, `velorio`, `viaduto`

**Personagens prontos** (29): `bruxa`, `chef`, `cientista`, `cowboy`, `crianca`, `detetive`, `dj`, `estudante`, `estudante2`, `executiva`, `executivo`, `fantasma`, `lia`, `medica`, `pirata`, `policial`, `rafa`, `rainha`, `roberta`, `roqueiro`, `soldado`, `valter`, `vovo`, `vovo2`, `zombie`, `zombie_corredor`, `zombie_enfermeiro`, `zombie_policial`, `zombie_rastejante`

**Poses** (51): `abracar_se`, `acenar`, `apontar_cima`, `carry`, `chamar`, `chao`, `chest`, `cocar_cabeca`, `cocar_nuca`, `comemorar`, `crawl`, `cross`, `crouch`, `dar_de_ombros`, `desespero`, `espiar_longe`, `explicar`, `fallen`, `forward`, `hand_l`, `hand_r`, `hands_up`, `hide`, `hold`, `hug`, `idle`, `implorar`, `jump`, `knock`, `knock2`, `mao_na_boca`, `maos_na_cintura`, `open_door`, `ouvir`, `pedir_calma`, `pensativo`, `phone`, `point`, `proteger_rosto`, `pull`, `punho`, `push`, `reach`, `reach_l`, `remove_bag`, `run`, `scared`, `segurar_barriga`, `silencio`, `sit`, `wave`

**Emoções** (10): `angry`, `cry`, `determined`, `fear`, `happy`, `neutral`, `panting`, `sad`, `shock`, `suspicious`

**Vistas** (4): `front`, `back`, `side`, `3q`

**Planos de detalhe (`subject`)** (5): `celular`, `chave`, `macaneta`, `olho`, `relogio`

**Sons (`sfx.name`)** (27): `bang`, `beep`, `bell`, `breath`, `car_alarm`, `click`, `crowd`, `door_close`, `door_open`, `echo_step`, `glass`, `growl`, `heartbeat`, `impact`, `knock`, `lock`, `no_service`, `notif`, `shuffle`, `sinal`, `siren`, `stamp`, `static`, `step`, `thunder`, `vibe`, `whoosh`

**Sons que aceitam `dur`** (5): `breath`, `crowd`, `heartbeat`, `sinal`, `static`

**Transições** (7): `cut`, `whip`, `flash`, `fade`, `zoom`, `glitch`, `dip`

**Acústicas** (5): `abafado`, `aberto`, `grande`, `media`, `sala`

**Objetos na mão (`prop`)** (7): `radio`, `flashlight`, `phone`, `handset`, `key`, `bag`, `adaga`

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
- **mezanino:** `centro`, `esq`, `dir`, `fundo` (na janela basculante do fundo, de costas), `guarda_corpo` (no guarda-corpo, olhando o vão da escada lá embaixo)
- **fenda:** `portal` (diante da Fenda, de costas (prestes a entrar)), `centro`, `esq`, `dir`, `frente` (perto da câmera, com a Fenda atrás)
- **masmorra:** `portal` (junto ao portal, lá no fundo (pequeno)), `fundo`, `meio`, `esq`, `dir`, `frente`
- **associacao:** `balcao` (de frente para o balcão, à direita dele), `painel` (olhando o painel de ranks, de costas), `centro`, `esq`, `dir`, `frente`
- **trono:** `trono` (ao pé do trono, lá no fundo), `meio`, `esq`, `dir`, `frente`
- **sala_aula:** `quadro` (diante do quadro, de costas (lendo as regras)), `mesa_prof` (atrás da mesa do professor), `porta` (na porta da sala, à esquerda), `carteira_esq`, `carteira_dir`, `meio` (no corredor entre as carteiras), `frente`
- **quadra:** `gol` (na frente do gol, lá no fundo), `area`, `arquibancada` (ao pé da arquibancada), `centro`, `dir`, `frente`
- **quarto:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `criado_mudo` (na frente de criado mudo), `cama` (na frente de cama), `guarda_roupa` (na frente de guarda roupa), `janela` (na frente de janela), `mochila` (ao lado de mochila)
- **quarto_crianca:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `beliche` (na frente de beliche), `comoda` (na frente de comoda), `berco` (na frente de berco), `janela` (na frente de janela), `cadeira_balanco` (ao lado de cadeira balanco), `brinquedo` (ao lado de brinquedo)
- **sala_estar:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `estante` (na frente de estante), `rack_tv` (na frente de rack tv), `planta` (na frente de planta), `abajur` (na frente de abajur), `janela` (na frente de janela), `sofa` (ao lado de sofa), `poltrona` (ao lado de poltrona)
- **cozinha:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `geladeira` (na frente de geladeira), `pia_cozinha` (na frente de pia cozinha), `fogao` (na frente de fogao), `armario` (na frente de armario), `janela` (na frente de janela), `mesa_cozinha` (ao lado de mesa cozinha), `cadeira` (ao lado de cadeira)
- **banheiro:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `privada` (na frente de privada), `pia_banheiro` (na frente de pia banheiro), `banheira` (na frente de banheira)
- **lavanderia:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `maquina_lavar` (na frente de maquina lavar), `maquina_lavar2` (na frente de maquina lavar), `pia_cozinha` (na frente de pia cozinha)
- **porao:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `pilha_caixas` (na frente de pilha caixas), `tambor` (na frente de tambor), `estante` (na frente de estante), `caixa` (na frente de caixa), `caixa2` (ao lado de caixa)
- **sotao:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `pilha_caixas` (na frente de pilha caixas), `caixa` (na frente de caixa), `janela` (na frente de janela), `cadeira_balanco` (ao lado de cadeira balanco), `brinquedo` (ao lado de brinquedo)
- **cabana:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `estante` (na frente de estante), `lareira` (na frente de lareira), `janela` (na frente de janela), `mesa` (ao lado de mesa), `cadeira_balanco` (ao lado de cadeira balanco)
- **velorio:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `planta` (na frente de planta), `caixao` (na frente de caixao), `planta2` (na frente de planta), `mesa` (ao lado de mesa), `mesa2` (ao lado de mesa), `cadeira` (ao lado de cadeira), `cadeira2` (ao lado de cadeira)
- **corredor_mercado:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `prateleira` (na frente de prateleira)
- **hortifruti:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `janela` (na frente de janela), `banca_frutas` (ao lado de banca frutas), `banca_frutas2` (ao lado de banca frutas), `banca_frutas3` (ao lado de banca frutas)
- **farmacia:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `prateleira` (na frente de prateleira), `prateleira2` (na frente de prateleira), `prateleira3` (na frente de prateleira), `balcao` (ao lado de balcao)
- **lanchonete:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `expositor` (na frente de expositor), `balcao` (ao lado de balcao), `banco` (ao lado de banco), `banco2` (ao lado de banco)
- **escritorio:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `arquivo` (na frente de arquivo), `planta` (na frente de planta), `janela` (na frente de janela), `mesa_escritorio` (ao lado de mesa escritorio), `cadeira_escritorio` (ao lado de cadeira escritorio)
- **biblioteca:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `estante` (na frente de estante), `estante2` (na frente de estante), `estante3` (na frente de estante), `estante4` (na frente de estante), `mesa` (ao lado de mesa), `cadeira` (ao lado de cadeira)
- **laboratorio:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `armario` (na frente de armario), `bancada` (na frente de bancada), `geladeira` (na frente de geladeira), `bancada2` (ao lado de bancada)
- **oficina:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `estante` (na frente de estante), `mesa` (na frente de mesa), `gerador` (na frente de gerador), `tambor` (na frente de tambor), `extintor` (ao lado de extintor), `escada_mao` (ao lado de escada mao)
- **garagem:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `porta` (na frente de porta), `estante` (na frente de estante), `bicicleta` (ao lado de bicicleta), `tambor` (na frente de tambor)
- **consultorio:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `armario` (na frente de armario), `maca` (na frente de maca), `pia_banheiro` (na frente de pia banheiro), `cadeira` (ao lado de cadeira)
- **quarto_hospital:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `suporte_soro` (na frente de suporte soro), `maca` (na frente de maca), `criado_mudo` (na frente de criado mudo), `janela` (na frente de janela), `cadeira` (ao lado de cadeira)
- **sala_espera:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `balcao` (na frente de balcao), `planta` (na frente de planta), `banco` (ao lado de banco)
- **celeiro:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `feno` (na frente de feno), `feno2` (na frente de feno), `porta` (na frente de porta), `tambor` (na frente de tambor), `escada_mao` (ao lado de escada mao), `feno3` (ao lado de feno)
- **quintal:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `muro` (ao lado de muro), `arvore` (ao lado de arvore), `varal` (ao lado de varal), `bicicleta` (ao lado de bicicleta), `lixeira` (ao lado de lixeira)
- **frente_casa:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `casa` (ao lado de casa), `cerca` (ao lado de cerca), `caixa_correio` (ao lado de caixa correio), `poste` (ao lado de poste), `arbusto` (ao lado de arbusto)
- **rua_bairro:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `casa` (ao lado de casa), `casa2` (ao lado de casa), `poste` (ao lado de poste), `poste2` (ao lado de poste), `carro` (ao lado de carro), `hidrante` (ao lado de hidrante)
- **avenida:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `predio` (ao lado de predio), `predio2` (ao lado de predio), `ponto_onibus` (ao lado de ponto onibus), `orelhao` (ao lado de orelhao), `poste` (ao lado de poste), `placa_rua` (ao lado de placa rua)
- **praca:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `arvore` (ao lado de arvore), `arvore2` (ao lado de arvore), `poste` (ao lado de poste), `banco_praca` (ao lado de banco praca), `lixeira` (ao lado de lixeira), `arbusto` (ao lado de arbusto)
- **parquinho:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `arvore` (ao lado de arvore), `balanco` (ao lado de balanco), `escorregador` (ao lado de escorregador), `banco_praca` (ao lado de banco praca), `brinquedo` (ao lado de brinquedo)
- **estrada:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `arvore` (ao lado de arvore), `arvore2` (ao lado de arvore), `placa_rua` (ao lado de placa rua), `cruz_estrada` (ao lado de cruz estrada), `poste` (ao lado de poste)
- **campo:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `casa` (ao lado de casa), `arvore` (ao lado de arvore), `cerca` (ao lado de cerca), `poco` (ao lado de poco), `feno` (ao lado de feno)
- **cemiterio:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `muro` (ao lado de muro), `arvore` (ao lado de arvore), `lapide` (ao lado de lapide), `lapide2` (ao lado de lapide), `lapide3` (ao lado de lapide), `lapide4` (ao lado de lapide), `lapide5` (ao lado de lapide), `lapide6` (ao lado de lapide), `cruz_estrada` (ao lado de cruz estrada)
- **acampamento:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `arvore` (ao lado de arvore), `arvore2` (ao lado de arvore), `barraca` (ao lado de barraca), `fogueira` (ao lado de fogueira), `pedra` (ao lado de pedra), `mochila` (ao lado de mochila)
- **praia:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `arvore` (ao lado de arvore), `barco` (ao lado de barco), `guarda_sol` (ao lado de guarda sol)
- **terreno_baldio:** `centro`, `esq`, `dir`, `fundo` (perto da parede do fundo (pequeno)), `frente` (perto da câmera), `muro` (ao lado de muro), `lixeira_rua` (ao lado de lixeira rua), `arbusto` (ao lado de arbusto), `tambor` (ao lado de tambor), `poste` (ao lado de poste)

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

## Cenário generativo (lofi/cenario_gen.py)

Ambientes prontos (use em `"scene"`) ou descrição no plano: `"cenario": {"base": "cozinha", "luz": "escuro", "mais": [{"m": "cracha", "em": "chao", "x": 0.3, "z": 0.6}], "sem": ["mesa_cozinha"], "mudar": [{"m": "geladeira", "aberta": true}]}`. Close do objeto da frase: `"cenario": {"close": "lata", "superficie": "prateleira", "ambiente": "corredor_mercado"}` com props `n`, `desliza`, `treme`, `cai`, `mao` (e `"hand": "<personagem>"`). Folha com todos: [`examples/ambientes.jpg`](examples/ambientes.jpg).

- **quarto** (interior): quarto de dormir: cama, criado-mudo com abajur, guarda-roupa, janela
- **quarto_crianca** (interior): quarto de criança: beliche, brinquedos, berço, cadeira de balanço
- **sala_estar** (interior): sala de estar: sofá, TV, poltrona, estante, abajur
- **cozinha** (interior): cozinha: geladeira, pia, fogão, armário, mesa com toalha
- **banheiro** (interior): banheiro: privada, pia com espelho, banheira e chuveiro
- **lavanderia** (interior): área de serviço: máquinas de lavar, tanque, prateleira
- **porao** (interior): porão: tijolo, caixas, tambores, lâmpada pelada
- **sotao** (interior): sótão: teto inclinado, caixas velhas, cadeira de balanço, espelho coberto
- **cabana** (interior): cabana na mata: lareira acesa, mesa, cadeira de balanço, janela para as árvores
- **velorio** (interior): sala de velório: caixão, velas, flores, cadeiras, crucifixo
- **corredor_mercado** (interior): corredor de mercado: gôndolas dos dois lados (latas, milho, feijão, arroz), placa no fundo
- **hortifruti** (interior): hortifrúti: bancas de frutas e legumes, vidro lateral para a rua
- **farmacia** (interior): farmácia: prateleiras de remédio, balcão, placa verde
- **lanchonete** (interior): lanchonete: balcão com banquetas, expositor de bebidas, placa LANCHES
- **escritorio** (interior): escritório: mesa com computador, arquivo, mural, janela com persiana
- **biblioteca** (interior): biblioteca: estantes até o teto, mesa de leitura com luminária
- **laboratorio** (interior): laboratório: bancadas com frascos, armário, aviso de perigo
- **oficina** (interior): oficina/garagem: ferramentas, tambor, gerador, escada, extintor
- **garagem** (interior): garagem de casa: porta de aço, bicicleta, prateleira de ferramentas
- **consultorio** (interior): consultório: maca, armário, pia, mural
- **quarto_hospital** (interior): quarto de hospital: leito ocupado, soro, cadeira, janela com persiana
- **sala_espera** (interior): sala de espera/recepção: fileira de cadeiras, TV na parede, relógio, balcão
- **celeiro** (interior): celeiro: fardos de feno, tambor, escada, lampião
- **quintal** (exterior): quintal de casa: muro, árvore, varal, bicicleta
- **frente_casa** (exterior): frente de uma casa: fachada, cerca, caixa de correio, poste
- **rua_bairro** (exterior): rua residencial: casas no fundo, postes, carro estacionado
- **avenida** (exterior): avenida: prédios, ponto de ônibus, orelhão, poste
- **praca** (exterior): praça: árvores, banco, poste, lixeira
- **parquinho** (exterior): parquinho: balanço, escorregador, banco, árvores
- **estrada** (exterior): estrada no meio do mato: faixa no meio, placa, cruz na beira
- **campo** (exterior): campo/fazenda: cerca de madeira, poço, celeiro vermelho, árvore
- **cemiterio** (exterior): cemitério: lápides em fileiras, árvore seca, muro, névoa
- **acampamento** (exterior): acampamento na mata: barraca, fogueira acesa, pinheiros
- **praia** (exterior): praia: mar no horizonte, guarda-sol, barco na areia, palmeira
- **terreno_baldio** (exterior): terreno baldio: muro pichado, caçamba, mato, pneus

**Paredes:** `pintada`, `azulejo`, `tijolo`, `madeira`, `concreto`, `papel_parede`, `listrado` · **Pisos/chão:** `taco`, `madeira`, `ceramica`, `xadrez`, `concreto`, `carpete`, `terra`, `grama`, `areia`, `asfalto`

**Luz (`luz`):** `quente`, `fria`, `fluorescente`, `dia`, `neutra`, `escuro`, `noite`, `vela`, `emergencia`, `tv`, `amanhecer`, `entardecer` · **Horizonte (externos):** `cidade`, `casas`, `mata`, `morros`, `mar`, `nada` · **Hora:** `dia`, `entardecer`, `amanhecer`, `noite`, `madrugada`

**Conteúdo de prateleira (`conteudo`):** `latas`, `milho`, `feijao`, `arroz`, `agua`, `garrafas`, `refri`, `caixas`, `cereal`, `remedios`, `livros`, `potes`, `ferramentas`, `papel`, `biscoito`, `racao`, `vazia`

**Superfícies do close:** `prateleira`, `chao`, `mesa`, `balcao`, `parede`, `nenhuma`

**No chão (encostado ou solto)** (52): `abajur`, `armario`, `arquivo`, `balcao`, `banca_frutas`, `bancada`, `banco`, `banheira`, `beliche`, `berco`, `bicicleta`, `botijao`, `cabideiro`, `cadeira`, `cadeira_balanco`, `cadeira_escritorio`, `cadeira_rodas`, `caixa`, `caixao`, `cama`, `carrinho`, `comoda`, `criado_mudo`, `escada_mao`, `estante`, `expositor`, `extintor`, `feno`, `fogao`, `freezer`, `geladeira`, `gerador`, `guarda_roupa`, `lareira`, `lixeira`, `maca`, `maquina_lavar`, `mesa`, `mesa_cozinha`, `mesa_escritorio`, `pia_banheiro`, `pia_cozinha`, `piano`, `pilha_caixas`, `planta`, `poltrona`, `prateleira`, `privada`, `rack_tv`, `sofa`, `suporte_soro`, `tambor`

**Na parede** (16): `ar_condicionado`, `armario_alto`, `calendario`, `camera_seguranca`, `chuveiro`, `cruz`, `espelho`, `janela`, `placa`, `porta`, `prateleira_parede`, `quadro`, `quadro_avisos`, `quadro_energia`, `relogio_parede`, `tv_parede`

**No teto** (4): `fluorescente`, `lampada`, `lustre`, `ventilador_teto`

**Pequenos, caídos no chão** (16): `brinquedo`, `cadeado`, `celular`, `chave`, `cracha`, `garrafa_caida`, `lanterna`, `lata_caida`, `livro_chao`, `mancha`, `mochila`, `palete`, `pegadas`, `poca`, `sapato`, `tapete`

**Em cima de mesa/balcão (`itens`)** (15): `abajur_mesa`, `caixa_registradora`, `caixa_remedio`, `celular_mesa`, `copo`, `garrafa`, `lata`, `notebook`, `papel`, `prancheta`, `prato`, `radinho`, `telefone`, `vaso_flor`, `vela`

**Externos** (31): `ambulancia`, `arbusto`, `arvore`, `balanco`, `banco_praca`, `barco`, `barraca`, `caixa_correio`, `caixa_dagua`, `carro`, `casa`, `cerca`, `cruz_estrada`, `escorregador`, `fogueira`, `guarda_sol`, `hidrante`, `lapide`, `lixeira_rua`, `moto`, `muro`, `orelhao`, `pedra`, `placa_rua`, `poco`, `ponto_onibus`, `portao`, `poste`, `predio`, `varal`, `viatura`
