"""Estilo "imagens": episódios montados com imagens geradas fora (ChatGPT etc.) em vez do desenho por código.

Fluxo:
  1. Planejar:  python3 -m lofi.imagens referencias series/<serie>
                -> prompts das fichas de referência de cada personagem (frente, 3/4, lado) para anexar no ChatGPT
  2. Roteiro:   cada cena tem uma linha  IMAGENS: fundo `hospital_corredor` (corredor de hospital à noite) · `lia_frente_medo` · `soldado_34_neutro`
                python3 -m lofi.imagens prompts series/<serie>/epNN_roteiro.md
                -> epNN_imagens.md: só as imagens que ainda não existem em series/<serie>/imagens/, cada uma com o prompt pronto
  Variantes opcionais de cada personagem: <nome>_piscando (olhos fechados) e <nome>_falando (boca aberta,
  usada enquanto a voz de "fala" estiver alta). Mesma imagem, só os olhos ou a boca mudam.
  3. Montar:    python3 -m lofi.imagens importar series/<serie> arquivo.png lia_frente_medo
                (tira o fundo liso se a imagem não vier transparente, corta as sobras e salva em imagens/<nome>.png)
                no JSON, cada plano usa  "imagens": {"fundo": "hospital_corredor", "personagens": [{"img": "lia_frente_medo", "pos": "esq", "fala": "lia"}]}
                python3 -m lofi.imagens faltam series/<serie>/epNN.json   -> confere se todas as imagens estão na pasta

Nomes: fundos = o lugar (`hospital_corredor`); personagens = <personagem>_<vista>_<emoção>[_<pose>]
(vistas: frente, 34, lado, costas; emoções: neutro, medo, choque, raiva, triste, determinado, feliz, desconfiado, choro;
poses: em_pe, correndo, andando, sentado, chao, apontando, segurando_radio, ...); objetos = obj_<nome>.
"""
import os, re, sys, json, glob, math
from PIL import Image, ImageDraw, ImageFilter, ImageChops

PASTA = "imagens"
MASTER_STYLE = """MASTER CHARACTER STYLE — MANDATORY

All characters must follow the exact same visual identity:

ART STYLE:

- Dark Cinematic Lo-Fi Cartoon 2D.
- Hand-painted digital illustration.
- Mature graphic novel aesthetic.
- Clean, slightly textured dark outlines.
- Soft painterly shading with subtle brush textures.
- Muted, desaturated colors.
- Cold blue-gray and dusty purple undertones.
- Detailed clothing textures, folds and shadows.
- Consistent rendering quality across all characters.

HEAD AND FACE — CRITICAL:

- Perfectly round, smooth, spherical cartoon head.
- Soft off-white, slightly grayish face color.
- Muted porcelain-white appearance, never pure bright white.
- Subtle cool-gray and lavender shadows around the edges.
- Gentle shading to emphasize the spherical shape.
- Small black oval eyes.
- Minimalist black eyebrows.
- Small, simple mouth, always visible in front and three-quarter views.
- No realistic nose, ears or human facial anatomy.
- Hair and facial hair may vary between characters.
- Preserve the same head shape and face color across the entire series.

BODY AND SKIN:

- All visible skin must use the same muted off-white grayish tone as the face.
- No natural human skin tones.
- Soft gray-lavender shadows on arms, hands, legs and neck.
- Never use pure white or glowing skin.
- Anatomically appropriate body proportions.
- Adults: approximately 6.5–7 heads tall.
- Children: age-appropriate proportions, approximately 5–5.5 heads tall.
- No chibi proportions.

COLOR AND LIGHTING:

- Muted, low-saturation color palette.
- Soft cinematic ambient lighting.
- Moderate contrast.
- Subtle cool shadows.
- No harsh highlights on white surfaces.
- No excessive brightness or glossy effects.

CHARACTER CONSISTENCY:

- Identical head shape and skin tone for every character.
- Consistent facial feature style.
- Consistent line thickness and shading technique.
- Hairstyles, clothing, accessories and body proportions may vary.
- Preserve each character's established appearance across scenes."""
NEGATIVO_MASTER = "Pure white skin, glowing white face, bright white limbs, realistic skin tones, human facial anatomy, realistic nose, photorealistic face, 3D render, Pixar style, anime, manga, chibi, oversized head, short adult legs, flat vector art, plastic skin, overly saturated colors, inconsistent character design"
ESTILO_PADRAO = ("Dark Cinematic Lo-Fi Cartoon 2D, hand-painted digital illustration, mature graphic novel aesthetic, clean slightly textured dark outlines, soft painterly "
                 "shading with subtle brush textures, muted desaturated colors, cold blue-gray and dusty purple undertones. Perfectly round, smooth, spherical cartoon head; "
                 "all skin in the same muted off-white grayish porcelain tone with cool-gray and lavender shadows; small black oval eyes, minimalist black eyebrows, small simple mouth; "
                 "no realistic nose, ears or human facial anatomy; adults 6.5-7 heads tall, children 5-5.5 heads tall. Avoid: " + NEGATIVO_MASTER)
