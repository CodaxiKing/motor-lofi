"""Planejamento narrativo, ganchos, experimentos, validador narrativo e a trava do ep. 1 de O Último Estoque.

Tudo determinístico: nenhum teste depende de avaliação subjetiva de IA nem de rede.
"""
import copy, hashlib, json, os, shutil
import pytest
from lofi import narrativa as N, ganchos as G, experimentos as X, validador_narrativo as V, protecao

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OST = os.path.join(RAIZ, "series", "o-ultimo-estoque")
RZ = os.path.join(RAIZ, "series", "rank-zero")
EP1_SHA = {   # conteúdo do ep. 1 travado em nov/2026 (mesmos bytes de antes da tarefa; hash com LF)
    "ep01.json": "76abad3b93785e5779e5f80ead065041ee244f1316ec7264c107e464f95e8caa",
    "ep01_roteiro.md": "65e85d09e5d370993519d1073b6dd6f50347675081436e9912f3b7fa7ab27ccf",
    "extra01.json": "a2bac419385554e6c902ffdffa203898436bbbc3994f7d3e000ebcd1f293b9a7",
    "extra01_roteiro.md": "13b822836d28b5c64bfa5cc8e230766455238e3256352babfd12b1335d9c5fc2",
}


def _sha(p): return protecao.sha256(p)           # quebras de linha normalizadas (Windows = CI)


def _serie(tmp_path, nome="s"):
    """Cópia de O Último Estoque sem a trava (para testar escrita), com plano do ep. 2."""
    d = tmp_path / nome; d.mkdir()
    for f in ("memoria.json", "mundo.json", "personagens.json", "biblia.md"): shutil.copy(os.path.join(OST, f), d / f)
    (d / "planos").mkdir(); shutil.copy(os.path.join(OST, "planos", "ep02.json"), d / "planos" / "ep02.json")
    return d


# ---------------- 16. ep. 1 de O Último Estoque intacto ----------------
def test_ep1_o_ultimo_estoque_identico():
    for nome, h in EP1_SHA.items(): assert _sha(os.path.join(OST, nome)) == h, f"{nome} mudou"
    assert protecao.conferir(OST) == []


def test_trava_recusa_gravar_no_ep1():
    with pytest.raises(protecao.Protegido): protecao.bloquear(os.path.join(OST, "ep01.json"))
    with pytest.raises(protecao.Protegido): protecao.bloquear(os.path.join(OST, "ep01_roteiro.md"))
    bib = open(os.path.join(OST, "biblia.md"), encoding="utf-8").read()
    linha_ep1 = next(l for l in bib.split("\n") if l.startswith("- EP 1: 18:50"))
    with pytest.raises(protecao.Protegido): protecao.bloquear(os.path.join(OST, "biblia.md"), bib.replace(linha_ep1, linha_ep1 + " (editado)"))
    protecao.bloquear(os.path.join(OST, "biblia.md"), bib)          # mudar outras linhas da bíblia é permitido


def test_literal_aplicar_respeita_a_trava(tmp_path):
    from lofi import literal
    with pytest.raises(protecao.Protegido): literal.aplicar(os.path.join(OST, "ep01.json"), os.path.join(OST, "ep01.json"))


# ---------------- 1–5. ganchos ----------------
def test_tres_ganchos_distintos_e_compativeis():
    plano = N.carregar_plano(os.path.join(OST, "planos", "ep02.json"))
    cands = G.gerar(plano, OST)
    assert [c["id"] for c in cands] == ["A", "B", "C"]
    assert len({c["estrategia"] for c in cands}) == 3                     # estratégias diferentes
    assert len({c["texto"] for c in cands}) == 3
    for c in cands:
        assert c["estrategia"] in G.ESTRATEGIAS
        assert G.compativel(c, plano)                                     # de uma cena comum aos dois caminhos
        assert 0 < c["duracao_s"] <= G.MAX_S                              # cabe nos primeiros 5 s
        assert c["explicacao"] and set(c["notas"]) == {"clareza", "relevancia", "originalidade", "continuidade", "duracao"}
        assert "você" not in c["texto"].lower() or "?" not in c["texto"]   # a pergunta final não vira gancho


def test_gancho_nao_entrega_o_que_o_episodio_revela():
    plano = N.carregar_plano(os.path.join(OST, "planos", "ep02.json"))
    for c in G.gerar(plano, OST): assert "é o sérgio" not in c["texto"].lower()


def test_duracao_estimada():
    assert G.duracao("As batidas vêm de dentro.") == pytest.approx(5 / G.WPS + 0.4, abs=0.01)
    assert G.duracao("um dois três / quatro") > G.duracao("um dois três quatro")


