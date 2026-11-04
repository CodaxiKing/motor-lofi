"""Cenário generativo (lofi/cenario_gen.py), biblioteca de móveis e conferência ao pé da letra (lofi/literal.py)."""
import json, os, shutil
from lofi import scenes, mapa, cenario_gen as CG, literal, moveis as MV
from lofi.core import W, H

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_ambientes_registrados_com_mapa():
    for nome in CG.AMBIENTES:
        assert nome in scenes.REGISTRY
        assert nome in mapa.MAPA and {"centro", "frente", "fundo"} <= set(mapa.MAPA[nome]["marcas"])
    assert mapa.conferir_mapa() == []


def test_moveis_desenham_sem_erro():
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (400, 400)); d = ImageDraw.Draw(img)
    for nome in MV.MOVEIS:
        MV.desenhar(d, nome, 200, 380, 1.0, lambda x, y: (int(x), int(y)), {}, alpha=True, ss=1)


def test_descricao_vira_cenario_com_os_moveis_pedidos():
    plano = {"start": 0, "end": 2, "cenario": {"base": "cozinha", "luz": "escuro", "sem": ["mesa_cozinha"],
                                                 "mudar": [{"m": "geladeira", "aberta": True}], "mais": [{"m": "cracha", "em": "chao", "x": 0.3, "z": 0.6}]}}
    s = mapa.resolver_plano(plano)
    assert s["scene"].startswith("gen_") and s["scene"] in scenes.REGISTRY
    cfg = CG.expandir(plano["cenario"])
    nomes = [m["m"] for m in cfg["moveis"]]
    assert "mesa_cozinha" not in nomes and "cracha" in nomes
    assert next(m for m in cfg["moveis"] if m["m"] == "geladeira")["aberta"] is True
    assert "cracha" in mapa.MAPA[s["scene"]]["marcas"]
    sc = scenes.get(s["scene"]); img = sc.render_back(0.2, 0, {})
    assert img.size == (W, H)
    assert mapa.resolver_plano(dict(plano))["scene"] == s["scene"]          # mesmo texto, mesmo cenário (cache)


def test_close_conta_objetos():
    nome = CG.registrar({"close": "lata", "superficie": "prateleira", "ambiente": "corredor_mercado"})
    sc = scenes.get(nome)
    a = sc.render_back(0.1, 0, {"n": 1}); b = sc.render_back(0.1, 0, {"n": 3})
    assert a.size == (W, H) and list(a.getdata()) != list(b.getdata())


def test_citados_na_ordem_e_sem_expressoes():
    assert literal.citados("O vidro do hortifrúti explode. Laranjas rolam") == ["janela", "banca_frutas"]
    assert literal.citados("Fiquem em casa.") == []
    assert "lata" in literal.citados("Você empurra a caixa de milho em lata.")


def test_aplicar_cobre_as_frases(tmp_path):
    origem = os.path.join(RAIZ, "tests", "fixtures", "literal.json")
    antes = literal.analisar(origem)
    saida = str(tmp_path / "literal.json")
    n, out = literal.aplicar(origem, saida)
    depois = literal.analisar(out)
    assert n > 0 and depois["nota"] > antes["nota"] and depois["nota"] >= 0.8
    sp = json.load(open(out, encoding="utf-8"))
    shots = sorted(sp["shots"], key=lambda s: s["start"])
    for x, y in zip(shots, shots[1:]): assert abs(x["end"] - y["start"]) < 0.05       # sem buracos nem sobreposição
    closes = {s["cenario"]["close"]: s for s in shots if isinstance(s.get("cenario"), dict) and s["cenario"].get("close")}
    assert [k[1] for k in closes["lata"]["props"]["n"]] == [1, 2, 3]                  # "Uma lata. Duas. Três."
    assert closes["caixa"]["cenario"]["opts"]["texto"] == "MILHO"
    assert closes["janela"]["cenario"]["opts"]["quebrada"] is True                     # "o vidro explode"
    assert closes["telefone"]["cenario"]["opts"]["visor"] == "17:45"
    assert "cracha" in closes
