"""Cenário generativo: monta o cenário a partir de uma descrição (ambiente + materiais + luz + móveis), em vez de uma
classe desenhada à mão. Serve para mostrar ao pé da letra o que a narração diz: cada frase pode ter o seu cenário, com
exatamente os móveis, o estado (porta aberta, TV chiando, luz apagada) e o objeto em close.

No roteiro técnico (plano):

    "scene": "cozinha"                                      -> ambiente pronto (lista em AMBIENTES / CATALOGO.md)
    "cenario": {"base": "cozinha", "luz": "escuro",         -> ambiente pronto com mudanças
                "mais": [{"m": "faca"...}], "sem": ["mesa_cozinha"], "hora": "noite"}
    "cenario": {"tipo": "interior", "parede": ["azulejo", [200, 210, 200]], "piso": "xadrez",
                "luz": "fria", "moveis": [{"m": "geladeira", "em": "fundo", "x": 0.2, "aberta": true}, ...]}
    "cenario": {"close": "lata", "superficie": "prateleira", "ambiente": "corredor_mercado", "n": 3}
                                                            -> close do objeto (o "inserto" da frase)

Cada móvel: {"m": nome, "em": "fundo" | "parede" | "teto" | "chao" | "esq" | "dir" | "frente", "x": 0–1 (ao longo da
parede ou do chão), "z": 0–1 (profundidade no chão: 0 = parede do fundo, 1 = perto da câmera), "h": cm do chão (parede),
"id": nome da marca}. Qualquer outra chave vai para o desenho do objeto (cor, aberta, aceso, texto, conteudo...).
Sem "em"/"x", o gerador escolhe o lugar sozinho. Marcas de posição saem automáticas: centro, esq, dir, fundo, frente e
uma marca na frente de cada móvel (o nome do móvel ou o "id").

O cenário gerado é registrado em lofi/scenes.py (REGISTRY) e em lofi/mapa.py (chão e marcas) com um nome estável
("gen_<hash>"), então render, verificador, mapa, áudio e continuidade tratam como qualquer outro cenário.

    python3 -m lofi.cenario_gen                      -> folha de todos os ambientes em examples/ambientes.png
    python3 -m lofi.cenario_gen cozinha quarto       -> _amb_<nome>.png de cada um
"""
import copy, hashlib, json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter
from .core import add_light, grad, lerp, font
from . import moveis as MV
from .moveis import MOVEIS, K_CM, esc

KP = 1.18                      # escala_personagens padrão dos episódios novos (os móveis acompanham o tamanho das pessoas)

# ============================== AMBIENTES PRONTOS ==============================
LUZES = {        # luz do lugar: (luz dos personagens, tratamento de cor, brilho geral 0–1, cor da luz ambiente)
    "quente":      ("warm", "quente", 0.92, (255, 200, 130)),
    "fria":        ("neutra", "frio", 1.0, (210, 236, 240)),
    "fluorescente": ("neutra", "frio", 1.0, (210, 240, 230)),
    "dia":         ("neutra", "neutro", 1.0, (255, 250, 236)),
    "neutra":      ("neutra", "neutro", 1.0, (240, 240, 240)),
    "escuro":      ("dark", "noite", 0.42, (90, 110, 170)),
    "noite":       ("night", "noite", 0.62, (110, 130, 200)),
    "vela":        ("warm", "quente", 0.5, (255, 160, 70)),
    "emergencia":  ("red", "emergencia", 0.55, (255, 60, 50)),
    "tv":          ("tv", "noite", 0.5, (80, 120, 230)),
    "amanhecer":   ("dawn", "amanhecer", 0.85, (240, 190, 170)),
    "entardecer":  ("warm", "quente", 0.85, (255, 170, 100)),
}