def test_generico_e_pronome_solto_perdem_nota():
    bom, _, _ = G.avaliar("O portal fecha com a Vega do lado de fora")
    ruim, n, exp = G.avaliar("Você não vai acreditar no que aconteceu")
    assert n["originalidade"] == 0 and ruim < bom
    _, n2, _ = G.avaliar("Ela esconde a mão")
    assert n2["clareza"] < 1


def test_escolha_integra_so_o_gancho(tmp_path):
    d = _serie(tmp_path); plano_p = str(d / "planos" / "ep02.json")
    G.gerar_arquivo(plano_p)
    md = (open(os.path.join(OST, "ep01_roteiro.md"), encoding="utf-8").read())   # formato real de roteiro como base
    (d / "ep02_roteiro.md").write_text(md, encoding="utf-8")
    antes_plano = N.carregar_plano(plano_p)
    r = G.escolher(plano_p, "B")
    depois_plano = N.carregar_plano(plano_p)
    assert r["escolhido"] == "B" and depois_plano["gancho"]["id"] == "B"
    assert {k: v for k, v in depois_plano.items() if k != "gancho"} == {k: v for k, v in antes_plano.items() if k != "gancho"}
    novo = (d / "ep02_roteiro.md").read_text(encoding="utf-8").split("\n"); velho = md.split("\n")
    assert len(novo) == len(velho)
    mudou = [i for i, (a, b) in enumerate(zip(velho, novo)) if a != b]
    assert mudou and all(velho[i].startswith(("FALA DO GANCHO:", "TEXTO:", "ESCOLHIDO:")) for i in mudou)


def test_regenerar_nao_repete_e_guarda_historico(tmp_path):
    d = _serie(tmp_path); p = str(d / "planos" / "ep02.json")
    a = G.gerar_arquivo(p); b = G.gerar_arquivo(p, regenerar=True)
    assert not {c["texto"] for c in a["candidatos"]} & {c["texto"] for c in b["candidatos"]}
    assert b["historico"] and N.carregar_plano(p) == N.carregar_plano(os.path.join(OST, "planos", "ep02.json"))   # o episódio não mudou


# ---------------- 6–10. experimentos e aprendizado ----------------
def _exp(tmp_path):
    d = tmp_path / "exp"; d.mkdir()
    cands = [{"id": "A", "estrategia": "antecipacao", "texto": "faltam dez minutos", "duracao_s": 1.9},
             {"id": "B", "estrategia": "incongruencia", "texto": "não é o ritmo deles", "duracao_s": 2.5}]
    X.registrar_variantes(str(d), 2, cands, "A", "teste")
    return str(d)


def test_registro_de_experimento_e_metricas(tmp_path):
    d = _exp(tmp_path)
    pa = X.publicar(d, 2, "A", "tiktok", "2026-11-10", duracao_video_s=220)
    m = X.registrar_metricas(d, pa, {"visualizacoes": "12.400", "retencao_3s": "61,5%", "comentarios": ""}, "2026-11-13")
    assert m["visualizacoes"] == 12400 and m["retencao_3s"] == pytest.approx(0.615)
    assert m["comentarios"] is None and m["replays"] is None             # ausente fica null, nunca zero
    assert m["horas_desde_publicacao"] == 72
    with pytest.raises(ValueError): X.registrar_metricas(d, pa, {"curtidas_inventadas": 3})
    with pytest.raises(ValueError): X.publicar(d, 2, "Z", "tiktok", "2026-11-10")


def test_importacao_csv(tmp_path):
    d = _exp(tmp_path); X.publicar(d, 2, "B", "instagram", "2026-11-10", pub_id="ig-b")
    csvp = tmp_path / "m.csv"
    csvp.write_text("publicacao,coletado_em,visualizacoes,retencao_3s,conclusao\nig-b,2026-11-12,900,0.5,-\n", encoding="utf-8")
    assert X.importar(d, str(csvp)) == 1
    m = X.carregar(d)["experimentos"][0]["publicacoes"][0]["metricas"][0]
    assert m["conclusao"] is None and m["retencao_3s"] == 0.5


