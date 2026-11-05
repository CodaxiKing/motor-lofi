import copy, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lofi import movimento, pronuncia, retencao, ritmo


def test_ritmo_estima_voz_e_avisa_audio_curto():
    txt = "## CENA 1 — 0 s a 30 s · A\nNARRAÇÃO (Lucas): [quiet] Uma frase curta.\n## CENA 2 — 30 s a 32 s · B\nNARRAÇÃO (Lucas): [quiet] " + "palavra " * 20 + "\n"
    r = ritmo.analisar(txt); assert r["planejado"] == 32 and r["ocupacao"] < ritmo.MIN_OCUPACAO
    av = ritmo.conferir(txt); assert any("curto" in a for a in av) and any("cena 2" in a for a in av)
    assert ritmo.segundos_fala("[x] Sim... [long pause] não.") > 2 / ritmo.PADRAO + 1.5


def test_pronuncia_aponta_numero_trocado():
    falas = ["[quiet] O relógio parou às três e dezessete.", "[quiet] Minha irmã sumiu."]
    res = pronuncia.comparar(falas, [{"s": 1.0, "e": 3.0, "t": "O relógio parou às 13h17."}, {"s": 4.0, "e": 5.0, "t": "Minha irmã sumiu."}])
    assert len(res) == 1 and res[0]["problemas"][0]["alta"]
    assert pronuncia.comparar(falas[1:], [{"s": 0, "e": 1, "t": "minha irmã sumiu"}]) == []


def _sp(a, d=6, **k):
    return dict({"shots": [{"start": 0, "end": d, "scene": "entrada", "actors": [a]}], "clips": []}, **k)


def test_movimento():
    assert any("parado" in m for _, m in movimento.analisar(_sp({"char": "lucas", "mark": "porta"})))
    assert any("deslizar" in m for _, m in movimento.analisar(_sp({"char": "lucas", "mark": [[0, "porta"], [2, "lado_esq"]], "emotion": [[0, "fear"], [1, "sad"]]})))
    assert not movimento.analisar(_sp({"char": "lucas", "mark": [[0, "porta"], [2, "lado_esq"]], "walk": True}))
    sp = {"clips": [], "shots": [{"start": 0, "end": 2, "scene": "apartamento", "actors": [{"char": "l", "mark": "sofa", "pose": "sit", "prop": "phone"}]},
                                 {"start": 2, "end": 4, "scene": "apartamento", "actors": [{"char": "l", "mark": "sofa"}]}]}
    txt = " ".join(m for _, m in movimento.analisar(sp)); assert "de pé" in txt and "perdeu o objeto" in txt


def test_retencao(tmp_path):
    spec = tmp_path / "ep01.json"
    spec.write_text(json.dumps({"episode": 1, "shots": [{"start": 0, "end": 10, "scene": "rua"}, {"start": 10, "end": 20, "type": "detail", "subject": "celular"}]}))
    curva = tmp_path / "c.csv"; curva.write_text("0,100\n10,90\n20,40\n")
    ps = retencao.importar(str(spec), str(curva), "tiktok")
    assert retencao.piores(ps, 1)[0]["plano"] == "celular"
    assert "Ep. 1" in retencao.relatorio(str(tmp_path))


def test_cache_so_refaz_o_plano_tocado(tmp_path):
    from lofi.render import Episode
    base = {"out": "e.mp4", "fps": 30, "total": 6.0, "voices": {}, "clips": [], "subs": [], "modo_redes": False, "pergunta": False, "sfx": [{"t": 1.0, "name": "click"}],
            "shots": [{"start": 0, "end": 2, "scene": "rua", "actors": []}, {"start": 2, "end": 4, "scene": "rua", "actors": []}, {"start": 4, "end": 6, "scene": "rua", "actors": []}]}
    p = tmp_path / "e.json"; p.write_text(json.dumps(base)); k1 = Episode(str(p))._chaves_planos()
    b2 = copy.deepcopy(base); b2["sfx"][0]["t"] = 5.0; p.write_text(json.dumps(b2)); k2 = Episode(str(p))._chaves_planos()
    assert k1[1][0] == k2[1][0] and k1[0][0] != k2[0][0] and k1[2][0] != k2[2][0]


def test_editor_aplica_mudancas_e_mantem_sincronia(tmp_path):
    from lofi import editor
    sp = {"total": 20.0, "subs": [{"voice": "l", "src": [0, 1], "text": ["A"]}], "clips": [{"voice": "l", "src": [0, 1], "at": 1.0}, {"voice": "l", "src": [2, 3], "at": 6.0}],
          "sfx": [{"t": 7.0, "name": "click"}], "hud": {"days": [[0, "DIA 0", "10:00"], [6, "DIA 0", "11:00"]]}, "pergunta": {"t": 8.0},
          "shots": [{"start": 0, "end": 5, "scene": "rua", "actors": [{"char": "l", "emotion": "neutral"}]},
                    {"start": 5, "end": 10, "type": "detail", "subject": "celular", "params": {"text": ["OI"]}},
                    {"start": 10, "end": 20, "type": "choice", "a": {}, "b": {}, "end_card": {"t": 12, "text": "X"}}]}
    p = tmp_path / "ep.json"; p.write_text(json.dumps(sp)); e = tmp_path / "e.json"
    e.write_text(json.dumps({"status": "gerar", "planos": {"0": {"frases": {"0": "NOVA / LEGENDA"}, "emotion": "fear", "extra": 1.5, "pedido": "mais perto"}, "1": {"tela": ["TCHAU"]}}}))
    r = editor.aplicar(str(p), str(e)); n = json.loads(p.read_text())
    assert r["status"] == "gerar" and r["pedidos"][0]["pedido"] == "mais perto"
    assert n["subs"][0]["text"] == ["NOVA", "LEGENDA"] and n["shots"][0]["actors"][0]["emotion"] == "fear" and n["shots"][1]["params"]["text"] == ["TCHAU"]
    assert n["shots"][1]["start"] == 6.5 and n["clips"][0]["at"] == 1.0 and n["clips"][1]["at"] == 7.5 and n["sfx"][0]["t"] == 8.5
    assert n["hud"]["days"][1][0] == 7.5 and n["pergunta"]["t"] == 9.5 and n["shots"][2]["end_card"]["t"] == 13.5 and n["total"] == 21.5
    assert n["shots"][0]["end"] == 6.5