AMBIENTES = {
    # ---------------- casa ----------------
    "quarto": dict(tipo="interior", parede=("pintada", (120, 130, 160)), piso="taco", luz="quente", acoustic="sala",
                   nota="quarto de dormir: cama, criado-mudo com abajur, guarda-roupa, janela",
                   moveis=[{"m": "criado_mudo", "x": 0.12}, {"m": "cama", "x": 0.42}, {"m": "guarda_roupa", "x": 0.84},
                           {"m": "janela", "em": "parede", "x": 0.2, "h": 100, "vista": "noite"}, {"m": "quadro", "em": "parede", "x": 0.42, "h": 135},
                           {"m": "lampada", "em": "teto", "x": 0.5, "z": 0.3}, {"m": "tapete", "em": "chao", "x": 0.5, "z": 0.45, "cor": (90, 70, 110)},
                           {"m": "mochila", "em": "chao", "x": 0.82, "z": 0.55}]),
    "quarto_crianca": dict(tipo="interior", parede=("listrado", (170, 190, 210)), piso="taco", luz="noite", acoustic="sala",
                           nota="quarto de criança: beliche, brinquedos, berço, cadeira de balanço",
                           moveis=[{"m": "beliche", "x": 0.18}, {"m": "comoda", "x": 0.5, "itens": ["vaso_flor", "abajur_mesa"]}, {"m": "berco", "x": 0.82},
                                   {"m": "janela", "em": "parede", "x": 0.5, "h": 120, "vista": "noite", "cor_cortina": (230, 190, 200)},
                                   {"m": "cadeira_balanco", "em": "chao", "x": 0.2, "z": 0.45}, {"m": "brinquedo", "em": "chao", "x": 0.62, "z": 0.5},
                                   {"m": "tapete", "em": "chao", "x": 0.5, "z": 0.42, "cor": (120, 160, 200)}]),
    "sala_estar": dict(tipo="interior", parede=("papel_parede", (150, 130, 110)), piso="taco", luz="quente", acoustic="sala",
                       nota="sala de estar: sofá, TV, poltrona, estante, abajur",
                       moveis=[{"m": "estante", "x": 0.08}, {"m": "rack_tv", "x": 0.38}, {"m": "planta", "x": 0.6}, {"m": "abajur", "x": 0.7},
                               {"m": "janela", "em": "parede", "x": 0.82, "h": 95, "vista": "cidade"}, {"m": "quadro", "em": "parede", "x": 0.38, "h": 150},
                               {"m": "sofa", "em": "chao", "x": 0.72, "z": 0.48}, {"m": "poltrona", "em": "chao", "x": 0.12, "z": 0.5},
                               {"m": "tapete", "em": "chao", "x": 0.45, "z": 0.45}, {"m": "ventilador_teto", "em": "teto", "x": 0.5, "z": 0.35}]),
    "cozinha": dict(tipo="interior", parede=("azulejo", (214, 222, 214)), piso="xadrez", luz="fria", acoustic="sala",
                    nota="cozinha: geladeira, pia, fogão, armário, mesa com toalha",
                    moveis=[{"m": "geladeira", "x": 0.1}, {"m": "pia_cozinha", "x": 0.4}, {"m": "fogao", "x": 0.66}, {"m": "armario", "x": 0.88, "alt": 90, "larg": 70},
                            {"m": "armario_alto", "em": "parede", "x": 0.42, "h": 150}, {"m": "janela", "em": "parede", "x": 0.75, "h": 120, "larg": 80, "cortina": False},
                            {"m": "relogio_parede", "em": "parede", "x": 0.18, "h": 205}, {"m": "fluorescente", "em": "teto", "x": 0.5, "z": 0.3},
                            {"m": "mesa_cozinha", "em": "chao", "x": 0.55, "z": 0.5, "itens": ["prato", "copo"]}, {"m": "cadeira", "em": "chao", "x": 0.3, "z": 0.5}]),
    "banheiro": dict(tipo="interior", parede=("azulejo", (190, 214, 220)), piso="ceramica", luz="fria", acoustic="media", largura=300,
                     nota="banheiro: privada, pia com espelho, banheira e chuveiro",
                     moveis=[{"m": "privada", "x": 0.15}, {"m": "pia_banheiro", "x": 0.42}, {"m": "banheira", "x": 0.78},
                             {"m": "espelho", "em": "parede", "x": 0.42, "h": 110}, {"m": "chuveiro", "em": "parede", "x": 0.86, "h": 190},
                             {"m": "lampada", "em": "teto", "x": 0.5, "z": 0.3, "cor_luz": (230, 240, 255)}]),
    "lavanderia": dict(tipo="interior", parede=("azulejo", (230, 230, 220)), piso="ceramica", luz="fria", acoustic="sala", largura=320,
                       nota="área de serviço: máquinas de lavar, tanque, prateleira",
                       moveis=[{"m": "maquina_lavar", "x": 0.18}, {"m": "maquina_lavar", "x": 0.4}, {"m": "pia_cozinha", "x": 0.75, "cor": (200, 200, 200)},
                               {"m": "prateleira_parede", "em": "parede", "x": 0.3, "h": 150, "conteudo": "potes"}, {"m": "lampada", "em": "teto", "x": 0.5, "z": 0.3}]),
    "porao": dict(tipo="interior", parede=("tijolo", (110, 80, 66)), piso="concreto", luz="escuro", acoustic="media", amb="eco",
                  nota="porão: tijolo, caixas, tambores, lâmpada pelada",
                  moveis=[{"m": "pilha_caixas", "x": 0.15}, {"m": "tambor", "x": 0.4}, {"m": "estante", "x": 0.62, "conteudo": "potes", "cor": (90, 90, 96)},
                          {"m": "caixa", "x": 0.85}, {"m": "lampada", "em": "teto", "x": 0.5, "z": 0.3, "fio": 70},
                          {"m": "caixa", "em": "chao", "x": 0.25, "z": 0.5, "aberta": True}, {"m": "poca", "em": "chao", "x": 0.7, "z": 0.55}]),
    "sotao": dict(tipo="interior", parede=("madeira", (120, 86, 56)), piso="madeira", luz="escuro", acoustic="sala", teto="inclinado",
                  nota="sótão: teto inclinado, caixas velhas, cadeira de balanço, espelho coberto",
                  moveis=[{"m": "pilha_caixas", "x": 0.15, "alt": 100}, {"m": "espelho", "x": 0.5, "em": "parede", "h": 30, "alt": 110},
                          {"m": "caixa", "x": 0.85}, {"m": "janela", "em": "parede", "x": 0.5, "h": 160, "larg": 50, "alt": 50, "cortina": False, "vista": "noite"},
                          {"m": "cadeira_balanco", "em": "chao", "x": 0.3, "z": 0.45}, {"m": "brinquedo", "em": "chao", "x": 0.7, "z": 0.5},
                          {"m": "lampada", "em": "teto", "x": 0.5, "z": 0.3, "fio": 30}]),
    "cabana": dict(tipo="interior", parede=("madeira", (130, 90, 56)), piso="madeira", luz="vela", acoustic="sala",
                   nota="cabana na mata: lareira acesa, mesa, cadeira de balanço, janela para as árvores",
                   moveis=[{"m": "estante", "x": 0.1, "conteudo": "potes"}, {"m": "lareira", "x": 0.48}, {"m": "janela", "em": "parede", "x": 0.85, "h": 100, "vista": "arvores"},
                           {"m": "mesa", "em": "chao", "x": 0.75, "z": 0.48, "itens": ["vela", "prato"]}, {"m": "cadeira_balanco", "em": "chao", "x": 0.25, "z": 0.5},
                           {"m": "tapete", "em": "chao", "x": 0.5, "z": 0.45, "cor": (120, 60, 40)}]),
    "velorio": dict(tipo="interior", parede=("pintada", (170, 160, 150)), piso="ceramica", luz="vela", acoustic="media",
                    nota="sala de velório: caixão, velas, flores, cadeiras, crucifixo",
                    moveis=[{"m": "planta", "x": 0.12}, {"m": "caixao", "x": 0.5}, {"m": "planta", "x": 0.88},
                            {"m": "cruz", "em": "parede", "x": 0.5, "h": 150}, {"m": "mesa", "x": 0.2, "em": "chao", "z": 0.25, "larg": 50, "itens": ["vela", "vela"]},
                            {"m": "mesa", "x": 0.8, "em": "chao", "z": 0.25, "larg": 50, "itens": ["vela", "vaso_flor"]},
                            {"m": "cadeira", "em": "chao", "x": 0.15, "z": 0.6}, {"m": "cadeira", "em": "chao", "x": 0.85, "z": 0.6}]),
    # ---------------- comércio e trabalho ----------------
    "corredor_mercado": dict(tipo="interior", parede=("pintada", (210, 214, 210)), piso="ceramica", luz="fluorescente", acoustic="media", amb="zumbido",
                             largura=260, lateral={"m": "prateleira", "conteudo": ["latas", "milho", "feijao", "arroz", "garrafas"]},
                             nota="corredor de mercado: gôndolas dos dois lados (latas, milho, feijão, arroz), placa no fundo",
                             moveis=[{"m": "prateleira", "x": 0.5, "conteudo": ["milho", "latas"], "texto": "ENLATADOS"},
                                     {"m": "placa", "em": "parede", "x": 0.5, "h": 215, "texto": "OFERTAS"},
                                     {"m": "fluorescente", "em": "teto", "x": 0.5, "z": 0.15}, {"m": "fluorescente", "em": "teto", "x": 0.5, "z": 0.45}]),
    "hortifruti": dict(tipo="interior", parede=("azulejo", (220, 230, 210)), piso="ceramica", luz="fluorescente", acoustic="media", amb="zumbido",
                       nota="hortifrúti: bancas de frutas e legumes, vidro lateral para a rua",
                       moveis=[{"m": "janela", "em": "parede", "x": 0.5, "h": 40, "larg": 360, "alt": 170, "vista": "cidade", "cortina": False},
                               {"m": "banca_frutas", "em": "chao", "x": 0.25, "z": 0.3}, {"m": "banca_frutas", "em": "chao", "x": 0.75, "z": 0.3, "seed": 9},
                               {"m": "banca_frutas", "em": "chao", "x": 0.5, "z": 0.55, "seed": 4}, {"m": "placa", "em": "parede", "x": 0.5, "h": 225, "texto": "HORTIFRÚTI", "cor": (60, 140, 70)},
                               {"m": "fluorescente", "em": "teto", "x": 0.5, "z": 0.3}]),
    "farmacia": dict(tipo="interior", parede=("pintada", (236, 240, 236)), piso="ceramica", luz="fluorescente", acoustic="media",
                     nota="farmácia: prateleiras de remédio, balcão, placa verde",
                     moveis=[{"m": "prateleira", "x": 0.15, "conteudo": "remedios", "cor_topo": (40, 150, 80)}, {"m": "prateleira", "x": 0.5, "conteudo": "remedios", "cor_topo": (40, 150, 80)},
                             {"m": "prateleira", "x": 0.85, "conteudo": ["papel", "remedios"], "cor_topo": (40, 150, 80)},
                             {"m": "placa", "em": "parede", "x": 0.5, "h": 225, "texto": "FARMÁCIA", "cor": (40, 150, 80)},
                             {"m": "balcao", "em": "chao", "x": 0.5, "z": 0.55, "cor": (230, 230, 230), "itens": ["caixa_registradora", "caixa_remedio"]},
                             {"m": "fluorescente", "em": "teto", "x": 0.5, "z": 0.3}]),
    "lanchonete": dict(tipo="interior", parede=("azulejo", (230, 200, 160)), piso="xadrez", luz="quente", acoustic="sala",
                       nota="lanchonete: balcão com banquetas, expositor de bebidas, placa LANCHES",
                       moveis=[{"m": "expositor", "x": 0.15}, {"m": "prateleira_parede", "em": "parede", "x": 0.6, "h": 150, "conteudo": "garrafas"},
                               {"m": "placa", "em": "parede", "x": 0.6, "h": 210, "texto": "LANCHES", "acesa": True},
                               {"m": "balcao", "em": "chao", "x": 0.6, "z": 0.3, "larg": 260, "cor": (180, 60, 50), "itens": ["caixa_registradora", "copo", "prato"]},
                               {"m": "banco", "em": "chao", "x": 0.4, "z": 0.5, "larg": 40}, {"m": "banco", "em": "chao", "x": 0.7, "z": 0.5, "larg": 40},
                               {"m": "lampada", "em": "teto", "x": 0.35, "z": 0.3}, {"m": "lampada", "em": "teto", "x": 0.7, "z": 0.3}]),
    "escritorio": dict(tipo="interior", parede=("pintada", (190, 196, 200)), piso="carpete", luz="fluorescente", acoustic="sala",
                       nota="escritório: mesa com computador, arquivo, mural, janela com persiana",
                       moveis=[{"m": "arquivo", "x": 0.1}, {"m": "planta", "x": 0.88}, {"m": "janela", "em": "parede", "x": 0.6, "h": 100, "persiana": True, "cortina": False, "vista": "cidade"},
                               {"m": "quadro_avisos", "em": "parede", "x": 0.25, "h": 120}, {"m": "relogio_parede", "em": "parede", "x": 0.88, "h": 200},
                               {"m": "mesa_escritorio", "em": "chao", "x": 0.5, "z": 0.35}, {"m": "cadeira_escritorio", "em": "chao", "x": 0.55, "z": 0.5},
                               {"m": "fluorescente", "em": "teto", "x": 0.5, "z": 0.3}]),
    "biblioteca": dict(tipo="interior", parede=("madeira", (110, 76, 50)), piso="taco", luz="quente", acoustic="media",
                       nota="biblioteca: estantes até o teto, mesa de leitura com luminária",
                       moveis=[{"m": "estante", "x": 0.1, "alt": 230}, {"m": "estante", "x": 0.37, "alt": 230}, {"m": "estante", "x": 0.63, "alt": 230}, {"m": "estante", "x": 0.9, "alt": 230},
                               {"m": "mesa", "em": "chao", "x": 0.5, "z": 0.5, "larg": 180, "itens": ["abajur_mesa", "papel", "abajur_mesa"]},
                               {"m": "cadeira", "em": "chao", "x": 0.3, "z": 0.55}, {"m": "lustre", "em": "teto", "x": 0.5, "z": 0.3}]),
    "laboratorio": dict(tipo="interior", parede=("azulejo", (220, 230, 236)), piso="ceramica", luz="fria", acoustic="media", amb="zumbido",
                        nota="laboratório: bancadas com frascos, armário, aviso de perigo",
                        moveis=[{"m": "armario", "x": 0.1, "cor": (200, 206, 210)}, {"m": "bancada", "x": 0.5}, {"m": "geladeira", "x": 0.9, "cor": (236, 240, 244)},
                                {"m": "placa", "em": "parede", "x": 0.5, "h": 200, "texto": "RISCO BIOLÓGICO", "cor": (240, 200, 40), "cor_texto": (30, 30, 30)},
                                {"m": "bancada", "em": "chao", "x": 0.5, "z": 0.5, "seed": 8}, {"m": "fluorescente", "em": "teto", "x": 0.5, "z": 0.3}]),
    "oficina": dict(tipo="interior", parede=("concreto", (130, 130, 126)), piso="concreto", luz="fluorescente", acoustic="media",
                    nota="oficina/garagem: ferramentas, tambor, gerador, escada, extintor",
                    moveis=[{"m": "estante", "x": 0.12, "conteudo": "ferramentas", "cor": (90, 96, 100)}, {"m": "mesa", "x": 0.42, "larg": 160, "cor": (110, 100, 90), "itens": ["lata", "garrafa"]},
                            {"m": "gerador", "x": 0.72}, {"m": "tambor", "x": 0.9}, {"m": "extintor", "em": "chao", "x": 0.05, "z": 0.2},
                            {"m": "escada_mao", "em": "chao", "x": 0.88, "z": 0.4}, {"m": "fluorescente", "em": "teto", "x": 0.5, "z": 0.3},
                            {"m": "mancha", "em": "chao", "x": 0.5, "z": 0.55}]),
    "garagem": dict(tipo="interior", parede=("concreto", (150, 150, 146)), piso="concreto", luz="fluorescente", acoustic="media", largura=560,
                    nota="garagem de casa: porta de aço, bicicleta, prateleira de ferramentas",
                    moveis=[{"m": "porta", "x": 0.5, "tipo": "aco", "larg": 300, "alt": 230}, {"m": "estante", "x": 0.08, "conteudo": "ferramentas", "cor": (90, 96, 100)},
                            {"m": "bicicleta", "em": "chao", "x": 0.85, "z": 0.25}, {"m": "tambor", "x": 0.93}, {"m": "lampada", "em": "teto", "x": 0.5, "z": 0.3},
                            {"m": "mancha", "em": "chao", "x": 0.45, "z": 0.45}]),
    "consultorio": dict(tipo="interior", parede=("pintada", (210, 226, 226)), piso="ceramica", luz="fria", acoustic="sala",
                        nota="consultório: maca, armário, pia, mural",
                        moveis=[{"m": "armario", "x": 0.12, "cor": (230, 230, 230), "alt": 160}, {"m": "maca", "x": 0.55, "lencol": True}, {"m": "pia_banheiro", "x": 0.9},
                                {"m": "quadro_avisos", "em": "parede", "x": 0.5, "h": 140}, {"m": "cadeira", "em": "chao", "x": 0.2, "z": 0.5, "cor": (60, 90, 140)},
                                {"m": "fluorescente", "em": "teto", "x": 0.5, "z": 0.3}]),
    "quarto_hospital": dict(tipo="interior", parede=("pintada", (200, 220, 214)), piso="ceramica", luz="fria", acoustic="sala", amb="zumbido",
                            nota="quarto de hospital: leito ocupado, soro, cadeira, janela com persiana",
                            moveis=[{"m": "suporte_soro", "x": 0.22}, {"m": "maca", "x": 0.5, "ocupada": True}, {"m": "criado_mudo", "x": 0.85, "itens": ["copo", "caixa_remedio"]},
                                    {"m": "janela", "em": "parede", "x": 0.82, "h": 110, "persiana": True, "cortina": False, "vista": "noite"},
                                    {"m": "tv_parede", "em": "parede", "x": 0.3, "h": 190}, {"m": "cadeira", "em": "chao", "x": 0.18, "z": 0.55, "cor": (60, 110, 120)},
                                    {"m": "fluorescente", "em": "teto", "x": 0.5, "z": 0.3}]),
    "sala_espera": dict(tipo="interior", parede=("pintada", (200, 206, 190)), piso="ceramica", luz="fluorescente", acoustic="media", amb="zumbido",
                        nota="sala de espera/recepção: fileira de cadeiras, TV na parede, relógio, balcão",
                        moveis=[{"m": "balcao", "x": 0.25, "cor": (200, 200, 206), "itens": ["telefone", "papel"]}, {"m": "planta", "x": 0.9},
                                {"m": "tv_parede", "em": "parede", "x": 0.62, "h": 180, "tv": "noticia"}, {"m": "relogio_parede", "em": "parede", "x": 0.25, "h": 200},
                                {"m": "banco", "em": "chao", "x": 0.65, "z": 0.45, "larg": 200, "cor": (60, 110, 160)}, {"m": "fluorescente", "em": "teto", "x": 0.5, "z": 0.3}]),
    "celeiro": dict(tipo="interior", parede=("madeira", (140, 70, 50)), piso="terra", luz="escuro", acoustic="media", amb="vento",
                    nota="celeiro: fardos de feno, tambor, escada, lampião",
                    moveis=[{"m": "feno", "x": 0.15}, {"m": "feno", "x": 0.15, "em": "fundo", "empilhar": 1}, {"m": "porta", "x": 0.55, "larg": 220, "alt": 230, "cor": (120, 60, 40)},
                            {"m": "tambor", "x": 0.88, "cor": (120, 70, 40)}, {"m": "escada_mao", "em": "chao", "x": 0.8, "z": 0.35, "cor": (120, 90, 60)},
                            {"m": "feno", "em": "chao", "x": 0.3, "z": 0.5}, {"m": "lampada", "em": "teto", "x": 0.5, "z": 0.3, "fio": 60}]),
    # ---------------- externos ----------------
    "quintal": dict(tipo="exterior", chao="grama", horizonte="casas", hora="noite", acoustic="aberto", amb="vento",
                    nota="quintal de casa: muro, árvore, varal, bicicleta",
                    moveis=[{"m": "muro", "z": 0.08, "x": 0.5, "larg": 1400}, {"m": "arvore", "z": 0.2, "x": 0.15}, {"m": "varal", "z": 0.3, "x": 0.6},
                            {"m": "bicicleta", "z": 0.55, "x": 0.85}, {"m": "lixeira", "z": 0.45, "x": 0.1}]),
    "frente_casa": dict(tipo="exterior", chao="grama", horizonte="mata", hora="noite", acoustic="aberto", amb="vento",
                        nota="frente de uma casa: fachada, cerca, caixa de correio, poste",
                        moveis=[{"m": "casa", "z": 0.12, "x": 0.5}, {"m": "cerca", "z": 0.35, "x": 0.5, "larg": 900}, {"m": "caixa_correio", "z": 0.42, "x": 0.25},
                                {"m": "poste", "z": 0.3, "x": 0.9}, {"m": "arbusto", "z": 0.3, "x": 0.08}]),
    "rua_bairro": dict(tipo="exterior", chao="asfalto", horizonte="casas", hora="noite", acoustic="aberto", amb="vento", rua=True,
                       nota="rua residencial: casas no fundo, postes, carro estacionado",
                       moveis=[{"m": "casa", "z": 0.08, "x": 0.2, "larg": 500}, {"m": "casa", "z": 0.08, "x": 0.8, "larg": 500, "cor": (170, 190, 200), "janelas_acesas": [False, True]},
                               {"m": "poste", "z": 0.25, "x": 0.08}, {"m": "poste", "z": 0.25, "x": 0.92}, {"m": "carro", "z": 0.4, "x": 0.25}, {"m": "hidrante", "z": 0.5, "x": 0.88}]),
    "avenida": dict(tipo="exterior", chao="asfalto", horizonte="cidade", hora="noite", acoustic="aberto", amb="vento", rua=True,
                    nota="avenida: prédios, ponto de ônibus, orelhão, poste",
                    moveis=[{"m": "predio", "z": 0.05, "x": 0.15}, {"m": "predio", "z": 0.05, "x": 0.85, "seed": 9}, {"m": "ponto_onibus", "z": 0.3, "x": 0.2},
                            {"m": "orelhao", "z": 0.35, "x": 0.82}, {"m": "poste", "z": 0.28, "x": 0.6}, {"m": "placa_rua", "z": 0.45, "x": 0.95, "texto": "PARE"}]),
    "praca": dict(tipo="exterior", chao="grama", horizonte="cidade", hora="noite", acoustic="aberto", amb="vento",
                  nota="praça: árvores, banco, poste, lixeira",
                  moveis=[{"m": "arvore", "z": 0.15, "x": 0.15}, {"m": "arvore", "z": 0.12, "x": 0.8, "seed": 8}, {"m": "poste", "z": 0.25, "x": 0.5},
                          {"m": "banco_praca", "z": 0.35, "x": 0.35}, {"m": "lixeira", "z": 0.4, "x": 0.62}, {"m": "arbusto", "z": 0.5, "x": 0.95}]),
    "parquinho": dict(tipo="exterior", chao="areia", horizonte="mata", hora="entardecer", acoustic="aberto", amb="vento",
                      nota="parquinho: balanço, escorregador, banco, árvores",
                      moveis=[{"m": "arvore", "z": 0.1, "x": 0.1}, {"m": "balanco", "z": 0.25, "x": 0.35}, {"m": "escorregador", "z": 0.25, "x": 0.78},
                              {"m": "banco_praca", "z": 0.45, "x": 0.15}, {"m": "brinquedo", "em": "chao", "z": 0.55, "x": 0.55}]),
    "estrada": dict(tipo="exterior", chao="asfalto", horizonte="mata", hora="noite", acoustic="aberto", amb="vento", estrada=True,
                    nota="estrada no meio do mato: faixa no meio, placa, cruz na beira",
                    moveis=[{"m": "arvore", "z": 0.1, "x": 0.05, "tipo": "pinheiro"}, {"m": "arvore", "z": 0.1, "x": 0.95, "tipo": "pinheiro"},
                            {"m": "placa_rua", "z": 0.3, "x": 0.9, "texto": "KM 47"}, {"m": "cruz_estrada", "z": 0.4, "x": 0.08}, {"m": "poste", "z": 0.2, "x": 0.85, "aceso": False}]),
    "campo": dict(tipo="exterior", chao="grama", horizonte="morros", hora="entardecer", acoustic="aberto", amb="vento",
                  nota="campo/fazenda: cerca de madeira, poço, celeiro vermelho, árvore",
                  moveis=[{"m": "casa", "z": 0.06, "x": 0.75, "cor": (160, 50, 40), "telhado": (80, 50, 40), "larg": 420, "janelas_acesas": False},
                          {"m": "arvore", "z": 0.1, "x": 0.2}, {"m": "cerca", "z": 0.3, "x": 0.5, "larg": 1200}, {"m": "poco", "z": 0.45, "x": 0.3}, {"m": "feno", "z": 0.5, "x": 0.82}]),
    "cemiterio": dict(tipo="exterior", chao="grama", horizonte="mata", hora="noite", acoustic="aberto", amb="vento", nevoa=0.55,
                      nota="cemitério: lápides em fileiras, árvore seca, muro, névoa",
                      moveis=[{"m": "muro", "z": 0.05, "x": 0.5, "larg": 1600, "alt": 160}, {"m": "arvore", "z": 0.12, "x": 0.85, "tipo": "seca"},
                              {"m": "lapide", "z": 0.18, "x": 0.15}, {"m": "lapide", "z": 0.18, "x": 0.4}, {"m": "lapide", "z": 0.18, "x": 0.62},
                              {"m": "lapide", "z": 0.38, "x": 0.1}, {"m": "lapide", "z": 0.38, "x": 0.35, "nome": "1952"}, {"m": "lapide", "z": 0.38, "x": 0.72, "terra": True},
                              {"m": "cruz_estrada", "z": 0.28, "x": 0.52}]),
    "acampamento": dict(tipo="exterior", chao="terra", horizonte="mata", hora="noite", acoustic="aberto", amb="vento",
                        nota="acampamento na mata: barraca, fogueira acesa, pinheiros",
                        moveis=[{"m": "arvore", "z": 0.08, "x": 0.1, "tipo": "pinheiro"}, {"m": "arvore", "z": 0.06, "x": 0.85, "tipo": "pinheiro"},
                                {"m": "barraca", "z": 0.25, "x": 0.3, "acesa": True}, {"m": "fogueira", "z": 0.45, "x": 0.6}, {"m": "pedra", "z": 0.5, "x": 0.85},
                                {"m": "mochila", "em": "chao", "z": 0.55, "x": 0.2}]),
    "praia": dict(tipo="exterior", chao="areia", horizonte="mar", hora="entardecer", acoustic="aberto", amb="vento",
                  nota="praia: mar no horizonte, guarda-sol, barco na areia, palmeira",
                  moveis=[{"m": "arvore", "z": 0.2, "x": 0.08, "tipo": "palmeira"}, {"m": "barco", "z": 0.25, "x": 0.7}, {"m": "guarda_sol", "z": 0.4, "x": 0.3}]),
    "terreno_baldio": dict(tipo="exterior", chao="terra", horizonte="cidade", hora="noite", acoustic="aberto", amb="vento",
                           nota="terreno baldio: muro pichado, caçamba, mato, pneus",
                           moveis=[{"m": "muro", "z": 0.1, "x": 0.5, "larg": 1500, "pichacao": "SAIAM", "tijolo": True}, {"m": "lixeira_rua", "z": 0.3, "x": 0.25},
                                   {"m": "arbusto", "z": 0.25, "x": 0.85}, {"m": "tambor", "z": 0.45, "x": 0.7, "cor": (120, 70, 40)}, {"m": "poste", "z": 0.2, "x": 0.55}]),
}

