"""Contagem automática dos votos A/B a partir dos prints dos comentários (TikTok, Instagram, YouTube).

    python3 -m lofi.votos contar series/dia-zero 4 print1.jpg print2.jpg:Instagram ...
        [--recortar]          salva os melhores comentários em series/<serie>/placar/epNN_cN.png (até 5)
        [--a "barulho,alarme"] [--b "silencio,esperar"]   palavras extras de cada opção

As opções e as palavras de cada uma vêm da tabela de episódios da bíblia ("A) Fazer barulho · B) Esperar em silêncio").
A rede de cada print sai do nome do arquivo (tiktok/insta/yt), de ":Rede" depois do caminho ou do próprio print.
Um voto por pessoa (somando os prints; vale o último); o comentário do criador não conta; comentário com A e B ao mesmo
tempo fica "dúvida" e não entra. Gera também <serie>/placar/epNN_conferencia.png (verde = A, laranja = B, cinza = não contou)
e imprime o plano "placar" pronto para colar no epNN.json.
"""
import sys, os, re, json, unicodedata
from PIL import Image, ImageDraw

CRIADOR = ("criador", "creator", "autor", "arquivo.zero", "arquivo zero")
FIM_COMENTARIO = re.compile(r"^(responder|reply|ver tradu|ver respostas|ver mais|curtir|\d+\s*(curtidas?|likes?|respostas?))", re.I)
RODAPE = re.compile(r"(\bresponder\b|\breply\b|\bh[aá]\s*\d+\s*(h|d|min|sem|s)\b|^\d+\s*(h|d|min|sem)\b)", re.I)
RUIDO = re.compile(r"^(responder|reply|ver tradu|curtir|\d+[smhd]|\d+\s*(min|h|sem|d)|há \d+)", re.I)
SELOS = re.compile(r"primeiro coment[aá]rio|first comment|fixado|pinned|curtido pel[oa] criador|liked by creator|autor", re.I)
VAZIAS = {"de", "da", "do", "o", "a", "e", "em", "no", "na", "com", "para", "pra", "um", "uma", "os", "as", "ou"}


def _norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def opcoes(pasta, ep):
    """{'A': (rotulo, [palavras]), 'B': (...)} lidas da tabela de episódios da bíblia."""
    bib = open(os.path.join(pasta, "biblia.md"), encoding="utf-8").read()
    for l in bib.split("\n"):
        cel = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cel) > 4 and cel[0] == str(ep):
            for c in cel:
                m = re.search(r"A\)\s*(.+?)\s*·\s*B\)\s*(.+)", c)
                if m:
                    a, b = m.group(1).strip(), m.group(2).strip()
                    return {"A": (a, _palavras(a)), "B": (b, _palavras(b))}
    return {"A": ("A", []), "B": ("B", [])}


def _palavras(rot):
    return [w for w in re.findall(r"\w+", _norm(rot)) if len(w) > 3 and w not in VAZIAS]


def _rede(caminho, texto):
    base = _norm(os.path.basename(caminho))
    for k, r in (("tiktok", "TikTok"), ("insta", "Instagram"), ("reels", "Instagram"), ("yt", "YouTube"), ("youtube", "YouTube")):
        if k in base: return r
    t = _norm(texto)
    if "curtida" in t or "ver traducao" in t: return "Instagram"
    if "respostas" in t and "responder" not in t: return "YouTube"
    return "TikTok"


def ler(caminho):
    """Linhas do print com posição: [(texto, x0, y0, x1, y1)], de cima para baixo."""
    import pytesseract
    im = Image.open(caminho).convert("RGB")
    lang = "por+eng" if "por" in pytesseract.get_languages() else "eng"
    d = pytesseract.image_to_data(im, lang=lang, output_type=pytesseract.Output.DICT, config="--psm 3")
    linhas = {}
    for i, w in enumerate(d["text"]):
        if not w.strip() or float(d["conf"][i]) < 30: continue
        k = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        x, y, ww, hh = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
        L = linhas.setdefault(k, [[], x, y, x + ww, y + hh])
        L[0].append(w); L[1] = min(L[1], x); L[2] = min(L[2], y); L[3] = max(L[3], x + ww); L[4] = max(L[4], y + hh)
    out = [(" ".join(v[0]), v[1], v[2], v[3], v[4]) for v in linhas.values()]
    return im, sorted(out, key=lambda l: (l[2], l[1]))


