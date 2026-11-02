"""Prévia do roteiro: uma imagem com um quadro por cena, ANTES de gravar as vozes.

    python3 -m lofi.previa series/dia-zero/ep05_roteiro.md            -> series/dia-zero/ep05_previa.png

Lê CENÁRIO (ou PLANO DE DETALHE), hora/clima, PERSONAGENS (nomes, marcas, vista, emoção, pose, mãos dadas, horda),
"só a mão de X" e `travelling` direto do roteiro e desenha cada cena com o motor. Embaixo de cada quadro: número da
cena, cenário, lugar no mapa e a hora. Serve para conferir se lugar, posições e objetos batem antes de gastar créditos
de voz. Não precisa de áudio.
"""
import json, os, re, sys, tempfile
from PIL import Image, ImageDraw
from . import scenes, detail, mapa, continuidade
from .rig import CHARS, POSES, EMOTIONS
from .core import font

TW, TH = 270, 480
HORAS = {"amanhecer": "amanhecer", "madrugada": "madrugada", "noite": "noite", "entardecer": "entardecer", "dia": "dia"}
VISTA = {"de costas": "back", "de lado": "side", "3q": "3q", "de frente": "front"}


def _nomes(pasta):
    nomes = set(CHARS)
    p = os.path.join(pasta, "personagens.json")
    if os.path.exists(p): nomes |= set(json.load(open(p, encoding="utf-8")).get("characters", json.load(open(p, encoding="utf-8"))))
    return nomes


def plano_da_cena(n, corpo, nomes):
    """Converte o texto de uma cena num plano do motor (aproximado, só para a prévia)."""
    det = re.search(r"PLANO DE DETALHE[^:\n]*:\s*`([^`]+)`", corpo, re.I)
    mao = re.search(r"m[ãa]o d[aeo]\s*`(\w+)`", corpo, re.I)
    if det and det.group(1) in detail.SUBJECTS:
        s = {"type": "detail", "subject": det.group(1)}
        if mao: s["hand"] = mao.group(1)
        if re.search(r"onde\W+carro|igni[çc][ãa]o", corpo, re.I): s["params"] = {"onde": "carro"}
        return s
    m = re.search(r"CEN[AÁ]RIO[^:\n]*:\**\s*`([^`]+)`", corpo, re.I)
    if not m or m.group(1) not in scenes.REGISTRY: return None
    cena = m.group(1); linha = corpo[m.start(): corpo.find("\n", m.start())]
    s = {"scene": cena, "hud": False}
    for k, v in HORAS.items():
        if re.search(rf"\b{k}\b", linha, re.I) and cena not in ("radio", "radio_carro", "carro"): s["time"] = v
    if re.search(r"chuva forte|`rain`\s*`forte`", corpo, re.I): s["rain"] = "forte"
    elif re.search(r"sem chuva|`rain`\s*`nenhuma`", corpo, re.I): s["rain"] = "nenhuma"
    f = re.search(r"`fog`\s*([\d.]+)", corpo); d = re.search(r"`dark`\s*([\d.]+)", corpo)
    if f: s["fog"] = float(f.group(1))
    if d: s["dark"] = float(d.group(1))
    if mao: s["hand"] = mao.group(1)
    pl = re.search(r"^PLANO[^:\n]*:(.*)$", corpo, re.M)
    if pl and "`travelling`" in pl.group(1):
        s["travelling"] = {"speed": 300, "dir": "frente" if "de frente" in pl.group(1) else ("fundo" if "por trás" in pl.group(1) else "lado")}
    if pl:   # enquadramento: plano aberto / conjunto / médio / close
        txt = pl.group(1).lower()
        for chave, plano in (("`close`", "close"), ("close", "close"), ("médio", "medio"), ("`medio`", "medio"), ("medio", "medio"),
                             ("conjunto", "conjunto"), ("aberto", "aberto"), ("geral", "aberto")):
            if chave in txt: s.setdefault("camera", {})["plano"] = plano; break
    pe = re.search(r"^PERSONAGENS[^:\n]*:(.*)$", corpo, re.M)
    atores = []
    marcas = mapa.marcas("_travelling" if s.get("travelling") else cena)
    if pe and not re.search(r"s[óo] a m[ãa]o", pe.group(1), re.I):
        for grupo in re.split(r"\s·\s", pe.group(1)):
            toks = re.findall(r"`([^`]+)`", grupo)
            quem = [t for t in toks if t in nomes]
            if "crowd" in toks: s["crowd"] = {"count": 8, "area": [80, 1300, 1000, 1500], "dir": 0, "speed": 8, "seed": n}
            if not quem: continue
            mk = [t for t in toks if t in marcas]
            vista = next((v for k, v in VISTA.items() if k in grupo), None) or ("3q" if "3q" in toks else None)
            emo = next((t for t in toks if t in EMOTIONS), None); pose = next((t for t in toks if t in POSES and t != "hold"), None)
            for i, q in enumerate(quem):
                a = {"char": q, "lipsync": False}
                if mk: a["mark"] = mk[0]; a["dx"] = (i - (len(quem) - 1) / 2) * 130
                if vista: a["view"] = vista
                if emo: a["emotion"] = emo
                if pose: a["pose"] = pose
                if pose == "sit" and "assento moto" in grupo: a["assento"] = "moto"; a["view"] = "side"
                if "fg" in toks: a.update(fg=True, x=330 + i * 480, y=2380, scale=3.0, view="back"); a.pop("mark", None)
                if "flashlight" in toks and i == 0: a["flashlight"] = 10
                if s.get("travelling"): a["walk"] = True; a.setdefault("mark", "centro"); a.setdefault("dx", (i - (len(quem) - 1) / 2) * 130)
                if q.startswith("zombie"): a["livre"] = True
                atores.append(a)
            if "hold" in toks and len(quem) >= 2: atores[-len(quem)]["hold"] = quem[1]
    # quem não tem marca vai para uma marca livre do cenário (ou para o meio do chão)
    livres = [k for k in marcas]
    for i, a in enumerate(atores):
        if "mark" not in a and not a.get("fg") and not ("x" in a):
            if livres: a["mark"] = livres[i % len(livres)]
    s["actors"] = atores
    return s