PAREDES = ("pintada", "azulejo", "tijolo", "madeira", "concreto", "papel_parede", "listrado")
PISOS = ("taco", "madeira", "ceramica", "xadrez", "concreto", "carpete", "terra", "grama", "areia", "asfalto")
HORIZONTES = ("cidade", "casas", "mata", "morros", "mar", "nada")
HORAS = ("dia", "entardecer", "amanhecer", "noite", "madrugada")
ALT_PADRAO = {"janela": 100, "quadro": 140, "relogio_parede": 200, "placa": 220, "armario_alto": 150, "ar_condicionado": 220, "tv_parede": 160,
              "espelho": 110, "cruz": 160, "calendario": 150, "quadro_energia": 130, "camera_seguranca": 240, "chuveiro": 190,
              "prateleira_parede": 140, "quadro_avisos": 120, "porta": 0}
RESERVADAS = {"m", "em", "x", "z", "h", "id", "camada", "escala", "empilhar"}


# ============================== DESCRIÇÃO → CONFIG ==============================
def expandir(spec):
    """Junta o ambiente base com as mudanças do plano. Aceita nome (str) ou dict."""
    if isinstance(spec, str): spec = {"base": spec}
    spec = copy.deepcopy(spec)
    base = spec.get("base") or spec.get("ambiente")
    cfg = copy.deepcopy(AMBIENTES.get(base, {})) if base and not spec.get("close") else {}
    if base and base not in AMBIENTES and not spec.get("close"): raise KeyError(f"ambiente desconhecido: {base}")
    for k, v in spec.items():
        if k in ("base", "ambiente", "mais", "sem", "mudar"): continue
        cfg[k] = v
    cfg.setdefault("tipo", "interior"); cfg.setdefault("moveis", [])
    sem = spec.get("sem") or []
    cfg["moveis"] = [m for m in cfg["moveis"] if m.get("m") not in sem and m.get("id") not in sem]
    for mud in spec.get("mudar") or []:                       # {"m": "geladeira", "aberta": true} muda o móvel existente
        alvo = next((m for m in cfg["moveis"] if m.get("id", m.get("m")) == mud.get("id", mud.get("m"))), None)
        if alvo: alvo.update({k: v for k, v in mud.items() if k not in ("m",)})
        else: cfg["moveis"].append(mud)
    cfg["moveis"] = cfg["moveis"] + list(spec.get("mais") or [])
    for m in cfg["moveis"]:
        if m.get("m") not in MOVEIS: raise KeyError(f"móvel desconhecido: {m.get('m')}")
    return cfg