NEGATIVO_REF = NEGATIVO_MASTER + ", text, logos, watermark."
MODELO_REFERENCIA = """Create a professional 2D character model sheet.

""" + MASTER_STYLE + """

CHARACTER:
{personagem}

CLOTHING:

{roupa}

CHARACTER SHEET COMPOSITION:
Show the exact same character in three full-body views, side by side:

1. Front view.
2. Three-quarter view.
3. Back view.

Maintain identical body proportions, clothing details, colors, facial features and accessories across all views.

Neutral standing pose with arms relaxed.

Plain light-gray background with very subtle grounding shadows.

Landscape composition, 3:2 aspect ratio.

NEGATIVE PROMPT:
{negativo}"""
FOLHAS = [
 ("Folha 1: 8 ângulos", ["front view", "front three-quarter view facing right", "right side profile", "back three-quarter view facing right", "back view", "back three-quarter view facing left", "left side profile", "front three-quarter view facing left"]),
 ("Folha 2: movimento", ["walking", "running", "jumping", "crawling on the ground", "crouching and hiding", "sitting on a chair", "sitting on the floor hugging the knees", "fallen on the ground"]),
 ("Folha 3: ações", ["pointing with the arm extended", "pushing a door open", "reaching forward", "hugging someone (only this person, arms open)", "carrying a heavy box in both arms", "talking on a smartphone", "speaking into a handheld CB radio", "holding a flashlight and aiming it"]),
 ("Folha 4: gestos", ["thinking, hand on the chin", "despair, hands on the head", "hand over the mouth", "finger on the lips asking for silence", "hand to the ear, listening", "hands up in surrender", "arms protecting the face", "hugging oneself and trembling"]),
]
VISTAS = {"frente": "de frente para a câmera", "34": "em três quartos (3/4), levemente virado", "lado": "de perfil (de lado)",
          "costas": "de costas para a câmera"}
EMOCOES = {"neutro": "expressão neutra", "medo": "expressão de medo, olhos arregalados", "choque": "expressão de choque, boca aberta",
           "raiva": "expressão de raiva, sobrancelhas franzidas", "triste": "expressão triste", "determinado": "expressão determinada",
           "feliz": "sorrindo", "desconfiado": "olhar desconfiado", "choro": "chorando", "cansado": "cansado, ofegante",
           "falando": "falando, boca entreaberta"}
POSES = {"em_pe": "de pé, corpo inteiro", "correndo": "correndo, corpo inteiro em movimento", "andando": "andando, corpo inteiro",
         "sentado": "sentado, corpo inteiro", "chao": "sentado no chão, abraçando os joelhos", "apontando": "apontando com o braço esticado",
         "agachado": "agachado, escondido", "caido": "caído no chão", "abraco": "abraçando alguém (só a pessoa, braços abertos)"}