def test_comparacao_com_dados_insuficientes(tmp_path):
    d = _exp(tmp_path)
    a = X.publicar(d, 2, "A", "tiktok", "2026-11-10"); b = X.publicar(d, 2, "B", "tiktok", "2026-11-10")
    X.registrar_metricas(d, a, {"visualizacoes": 300, "retencao_3s": 0.7}, "2026-11-11")
    X.registrar_metricas(d, b, {"visualizacoes": 280, "retencao_3s": 0.4}, "2026-11-11")
    c = X.comparar(d, 2)
    assert c["veredito"] == "inconclusivo"
    motivos = " ".join(c["grupos"][0]["motivos"])
    assert "amostra pequena" in motivos and "cedo" in motivos


def test_comparacao_nao_mistura_plataformas_e_metrica_ausente(tmp_path):
    d = _exp(tmp_path)
    a = X.publicar(d, 2, "A", "tiktok", "2026-11-10"); b = X.publicar(d, 2, "B", "youtube", "2026-11-10")
    X.registrar_metricas(d, a, {"visualizacoes": 50000, "retencao_3s": 0.7}, "2026-11-15")
    X.registrar_metricas(d, b, {"visualizacoes": 50000, "retencao_3s": 0.3}, "2026-11-15")
    assert X.comparar(d, 2)["veredito"] == "inconclusivo"                # cada rede sozinha tem uma variante só


def test_diferenca_observada_e_recomendacao(tmp_path):
    d = _exp(tmp_path)
    a = X.publicar(d, 2, "A", "tiktok", "2026-11-10"); b = X.publicar(d, 2, "B", "tiktok", "2026-11-10")
    X.registrar_metricas(d, a, {"visualizacoes": 20000, "retencao_3s": 0.62}, "2026-11-14")
    X.registrar_metricas(d, b, {"visualizacoes": 20000, "retencao_3s": 0.55}, "2026-11-14")
    c = X.comparar(d, 2)
    g = c["grupos"][0]
    assert g["veredito"] == "diferenca_observada" and g["melhor"] == "A" and g["teste"]["p"] < 0.05
    assert any("não prova" in m for m in g["motivos"])
    r = X.recomendar(d)
    assert r["evidencia"] == "parcial" and r["por_estrategia"]["antecipacao"]["vitorias"] == 1
    assert X.evidencia_por_estrategia(d)
    dados = X.carregar(d); dados["recomendacoes"] = False; X.salvar(d, dados)   # desligável
    assert X.evidencia_por_estrategia(d) == {}


def test_sem_dados_usa_criterios_narrativos(tmp_path):
    r = X.recomendar(_exp(tmp_path))
    assert r["evidencia"] == "insuficiente" and any("critérios narrativos" in o for o in r["observacoes"])


# ---------------- 11–15. continuidade e validador ----------------
def _plano_base():
    return copy.deepcopy(N.carregar_plano(os.path.join(OST, "planos", "ep02.json")))


def _val(plano):
    _, mem, mundo, pers = N.contexto(os.path.join(OST, "planos", "ep02.json"))
    return {p[1] for p in N.validar_plano(plano, mem, mundo, pers)}


def test_planos_das_series_validos_em_cadeia():
    for pasta in (OST, RZ):
        res = N.validar_serie(pasta)
        assert res and all(not [p for p in v if p[0] == "ERRO"] for v in res.values()), res


def test_continuidade_espacial_e_temporal():
    p = _plano_base(); c = next(c for c in p["cadeia"] if c["n"] == 7)
    c["lugar"] = "delegacia"; c["transicao"] = {"tipo": "continuacao"}
    assert "salto_de_lugar" in _val(p)
    p = _plano_base(); c = next(c for c in p["cadeia"] if c["n"] == 9); c["hora"] = "20:00"
    assert "tempo_volta" in _val(p)
    p = _plano_base(); c = next(c for c in p["cadeia"] if c["n"] == 3); c["transicao"] = {"tipo": "continuacao"}; c["hora"] = "22:58"
    for x in p["cadeia"]:
        if x["n"] in (4, 5): x["hora"] = "23:00"
    assert "salto_de_tempo" in _val(p)


def test_contradicoes_entre_episodios_e_informacao_indevida():
    p = _plano_base(); p["estado_inicial"]["por_voto"].pop("A")
    assert "voto_ignorado" in _val(p)                                    # o ep. 1 terminou com A/B
    p = _plano_base(); c = next(c for c in p["cadeia"] if c["n"] == 9); c["narracao"].append("É uma gravação.")
    assert "informacao_indevida" in _val(p)                              # o canal A só é revelado no ep. 4
    p = _plano_base(); c = next(c for c in p["cadeia"] if c["n"] == 8); c["usa"] = {"leo": ["lanterna"]}
    assert "objeto_sumido" in _val(p)
    p = _plano_base(); _, _, mundo, pers = N.contexto(os.path.join(OST, "planos", "ep02.json"))
    mem = {"fatos": [], "fim": {}, "pendencias": [{"id": "x", "texto": "a promessa do ep. 1", "ate_ep": 2, "palavras": ["unicórnio"]}]}
    assert "consequencia_ignorada" in {q[1] for q in N.validar_plano(p, mem, mundo, pers)}