# ============================== GEOMETRIA ==============================
class Sala:
    """Caixa em perspectiva de um ponto: parede do fundo, laterais, teto e chão. Coordenadas do cenário (1080×1920)."""
    def __init__(self, cfg):
        self.yf = cfg.get("chao_y", 1380); self.s_far = cfg.get("escala_fundo", 0.82)
        self.kf = K_CM * KP * self.s_far
        olho = cfg.get("olho", 175)
        self.yv = self.yf - olho * self.kf
        self.s_near = self.s_far * (1900 - self.yv) / (self.yf - self.yv)
        larg = cfg.get("largura", 400); self.bx0 = 540 - larg * self.kf / 2; self.bx1 = 540 + larg * self.kf / 2
        self.ytop = self.yf - cfg.get("pe_direito", 280) * self.kf
        self.inclinado = cfg.get("teto") == "inclinado"
    def scale(self, y): return self.s_far * (y - self.yv) / (self.yf - self.yv)
    def k(self, y): return K_CM * KP * self.scale(y)
    def y_de(self, z): return lerp(self.yf, 1900, z)
    def xl(self, y): return 540 + (self.bx0 - 540) * (y - self.yv) / (self.yf - self.yv)
    def xr(self, y): return 540 + (self.bx1 - 540) * (y - self.yv) / (self.yf - self.yv)
    def teto_y(self, y):
        f = (y - self.yv) / (self.yf - self.yv); return self.yv - (self.yv - self.ytop) * f
    def ground(self): return (self.yf, 1900, self.s_far, self.s_near)
    def chao(self):
        def y_em(x, lado):   # y onde a linha do chão (esq/dir) cruza x
            bx = self.bx0 if lado < 0 else self.bx1
            return self.yv + (self.yf - self.yv) * (x - 540) / (bx - 540)
        return [(int(self.bx0), int(self.yf)), (int(self.bx1), int(self.yf)), (1080, int(min(1900, y_em(1080, 1)))), (1080, 1900), (0, 1900), (0, int(min(1900, y_em(0, -1))))]


class Campo:
    """Externo: céu, horizonte e chão plano até a câmera."""
    def __init__(self, cfg):
        self.yh = cfg.get("horizonte_y", 1100); self.s1 = cfg.get("escala_frente", 1.6)
        self.yf = self.yh + 60
        self.s_far = self.s1 * (self.yf - self.yh) / (1900 - self.yh)
    def scale(self, y): return self.s1 * (y - self.yh) / (1900 - self.yh)
    def k(self, y): return K_CM * KP * max(0.02, self.scale(y))
    def y_de(self, z): return lerp(self.yf, 1900, 0.12 + 0.88 * z)
    def ground(self): return (self.yf, 1900, self.s_far, self.s1)
    def chao(self): return [(0, int(self.yf)), (1080, int(self.yf)), (1080, 1900), (0, 1900)]


def planta(cfg):
    """Posição de cada móvel: lista de dicts com nome, (x, y) do apoio no cenário, k (px/cm), camada e marca."""
    ext = cfg.get("tipo") == "exterior"
    G = Campo(cfg) if ext else Sala(cfg)
    itens = []; cursor_fundo = []
    fundo = [m for m in cfg["moveis"] if (m.get("em") or _padrao_em(m, ext)) == "fundo"]
    # distribuição automática no fundo: quem não tem x ocupa o espaço livre na ordem
    livres = [m for m in fundo if "x" not in m]
    for i, m in enumerate(livres): m["_xauto"] = (i + 0.5) / len(livres)
    pilha = {}
    for idx, m in enumerate(cfg["moveis"]):
        nome = m["m"]; mv = MOVEIS[nome]; em = m.get("em") or _padrao_em(m, ext)
        opts = {k: v for k, v in m.items() if k not in RESERVADAS and not k.startswith("_")}
        u = m.get("x", m.get("_xauto", 0.5)); esc_ = m.get("escala", 1.0)
        camada = m.get("camada", "fundo")
        if ext:
            z = m.get("z", 0.1 if em != "chao" else 0.5); y = G.y_de(z); k = G.k(y) * esc_
            x = lerp(-60, 1140, u)
        elif em == "fundo":
            y = G.yf + 4; k = G.kf * esc_; x = lerp(G.bx0 + mv.larg * k / 2, G.bx1 - mv.larg * k / 2, u) if mv.larg * k < (G.bx1 - G.bx0) else 540
            if m.get("empilhar"):
                y -= pilha.get(round(x), 0)
            pilha[round(x)] = pilha.get(round(x), 0) + mv.alt * k
        elif em == "parede":
            k = G.kf * esc_; x = lerp(G.bx0 + mv.larg * k / 2 + 8, G.bx1 - mv.larg * k / 2 - 8, u)
            y = G.yf - m.get("h", ALT_PADRAO.get(nome, 120)) * k
        elif em == "teto":
            z = m.get("z", 0.3); yy = G.y_de(z); k = G.k(yy) * esc_; x = lerp(G.xl(yy), G.xr(yy), u) if G.xr(yy) - G.xl(yy) < 1080 else lerp(80, 1000, u)
            y = G.teto_y(yy) + (40 if G.inclinado else 0)
        elif em in ("esq", "dir"):
            z = m.get("z", 0.15); y = G.y_de(z); k = G.k(y) * esc_; half = mv.larg * k / 2
            x = max(half - 30, G.xl(y) + half) if em == "esq" else min(1110 - half, G.xr(y) - half)
        elif em == "frente":
            y = 1960; k = G.k(1900) * esc_ * 1.3; x = lerp(-40, 1120, u); camada = "frente"
        else:   # chao: solto no chão
            z = m.get("z", 0.5); y = G.y_de(z); k = G.k(y) * esc_
            xa, xb = max(40, G.xl(y)), min(1040, G.xr(y)); x = lerp(xa + mv.larg * k / 2, xb - mv.larg * k / 2, u) if xb - xa > mv.larg * k else 540
        itens.append({"m": nome, "x": x, "y": y, "k": k, "em": em, "opts": opts, "camada": camada, "lugar": mv.lugar,
                      "id": m.get("id"), "seed": idx * 7 + 3, "larg": mv.larg * k, "alt": mv.alt * k})
    return G, itens


def _padrao_em(m, ext):
    lug = MOVEIS[m["m"]].lugar
    if ext: return "chao"
    return {"parede": "parede", "teto": "teto", "chao": "chao", "fora": "chao", "cima": "chao"}.get(lug, "fundo")