CORES = {"preto": (20, 20, 22), "branco": (240, 240, 240), "cinza": (128, 128, 128), "cinza escuro": (70, 70, 75), "vermelho": (200, 40, 40),
         "vinho": (110, 30, 40), "laranja": (230, 130, 40), "amarelo": (236, 200, 50), "verde": (60, 140, 70), "verde escuro": (40, 80, 50), "verde-oliva": (75, 90, 60),
         "azul": (50, 90, 190), "azul-marinho": (30, 40, 80), "azul-claro": (120, 170, 220), "azul-esverdeado": (96, 168, 178),
         "roxo": (110, 60, 160), "rosa": (230, 120, 170), "marrom": (110, 70, 40), "bege": (210, 190, 150), "castanho": (60, 40, 30)}
ROUPAS = {"shirt": "camisa", "tshirt": "camiseta", "puffer": "jaqueta acolchoada (puffer)", "hoodie": "moletom com capuz", "sweater": "suéter",
          "leather": "jaqueta de couro", "suit": "terno", "trench": "sobretudo", "labcoat": "jaleco branco", "scrubs": "uniforme hospitalar (pijama cirúrgico)",
          "uniform": "farda", "chef": "dólmã de chef", "dress": "vestido", "torn": "roupa rasgada e suja"}
CABELOS = {"short": "cabelo curto {c}", "long": "cabelo comprido {c}", "ponytail": "cabelo {c} preso em rabo de cavalo",
           "bun": "cabelo {c} preso num coque no alto da cabeça", "bob": "cabelo chanel {c}", "curly": "cabelo cacheado {c}",
           "afro": "cabelo black power {c}", "braids": "tranças {c}", "pigtails": "maria-chiquinha {c}", "spiky": "cabelo espetado {c}",
           "mohawk": "moicano {c}", "bald": "careca"}
CHAPEUS = {"beanie": "gorro de lã listrado", "cap": "boné", "helmet": "capacete militar", "hood": "capuz levantado", "fedora": "chapéu fedora",
           "cowboy": "chapéu de cowboy", "capacete_moto": "capacete de moto aberto"}
PELES = {"palido": "pele bem clara", "claro": "pele clara", "medio": "pele morena clara", "moreno": "pele morena", "escuro": "pele negra",
         "oliva": "pele oliva"}


def _cor(rgb):
    if not rgb: return ""
    if isinstance(rgb, str): return rgb
    return min(CORES, key=lambda k: sum((a - b) ** 2 for a, b in zip(CORES[k], rgb)))


# ---------------------------------------------------------------- descrição dos personagens
def descricao(nome, ficha):
    """Aparência fixa do personagem para os prompts: o campo "aparencia" da ficha, ou montada a partir do guarda-roupa."""
    if ficha.get("aparencia"): return ficha["aparencia"]
    try:
        from .rig import CHARS
        ficha = {**CHARS.get(nome, {}), **ficha}
    except Exception: pass
    p = []
    if ficha.get("body") == "child": p.append("criança")
    elif ficha.get("body") == "old": p.append("pessoa idosa")
    sk = ficha.get("skin")
    if isinstance(sk, str) and sk in PELES: p.append(PELES[sk])
    if ficha.get("hair"): p.append(CABELOS.get(ficha["hair"], ficha["hair"] + " {c}").replace("{c}", _cor(ficha.get("hair_color"))).strip())
    if ficha.get("facial"): p.append({"beard": "barba", "mustache": "bigode", "stubble": "barba por fazer"}.get(ficha["facial"], ficha["facial"]))
    if ficha.get("hat"): p.append(f"{CHAPEUS.get(ficha['hat'], ficha['hat'])} {_cor(ficha.get('hat_color'))}".strip())
    roupa = ROUPAS.get(ficha.get("top_style", "shirt"), ficha.get("top_style", ""))
    if ficha.get("top"): p.append(f"{roupa} {_cor(ficha['top'])}")
    if ficha.get("legs") and ficha.get("top_style") != "dress": p.append(f"calça {_cor(ficha['legs'])}")
    if ficha.get("scarf"): p.append(f"cachecol {_cor(ficha['scarf'])}")
    if ficha.get("backpack"): p.append(f"mochila {_cor(ficha['backpack'])}")
    if ficha.get("glasses"): p.append("óculos")
    if ficha.get("infected") or nome.startswith("zombie"): p.append("zumbi: pele acinzentada, olhos brancos brilhando, andar torto")
    return ", ".join(x for x in p if x)