def previa(caminho, saida=None):
    pasta = os.path.dirname(os.path.abspath(caminho)); txt = open(caminho, encoding="utf-8").read()
    nomes = _nomes(pasta); mundo = continuidade.carregar(pasta)
    planos, rotulos = [], []
    for n, corpo in continuidade.cenas(txt):
        s = plano_da_cena(n, corpo, nomes)
        if s is None: continue
        hora = re.search(r"DIA\s*(\d+)\s*[·\-,]?\s*(\d{1,2}:\d{2})", corpo)
        lug = continuidade.lugar_de(mundo, s.get("scene")) if s.get("scene") else "detalhe"
        tag = "INSERÇÃO" if re.search(r"INSER[ÇC][ÃA]O", corpo, re.I) else ("LIGAÇÃO" if re.search(r"LIGA[ÇC][ÃA]O\s*:", corpo, re.I) else "")
        rotulos.append((f"CENA {n}" + (f" · {tag}" if tag else ""), s.get("scene") or s.get("subject"),
                        (lug or "") + (f" · D{hora.group(1)} {hora.group(2)}" if hora else "")))
        planos.append(s)
    if not planos: raise SystemExit("nenhuma cena reconhecida no roteiro")
    shots = []
    for i, s in enumerate(planos): shots.append(dict(s, start=i * 2.0, end=i * 2.0 + 2.0, transition="cut"))
    spec = {"out": "x.mp4", "fps": 30, "total": len(shots) * 2.0, "voices": {}, "shots": shots, "legado": True, "gestures": False}
    pj = os.path.join(pasta, "personagens.json")
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, dir=pasta); json.dump(spec, tmp); tmp.close()
    try:
        from .render import Episode
        ep = Episode(tmp.name)
        ims = [ep.frame(i * 2.0 + 1.0).resize((TW, TH)) for i in range(len(shots))]
    finally:
        os.unlink(tmp.name)
    cols = 6; rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TW, rows * (TH + 70)), (250, 248, 242)); d = ImageDraw.Draw(sheet)
    for i, (im, (a, b, c)) in enumerate(zip(ims, rotulos)):
        x, y = (i % cols) * TW, (i // cols) * (TH + 70)
        sheet.paste(im, (x, y))
        d.text((x + 6, y + TH + 4), a, font=font("sansb", 18), fill=(180, 30, 30) if "INSER" in a else (20, 20, 20))
        d.text((x + 6, y + TH + 26), b or "", font=font("sans", 17), fill=(40, 40, 40))
        d.text((x + 6, y + TH + 46), c, font=font("sans", 15), fill=(90, 90, 90))
    saida = saida or re.sub(r"_roteiro\.md$", "_previa.png", caminho)
    sheet.save(saida); return saida


if __name__ == "__main__":
    print(previa(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
