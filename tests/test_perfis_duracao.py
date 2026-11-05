import importlib.util
from pathlib import Path

import pytest

from lofi.perfis_duracao import PERFIS, conferir_duracao, selecionar

spec = importlib.util.spec_from_file_location("validador_perfis", Path(__file__).with_name("validar_roteiro.py"))
validador = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validador)


def roteiro(total=90, quantidade=9):
    inicio = "GANCHO\nEPISÓDIO 1/5\nELEVENLABS [whispers]\nA) Abrir\nB) Fugir\nCONTINUA NO EPISÓDIO\n"
    return inicio + "\n".join(
        f"## CENA {n} — {(n-1)*total/quantidade:g} s a {n*total/quantidade:g} s\n"
        for n in range(1, quantidade + 1))


@pytest.mark.parametrize("nome", PERFIS)
def test_limites(nome):
    regras = PERFIS[nome]
    for total in (regras["min_s"], regras["max_s"] or 600):
        assert not conferir_duracao(roteiro(total), nome, regras)
    assert conferir_duracao(roteiro(regras["min_s"] - 1), nome, regras)
    if regras["max_s"]:
        assert conferir_duracao(roteiro(regras["max_s"] + 1), nome, regras)


def test_precedencia(tmp_path):
    (tmp_path / "biblia.md").write_text("Perfil de duração: medio", encoding="utf-8")
    caminho = tmp_path / "ep01_roteiro.md"
    assert selecionar("", caminho)[0] == "medio"
    assert selecionar("Perfil de duração: curto", caminho)[0] == "curto"
    assert selecionar("Perfil de duração: curto", caminho, "longo")[0] == "longo"
    assert selecionar("")[0] == "tradicional"


def test_curto_aceito_sem_exigencias_longas():
    erros, avisos = validador.validar(roteiro(), perfil="curto")
    assert not erros
    assert not any("COMPLEXIDADE" in a for a in avisos)


def test_padrao_preserva_exigencias():
    erros, avisos = validador.validar(roteiro())
    assert any("mínimo 12" in e for e in erros)
    assert any("90" in e for e in validador.validar(roteiro(89))[0])
    assert any("COMPLEXIDADE" in a for a in avisos)


def test_perfil_no_roteiro():
    erros, _ = validador.validar("Perfil de duração: curto\n" + roteiro())
    assert not erros


def test_perfil_invalido():
    erros, _ = validador.validar("Perfil de duração: desconhecido\n" + roteiro())
    assert "inválido" in erros[0]


def test_curto_nao_usa_tempo_da_fala():
    assert conferir_duracao(roteiro(10) + "Esperei 30 s", "curto", PERFIS["curto"])
    assert conferir_duracao("SOM: 30 s", "curto", PERFIS["curto"])


def test_minimo_cenas_independente_da_duracao():
    erros, _ = validador.validar(roteiro(90, 2), perfil="curto")
    assert any("mínimo 9" in e for e in erros)


@pytest.mark.parametrize("nome", PERFIS)
def test_nenhum_perfil_aceita_menos_de_90_segundos(nome):
    assert conferir_duracao(roteiro(89), nome, PERFIS[nome])