def _serie(caminho):
    pasta = caminho if os.path.isdir(caminho) else os.path.dirname(os.path.abspath(caminho))
    bib = open(os.path.join(pasta, "biblia.md"), encoding="utf-8").read() if os.path.exists(os.path.join(pasta, "biblia.md")) else ""
    pj = os.path.join(pasta, "personagens.json")
    fichas = {k: v for k, v in json.load(open(pj, encoding="utf-8")).items() if not k.startswith("_")} if os.path.exists(pj) else {}
    m = re.search(r"Prompt de estilo\W*:\s*(.+)", bib)
    estilo = m.group(1).strip() if m else ESTILO_PADRAO
    return pasta, bib, fichas, estilo


def existentes(pasta):
    return {os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(pasta, PASTA, "*.png"))}


# ---------------------------------------------------------------- prompts
def prompt_personagem(nome_img, fichas, estilo, extra=""):
    partes = nome_img.split("_")
    quem = partes[0]
    i = 1
    while i < len(partes) and "_".join(partes[:i + 1]) in fichas: i += 1
    quem = "_".join(partes[:i]); resto = partes[i:]
    vista = next((VISTAS[r] for r in resto if r in VISTAS), VISTAS["frente"])
    emo = next((EMOCOES[r] for r in resto if r in EMOCOES), EMOCOES["neutro"])
    pose_k = "_".join(r for r in resto if r not in VISTAS and r not in EMOCOES)
    pose = POSES.get(pose_k, pose_k.replace("_", " ") if pose_k else POSES["em_pe"])
    desc = descricao(quem, fichas.get(quem, {}))
    return (f"{estilo}. Personagem {quem.upper()}: {desc}. {pose}, {vista}, {emo}"
            + (f", {extra}" if extra else "") + ". Corpo inteiro centralizado, sem cortar pés nem cabeça. "
            "FUNDO TRANSPARENTE (PNG); se não der, fundo branco liso sem sombra no chão. Use a ficha de referência anexada "
            "para manter o mesmo rosto, cabelo e roupa. Formato retrato 2:3.")


def prompt_fundo(nome_img, estilo, extra=""):
    lugar = nome_img.replace("fundo_", "").replace("_", " ")
    return (f"{estilo}. Cenário: {extra or lugar}. SEM PESSOAS, sem personagens. Formato paisagem 3:2, com o que importa no "
            "terço central (a imagem é cortada em pé para o TikTok e deitada para o YouTube) e chão visível na parte de baixo.")


def prompt_objeto(nome_img, estilo, extra=""):
    obj = nome_img.replace("obj_", "").replace("_", " ")
    return (f"{estilo}. Objeto isolado: {extra or obj}. FUNDO TRANSPARENTE (PNG); se não der, fundo branco liso. Formato quadrado.")


ITEM = re.compile(r"(fundo\s+)?`([a-z0-9_]+)`\s*(\(([^)]*)\))?", re.I)


def ler_roteiro(caminho):
    """[(cena, nome, tipo, detalhe)] das linhas IMAGENS: do roteiro."""
    txt = open(caminho, encoding="utf-8").read(); itens = []; cena = None
    for linha in txt.split("\n"):
        mc = re.match(r"^#+\s*CENA\s+(\d+)", linha, re.I)
        if mc: cena = int(mc.group(1))
        mi = re.match(r"^\s*\**IMAGENS\**\s*:\s*(.*)", linha, re.I)
        if not mi: continue
        for m in ITEM.finditer(mi.group(1)):
            nome = m.group(2).lower(); det = (m.group(4) or "").strip()
            tipo = "fundo" if m.group(1) or nome.startswith("fundo_") else ("objeto" if nome.startswith("obj_") else "personagem")
            if tipo == "fundo" and not nome.startswith("fundo_"): nome = "fundo_" + nome
            itens.append((cena, nome, tipo, det))
    return itens