def marcas_de(cfg):
    """Chão e marcas automáticas (mapa.py)."""
    G, itens = planta(cfg)
    def ym(z): return int(G.y_de(z))
    mk = {"centro": {"x": 540, "y": ym(0.55)}, "esq": {"x": 290, "y": ym(0.6)}, "dir": {"x": 790, "y": ym(0.6)},
          "fundo": {"x": 540, "y": ym(0.12), "nota": "perto da parede do fundo (pequeno)"}, "frente": {"x": 540, "y": ym(0.9), "nota": "perto da câmera"}}
    usados = {}
    for it in itens:
        if it["em"] in ("parede", "teto", "frente") and it["m"] not in ("porta", "janela"): continue
        if it["lugar"] == "chao" and it["m"] in ("tapete", "poca", "mancha", "pegadas"): continue
        base = it["id"] or it["m"]; n = usados.get(base, 0); usados[base] = n + 1
        nome = base if n == 0 else f"{base}{n + 1}"
        if it["em"] in ("fundo", "parede"):
            x, y = it["x"], (G.yf if it["em"] == "parede" else it["y"]) + 70
            nota = f"na frente de {it['m'].replace('_', ' ')}"
            v = "back" if it["m"] in ("porta", "janela", "pia_cozinha", "fogao", "geladeira", "prateleira", "estante", "expositor", "bancada") else None
        else:
            lado = 1 if it["x"] < 540 else -1
            x, y = it["x"] + lado * (it["larg"] / 2 + 70), it["y"] + 12
            nota = f"ao lado de {it['m'].replace('_', ' ')}"; v = None
        x = int(max(70, min(1010, x))); y = int(max(G.yf + 20, min(1880, y)))
        mk[nome] = {"x": x, "y": y, "nota": nota}
        if v: mk[nome]["view"] = v
    return {"chao": G.chao(), "marcas": mk}


# ============================== MATERIAIS ==============================
def _parede(d, P, PS, pts, mat, cor, box, seed=1):
    """Pinta um polígono de parede com o material. box = (x0, y0, x1, y1) para o padrão."""
    d.polygon(PS(*pts), fill=cor + (255,))
    x0, y0, x1, y1 = box; r = random.Random(seed)
    if mat == "azulejo":
        lc = esc(cor, 0.86) + (255,)
        for x in range(int(x0), int(x1), 34): d.line(PS((x, y0), (x, y1)), fill=lc, width=2)
        for y in range(int(y0), int(y1), 34): d.line(PS((x0, y), (x1, y)), fill=lc, width=2)
    elif mat == "tijolo":
        lc = esc(cor, 0.7) + (255,)
        for j, y in enumerate(range(int(y0), int(y1), 26)):
            d.line(PS((x0, y), (x1, y)), fill=lc, width=3)
            for x in range(int(x0) + (j % 2) * 30, int(x1), 60): d.line(PS((x, y), (x, y + 26)), fill=lc, width=3)
    elif mat == "madeira":
        for x in range(int(x0), int(x1), 46):
            d.line(PS((x, y0), (x, y1)), fill=esc(cor, 0.72) + (255,), width=3)
            for _ in range(2):
                yy = r.uniform(y0, y1); d.ellipse(PS((x + 14, yy), (x + 26, yy + 8)), outline=esc(cor, 0.8) + (255,), width=2)
    elif mat == "concreto":
        for _ in range(int((x1 - x0) * (y1 - y0) / 9000)):
            xx, yy = r.uniform(x0, x1), r.uniform(y0, y1); d.ellipse(PS((xx, yy), (xx + r.uniform(6, 30), yy + r.uniform(4, 16))), fill=esc(cor, r.uniform(0.88, 0.97)) + (255,))
    elif mat in ("papel_parede", "listrado"):
        step = 40 if mat == "listrado" else 70
        for x in range(int(x0), int(x1), step):
            d.rectangle(PS((x, y0), (x + step * 0.45, y1)), fill=esc(cor, 0.9 if mat == "listrado" else 0.94) + (255,))
            if mat == "papel_parede":
                for y in range(int(y0) + 30, int(y1), 80): d.ellipse(PS((x + step * 0.6, y), (x + step * 0.85, y + 22)), fill=esc(cor, 1.12) + (255,))


COR_PISO = {"taco": (150, 110, 74), "madeira": (126, 92, 62), "ceramica": (200, 196, 186), "xadrez": (226, 226, 220), "concreto": (128, 128, 126),
            "carpete": (90, 96, 110), "terra": (110, 84, 60), "grama": (62, 104, 60), "areia": (214, 190, 140), "asfalto": (54, 56, 62)}


def _piso_sala(d, P, PS, G, mat, cor, CWX, M):
    yb = 1920; pts = [(G.bx0, G.yf), (G.bx1, G.yf), (G.xr(yb), yb), (G.xl(yb), yb)]
    d.polygon(PS(*pts), fill=cor + (255,))
    lc = esc(cor, 0.84) + (255,)
    nrows = 16
    ys = [G.yf + (yb - G.yf) * ((i / nrows) ** 1.7) for i in range(nrows + 1)]
    ncol = 14 if mat not in ("taco", "madeira") else 9
    xs_back = [lerp(G.bx0, G.bx1, j / ncol) for j in range(ncol + 1)]
    def x_at(xb, y): return 540 + (xb - 540) * (y - G.yv) / (G.yf - G.yv)
    if mat == "xadrez":
        escuro = esc(cor, 0.35) + (255,)
        for i in range(nrows):
            for j in range(-30, ncol + 30):
                if (i + j) % 2: continue
                xa, xb = lerp(G.bx0, G.bx1, j / ncol), lerp(G.bx0, G.bx1, (j + 1) / ncol)
                q = [(x_at(xa, ys[i]), ys[i]), (x_at(xb, ys[i]), ys[i]), (x_at(xb, ys[i + 1]), ys[i + 1]), (x_at(xa, ys[i + 1]), ys[i + 1])]
                d.polygon(PS(*q), fill=escuro)
        return
    if mat in ("ceramica", "taco", "madeira"):
        for xb in [lerp(G.bx0, G.bx1, j / ncol) for j in range(-40, ncol + 41)]:
            d.line(PS((xb, G.yf), (x_at(xb, yb), yb)), fill=lc, width=2)
    if mat in ("ceramica", "taco", "madeira", "concreto"):
        for y in ys[1:]: d.line(PS((-M, y), (1080 + M, y)), fill=lc, width=2 if mat != "concreto" else 1)
    if mat in ("carpete", "terra", "concreto"):
        r = random.Random(9)
        for _ in range(500):
            y = r.uniform(G.yf, yb); x = r.uniform(-M, 1080 + M); s = 2 + (y - G.yf) / 120
            d.ellipse(PS((x, y), (x + s * 2, y + s)), fill=esc(cor, r.uniform(0.85, 1.08)) + (255,))


# ============================== CENA GERADA ==============================
from .scenes import Scene, canvas, P, PS, down, S, M, W, CWX, skyline


def _luzes(img, luzes, k_alpha=0.55):
    for (x, y, raio, cor, a) in luzes:
        raio = max(20, min(raio, 420))
        img = add_light(img, PS((x - raio, y - raio * 0.8), (x + raio, y + raio * 0.8)), cor, max(8, int(raio * 0.5)) * S, int(a * k_alpha))
    return img


