"""Capas do TikTok e do Instagram: tamanho, nomes e quadro sem contador."""
import os, json, shutil
from PIL import Image
from lofi.extras import capa, PLATAFORMAS

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _spec(tmp_path, **extra):
    sp = json.load(open(os.path.join(RAIZ, "examples", "demo4", "demo4.json"), encoding="utf-8"))
    sp.update({"voices": {}, "clips": [], "subs": [], "series_title": "DIA ZERO", "episode": 3, "episodes_total": 5,
               "episode_title": "A VOZ DO RÁDIO"}, **extra)
    p = tmp_path / "ep03.json"; p.write_text(json.dumps(sp, ensure_ascii=False), encoding="utf-8")
    return str(p)


def test_duas_plataformas(tmp_path):
    spec = _spec(tmp_path)
    for plat in PLATAFORMAS:
        out = capa(spec, plataforma=plat)
        assert os.path.basename(out) == f"ep03_capa_{plat}.png"
        assert Image.open(out).size == (1080, 1920)


def test_area_segura_dentro_do_recorte_do_grid():
    # tudo o que importa precisa caber no recorte 3:4 do grid (y 240–1680) nas duas redes
    for cfg in PLATAFORMAS.values():
        x0, y0, x1, y1 = cfg["seguro"]
        assert 0 <= x0 < x1 <= 1080 and 240 <= y0 < y1 <= 1680
        assert y0 <= cfg["titulo_y"] - 80 and cfg["nome_y"] + 50 <= y1


def test_comentarios(tmp_path):
    spec = _spec(tmp_path, formato="comentarios")
    shutil.move(spec, tmp_path / "c01.json")
    out = capa(str(tmp_path / "c01.json"), plataforma="instagram")
    assert os.path.basename(out) == "c01_capa_instagram.png"
