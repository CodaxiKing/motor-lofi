"""Experimentos de gancho: variantes de abertura, publicações, métricas reais e comparação justa.

Não há integração oficial com TikTok/Instagram/YouTube no motor (só os prints de comentários do lofi.votos), então as
métricas entram por importação manual (CSV ou JSON exportado do painel de cada rede). Nada é coletado por raspagem,
nada é publicado e nenhum valor ausente é inventado: métrica que a rede não deu fica null.

Arquivo da série: series/<serie>/experimentos.json
{
  "recomendacoes": true,                         # false desliga as recomendações baseadas em métricas
  "experimentos": [{
    "episodio": 2, "variantes": [{"id": "A", "estrategia": "antecipacao", "texto": "...", "duracao_s": 3.1}, ...],
    "selecionada": "B", "criterio": "...", "registrado_em": "...",
    "publicacoes": [{"id": "tt-ep02-b", "variante": "B", "plataforma": "tiktok", "publicado_em": "2026-11-10",
                     "duracao_video_s": 222, "mudancas": ["capa nova"], "metricas": [{"coletado_em": "2026-11-12",
                     "horas_desde_publicacao": 48, "visualizacoes": 5400, "tempo_medio_s": 41.0, "retencao_3s": 0.62,
                     "retencao_5s": 0.48, "conclusao": 0.12, "replays": null, "compartilhamentos": 31, "comentarios": 120,
                     "seguidores": 44, "fonte": "manual"}]}]
  }]
}

    python3 -m lofi.experimentos publicar  series/x 2 B tiktok 2026-11-10 --id tt-ep02-b --duracao 222
    python3 -m lofi.experimentos importar  series/x metricas.csv      (colunas: publicacao, coletado_em, horas_desde_publicacao, visualizacoes, ...)
    python3 -m lofi.experimentos comparar  series/x 2
    python3 -m lofi.experimentos recomendar series/x                   (ou series/ para todas as séries)
"""
import csv, datetime, json, math, os, re, sys

METRICAS = ("visualizacoes", "tempo_medio_s", "retencao_inicial", "retencao_3s", "retencao_5s", "conclusao", "replays",
            "compartilhamentos", "comentarios", "seguidores")
PROPORCOES = ("retencao_inicial", "retencao_3s", "retencao_5s", "conclusao")
PLATAFORMAS = ("tiktok", "instagram", "youtube", "kwai", "outra")
MIN_VIEWS = 1000          # abaixo disso a proporção é ruidosa demais para comparar
MIN_HORAS = 48            # métricas de vídeo novo ainda mudam muito
ALFA = 0.05


def _p(pasta): return os.path.join(pasta, "experimentos.json")


def carregar(pasta):
    p = _p(pasta)
    d = json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else {}
    d.setdefault("recomendacoes", True); d.setdefault("experimentos", [])
    return d


