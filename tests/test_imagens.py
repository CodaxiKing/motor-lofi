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