class Gerado(Scene):
    """Cenário montado pela descrição (ver o topo do arquivo)."""
    name = "gerado"; SPEC = {}
    def __init__(self, spec=None):
        if spec is not None: self.SPEC = spec
        cfg = expandir(self.SPEC); self.cfg = cfg
        lz = LUZES.get(cfg.get("luz") or ("noite" if cfg.get("tipo") == "exterior" else "quente"), LUZES["quente"])
        hora = cfg.get("hora")
        if cfg.get("tipo") == "exterior" and hora and not cfg.get("luz"):
            lz = LUZES.get({"dia": "dia", "madrugada": "escuro"}.get(hora, hora), LUZES["noite"])
        self.light, self.grade, self.brilho, self.cor_luz = lz
        self.light = cfg.get("luz_personagens", self.light); self.grade = cfg.get("grade", self.grade)
        self.acoustic = cfg.get("acoustic", "sala" if cfg.get("tipo") != "exterior" else "aberto")
        self.amb = cfg.get("amb", "zumbido" if cfg.get("luz") in ("fria", "fluorescente") else ("vento" if cfg.get("tipo") == "exterior" else "chuva_dentro"))
        self.G, self.itens = planta(cfg)
        self.ground = self.G.ground()
        self.depths = (0.15, 0.5, 1.2) if cfg.get("tipo") == "exterior" else (0.35, 0.35, 1.2)
        if cfg.get("chuva"):
            self.rain_full = True; self.rain_strength = {"forte": 1.4, "fraca": 0.5}.get(cfg["chuva"], 1.0); self.wet = True
            if cfg.get("tipo") == "exterior": self.amb = "chuva_fora"
        if cfg.get("nevoa"): self.fog_cfg = dict(y=self.G.yf - 60, height=700, alpha=float(cfg["nevoa"]), col=(120, 126, 146), speed=12)
        self.fogo = [(it["x"], it["y"] - it["alt"] * 0.4, it["larg"]) for it in self.itens if it["m"] in ("fogueira", "lareira")]
        self.telas = [it for it in self.itens if it["m"] in ("rack_tv", "tv_parede")]
        super().__init__()

    # ---------------- montagem ----------------
    def build(self):
        cfg = self.cfg
        if cfg.get("tipo") == "exterior": return self._build_ext()
        G = self.G
        back = canvas(alpha=True); d = ImageDraw.Draw(back)
        mat, cor = (cfg.get("parede") or ("pintada", (150, 150, 160)))
        cor = tuple(cor); lado = esc(cor, 0.82); teto = esc(cor, 0.7)
        # teto e laterais (polígonos que passam da tela) e parede do fundo
        far = 4000
        def ext(x, y, k=far):   # prolonga do ponto de fuga através de (x, y)
            vx, vy = x - 540, y - G.yv; n = math.hypot(vx, vy) or 1; return (x + vx / n * k, y + vy / n * k)
        if G.inclinado:
            d.polygon(PS((-M - 400, -400), (1080 + M + 400, -400), (1080 + M + 400, G.ytop), (-M - 400, G.ytop)), fill=esc(cor, 0.55) + (255,))
            d.polygon(PS((G.bx0, G.ytop), ext(G.bx0, G.ytop), (-M - 400, -400), (540, G.ytop - 300)), fill=esc(cor, 0.62) + (255,))
            d.polygon(PS((G.bx1, G.ytop), ext(G.bx1, G.ytop), (1080 + M + 400, -400), (540, G.ytop - 300)), fill=esc(cor, 0.58) + (255,))
            for k_ in range(1, 6):
                xx = lerp(G.bx0, G.bx1, k_ / 6); d.line(PS((xx, G.ytop), (540 + (xx - 540) * 6, -900)), fill=esc(cor, 0.45) + (255,), width=6 * S)
        else:
            d.polygon(PS((G.bx0, G.ytop), (G.bx1, G.ytop), ext(G.bx1, G.ytop), ext(G.bx0, G.ytop)), fill=teto + (255,))
        _parede(d, P, PS, [(G.bx0, G.ytop), (G.bx0, G.yf), ext(G.bx0, G.yf), ext(G.bx0, G.ytop)], mat, lado, (-M - 600, -600, G.bx0, 2400), 3)
        _parede(d, P, PS, [(G.bx1, G.ytop), (G.bx1, G.yf), ext(G.bx1, G.yf), ext(G.bx1, G.ytop)], mat, esc(cor, 0.88), (G.bx1, -600, 1080 + M + 600, 2400), 4)
        _parede(d, P, PS, [(G.bx0, G.ytop), (G.bx1, G.ytop), (G.bx1, G.yf), (G.bx0, G.yf)], mat, cor, (G.bx0, G.ytop, G.bx1, G.yf), 5)
        if cfg.get("meia_parede"):                     # barra pintada até 1,1 m
            bc = tuple(cfg["meia_parede"]); yb = G.yf - 110 * G.kf
            d.rectangle(PS((G.bx0, yb), (G.bx1, G.yf)), fill=bc + (255,))
        # cantos e rodapé
        for (xa, ya) in ((G.bx0, G.ytop), (G.bx1, G.ytop), (G.bx0, G.yf), (G.bx1, G.yf)):
            d.line(PS((xa, ya), ext(xa, ya)), fill=esc(cor, 0.5) + (255,), width=3 * S)
        d.line(PS((G.bx0, G.ytop), (G.bx1, G.ytop)), fill=esc(cor, 0.5) + (255,), width=3 * S)
        # chão
        pm = cfg.get("piso", "taco"); pc = tuple(cfg.get("cor_piso", COR_PISO.get(pm, (140, 120, 100))))
        _piso_sala(d, P, PS, G, pm, pc, CWX, M)
        d.line(PS((G.bx0, G.yf), (G.bx1, G.yf)), fill=esc(cor, 0.45) + (255,), width=6 * S)
        if cfg.get("lateral"): self._lateral(d, cfg["lateral"])
        luzes = []
        ordem = sorted(self.itens, key=lambda it: ({"parede": 0, "teto": 1}.get(it["em"], 2), it["y"]))
        front = None
        for it in ordem:
            if it["camada"] == "frente":
                if front is None: front = canvas(alpha=True)
                luzes += MV.desenhar(ImageDraw.Draw(front), it["m"], it["x"], it["y"], it["k"], P, it["opts"], it["seed"]); continue
            if it["em"] not in ("parede", "teto") and it["lugar"] not in ("chao",):
                w = it["larg"] * 0.55; d.ellipse(PS((it["x"] - w, it["y"] - 10), (it["x"] + w, it["y"] + 10)), fill=esc(pc, 0.55) + (255,))
            luzes += MV.desenhar(d, it["m"], it["x"], it["y"], it["k"], P, it["opts"], it["seed"])
        img = back
        # luz ambiente do lugar (de cima, no meio da sala) + luzes dos objetos
        img = add_light(img, PS((G.bx0 - 100, G.ytop - 200), (G.bx1 + 100, G.yf + 300)), self.cor_luz, 160 * S, int(10 + 18 * self.brilho))
        img = _luzes(img, luzes)
        if self.brilho < 1:
            sombra = Image.new("RGBA", img.size, (6, 8, 16, int(255 * (1 - self.brilho) * 0.85)))
            img = Image.alpha_composite(img, sombra)
            img = _luzes(img, luzes, 0.45)                                # o que acende continua aceso no escuro
        back = img.convert("RGB")
        if front is not None: front = front.filter(ImageFilter.GaussianBlur(7 * S))
        return down(back), None, (down(front) if front is not None else None)

    def _lateral(self, d, lat):
        """Gôndolas em perspectiva nas duas paredes laterais (corredor de mercado, biblioteca, depósito)."""
        G = self.G; conts = lat.get("conteudo", ["latas"]); conts = conts if isinstance(conts, list) else [conts]
        info = [MV.PRODUTOS.get(c, MV.PRODUTOS["latas"]) for c in conts]
        r = random.Random(11); alt = lat.get("alt", 175); cor = tuple(lat.get("cor", (190, 196, 204)))
        for side in (-1, 1):
            xe = G.xl if side < 0 else G.xr
            segs = 7
            for k in range(segs):
                z0, z1 = k / segs, (k + 1) / segs
                y0, y1 = G.y_de(z0), G.y_de(z1)
                x0, x1 = xe(y0), xe(y1)
                k0, k1 = G.k(y0), G.k(y1)
                t0, t1 = y0 - alt * k0, y1 - alt * k1
                d.polygon(PS((x0, t0), (x1, t1), (x1, y1), (x0, y0)), fill=esc(cor, 0.4) + (255,))
                d.line(PS((x0, t0), (x0, y0)), fill=cor + (255,), width=max(2, int(4 * k0)) * S)
                for j in range(5):
                    f = (j + 0.15) / 5
                    ya, yb = lerp(y0, t0, f), lerp(y1, t1, f)
                    d.line(PS((x0, ya), (x1, yb)), fill=cor + (255,), width=max(2, int(5 * k0)) * S)
                    inf = info[j % len(info)]
                    if not inf["forma"]: continue
                    hh = alt / 5 * 0.7
                    for q in range(6):
                        u = (q + r.random() * 0.4) / 6
                        x = lerp(x0, x1, u); yy = lerp(ya, yb, u); kk = lerp(k0, k1, u); h = hh * kk; ww = (9 if inf["forma"] == "lata" else 14) * kk
                        c = r.choice(inf["cores"])
                        if r.random() < 0.85:
                            d.rectangle(PS((min(x, x - side * ww), yy - h), (max(x, x - side * ww), yy)), fill=c + (255,))
                            if inf["forma"] == "lata": d.rectangle(PS((min(x, x - side * ww), yy - h * 0.7), (max(x, x - side * ww), yy - h * 0.3)), fill=esc(c, 1.3) + (255,))

    def _build_ext(self):
        cfg = self.cfg; G = self.G; hora = cfg.get("hora", "noite")
        ceus = {"dia": ((120, 170, 220), (200, 220, 236)), "entardecer": ((70, 70, 120), (240, 150, 90)), "amanhecer": ((96, 104, 138), (220, 170, 150)),
                "noite": ((10, 14, 30), (40, 36, 60)), "madrugada": ((4, 6, 14), (20, 22, 36))}
        top, bot = ceus.get(hora, ceus["noite"])
        back = canvas(alpha=True)
        sky = grad(CWX * S, int(G.yh * S) + 4, top, bot).convert("RGBA"); back.paste(sky, (0, 0))
        d = ImageDraw.Draw(back); r = random.Random(cfg.get("seed", 7))
        if hora in ("noite", "madrugada"):
            for _ in range(140): x, y = r.uniform(-M, 1080 + M), r.uniform(0, G.yh * 0.7); d.ellipse(PS((x, y), (x + 2.4, y + 2.4)), fill=(230, 230, 240, 255))
            d.ellipse(PS((780, 260), (880, 360)), fill=(225, 222, 205, 255))
        elif hora in ("entardecer", "amanhecer"):
            back = add_light(back, PS((380, G.yh - 260), (700, G.yh + 60)), (255, 170, 100), 90 * S, 200); d = ImageDraw.Draw(back)
            d.ellipse(PS((490, G.yh - 110), (590, G.yh - 10)), fill=(255, 220, 160, 255))
        hz = cfg.get("horizonte", "mata"); noite = hora in ("noite", "madrugada")
        if hz == "cidade":
            sk = skyline(CWX * S, int(G.yh * 0.55 * S), 33, sky=(top, bot), far=esc(bot, 0.6), near=esc(bot, 0.42), lit=0.3 if noite else 0.0, hmin=0.3, hmax=0.95)
            back.paste(sk.convert("RGBA"), (0, int(G.yh * 0.45 * S)))
        elif hz == "casas":
            x = -M
            while x < 1080 + M:
                w_ = r.uniform(120, 220); h_ = r.uniform(70, 140); c = esc(bot, r.uniform(0.35, 0.55))
                d.rectangle(PS((x, G.yh - h_), (x + w_, G.yh)), fill=c + (255,)); d.polygon(PS((x - 10, G.yh - h_), (x + w_ + 10, G.yh - h_), (x + w_ / 2, G.yh - h_ - 60)), fill=esc(c, 0.85) + (255,))
                if noite and r.random() < 0.5: d.rectangle(PS((x + w_ * 0.3, G.yh - h_ * 0.6), (x + w_ * 0.5, G.yh - h_ * 0.3)), fill=(250, 210, 130, 255))
                x += w_ + r.uniform(10, 40)
        elif hz in ("mata", "morros"):
            cm = esc(bot, 0.35) if noite else (60, 96, 70)
            if hz == "morros":
                pts = [(-M - 50, G.yh)] + [(x, G.yh - 140 - 90 * math.sin(x / 260 + 1) - 40 * math.sin(x / 90)) for x in range(-M, 1080 + M + 40, 40)] + [(1080 + M + 50, G.yh)]
                d.polygon(PS(*pts), fill=esc(cm, 1.2) + (255,))
            for x in range(-M, 1080 + M, 22):
                h_ = r.uniform(80, 200); d.polygon(PS((x - 30, G.yh), (x + 30, G.yh), (x, G.yh - h_)), fill=esc(cm, r.uniform(0.8, 1.05)) + (255,))
        elif hz == "mar":
            d.rectangle(PS((-M, G.yh - 6), (1080 + M, G.yf + 120)), fill=(40, 70, 110, 255) if not noite else (14, 22, 40, 255))
            for k in range(40): y = G.yh + r.uniform(0, 150); x = r.uniform(-M, 1080 + M); d.line(PS((x, y), (x + r.uniform(20, 60), y)), fill=(200, 210, 230, 255), width=2 * S)
        # chão
        cm_ = cfg.get("chao", "grama"); pc = tuple(cfg.get("cor_piso", COR_PISO.get(cm_, (80, 90, 70))))
        if noite: pc = esc(pc, 0.6)
        y0 = G.yf if hz != "mar" else G.yf + 100
        g = grad(CWX * S, int((1920 - y0) * S) + 2, esc(pc, 0.75), pc).convert("RGBA"); back.paste(g, (0, int(y0 * S)))
        d = ImageDraw.Draw(back)
        for _ in range(900):
            y = r.uniform(y0, 1920); x = r.uniform(-M, 1080 + M); s_ = 1 + (y - y0) / 90
            if cm_ == "grama": d.line(PS((x, y), (x + r.uniform(-2, 2), y - s_ * 3)), fill=esc(pc, r.uniform(0.75, 1.25)) + (255,), width=max(1, int(s_ / 2)) * S)
            else: d.ellipse(PS((x, y), (x + s_ * 2, y + s_)), fill=esc(pc, r.uniform(0.8, 1.15)) + (255,))
        if cfg.get("rua") or cfg.get("estrada"):
            wf, wn = (60, 900) if cfg.get("estrada") else (420, 1500)
            asf = esc(COR_PISO["asfalto"], 0.8 if noite else 1.0)
            d.polygon(PS((540 - wf, G.yf), (540 + wf, G.yf), (540 + wn, 1920), (540 - wn, 1920)), fill=asf + (255,))
            if cfg.get("rua"):
                d.polygon(PS((-M, G.yf + 10), (540 - wf, G.yf), (540 - wn, 1920), (-M, 1920)), fill=(120, 116, 110, 255))
                d.polygon(PS((1080 + M, G.yf + 10), (540 + wf, G.yf), (540 + wn, 1920), (1080 + M, 1920)), fill=(120, 116, 110, 255))
            for k in range(12):
                a, b = (k / 12) ** 2, ((k + 0.5) / 12) ** 2
                ya, yb = lerp(G.yf, 1920, a), lerp(G.yf, 1920, b)
                wa, wb = lerp(3, 26, a), lerp(3, 26, b)
                d.polygon(PS((540 - wa, ya), (540 + wa, ya), (540 + wb, yb), (540 - wb, yb)), fill=(230, 210, 90, 255))
        luzes = []; front = None
        for it in sorted(self.itens, key=lambda it: it["y"]):
            dd = d
            if it["camada"] == "frente":
                if front is None: front = canvas(alpha=True)
                dd = ImageDraw.Draw(front)
            elif it["lugar"] != "chao":
                w = it["larg"] * 0.5; d.ellipse(PS((it["x"] - w, it["y"] - 6 * it["k"]), (it["x"] + w, it["y"] + 6 * it["k"])), fill=esc(pc, 0.6) + (255,))
            luzes += MV.desenhar(dd, it["m"], it["x"], it["y"], it["k"], P, it["opts"], it["seed"])
        img = back
        if not noite: img = add_light(img, PS((-M, 0), (1080 + M, G.yh)), self.cor_luz, 200 * S, 40)
        else:
            sombra = Image.new("RGBA", img.size, (6, 8, 20, int(255 * (1 - self.brilho) * 0.8))); img = Image.alpha_composite(img, sombra)
        img = _luzes(img, luzes)
        back = img.convert("RGB")
        if front is not None: front = front.filter(ImageFilter.GaussianBlur(7 * S))
        # o céu/horizonte fica numa camada mais lenta (paralaxe): fundo = tudo; meio = nada (o chão anda junto no fundo)
        return down(back), None, (down(front) if front is not None else None)

    # ---------------- a cada quadro ----------------
    def dynamic(self, img, t, camx, props):
        dx = -max(-110, min(110, camx * self.depths[0]))
        if self.telas and props.get("tv"):
            d = ImageDraw.Draw(img)
            for it in self.telas:
                k = it["k"]
                if it["m"] == "rack_tv": x0, y0, x1, y1 = it["x"] - 50 * k, it["y"] - 112 * k, it["x"] + 50 * k, it["y"] - 54 * k
                else: x0, y0, x1, y1 = it["x"] - 55 * k, it["y"] - 62 * k, it["x"] + 55 * k, it["y"]
                x0 += dx; x1 += dx
                if props["tv"] in ("static", "chiado"):
                    import numpy as _np
                    n = _np.random.default_rng(int(t * 24)).integers(40, 220, (24, 40)).astype("uint8")
                    img.paste(Image.fromarray(n).resize((max(1, int(x1 - x0)), max(1, int(y1 - y0)))).convert("RGB"), (int(x0), int(y0)))
                else:
                    fl = 0.75 + 0.25 * math.sin(t * 17) * math.sin(t * 5.3)
                    d.rectangle([x0, y0, x1, y1], fill=(int(90 * fl), int(140 * fl), int(240 * fl)))
                img.paste(add_light(img, (x0 - 260, y0 - 200, x1 + 260, y1 + 500), (70, 100, 200), 100, 110))
        if self.fogo:
            for (x, y, w) in self.fogo:
                a = int(40 + 30 * math.sin(t * 9) * math.sin(t * 4.1))
                img.paste(add_light(img, (x + dx - w * 1.4, y - w, x + dx + w * 1.4, y + w), (255, 120, 40), 80, max(0, a)))
        fl = props.get("flicker", self.cfg.get("flicker", 0))
        if fl:
            on = random.Random(int(t * 10) * 17 + 2).random() > fl
            if not on: img.paste(Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.6))
            props["_lamp_on"] = on
        luz = props.get("luz")
        if luz is not None and float(luz) < 1:
            img.paste(Image.blend(img, Image.new("RGB", img.size, (4, 6, 14)), 0.85 * (1 - float(luz))))
        em = props.get("emergencia")
        if em:
            pul = 0.6 + 0.4 * math.sin(t * 3)
            img.paste(Image.blend(img, Image.new("RGB", img.size, (160, 10, 10)), 0.35 * float(em) * pul))