def salvar(pasta, d):
    from .protecao import bloquear
    bloquear(_p(pasta))
    json.dump(d, open(_p(pasta), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)


def _agora(): return datetime.datetime.now().replace(microsecond=0).isoformat()


def _exp(d, ep):
    e = next((x for x in d["experimentos"] if x["episodio"] == int(ep)), None)
    if e is None:
        e = {"episodio": int(ep), "variantes": [], "selecionada": None, "publicacoes": []}; d["experimentos"].append(e)
    return e


# ---------------- registro ----------------
def registrar_variantes(pasta, ep, candidatos, selecionada, criterio=""):
    """Guarda as alternativas geradas e qual entrou no roteiro. Re-registrar preserva as publicações e o histórico."""
    d = carregar(pasta); e = _exp(d, ep)
    if e["variantes"] and [v["texto"] for v in e["variantes"]] != [c["texto"] for c in candidatos]:
        e.setdefault("historico", []).append({"variantes": e["variantes"], "selecionada": e["selecionada"], "ate": _agora()})
    e["variantes"] = [{"id": c["id"], "estrategia": c["estrategia"], "texto": c["texto"], "duracao_s": c.get("duracao_s")} for c in candidatos]
    e["selecionada"] = selecionada; e["criterio"] = criterio; e["registrado_em"] = _agora()
    salvar(pasta, d); return e


def publicar(pasta, ep, variante, plataforma, publicado_em, pub_id=None, duracao_video_s=None, mudancas=(), url=None):
    """Vincula uma publicação (feita pelo autor, fora do motor) à variante usada. Não publica nada."""
    if plataforma not in PLATAFORMAS: raise ValueError(f"plataforma '{plataforma}' (use {', '.join(PLATAFORMAS)})")
    datetime.date.fromisoformat(publicado_em)
    d = carregar(pasta); e = _exp(d, ep)
    if e["variantes"] and variante not in [v["id"] for v in e["variantes"]]: raise ValueError(f"variante {variante} não existe no ep. {ep}")
    pub_id = pub_id or f"{plataforma}-ep{int(ep):02d}-{variante.lower()}-{publicado_em}"
    if any(p["id"] == pub_id for x in d["experimentos"] for p in x["publicacoes"]): raise ValueError(f"publicação '{pub_id}' já existe")
    e["publicacoes"].append({"id": pub_id, "variante": variante, "plataforma": plataforma, "publicado_em": publicado_em,
                             "duracao_video_s": duracao_video_s, "mudancas": list(mudancas), "url": url, "metricas": []})
    salvar(pasta, d); return pub_id


def _num(v, nome):
    """Converte um valor do painel. Vazio/'-'/'n/d' = None (ausente, nunca zero). Proporções aceitam 0–1 ou 0–100%."""
    if v is None: return None
    if isinstance(v, (int, float)): x = float(v)
    else:
        s = str(v).strip().lower().replace("%", "").replace(" ", "")
        if s in ("", "-", "n/d", "nd", "na", "null", "none", "—"): return None
        if "," in s and "." in s: s = s.replace(".", "").replace(",", ".")
        elif "," in s: s = s.replace(",", ".")
        elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s) and nome not in PROPORCOES: s = s.replace(".", "")   # 12.400 = doze mil e quatrocentos
        x = float(s)
    if x < 0: raise ValueError(f"{nome} negativo")
    if nome in PROPORCOES:
        if x > 1: x = x / 100.0
        if x > 1: raise ValueError(f"{nome} acima de 100%")
    return x


def registrar_metricas(pasta, pub_id, valores, coletado_em=None, horas=None, fonte="manual"):
    d = carregar(pasta)
    pub = next((p for e in d["experimentos"] for p in e["publicacoes"] if p["id"] == pub_id), None)
    if pub is None: raise KeyError(f"publicação '{pub_id}' não registrada (use 'publicar' antes)")
    desconhecidas = set(valores) - set(METRICAS)
    if desconhecidas: raise ValueError(f"métricas desconhecidas: {', '.join(sorted(desconhecidas))}")
    m = {k: _num(valores.get(k), k) for k in METRICAS}
    if m["visualizacoes"] is not None: m["visualizacoes"] = int(m["visualizacoes"])
    coletado_em = coletado_em or datetime.date.today().isoformat()
    if horas is None:
        try: horas = (datetime.date.fromisoformat(coletado_em[:10]) - datetime.date.fromisoformat(pub["publicado_em"])).days * 24
        except ValueError: horas = None
    m.update({"coletado_em": coletado_em, "horas_desde_publicacao": horas, "fonte": fonte})
    pub["metricas"].append(m); salvar(pasta, d); return m


def importar(pasta, arquivo):
    """CSV ou JSON (lista de linhas) com a coluna 'publicacao' + métricas. Devolve quantas linhas entraram."""
    if arquivo.lower().endswith(".json"): linhas = json.load(open(arquivo, encoding="utf-8"))
    else: linhas = list(csv.DictReader(open(arquivo, encoding="utf-8-sig")))
    n = 0
    for l in linhas:
        l = dict(l); pid = l.pop("publicacao"); col = l.pop("coletado_em", None); hr = l.pop("horas_desde_publicacao", None)
        fonte = l.pop("fonte", "manual") or "manual"
        hr = _num(hr, "horas") if hr not in (None, "") else None
        registrar_metricas(pasta, pid, {k: v for k, v in l.items() if k in METRICAS or v not in (None, "")}, col, hr, fonte); n += 1
    return n


# ---------------- comparação ----------------
def _ultima(pub):
    return pub["metricas"][-1] if pub["metricas"] else None


def _z2(p1, n1, p2, n2):
    """Teste z de duas proporções (bilateral). Devolve (z, p)."""
    p = (p1 * n1 + p2 * n2) / (n1 + n2); se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0: return 0.0, 1.0
    z = (p1 - p2) / se
    return z, math.erfc(abs(z) / math.sqrt(2))