def prompts(caminho_roteiro, todas=False):
    pasta, bib, fichas, estilo = _serie(caminho_roteiro)
    ja = existentes(pasta); vistos = {}; saida = []
    for cena, nome, tipo, det in ler_roteiro(caminho_roteiro):
        if nome in vistos: vistos[nome][0].append(cena); continue
        if nome in ja and not todas: continue
        p = prompt_fundo(nome, estilo, det) if tipo == "fundo" else (prompt_objeto(nome, estilo, det) if tipo == "objeto"
                                                                      else prompt_personagem(nome, fichas, estilo, det))
        vistos[nome] = ([cena], tipo, p); saida.append(nome)
    for nome in list(saida):                    # personagens que aparecem em 2+ cenas: variante piscando (opcional)
        cenas_, tipo, _ = vistos[nome]
        pn = nome + "_piscando"
        if tipo == "personagem" and len(set(cenas_)) >= 2 and pn not in ja and pn not in vistos:
            vistos[pn] = (cenas_, "piscar (opcional)", f"Edite a imagem {nome} que você acabou de gerar: exatamente a mesma imagem, "
                          "mesma pose, roupa e traços, só com os OLHOS FECHADOS (piscando). Mantenha o fundo igual (transparente ou branco liso).")
            saida.append(pn)
    base = os.path.splitext(caminho_roteiro)[0].replace("_roteiro", "")
    out = base + "_imagens.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# Imagens para gerar — {os.path.basename(base)}\n\n")
        f.write(f"{len(saida)} imagens novas (as que já estão em `{PASTA}/` foram reaproveitadas). Gere cada uma e mande com o nome indicado.\n\n")
        for k, nome in enumerate(saida, 1):
            cenas, tipo, p = vistos[nome]
            f.write(f"## {k}. `{nome}` · {tipo} · cenas {', '.join(str(c) for c in cenas if c is not None)}\n\n```\n{p}\n```\n\n")
    print(f"{len(saida)} imagens novas -> {out}")
    return out, [(n, vistos[n]) for n in saida]


def prompt_referencia(nome, ficha):
    """Ficha de referência (frente, 3/4 e costas) no modelo padrão. Campos da ficha: ref_personagem (frase + traços), ref_roupa (lista),
    ref_importante e ref_negativo (só quando o personagem foge do adulto padrão, como crianças e criaturas)."""
    lista = lambda v: "\n".join(f"- {x}" for x in v) if isinstance(v, list) else str(v)
    pers = ficha.get("ref_personagem")
    personagem = (pers[0] + "\n\n" + lista(pers[1:])) if isinstance(pers, list) else (pers or f"{nome.capitalize()}: {descricao(nome, ficha)}.")
    return MODELO_REFERENCIA.format(personagem=personagem, roupa=lista(ficha.get("ref_roupa", "Clothing as described above.")),
                                    negativo=ficha.get("ref_negativo", NEGATIVO_REF))


def _linha_elenco(n, nome, ficha):
    """Uma linha do elenco: só o que muda entre os personagens (rosto e pele já estão no estilo)."""
    p = ficha.get("ref_personagem")
    if not isinstance(p, list): return f"Row {n}: {descricao(nome, ficha)}"
    fora = ("cartoon face", "oval eyes", "eyebrows", "simplified mouth", "legs", "shoulder width")
    tracos = [x.rstrip(".") for x in p[1:] if not any(f in x for f in fora)]
    return f"Row {n}: {p[0].rstrip('.')}. " + "; ".join(tracos) + ". Wearing: " + "; ".join(x.rstrip(".") for x in ficha.get("ref_roupa", [])) + "."