def comentarios(linhas, largura, im=None):
    """Agrupa as linhas em comentários: nome na 1ª linha, texto depois; fecha no rodapé ("Há 21h", "Responder")
    ou num buraco grande. O texto de cada comentário é relido ampliado (pega votos de uma letra só, como "B")."""
    blocos, cur = [], []
    for ln in linhas:
        if cur and ln[2] - cur[-1][4] > 90:
            blocos.append(cur); cur = []
        cur.append(ln)
        if RODAPE.search(ln[0]) or FIM_COMENTARIO.match(ln[0].strip()):
            blocos.append(cur); cur = []
    if cur: blocos.append(cur)
    out = []
    for b in blocos:
        rod = [l for l in b if RODAPE.search(l[0]) or FIM_COMENTARIO.match(l[0].strip())]
        corpo = [l for l in b if l not in rod or not FIM_COMENTARIO.match(l[0].strip())]
        corpo = [(RODAPE.split(l[0])[0].strip() if l in rod else l[0], *l[1:]) for l in corpo]
        corpo = [l for l in corpo if l[0] and not RUIDO.match(l[0].strip())]
        if not corpo: continue
        nome = corpo[0][0].strip(); texto = " ".join(l[0] for l in corpo[1:])
        y_fim = (rod[0][2] if rod else max(l[4] for l in b))
        if im is not None and y_fim - corpo[0][4] > 12:
            relido = _reler(im, (int(largura * 0.11), corpo[0][4] + 2, int(largura * 0.86), y_fim - 2))
            if relido and (len(relido) >= len(texto) * 0.6 or len(texto.strip()) <= 3): texto = relido
        texto = SELOS.sub(" ", texto)
        if not texto.strip() and len(corpo) == 1: texto, nome = nome, "?"
        y0 = min(l[2] for l in b); y1 = max(l[4] for l in b)
        out.append(dict(nome=nome, texto=texto.strip(), caixa=(0, max(0, y0 - 24), largura, y1 + 24), x_texto=corpo[0][1]))
    return out


def _reler(im, caixa):
    import pytesseract
    from PIL import ImageOps
    c = ImageOps.autocontrast(im.crop(caixa).convert("L")); c = c.resize((c.width * 2, c.height * 2))
    try: return " ".join(pytesseract.image_to_string(c, lang="por", config="--psm 6").split())
    except Exception: return ""


def voto(texto, ops):
    """'A', 'B', 'duvida' ou None."""
    t = _norm(texto).strip()
    if not t: return None
    achou = set()
    # letra sozinha: "A", "B!", "letra a", "opção B", "vou de A", "(B)", "time A", "A A A"
    if re.fullmatch(r"[\W_]*(?:(?:letra|opcao|vou de|voto|time|equipe|eu escolho|escolho)\s+)?([ab])(?:[\W_]+\1)*[\W_]*(?:[\W_]+.*)?", t) and len(t.split()) <= 6:
        m = re.search(r"(?:^|[^a-z])([ab])(?:[^a-z]|$)", t)
        if m and (len(t.split()) <= 2 or re.search(r"(letra|opcao|vou de|voto|time|escolho)\s+[ab]\b", t)): achou.add(m.group(1).upper())
    for k in ("A", "B"):
        if re.search(rf"\b(letra|opcao|vou de|voto|voto na|voto no|time)\s+{k.lower()}\b", t): achou.add(k)
        if re.search(rf"(^|\s)\(?{k}\)?\s*[!.]*$", texto.strip()) and len(t.split()) <= 3: achou.add(k)
        if any(re.search(rf"\b{re.escape(p)}", t) for p in ops[k][1]): achou.add(k)
    if len(achou) == 1: return achou.pop()
    return "duvida" if len(achou) > 1 else None