def comparar(pasta, ep, metrica="retencao_3s"):
    """Compara as variantes do ep. por plataforma. Só declara diferença com amostra e tempo suficientes, e sempre como
    associação observada (não causa). Devolve dict com 'veredito' e 'ressalvas'."""
    d = carregar(pasta); e = next((x for x in d["experimentos"] if x["episodio"] == int(ep)), None)
    if not e: return {"episodio": ep, "veredito": "sem_dados", "ressalvas": ["nenhum experimento registrado"], "grupos": []}
    out = {"episodio": int(ep), "metrica": metrica, "grupos": [], "ressalvas": []}
    vereditos = []
    for plat in sorted({p["plataforma"] for p in e["publicacoes"]}):
        pubs = [p for p in e["publicacoes"] if p["plataforma"] == plat and _ultima(p)]
        linhas = []
        for p in pubs:
            m = _ultima(p)
            linhas.append({"publicacao": p["id"], "variante": p["variante"], "valor": m.get(metrica), "n": m.get("visualizacoes"),
                           "horas": m.get("horas_desde_publicacao"), "publicado_em": p["publicado_em"], "duracao_video_s": p.get("duracao_video_s"),
                           "mudancas": p.get("mudancas", [])})
        g = {"plataforma": plat, "linhas": linhas, "veredito": "inconclusivo", "motivos": []}
        vs = {l["variante"] for l in linhas}
        validas = [l for l in linhas if l["valor"] is not None and l["n"]]
        if len(vs) < 2: g["motivos"].append("só uma variante publicada nesta plataforma: não há com o que comparar")
        elif len({l["variante"] for l in validas}) < 2: g["motivos"].append(f"'{metrica}' ausente em pelo menos uma variante (a rede não informou)")
        else:
            poucas = [l for l in validas if l["n"] < MIN_VIEWS]; cedo = [l for l in validas if l["horas"] is not None and l["horas"] < MIN_HORAS]
            if poucas: g["motivos"].append(f"amostra pequena ({', '.join(str(l['n']) for l in poucas)} visualizações; mínimo {MIN_VIEWS})")
            if cedo: g["motivos"].append(f"coletado cedo demais ({', '.join(str(l['horas']) for l in cedo)} h; mínimo {MIN_HORAS} h)")
            if len({l['duracao_video_s'] for l in validas}) > 1: g["motivos"].append("durações de vídeo diferentes entre as publicações")
            if any(l["mudancas"] for l in validas): g["motivos"].append("houve outras mudanças além do gancho: " + "; ".join(sorted({m for l in validas for m in l['mudancas']})))
            if len({l['publicado_em'] for l in validas}) > 1: g["motivos"].append("publicadas em datas diferentes (audiência e alcance mudam)")
            if not poucas and not cedo and metrica in PROPORCOES:
                melhor = max(validas, key=lambda l: l["valor"]); pior = min(validas, key=lambda l: l["valor"])
                z, p = _z2(melhor["valor"], melhor["n"], pior["valor"], pior["n"])
                g["teste"] = {"z": round(z, 2), "p": round(p, 4), "entre": [melhor["variante"], pior["variante"]]}
                if p < ALFA and melhor["variante"] != pior["variante"]:
                    g["veredito"] = "diferenca_observada"; g["melhor"] = melhor["variante"]
                    g["motivos"].append(f"diferença de {metrica} com p={p:.4f}: associação observada, não prova que o gancho causou")
                else: g["motivos"].append(f"diferença dentro do ruído (p={p:.2f})")
            elif metrica not in PROPORCOES and not poucas and not cedo:
                g["motivos"].append(f"'{metrica}' não é proporção: sem teste estatístico, só descrição")
        vereditos.append(g["veredito"]); out["grupos"].append(g)
    out["veredito"] = "diferenca_observada" if "diferenca_observada" in vereditos else ("inconclusivo" if vereditos else "sem_dados")
    if not vereditos: out["ressalvas"].append("nenhuma publicação com métricas")
    out["ressalvas"].append("comparação por plataforma; resultados de redes diferentes nunca se misturam")
    return out


# ---------------- aprendizado ----------------
def _series(pasta):
    if os.path.isfile(_p(pasta)) or os.path.isfile(os.path.join(pasta, "biblia.md")): return [pasta]
    return [os.path.join(pasta, x) for x in sorted(os.listdir(pasta)) if os.path.isdir(os.path.join(pasta, x))]


def _genero(pasta):
    p = os.path.join(pasta, "biblia.md")
    if not os.path.isfile(p): return None
    l = open(p, encoding="utf-8").read().split("\n")[1:2]
    return l[0].split("·")[1].strip() if l and "·" in l[0] else None