# ============================== CLOSE (inserto do objeto) ==============================
SUPERFICIES = ("prateleira", "chao", "mesa", "balcao", "parede", "nenhuma")


class Close(Scene):
    """Close de um objeto: o objeto grande no meio, a superfície onde ele está e o ambiente desfocado atrás.
    props: "n" (quantas cópias, ex. [[0, 1], [0.6, 2], [1.2, 3]] = uma lata, duas, três), "desliza" 0–1 (entra de
    lado: caixa empurrada), "treme" 0–1, "cai" 0–1 (cai de cima), "mao" 0–1 (a mão de "hand" chega até o objeto),
    "aceso"/"aberta"/"visor"/"texto" (passados ao desenho do objeto), "luz" 0–1."""
    name = "close"; SPEC = {}; acoustic = "sala"
    def __init__(self, spec=None):
        if spec is not None: self.SPEC = spec
        sp = dict(self.SPEC); self.sp = sp
        self.obj = sp["close"]
        if self.obj not in MOVEIS: raise KeyError(f"objeto desconhecido no close: {self.obj}")
        mv = MOVEIS[self.obj]
        self.sup = sp.get("superficie") or {"chao": "chao", "parede": "parede", "cima": "mesa", "teto": "nenhuma", "fora": "nenhuma"}.get(mv.lugar, "chao")
        amb = sp.get("ambiente")
        self.amb_cfg = expandir(amb) if amb else None
        lz = LUZES.get(sp.get("luz") or (self.amb_cfg or {}).get("luz") or "neutra", LUZES["neutra"])
        self.light, self.grade, self.brilho, self.cor_luz = lz
        self.grade = sp.get("grade", self.grade)
        larg = sp.get("larg", mv.larg); alt = max(sp.get("alt", mv.alt), larg * 0.25)
        self.k = sp.get("k") or min(520 / larg, 640 / alt, 46)
        self.base_y = {"prateleira": 1360, "chao": 1300, "mesa": 1300, "balcao": 1300, "parede": 960 + alt * self.k / 2, "nenhuma": 1200 + alt * self.k / 2}[self.sup]
        if mv.lugar == "teto": self.base_y = 760
        self.ground = (1200, 1900, 1.4, 2.2); self.depths = (0.15, 0.6, 1.2)
        super().__init__()
    def build(self):
        back = canvas(alpha=True)
        if self.amb_cfg:                                  # o ambiente de verdade, desfocado, atrás do objeto
            g = Gerado(self.sp["ambiente"]); b = g.back.convert("RGB")
            w, h = b.size; z = 1.7
            b = b.crop((int(w / 2 - w / 2 / z), int(h * 0.42 - h / 2 / z), int(w / 2 + w / 2 / z), int(h * 0.42 + h / 2 / z))).resize((CWX * S, 1920 * S))
            back.paste(b.filter(ImageFilter.GaussianBlur(26 * S)).convert("RGBA"), (0, 0))
        else:
            back.paste(grad(CWX * S, 1920 * S, (40, 44, 56), (16, 18, 26)).convert("RGBA"), (0, 0))
        d = ImageDraw.Draw(back); by = self.base_y; sup = self.sup
        pc = tuple((self.amb_cfg or {}).get("cor_piso", COR_PISO.get((self.amb_cfg or {}).get("piso", "ceramica"), (150, 140, 130))))
        if sup == "prateleira":
            cor = tuple(self.sp.get("cor_prateleira", (206, 210, 216)))
            d.rectangle(PS((-M, by), (1080 + M, by + 60)), fill=cor + (255,)); d.rectangle(PS((-M, by + 60), (1080 + M, 1920)), fill=esc(cor, 0.35) + (255,))
            d.rectangle(PS((-M, by + 6), (1080 + M, by + 44)), fill=(244, 236, 120, 255)); d.text(P(120, by + 25), self.sp.get("preco", "R$ 6,49"), font=font("sansb", 26 * S), fill=(40, 40, 40, 255), anchor="lm")
            d.rectangle(PS((-M, -10), (1080 + M, 230)), fill=esc(cor, 0.9) + (255,)); d.rectangle(PS((-M, 230), (1080 + M, 250)), fill=esc(cor, 0.6) + (255,))
            viz = self.sp.get("vizinhos", "milho" if self.obj in ("lata", "lata_caida") else None)
            if viz:                                          # produtos vizinhos nas laterais (desfocados depois)
                lado = canvas(alpha=True); ld = ImageDraw.Draw(lado); p = MV.Pincel(ld, 0, 0, min(self.k, 22), P)
                for side in (-1, 1):
                    p.x = 540 + side * 470; p.y = by
                    MV.encher(p, viz, -120, 120, 0, 40, seed=3 + side)
                back = Image.alpha_composite(back, lado.filter(ImageFilter.GaussianBlur(5 * S))); d = ImageDraw.Draw(back)
        elif sup in ("chao",):
            g = grad(CWX * S, int((1920 - by + 500) * S), esc(pc, 0.55), esc(pc, 1.0)).convert("RGBA"); back.paste(g, (0, int((by - 500) * S)))
            for k in range(10):
                y = by - 500 + (k / 10) ** 1.6 * (1920 - by + 500); d.line(PS((-M, y), (1080 + M, y)), fill=esc(pc, 0.8) + (255,), width=3 * S)
            for x in range(-600, 1700, 160): d.line(PS((540 + (x - 540) * 0.3, by - 500), (x, 1920)), fill=esc(pc, 0.8) + (255,), width=3 * S)
        elif sup in ("mesa", "balcao"):
            cor = tuple(self.sp.get("cor_tampo", (120, 84, 54) if sup == "mesa" else (220, 220, 214)))
            d.polygon(PS((-M, by - 160), (1080 + M, by - 160), (1080 + M, 1920), (-M, 1920)), fill=cor + (255,))
            d.line(PS((-M, by - 160), (1080 + M, by - 160)), fill=esc(cor, 1.25) + (255,), width=6 * S)
            if sup == "mesa":
                for y in range(int(by - 120), 1920, 70): d.line(PS((-M, y), (1080 + M, y + 20)), fill=esc(cor, 0.88) + (255,), width=2 * S)
        elif sup == "parede":
            amb = self.amb_cfg or {}; mat, cor = amb.get("parede") or ("pintada", (150, 150, 160))
            _parede(d, P, PS, [(-M, -10), (1080 + M, -10), (1080 + M, 1930), (-M, 1930)], mat, tuple(cor), (-M, 0, 1080 + M, 1920), 2)
        back = add_light(back, PS((140, by - 700), (940, by + 200)), self.cor_luz, 140 * S, 70)
        if self.brilho < 1:
            back = Image.alpha_composite(back, Image.new("RGBA", back.size, (6, 8, 16, int(255 * (1 - self.brilho) * 0.8))))
        return down(back.convert("RGB")), None, None
    def dynamic(self, img, t, camx, props):
        dx = -max(-110, min(110, camx * self.depths[0]))
        opts = dict(self.sp.get("opts") or {})
        for k in ("aceso", "aberta", "aberto", "visor", "texto", "tv", "pisca", "nome", "cor", "ligado", "acesa", "conteudo", "hora", "batido", "farol", "baixo", "capacho", "destaque"):
            if k in props: opts[k] = props[k]
        n = int(round(float(props.get("n", self.sp.get("n", 1)) or 1)))
        mv = MOVEIS[self.obj]; k = min(self.k, 820 / (n * mv.larg * 1.12)) if n > 1 else self.k
        sx = mv.larg * k * 1.12
        x0 = 540 - sx * (n - 1) / 2
        des = props.get("desliza"); cai = props.get("cai"); tr = float(props.get("treme", 0) or 0)
        ox = 0.0; oy = 0.0
        if des is not None: ox = -(1 - float(des)) * 700
        if cai is not None: oy = -(1 - min(1.0, float(cai))) * 900
        if tr: ox += math.sin(t * 61) * 14 * tr; oy += math.sin(t * 47) * 6 * tr
        d = ImageDraw.Draw(img); luzes = []
        PP = lambda x, y: (int(x + dx), int(y))
        for i in range(max(1, n)):
            x = x0 + i * sx + ox; y = self.base_y + oy
            if self.sup not in ("parede", "nenhuma") and mv.lugar != "teto":
                from .core import darken
                darken(img, [x - mv.larg * k * 0.6 + dx, y - 14, x + mv.larg * k * 0.6 + dx, y + 18], alpha=150, blur=10); d = ImageDraw.Draw(img)
            luzes += MV.desenhar(d, self.obj, x, y, k, PP, dict(opts, _i=i + 1), seed=i + 1, alpha=False, ss=1)
        for (lx, ly, raio, cor, a) in luzes:
            img.paste(add_light(img, (lx + dx - raio, ly - raio, lx + dx + raio, ly + raio), cor, max(6, int(raio * 0.5)), a))
        mao = props.get("mao"); hv = (props.get("_hand") or (None, None))[0]
        if mao is not None and hv:
            from .partes import braco
            alvo = (x0 + (n - 1) * sx + ox + mv.larg * k * 0.25 + dx, self.base_y + oy - min(mv.alt * k * 0.55, 300))
            ini = (1250, 2200); f = float(mao)
            braco(img, (1300, 2350), (lerp(ini[0], alvo[0], f), lerp(ini[1], alvo[1], f)), hv)
        luz = props.get("luz")
        if luz is not None and float(luz) < 1:
            img.paste(Image.blend(img, Image.new("RGB", img.size, (4, 6, 14)), 0.85 * (1 - float(luz))))