def test_compatibilidade_com_roteiros_existentes():
    for f in ("o-ultimo-estoque/ep01_roteiro.md", "apagao/ep01_roteiro.md", "sinal-de-vida/ep01_roteiro.md", "dia-zero/ep05_roteiro.md"):
        assert not [p for p in V.validar_roteiro(os.path.join(RAIZ, "series", f)) if p[0] == "ERRO"], f
    assert not [p for p in V.validar_json(os.path.join(OST, "ep01.json")) if p[0] == "ERRO"]


ROTEIRO_RUIM = """# TESTE · EPISÓDIO 2/5

## CENA 0 · GANCHO (0–3 s)
FALA DO GANCHO: `narrador` "O vidro explode." (a mesma da CENA 1)
TEXTO: O VIDRO / EXPLODE

---

## CENA 1 — 3 s a 10 s · Mercado
CENÁRIO: `mercado` · DIA 0 · 19:20
NARRAÇÃO: Você anda. / O corredor está vazio.

## CENA 2 — 10 s a 20 s · Vidro
CENÁRIO: `mercado` · DIA 0 · 19:22
NARRAÇÃO: O vidro *explode*. / Laranjas rolam.

## CENA 3 — 20 s a 30 s · Rua
CENÁRIO: `rua` · DIA 0 · 19:25
NARRAÇÃO: Lá fora, a rua.

## CENA 4 — 30 s a 40 s · Posto
CENÁRIO: `delegacia` · DIA 0 · 23:50
NARRAÇÃO: O portão leste. É uma gravação, sempre a mesma, há horas e horas e horas sem parar nunca mais.
"""


def test_deteccao_e_correcao_localizada(tmp_path):
    d = _serie(tmp_path, "r"); p = d / "ep02_roteiro.md"; p.write_text(ROTEIRO_RUIM, encoding="utf-8")
    cods = {x[1] for x in V.validar_roteiro(str(p))}
    assert {"gancho_desconectado", "transicao_sem_contexto", "informacao_indevida", "exposicao", "salto_de_tempo"} <= cods
    antes = ROTEIRO_RUIM.split("\n")
    r = V.corrigir(str(p))
    restantes = {x[1] for x in r["restantes"]}
    assert "gancho_desconectado" not in restantes and "transicao_sem_contexto" not in restantes and "salto_de_tempo" not in restantes
    assert "informacao_indevida" in restantes                            # sem conserto mecânico: fica para o autor
    assert 1 <= r["rodadas"] <= 3
    depois = p.read_text(encoding="utf-8").split("\n")
    inseridas = [l for l in depois if l not in antes]
    assert all(l.startswith(("LIGAÇÃO:", "O TEMPO PASSA", "FALA DO GANCHO:")) for l in inseridas)
    assert [l for l in antes if l not in depois] == [antes[3]]          # só a linha do gancho foi reescrita


def test_correcao_nao_grava_em_arquivo_travado():
    with pytest.raises(protecao.Protegido): V.corrigir(os.path.join(OST, "ep01_roteiro.md"))


def test_esqueleto_do_roteiro_passa_no_validador(tmp_path):
    d = _serie(tmp_path, "e"); plano = N.carregar_plano(str(d / "planos" / "ep02.json"))
    for voto in ("A", "B"):
        md = N.esqueleto(plano, voto); p = d / f"ep02_roteiro.md"; p.write_text(md, encoding="utf-8")
        assert "CENA 0 · GANCHO" in md and plano["gancho"]["texto"] in md
        erros = [x for x in V.validar_roteiro(str(p)) if x[0] == "ERRO"]
        assert not erros, erros


def test_fechar_leva_estado_e_fatos_adiante():
    plano = _plano_base(); _, mem, _, _ = N.contexto(os.path.join(OST, "planos", "ep02.json"))
    m = N.fechar(plano, mem, "A")
    assert m["fim"]["2"]["hora"] == "22:52" and m["fim"]["2"]["pergunta"] == plano["pergunta"]
    assert next(f for f in m["fatos"] if f["id"] == "frio_lentos")["publico_sabe"] is True
    assert not any(p["id"] == "portao_22h" for p in m["pendencias"])
    assert mem != m                                                      # não altera a memória original
