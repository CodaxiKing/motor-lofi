import json
import os
import tempfile

from PIL import Image

SPEC = {"fps": 30, "total": 8, "efeitos": "nenhum",
        "interface": {"status": [{"rotulo": "ÁGUA", "valor": 1.0, "texto": "CHEIA"}, {"rotulo": "CEL", "valor": 0.58}],
                      "relogio": {"dia": "SÁB", "inicio": "06:20", "seg_por_min": 8},
                      "missao": {"titulo": "Prepare o abrigo", "prazo": "90:00"}},
        "shots": [
            {"start": 0, "end": 2, "scene": "apartamento", "actors": [],
             "dialogo": {"nome": "PAI", "texto": "Não saiam agora."}},
            {"start": 2, "end": 4, "scene": "apartamento", "actors": [], "alerta": {"titulo": "Fique em casa", "texto": "x"}},
            {"start": 4, "end": 6, "scene": "apartamento", "actors": [], "hora": "07:00", "status": {"CEL": 0.1},
             "reticula": 1.0, "glitch": [4.0]},
            {"start": 6, "end": 8, "scene": "apartamento", "actors": [], "interface": False}]}


def _ep(d, spec=SPEC):
    json.dump(spec, open(os.path.join(d, "ep.json"), "w", encoding="utf-8"), ensure_ascii=False)
    from lofi.render import Episode
    return Episode(os.path.join(d, "ep.json"))


def test_estado_da_interface_ao_longo_do_tempo():
    from lofi import interface
    with tempfile.TemporaryDirectory() as d:
        ep = _ep(d)
        assert interface._clock_now(ep, 0.0) == ("SÁB", "06:20")
        assert interface._clock_now(ep, 3.9) == ("SÁB", "06:20")          # 8 s por minuto: ainda 06:20
        assert interface._clock_now(ep, 4.5) == ("SÁB", "07:00")          # o plano acerta a hora
        assert interface._status_now(ep, 1.0)["CEL"][0] == 0.58
        assert interface._status_now(ep, 5.0)["CEL"][0] == 0.1            # valor muda a partir do plano
        assert interface._mission_now(ep, 1.0)["titulo"] == "Prepare o abrigo"


def test_quadros_com_interface_e_efeitos():
    with tempfile.TemporaryDirectory() as d:
        ep = _ep(d)
        plain = _ep(d, {**SPEC, "interface": None, "shots": [{**s, "interface": False} for s in SPEC["shots"]]})
        for t in (1.5, 3.0, 4.05):
            a, b = ep.frame(t), plain.frame(t)
            assert a.size == b.size and a.tobytes() != b.tobytes(), t       # interface/efeito aparece
        sem = ep.frame(7.0)                                                 # "interface": false esconde
        assert sem.tobytes() == plain.frame(7.0).tobytes()
        # alerta: borda vermelha
        px = ep.frame(2.16).resize((54, 96)).getpixel((1, 48))            # pico do pulso do alerta
        base = plain.frame(2.16).resize((54, 96)).getpixel((1, 48))
        assert px[0] > base[0] + 15                                        # borda fica mais vermelha
