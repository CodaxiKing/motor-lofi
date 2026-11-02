from lofi.votos import voto, _palavras

OPS = {"A": ("Fazer barulho", _palavras("Fazer barulho")), "B": ("Esperar em silêncio", _palavras("Esperar em silêncio"))}


def test_letra_sozinha():
    assert voto("a", OPS) == "A"
    assert voto("B", OPS) == "B"
    assert voto("“B", OPS) == "B"
    assert voto("BBBB", OPS) is None or voto("B B B", OPS) == "B"


def test_frases():
    assert voto("vou de A", OPS) == "A"
    assert voto("letra b com certeza", OPS) == "B"
    assert voto("faz barulho logo", OPS) == "A"
    assert voto("melhor esperar quieto", OPS) == "B"


def test_artigo_nao_conta_e_duvida():
    assert voto("a ponte estava a um quarteirão", OPS) is None
    assert voto("A ou B? barulho ou esperar", OPS) == "duvida"
