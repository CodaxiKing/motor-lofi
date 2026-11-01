"""Enquadramento perto (padrão): 1 personagem = médio, 2 ou mais = conjunto, aberto quando pedido ou no modo antigo."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lofi.render import Episode
from lofi import scenes


def _ep(tmp_path, shot, **topo):
    spec = {"out": "x.mp4", "total": 4, "shots": [dict({"start": 0, "end": 4}, **shot)], **topo}
    p = tmp_path / "ep.json"; p.write_text(json.dumps(spec)); return Episode(str(p))


def _zoom(ep):
    s = ep.shots[0]; ep._treal = 1.0
    return ep.camera(s, scenes.get(s["scene"]), 1.0, 1.0, 0.25)[1][0]


def test_um_personagem_vira_medio(tmp_path):
    ep = _ep(tmp_path, {"scene": "loja", "actors": [{"char": "detetive", "mark": "centro"}]})
    assert ep.plano_de(ep.shots[0], scenes.get("loja")) == "medio" and _zoom(ep) > 2.5


def test_dois_personagens_viram_conjunto(tmp_path):
    ep = _ep(tmp_path, {"scene": "posto", "actors": [{"char": "detetive", "mark": "frente_esq"}, {"char": "medica", "mark": "frente_dir"}]})
    assert ep.plano_de(ep.shots[0], scenes.get("posto")) == "conjunto" and 1.0 <= _zoom(ep) <= 3.2


def test_aberto_quando_pedido_ou_no_modo_antigo(tmp_path):
    a = {"char": "detetive", "mark": "centro"}
    assert _zoom(_ep(tmp_path, {"scene": "loja", "camera": {"plano": "aberto"}, "actors": [a]})) == 1.0
    assert _zoom(_ep(tmp_path, {"scene": "loja", "actors": [a]}, plano_padrao="aberto")) == 1.0


def test_close_de_objeto_nao_muda(tmp_path):
    ep = _ep(tmp_path, {"scene": "cftv", "hand": "detetive"})
    assert ep.plano_de(ep.shots[0], scenes.get("cftv")) == "aberto"
