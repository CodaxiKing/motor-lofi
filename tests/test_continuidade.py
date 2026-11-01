"""Continuidade: pulo de lugar sem LIGAÇÃO e objeto fora do lugar são erros do validador de roteiro."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from validar_roteiro import conferir_continuidade as _cc, carregar_nomes
CAT = carregar_nomes(".")[0]
conferir_continuidade = lambda txt, _=None: _cc(txt, CAT)
from lofi.mapa import lugar


def _rot(*cenas):
    return "\n".join(f"## CENA {i + 1} — x\n{extra}\nCENÁRIO: `{c}`\n" for i, (c, extra) in enumerate(cenas))


def test_lugares():
    assert lugar("radio_carro") == lugar("carro") and lugar("entrada_metro") == lugar("rua")


def test_pulo_sem_ligacao():
    assert any("pulo de lugar" in e for e in conferir_continuidade(_rot(("posto", ""), ("metro", "")), None))


def test_ligacao_e_insercao_ok():
    assert not conferir_continuidade(_rot(("posto", ""), ("entrada_metro", "LIGAÇÃO: andam até a estação"),
                                          ("ponte", "INSERÇÃO: a ponte de longe"), ("entrada_metro", "")), None)


def test_radio_de_casa_no_carro():
    erros = conferir_continuidade(_rot(("carro", ""), ("radio", "")), None)
    assert any("radio_carro" in e for e in erros)
    assert not conferir_continuidade(_rot(("carro", ""), ("radio_carro", "")), None)