def recomendar(pasta, metrica="retencao_3s"):
    """Tendências só com dados reais. Sem evidência, diz que não há e devolve os critérios narrativos."""
    resultado = {"metrica": metrica, "evidencia": "insuficiente", "por_estrategia": {}, "inconclusivos": [], "repeticao": [],
                 "duracao": None, "observacoes": []}
    pontos = []
    for s in _series(pasta):
        d = carregar(s)
        if not d.get("recomendacoes", True):
            resultado["observacoes"].append(f"{os.path.basename(s)}: recomendações por métrica desligadas"); continue
        gen = _genero(s)
        sel = [x.get("selecionada") and next((v["estrategia"] for v in x["variantes"] if v["id"] == x["selecionada"]), None) for x in sorted(d["experimentos"], key=lambda x: x["episodio"])]
        for i in range(2, len(sel)):
            if sel[i] and sel[i] == sel[i - 1] == sel[i - 2]: resultado["repeticao"].append(f"{os.path.basename(s)}: '{sel[i]}' abriu 3 episódios seguidos")
        for e in d["experimentos"]:
            c = comparar(s, e["episodio"], metrica); est = {v["id"]: v for v in e["variantes"]}
            for g in c["grupos"]:
                if g["veredito"] == "diferenca_observada":
                    v = est.get(g["melhor"], {}); k = v.get("estrategia")
                    r = resultado["por_estrategia"].setdefault(k, {"vitorias": 0, "casos": []})
                    r["vitorias"] += 1; r["casos"].append(f"{os.path.basename(s)} ep. {e['episodio']} · {g['plataforma']} · p={g['teste']['p']}" + (f" · {gen}" if gen else ""))
                elif g["linhas"]:
                    resultado["inconclusivos"].append(f"{os.path.basename(s)} ep. {e['episodio']} · {g['plataforma']}: " + "; ".join(g["motivos"][:2]))
                for l in g["linhas"]:
                    vv = est.get(l["variante"], {})
                    if l["valor"] is not None and vv.get("duracao_s") and l["n"] and l["n"] >= MIN_VIEWS: pontos.append((vv["duracao_s"], l["valor"]))
    if resultado["por_estrategia"]: resultado["evidencia"] = "parcial"
    if len(pontos) >= 8:
        xs, ys = zip(*pontos); mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        cov = sum((x - mx) * (y - my) for x, y in pontos); vx = sum((x - mx) ** 2 for x in xs); vy = sum((y - my) ** 2 for y in ys)
        r = cov / math.sqrt(vx * vy) if vx and vy else 0
        resultado["duracao"] = f"correlação de Pearson entre duração do gancho e {metrica}: r={r:.2f} em {len(pontos)} publicações (descritivo)"
    else:
        resultado["duracao"] = f"poucos pontos ({len(pontos)}) para relacionar duração do gancho e {metrica} (mínimo 8)"
    if resultado["evidencia"] == "insuficiente":
        resultado["observacoes"].append("ainda não existe evidência empírica: a escolha usa só critérios narrativos (clareza, relevância, originalidade, continuidade)")
    resultado["observacoes"].append("nenhuma estratégia garante alcance; diferenças observadas são associações, não causa")
    return resultado


def evidencia_por_estrategia(pasta):
    """{estrategia: "texto da evidência"} para o bônus pequeno do lofi.ganchos (vazio sem dados ou com recomendações desligadas)."""
    if not carregar(pasta).get("recomendacoes", True): return {}
    r = recomendar(pasta)
    return {k: f"{v['vitorias']} resultado(s) com diferença observada: {v['casos'][0]}" for k, v in r["por_estrategia"].items() if k}


if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    a = sys.argv[1:]; cmd = a[0]
    def opt(n, d=None): return a[a.index(n) + 1] if n in a else d
    if cmd == "publicar":
        print(publicar(a[1], int(a[2]), a[3], a[4], a[5], opt("--id"), float(opt("--duracao")) if opt("--duracao") else None,
                       [x for x in (opt("--mudancas") or "").split(";") if x], opt("--url")))
    elif cmd == "importar": print(f"{importar(a[1], a[2])} linha(s) importada(s)")
    elif cmd == "comparar": print(json.dumps(comparar(a[1], int(a[2]), opt("--metrica", "retencao_3s")), ensure_ascii=False, indent=1))
    elif cmd == "recomendar": print(json.dumps(recomendar(a[1], opt("--metrica", "retencao_3s")), ensure_ascii=False, indent=1))
