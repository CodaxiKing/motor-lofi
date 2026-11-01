"""Travelling lateral: o cenário rola, a tira repete sem corte e as marcas do travelling ficam no chão."""
import numpy as np
from lofi import scenes, mapa
from lofi.travelling import _wrapcrop
from lofi.core import W


def test_cenario_rola_e_repete_sem_corte():
    sc = scenes.get("rua", travelling=True)
    a = np.asarray(sc.render_back(0, 0, {"_scroll": 0}), dtype=float)
    b = np.asarray(sc.render_back(0, 0, {"_scroll": 400}), dtype=float)
    assert np.abs(a - b).mean() > 3                       # o cenário mudou com o movimento
    n = sc.perto.width
    corte = np.asarray(_wrapcrop(sc.perto, n - W // 2).convert("RGB"), dtype=float)
    salto = np.abs(corte[1600:1840, W // 2] - corte[1600:1840, W // 2 - 1]).mean()
    assert salto < 25                                      # sem degrau visível na emenda


def test_todos_os_temas_constroem():
    for nome in ("floresta", "metro", "esgoto", "ponte", "hospital"):
        assert scenes.get(nome, travelling=True).render_back(0, 0, {"_scroll": 100}).size[0] == W


def test_marcas_do_travelling_no_chao():
    for n, mk in mapa.marcas("_travelling").items():
        assert mapa.no_chao("_travelling", mk["x"], mk["y"], folga=0), n


def test_chegada_desacelera_e_para_no_alvo():
    from lofi.travelling import posicao
    tv = {"speed": 400, "chegada": "carro", "para": 1.5, "chegada_x": 760}
    s_fim, (tipo, x_fim) = posicao(tv, 5.0, 5.0)
    s_quase, _ = posicao(tv, 4.9, 5.0)
    assert tipo == "carro" and abs(x_fim - 760) < 1 and s_fim - s_quase < 400 * 0.1 * 0.2   # quase parado no fim
    assert posicao(tv, 1.0, 5.0)[1][1] > W                                                  # no começo o carro está fora do quadro


def test_frente_e_fundo_rolam():
    sc = scenes.get("corredor", travelling="frente")
    a = np.asarray(sc.render_back(0, 0, {"_scroll": 0}), dtype=float)
    b = np.asarray(sc.render_back(0, 0, {"_scroll": 300}), dtype=float)
    assert np.abs(a - b).mean() > 2