# ============================== REGISTRO ==============================
def _nome(spec):
    return "gen_" + hashlib.sha1(json.dumps(spec, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:10]


def registrar(spec):
    """Registra (uma vez) o cenário descrito em `spec` e devolve o nome para "scene"."""
    from . import scenes, mapa
    if isinstance(spec, str):
        if spec in scenes.REGISTRY: return spec
        spec = {"base": spec}
    nome = _nome(spec)
    if nome in scenes.REGISTRY: return nome
    if spec.get("close"):
        cls = type("Close_" + nome, (Close,), {"name": nome, "SPEC": spec})
        mapa.MAPA[nome] = {"chao": None, "marcas": {}}
        mapa.LUGAR[nome] = None
    else:
        cfg = expandir(spec)
        cls = type("Gerado_" + nome, (Gerado,), {"name": nome, "SPEC": spec,
                                                 "amb": cfg.get("amb", "zumbido" if cfg.get("luz") in ("fria", "fluorescente") else ("vento" if cfg.get("tipo") == "exterior" else "chuva_dentro")),
                                                 "acoustic": cfg.get("acoustic", "sala" if cfg.get("tipo") != "exterior" else "aberto")})
        mapa.MAPA[nome] = marcas_de(cfg)
        mapa.LUGAR[nome] = spec.get("lugar", spec.get("base"))
        _vida(nome, cfg)
    scenes.REGISTRY[nome] = cls
    return nome


def _vida(nome, cfg):
    """Vida automática (lofi/cenario_vivo.py): lâmpadas que piscam, mariposas no poste, vaga-lumes no mato."""
    from . import cenario_vivo as cv
    G, itens = planta(cfg); v = {}
    fl = [(int(it["x"]), int(it["y"] - 4 * it["k"])) for it in itens if it["m"] == "fluorescente"]
    if fl: v["pisca"] = fl
    lp = [(int(it["x"]), int(it["y"] - 60 * it["k"])) for it in itens if it["m"] in ("lampada",)]
    pos = [(int(it["x"] + 61 * it["k"]), int(it["y"] - 500 * it["k"])) for it in itens if it["m"] == "poste" and it["opts"].get("aceso", True)]
    if lp or pos: v["mariposas"] = (lp + pos)[:3]
    if cfg.get("tipo") == "exterior" and cfg.get("hora", "noite") in ("noite", "madrugada") and cfg.get("chao") in ("grama", "terra"):
        v["vagalumes"] = (40, int(G.yf), 1040, 1750)
    if cfg.get("tipo") != "exterior" and cfg.get("piso") in ("concreto", "terra"): v["poeira"] = (300, 400, 800, 1500)
    if v: cv.VIDA[nome] = v
    if cfg.get("tipo") != "exterior": cv.INTERNOS.add(nome)


def registrar_ambientes():
    """Os ambientes prontos entram no REGISTRY com o próprio nome (ex.: "scene": "cozinha")."""
    from . import scenes, mapa
    for nome, amb in AMBIENTES.items():
        if nome in scenes.REGISTRY: continue
        cls = type("Amb_" + nome, (Gerado,), {"name": nome, "SPEC": {"base": nome},
                                              "amb": amb.get("amb", "zumbido" if amb.get("luz") in ("fria", "fluorescente") else ("vento" if amb.get("tipo") == "exterior" else "chuva_dentro")),
                                              "acoustic": amb.get("acoustic", "sala")})
        scenes.REGISTRY[nome] = cls
        cfg = expandir({"base": nome})
        mapa.MAPA[nome] = marcas_de(cfg)
        mapa.LUGAR.setdefault(nome, nome)
        _vida(nome, cfg)


def resolver_plano(shot):
    """Troca "cenario" (descrição) por "scene": <nome registrado>. Usado por mapa.resolver_plano."""
    if isinstance(shot.get("cenario"), (dict, str)):
        shot["scene"] = registrar(shot["cenario"])
    return shot


# ============================== FOLHA DE CONFERÊNCIA ==============================
def folha(nomes, saida, cols=5):
    from . import scenes
    registrar_ambientes()
    th = []
    for n in nomes:
        sc = scenes.get(n); img = sc.render_back(0.5, 0, {})
        img = sc.render_front(img, 0.5, 0, {}, [])
        im = img.resize((270, 480)); dd = ImageDraw.Draw(im)
        dd.rectangle([0, 444, 270, 480], fill=(0, 0, 0)); dd.text((8, 450), n, font=font("sansb", 22), fill=(255, 255, 255))
        th.append(im)
    rows = (len(th) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 270, rows * 480), (0, 0, 0))
    for i, im in enumerate(th): sheet.paste(im, ((i % cols) * 270, (i // cols) * 480))
    sheet.save(saida, quality=88)
    return saida


registrar_ambientes()


if __name__ == "__main__":
    args = sys.argv[1:]
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not args:
        print(folha(list(AMBIENTES), os.path.join(raiz, "examples", "ambientes.jpg")))
    else:
        for n in args: print(folha([n], f"_amb_{n}.png", cols=1))
