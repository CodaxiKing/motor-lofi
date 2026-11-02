"""Modo redes: selo no lugar da cartela, loop, cortes automáticos, pergunta, legenda com palavra-chave e área segura."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lofi.render import Episode
from lofi import text, scenes


def _ep(tmp_path, **topo):
    shots = [{"start": 0, "end": 2, "scene": "loja", "hook": {"text": "NÃO OLHE"}, "actors": [{"char": "detetive", "mark": "centro"}]},
             {"start": 2, "end": 14, "scene": "loja", "actors": [{"char": "detetive", "mark": "caixa"}, {"char": "medica", "mark": "balcao"}]},
             {"start": 14, "end": 20, "scene": "posto", "actors": [{"char": "detetive", "mark": "frente"}]},
             {"start": 20, "end": 26, "type": "choice", "a": {"label": "A", "scene": "loja"}, "b": {"label": "B", "scene": "loja"}}]
    spec = {"out": "x.mp4", "total": 26, "episode": 1, "episodes_total": 5, "shots": shots, **topo}
    p = tmp_path / "ep.json"; p.write_text(json.dumps(spec)); return Episode(str(p))


def test_loop_no_fim_e_modo_antigo(tmp_path):
    ep = _ep(tmp_path)
    assert ep.redes and ep.shots[-1]["type"] == "loop" and abs(ep.total - 26.5) < 1e-6
    velho = _ep(tmp_path, plano_padrao="aberto")
    assert not velho.redes and velho.shots[-1]["type"] == "choice"
    text.set_redes(True)


def test_cortes_automaticos(tmp_path):
    ep = _ep(tmp_path)
    cortes = ep.cortes(ep.shots[1])
    assert len(cortes) >= 3 and all(1.8 <= b - a <= 4.7 for a, b, _, _ in cortes)
    assert cortes[0][2] == 0 and cortes[1][2] == 1               # base, depois close
    assert len(ep.cortes(ep.shots[0])) == 1                      # gancho não corta


def test_pergunta_automatica(tmp_path):
    ep = _ep(tmp_path, pergunta={"text": "VOCÊ ATENDERIA?"})
    t0, t1, txt = ep.pergunta()
    assert txt == "VOCÊ ATENDERIA?" and 26 * 0.48 <= t0 and abs(t1 - t0 - 3.0) < 1e-6
    assert _ep(tmp_path, pergunta=False).pergunta() is None


def test_palavra_chave_e_area_segura():
    text.set_redes(True)
    assert [k for _, k in text.palavras("AS LUZES PISCARAM.")] == [False, False, True]
    assert [w for w, k in text.palavras("O *SININHO* TOCOU.") if k] == ["SININHO"]
    assert text.SUB_Y <= text.SAFE_Y_MAX <= 1440 and text.SAFE_W <= 1080 - 200


def test_quadros_renderizam(tmp_path):
    ep = _ep(tmp_path, voto="TELHADO")
    for t in (0.0, 3.0, 8.0, 17.5, 22.0, 26.2):
        assert ep.frame(t).size == (1080, 1920)
