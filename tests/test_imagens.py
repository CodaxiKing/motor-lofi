"""Estilo "imagens": prompts a partir do roteiro, importação sem fundo e montagem do quadro."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageDraw
from lofi import imagens


def _serie(d):
    json.dump({"lia": {"top_style": "scrubs", "top": [96, 168, 178], "hair": "bun", "hair_color": [40, 28, 24]}},
              open(os.path.join(d, "personagens.json"), "w"))
    open(os.path.join(d, "biblia.md"), "w").write("Estilo: imagens\nPrompt de estilo: cartoon teste\n")
    open(os.path.join(d, "ep01_roteiro.md"), "w").write(
        "## CENA 1 — 0 s a 5 s\nIMAGENS: fundo `hospital` (corredor) · `lia_frente_medo`\n"
        "## CENA 2 — 5 s a 9 s\nIMAGENS: fundo `hospital` · `lia_lado_choque_correndo`\n")


def test_prompts_e_reaproveitamento():
    with tempfile.TemporaryDirectory() as d:
        _serie(d)
        out, itens = imagens.prompts(os.path.join(d, "ep01_roteiro.md"))
        nomes = [n for n, _ in itens]
        assert nomes == ["fundo_hospital", "lia_frente_medo", "lia_lado_choque_correndo"]
        txt = open(out, encoding="utf-8").read()
        assert "cartoon teste" in txt and "coque" in txt and "FUNDO TRANSPARENTE" in txt and "SEM PESSOAS" in txt
        os.makedirs(os.path.join(d, "imagens")); Image.new("RGB", (30, 20)).save(os.path.join(d, "imagens", "fundo_hospital.png"))
        _, itens = imagens.prompts(os.path.join(d, "ep01_roteiro.md"))
        assert [n for n, _ in itens] == ["lia_frente_medo", "lia_lado_choque_correndo"]     # o que já existe não volta


def test_importar_tira_fundo_e_monta_quadro():
    with tempfile.TemporaryDirectory() as d:
        _serie(d)
        p = os.path.join(d, "baixada.png")
        im = Image.new("RGB", (100, 200), (250, 250, 250)); ImageDraw.Draw(im).rectangle([30, 20, 70, 190], fill=(200, 30, 30)); im.save(p)
        out = imagens.importar(d, p, "lia_frente_medo")
        r = Image.open(out)
        assert r.mode == "RGBA" and r.size[0] < 60 and r.getpixel((r.width // 2, r.height // 2))[3] == 255
        Image.new("RGB", (300, 200), (10, 20, 40)).save(os.path.join(d, "imagens", "fundo_hospital.png"))
        shot = {"start": 0, "end": 2, "imagens": {"fundo": "hospital", "personagens": [{"img": "lia_frente_medo", "fala": "lia"}]}}
        a = imagens.quadro(shot, 0.5, d, (108, 192), lambda v, t: 0.0)
        b = imagens.quadro(shot, 0.5, d, (108, 192), lambda v, t: 1.0)
        assert a.size == (108, 192) and a.tobytes() != b.tobytes()            # quem fala se mexe
        assert imagens.quadro(shot, 0.5, d, (192, 108)).size == (192, 108)    # deitado
        json.dump({"shots": [shot, {"start": 2, "end": 3, "imagens": {"fundo": "rua"}}]}, open(os.path.join(d, "ep.json"), "w"))
        assert imagens.faltam(os.path.join(d, "ep.json")) == [(2, "fundo_rua")]


def test_piscar_andar_frente_e_barras():
    with tempfile.TemporaryDirectory() as d:
        _serie(d); os.makedirs(os.path.join(d, "imagens"))
        Image.new("RGB", (300, 200), (10, 20, 40)).save(os.path.join(d, "imagens", "fundo_hospital.png"))
        for nome, cor in (("lia_frente_medo", (200, 30, 30, 255)), ("lia_frente_medo_piscando", (30, 200, 30, 255))):
            fig = Image.new("RGBA", (44, 84), (0, 0, 0, 0)); ImageDraw.Draw(fig).rectangle([2, 2, 41, 81], fill=cor)
            fig.save(os.path.join(d, "imagens", nome + ".png"))
        Image.new("RGBA", (20, 20), (250, 250, 0, 255)).save(os.path.join(d, "imagens", "obj_grade.png"))
        shot = {"start": 0, "end": 4, "imagens": {"fundo": "hospital", "personagens": [{"img": "lia_frente_medo"}],
                                                   "frente": [{"img": "obj_grade", "flutuar": True}]}}
        piscando = imagens.quadro(shot, 0.05, d, (108, 192)); aberto = imagens.quadro(shot, 1.0, d, (108, 192))
        verde = lambda im: sum(1 for p in im.getdata() if p[1] > 150 and p[0] < 80)
        assert verde(piscando) > 50 and verde(aberto) == 0                    # olhos fechados por um instante
        shot["imagens"]["personagens"][0]["andar"] = ["esq", "dir"]
        def x_vermelho(im):
            xs = [i % im.width for i, p in enumerate(im.getdata()) if p[0] > 150 and p[1] < 80]
            return sum(xs) / len(xs)
        assert x_vermelho(imagens.quadro(shot, 3.9, d, (108, 192))) > x_vermelho(imagens.quadro(shot, 0.5, d, (108, 192))) + 20
    from lofi import text
    im = Image.new("RGB", (1080, 1920)); text.barras(im, 5.0, [{"label": "ENERGIA", "value": [[0, 1.0], [10, 0.0]]}])
    assert im.getbbox() is not None