def contar(pasta, ep, prints, extra_a=(), extra_b=(), recortar=False):
    ops = opcoes(pasta, ep)
    ops["A"] = (ops["A"][0], ops["A"][1] + [_norm(x) for x in extra_a])
    ops["B"] = (ops["B"][0], ops["B"][1] + [_norm(x) for x in extra_b])
    por_pessoa, todos, imgs = {}, [], []
    for pi, arg in enumerate(prints):
        caminho, _, rede_forcada = arg.partition(":") if not os.path.exists(arg) else (arg, "", "")
        im, linhas = ler(caminho)
        rede = rede_forcada or _rede(caminho, " ".join(l[0] for l in linhas))
        dr = ImageDraw.Draw(im)
        for c in comentarios(linhas, im.width, im.copy()):
            criador = any(k in _norm(c["nome"] + " " + c["texto"]) for k in CRIADOR)
            v = None if criador else voto(c["texto"] or c["nome"], ops)
            c.update(rede=rede, voto=v, print=caminho, criador=criador, idx=pi)
            todos.append(c)
            cor = {"A": (40, 200, 90), "B": (240, 140, 30)}.get(v, (150, 150, 150))
            dr.rectangle(c["caixa"], outline=cor, width=8)
            if v: dr.text((c["caixa"][2] - 120, c["caixa"][1] + 10), v, fill=cor)
            if v in ("A", "B"):
                chave = (_norm(c["nome"]), rede) if c["nome"] != "?" else (f"?{pi}-{len(todos)}", rede)
                por_pessoa[chave] = c
        imgs.append(im)
    votos = {"A": 0, "B": 0}; redes = {}
    for c in por_pessoa.values():
        votos[c["voto"]] += 1; redes[c["rede"]] = redes.get(c["rede"], 0) + 1
    dest = os.path.join(pasta, "placar"); os.makedirs(dest, exist_ok=True)
    # folha de conferência
    if imgs:
        k = 900 / max(i.height for i in imgs)
        th = [i.resize((int(i.width * k), int(i.height * k))) for i in imgs]
        folha = Image.new("RGB", (sum(t.width for t in th) + 20 * (len(th) - 1), 900), (255, 255, 255)); x = 0
        for t in th: folha.paste(t, (x, 0)); x += t.width + 20
        folha.save(os.path.join(dest, f"ep{ep:02d}_conferencia.png"))
    # melhores comentários para o placar: com voto, texto legível, os dois lados se houver
    cand = sorted(por_pessoa.values(), key=lambda c: (-min(len(c["texto"]), 60), c["caixa"][1]))
    escolha = []
    for lado in ("A", "B"):
        escolha += [c for c in cand if c["voto"] == lado][:3 if lado == max(votos, key=votos.get) else 2]
    escolha = escolha[:5]
    comentarios_spec = []
    if recortar:
        for n, c in enumerate(escolha, 1):
            out = os.path.join(dest, f"ep{ep:02d}_c{n}.png")
            x0, y0, x1, y1 = c["caixa"]
            Image.open(c["print"]).convert("RGB").crop((x0, y0, int(x1 * 0.97), y1)).save(out)
            comentarios_spec.append({"img": f"placar/ep{ep:02d}_c{n}.png", "vote": c["voto"]})
    return dict(opcoes={k: v[0] for k, v in ops.items()}, votos=votos, redes=redes, contados=list(por_pessoa.values()),
                todos=todos, recortes=comentarios_spec)


def _cli(a):
    if len(a) < 3 or a[0] != "contar": print(__doc__); sys.exit(1)
    pasta, ep = a[1], int(a[2]); resto = a[3:]
    ea = eb = (); rec = "--recortar" in resto
    if "--a" in resto: ea = resto[resto.index("--a") + 1].split(",")
    if "--b" in resto: eb = resto[resto.index("--b") + 1].split(",")
    prints = [x for i, x in enumerate(resto) if not x.startswith("--") and (i == 0 or resto[i - 1] not in ("--a", "--b"))]
    r = contar(pasta, ep, prints, ea, eb, rec)
    print(f"Opções: A) {r['opcoes']['A']} · B) {r['opcoes']['B']}")
    for c in r["todos"]:
        marca = "criador" if c["criador"] else (c["voto"] or "—")
        print(f"  [{marca:>7}] {c['rede']:<9} {c['nome'][:22]:<22} | {c['texto'][:60]}")
    tot = sum(r["votos"].values())
    print(f"\nVOTOS: A {r['votos']['A']} × B {r['votos']['B']}" + (f"  ({round(100 * r['votos']['A'] / tot)}% × {round(100 * r['votos']['B'] / tot)}%)" if tot else ""))
    print("Por rede:", ", ".join(f"{k} {v}" for k, v in r["redes"].items()) or "—")
    if tot and r["votos"]["A"] == r["votos"]["B"]: print("EMPATE: o placar mostra a roleta; ela para na opção registrada na bíblia.")
    print(f"Conferência: {os.path.join(pasta, 'placar', f'ep{ep:02d}_conferencia.png')} (verde = A, laranja = B, cinza = não contou)")
    winner = max(r["votos"], key=r["votos"].get) if tot and r["votos"]["A"] != r["votos"]["B"] else "?"
    shot = {"type": "placar", "labels": {k: v.upper() for k, v in r["opcoes"].items()}, "votes": r["votos"],
            "platforms": r["redes"], "comments": r["recortes"], "winner": winner}
    print("\nPlano para o epNN.json (confira o winner com a bíblia):\n" + json.dumps(shot, ensure_ascii=False))


if __name__ == "__main__":
    _cli(sys.argv[1:])