def folhas(pasta_serie):
    """Folhas do elenco inteiro: cada personagem numa linha, 8 colunas. Saída: imagens_folhas.md."""
    pasta, bib, fichas, estilo = _serie(pasta_serie)
    nomes = [n for n in fichas if not (n.startswith("zombie") and n != "zombie")]
    elenco = "\n".join(_linha_elenco(i + 1, n, fichas[n]) for i, n in enumerate(nomes))
    out = os.path.join(pasta, "imagens_folhas.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("# Folhas do elenco\n\nCada personagem numa linha, 8 posições por linha. Para uma folha maior de um só personagem, deixe só a linha dele em CHARACTERS.\n\n")
        for titulo, pos in FOLHAS:
            colunas = "\n".join(f"{i + 1}. {x}." for i, x in enumerate(pos))
            f.write(f"## {titulo}\n\n```\nCreate a professional 2D character sheet of the whole cast, with each character in one horizontal row, one below the other, "
                    f"from top to bottom, in the exact order listed.\n\n{MASTER_STYLE}\n\nCHARACTERS, ONE ROW EACH:\n{elenco}\n\nCOLUMNS, THE SAME 8 POSITIONS IN EVERY ROW, FROM LEFT TO RIGHT:\n{colunas}\n\n"
                    "COMPOSITION:\nA clean grid with one full-body figure per cell, evenly spaced, none overlapping or cropped, same scale for every adult. "
                    "Keep every character's body, clothing, colors and accessories identical in all 8 positions. Plain light-gray background with very subtle grounding shadows. "
                    f"Vertical composition, 2:3 aspect ratio.\n\nNEGATIVE PROMPT:\n{NEGATIVO_REF}\n```\n\n")
    print("folhas ->", out); return out


def referencias(pasta_serie):
    pasta, bib, fichas, estilo = _serie(pasta_serie)
    out = os.path.join(pasta, "imagens_referencias.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("# Fichas de referência dos personagens\n\nGere uma por personagem e anexe no ChatGPT junto com cada prompt de pose, "
                "para o rosto, o cabelo e a roupa saírem sempre iguais. Salve como `ref_<personagem>.png`.\n\n")
        for nome, ficha in fichas.items():
            if nome.startswith("zombie") and nome != "zombie": continue
            f.write(f"## `ref_{nome}`\n\n```\n{prompt_referencia(nome, ficha)}\n```\n\n")
    print("referências ->", out); return out


# ---------------------------------------------------------------- importar (tirar fundo liso e sobras)
def tirar_fundo(im, tol=38):
    """Sem transparência: apaga o fundo liso ligado às bordas (preenchimento a partir dos cantos e do meio das bordas)."""
    im = im.convert("RGBA")
    a = im.split()[3]
    if a.getextrema()[0] < 250: return im                       # já tem transparência
    rgb = im.convert("RGB"); w, h = rgb.size
    marca = (255, 0, 255)
    for p in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (0, h // 2), (w - 1, h // 2)]:
        if rgb.getpixel(p) != marca: ImageDraw.floodfill(rgb, p, marca, thresh=tol)
    import numpy as np
    arr = np.asarray(rgb); fundo = (arr[..., 0] == 255) & (arr[..., 1] == 0) & (arr[..., 2] == 255)
    mask = Image.fromarray(np.where(fundo, 0, 255).astype("uint8")).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    im.putalpha(ImageChops.multiply(a, mask))
    return im


def importar(pasta_serie, arquivo, nome):
    os.makedirs(os.path.join(pasta_serie, PASTA), exist_ok=True)
    im = Image.open(arquivo)
    if nome.startswith("fundo_") or nome.startswith("ref_"):
        im = im.convert("RGB")
    else:
        im = tirar_fundo(im)
        bb = im.split()[3].point(lambda v: 255 if v > 20 else 0).getbbox()
        if bb: im = im.crop(bb)
    out = os.path.join(pasta_serie, PASTA, nome + ".png"); im.save(out)
    print("salvo:", out, im.size); return out


# ---------------------------------------------------------------- montar a cena (usado pelo render)
_CACHE = {}


def carregar(pasta_serie, nome):
    cam = os.path.join(pasta_serie, PASTA, nome + ".png")
    if not os.path.exists(cam): raise FileNotFoundError(f"imagem não encontrada: {PASTA}/{nome}.png")
    k = (cam, os.path.getmtime(cam))
    if k not in _CACHE:
        if len(_CACHE) > 60: _CACHE.clear()
        im = Image.open(cam).convert("RGBA")
        if not nome.startswith(("fundo_", "ref_")) and im.split()[3].getextrema()[0] >= 250: im = tirar_fundo(im)
        _CACHE[k] = im
    return _CACHE[k]


POS = {"esq": 0.28, "esquerda": 0.28, "centro": 0.5, "meio": 0.5, "dir": 0.72, "direita": 0.72}


def quadro(shot, t, pasta_serie, size, nivel=None):
    """Desenha o plano `"imagens": {...}` no tempo t (segundos do episódio). nivel(voz, t) -> 0..1 faz quem fala se mexer."""
    W_, H_ = size; cfg = shot["imagens"]; rel = max(0.0, t - shot["start"])
    dur = max(1e-3, shot["end"] - shot["start"]); u = min(1.0, rel / dur)
    largo = W_ > H_
    canvas = Image.new("RGB", size, (8, 8, 12))
    pessoas = cfg.get("personagens", [])
    # câmera: aproximação lenta por padrão; "plano": "medio" / "close" aproxima de quem está em "alvo" (padrão: o 1º)
    plano = cfg.get("plano", "aberto")
    z = {"aberto": 1.0, "medio": 1.35, "close": 2.0}.get(plano, 1.0)
    z *= 1 + 0.06 * u * cfg.get("aproximar", 1.0)
    layers = []                          # (imagem, x, y, escala, profundidade)
    sway = math.sin(t * 0.65) * W_ * 0.006 * cfg.get("balanco", 1.0)      # câmera balança de leve; o fundo mexe menos (paralaxe)
    if cfg.get("fundo"):
        fundo = carregar(pasta_serie, cfg["fundo"] if cfg["fundo"].startswith("fundo_") else "fundo_" + cfg["fundo"])
        s = max(W_ / fundo.width, H_ / fundo.height) * 1.03
        fy = cfg.get("fundo_y", 0.5)
        layers.append((fundo, (W_ - fundo.width * s) / 2, (H_ - fundo.height * s) * fy, s, 0.3))
    alt_pad = 0.80 if largo else (0.52 if len(pessoas) > 1 else 0.60)
    for k, p in enumerate(pessoas):
        im = carregar(pasta_serie, p["img"])
        pisc = p.get("piscar", p["img"] + "_piscando")              # olhos fechados por 0,12 s a cada ~3,6 s
        periodo = 3.6 + (k * 0.7)
        piscou = pisc and (t + k * 1.3) % periodo < 0.12 and os.path.exists(os.path.join(pasta_serie, PASTA, pisc + ".png"))
        if piscou:
            im = carregar(pasta_serie, pisc)
        # boca: com a voz alta, troca pela variante de boca aberta (<img>_falando), se existir
        boca = p.get("boca", p["img"] + "_falando")
        if (not piscou and nivel and p.get("fala") and boca and nivel(p["fala"], t) > 0.35
                and os.path.exists(os.path.join(pasta_serie, PASTA, boca + ".png"))):
            im = carregar(pasta_serie, boca)
        if p.get("espelhar"): im = im.transpose(Image.FLIP_LEFT_RIGHT)
        pos = p.get("pos", "centro"); fx = POS.get(pos, pos if isinstance(pos, (int, float)) else 0.5)
        if p.get("andar"):                                           # atravessa a cena: [de, até] (esq/centro/dir ou 0–1)
            a_, b_ = [POS.get(v, v) if isinstance(v, str) else v for v in p["andar"]]
            fx = a_ + (b_ - a_) * u
        if not largo and len(pessoas) > 1 and isinstance(pos, str) and not p.get("andar"): fx = 0.5 + (fx - 0.5) * 1.15
        alt = p.get("altura", alt_pad) * H_
        s = alt / im.height
        dy = 0.0
        respiro = math.sin(2 * math.pi * rel * 0.22 + k) * H_ * 0.0025
        if p.get("andar"): respiro = -abs(math.sin(rel * 8)) * H_ * 0.006                   # passo: sobe e desce
        if nivel and p.get("fala"):
            n = max(0.0, min(1.0, nivel(p["fala"], t)))
            dy -= n * H_ * 0.006; s *= 1 + 0.012 * n
        chao = p.get("chao", 0.97 if largo else 0.93)
        x = fx * W_ - im.width * s / 2; y = chao * H_ - im.height * s + dy + respiro
        layers.append((im, x, y, s, 1.0))
    def _obj(o, prof):
        im = carregar(pasta_serie, o["img"]); s = o.get("altura", 0.2) * H_ / im.height
        y = o.get("y", 0.7) * H_
        if o.get("flutuar"): y += math.sin(rel * o.get("velocidade", 1.0) * 2) * H_ * 0.006
        if o.get("pulsar"): s *= 1 + 0.02 * math.sin(rel * 3)
        return (im, o.get("x", 0.5) * W_ - im.width * s / 2, y - im.height * s / 2, s, prof)
    for o in cfg.get("objetos", []): layers.append(_obj(o, 1.0))
    for o in cfg.get("frente", []): layers.append(_obj(dict({"altura": 0.5, "y": 0.85}, **o), 1.4))   # primeiro plano (mexe mais)
    # ponto que a câmera segue
    if z > 1.0 and pessoas:
        al = cfg.get("alvo", 0); im, x, y, s, _ = layers[(1 if cfg.get("fundo") else 0) + min(al, len(pessoas) - 1)]
        alvo_x = x + im.width * s / 2; alvo_y = y + im.height * s * (0.16 if plano == "close" else 0.32)
    else:
        alvo_x, alvo_y = W_ / 2, H_ / 2
    ox = W_ / 2 - alvo_x * z; oy = (H_ * (0.42 if z > 1.0 else 0.5)) - alvo_y * z
    ox = min(0, max(W_ - W_ * z, ox)); oy = min(0, max(H_ - H_ * z, oy))
    for im, x, y, s, prof in layers:
        ss = s * z; w, h = max(1, int(im.width * ss)), max(1, int(im.height * ss))
        spr = im.resize((w, h), Image.BILINEAR)
        canvas.paste(spr, (int((x + sway * prof) * z + ox), int(y * z + oy)), spr)
    for ef in cfg.get("efeitos", []):
        nomef = ef if isinstance(ef, str) else ef.get("tipo")
        if nomef == "flicker":
            k = 1 - 0.18 * (0.5 + 0.5 * math.sin(t * 2.6 * 2 * math.pi)) ** 8
            canvas = Image.eval(canvas, lambda v, k=k: int(v * k))
        elif nomef == "escuro":
            canvas = Image.eval(canvas, lambda v: int(v * 0.55))
    return canvas


def faltam(spec_path):
    sp = json.load(open(spec_path, encoding="utf-8")); pasta = os.path.dirname(os.path.abspath(spec_path))
    ja = existentes(pasta); falta = []
    for s in sp.get("shots", []):
        cfg = s.get("imagens")
        if not cfg: continue
        nomes = [p["img"] for p in cfg.get("personagens", [])] + [o["img"] for o in cfg.get("objetos", []) + cfg.get("frente", [])]
        if cfg.get("fundo"): nomes.append(cfg["fundo"] if cfg["fundo"].startswith("fundo_") else "fundo_" + cfg["fundo"])
        falta += [(s["start"], n) for n in nomes if n not in ja]
    return falta


if __name__ == "__main__":
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "prompts": prompts(sys.argv[2], "--todas" in sys.argv)
    elif cmd == "referencias": referencias(sys.argv[2])
    elif cmd == "folhas": folhas(sys.argv[2])
    elif cmd == "importar": importar(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "faltam":
        f = faltam(sys.argv[2])
        for t, n in f: print(f"falta {PASTA}/{n}.png (plano em {t}s)")
        print("tudo certo" if not f else f"{len(f)} imagem(ns) faltando"); sys.exit(1 if f else 0)
    else: print(__doc__)
