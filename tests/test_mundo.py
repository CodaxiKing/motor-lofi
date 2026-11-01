"""Mapa da cidade (mundo.json): rota entre lugares, começo onde o anterior parou, inventário e relógio."""
import json
from lofi import continuidade as C

MUNDO = {"lugares": {"rua": {"cenarios": ["rua", "entrada_metro"]}, "posto": {"cenarios": ["posto"]},
                     "metro": {"cenarios": ["metro"]}, "carro": {"cenarios": ["carro"]}},
         "ligacoes": [["rua", "posto"], ["rua", "metro"], ["rua", "carro"]]}
INICIO = {"lugar": "posto", "dia": 4, "hora": "05:50", "inventario": {"roberta": ["lanterna"]}}


def _rot(*cenas):
    return "\n".join(f"## CENA {i + 1} — x\n{extra}\nCENÁRIO: `{c}` {hora}\n" for i, (c, hora, extra) in enumerate(cenas))


def test_rota():
    assert C.rota(MUNDO, "posto", "metro") == ["posto", "rua", "metro"]


def test_caminho_que_nao_liga_direto():
    e, _ = C.percorrer(_rot(("posto", "", ""), ("metro", "", "LIGAÇÃO: descem")), MUNDO, INICIO)
    assert any("posto → rua → metro" in x for x in e)


def test_comeca_onde_parou():
    e, _ = C.percorrer(_rot(("carro", "", "")), MUNDO, INICIO)
    assert any("terminou em 'posto'" in x for x in e)


def test_inventario_e_pega():
    e, _ = C.percorrer(_rot(("posto", "", ""), ("rua", "", "LIGAÇÃO: saem\n`radio_portatil`")), MUNDO, INICIO)
    rot = _rot(("posto", "", ""), ("posto", "", "PEGA: rafa radio")).replace("CENÁRIO: `posto` \n", "CENÁRIO: `posto`\n", 1)
    rot += "## CENA 3 — x\nCENÁRIO: `radio_portatil`\n"
    e, fim = C.percorrer(rot, MUNDO, INICIO)
    assert not e and "radio" in fim["inventario"]["rafa"]
    e, _ = C.percorrer("## CENA 1 — x\nCENÁRIO: `radio_portatil`\n", MUNDO, {"lugar": "posto", "inventario": {}})
    assert any("ninguém carrega" in x for x in e)


def test_relogio():
    e, _ = C.percorrer(_rot(("posto", "DIA 4 · 05:00", "")), MUNDO, INICIO)
    assert any("voltou no tempo" in x for x in e)
    e, _ = C.percorrer(_rot(("posto", "DIA 4 · 06:00", ""), ("posto", "DIA 4 · 22:00", "")), MUNDO, INICIO)
    assert any("sem mostrar o tempo" in x for x in e)
    rot = _rot(("posto", "DIA 4 · 06:00", ""), ("posto", "DIA 4 · 22:00", "PLANO DE DETALHE: `relogio`"))
    assert not C.percorrer(rot, MUNDO, INICIO)[0]


def test_escolhas_da_biblia(tmp_path):
    from lofi.extras import ler_escolhas
    b = tmp_path / "biblia.md"
    b.write_text("| Nº | Dia | Fase | Status | Pergunta | Voto | Placar |\n|---|---|---|---|---|---|---|\n"
                 "| 1 | 1 | início | montado | A) Abrir · B) Espiar | ESPIAR | 340x210 |\n"
                 "| 2 | 2 | x | montado | A) Escada · B) Telhado | ESCADA | 62% |\n| 3 | 3 | x | montado | A) X · B) Y | (aguardando) | |\n",
                 encoding="utf-8")
    r = ler_escolhas(str(b))
    assert r[0][3] == "B" and r[0][4] == 62 and r[1] == (2, "Escada", "Telhado", "A", 62, 38) and len(r) == 2
