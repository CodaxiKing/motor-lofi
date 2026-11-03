import json
import os
import shutil
import subprocess
import tempfile

import pytest

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg ausente")


def _clip(path, color, seconds):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c={color}:s=240x426:r=24:d={seconds}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", path], check=True)


def test_video_clip_como_fundo_e_quadro_limpo():
    from lofi.render import Episode
    with tempfile.TemporaryDirectory() as d:
        _clip(os.path.join(d, "clip.mp4"), "blue", 1)
        spec = {"fps": 30, "total": 4, "efeitos": "nenhum", "shots": [
            {"start": 0, "end": 2, "scene": "apartamento", "video_clip": "clip.mp4", "actors": []},
            {"start": 2, "end": 4, "scene": "apartamento", "actors": []}]}
        json.dump(spec, open(os.path.join(d, "ep.json"), "w"))
        ep = Episode(os.path.join(d, "ep.json"))
        azul = lambda im: (lambda p: p[2] > 120 and p[2] > p[0] + 60)(im.resize((1, 1)).getpixel((0, 0)))
        assert azul(ep.frame(0.5))                      # o clipe é o fundo do plano...
        assert azul(ep.frame(1.8))                      # ...e segura o último quadro depois que acaba
        assert not azul(ep.frame(3.0))                  # o plano seguinte volta ao cenário desenhado
        assert not azul(ep.frame_limpo(0.5))            # quadro limpo ignora o clipe: é a cena para animar
        assert ep.frame_limpo(0.5).size == ep.frame(0.5).size


def test_clipe_em_pe_no_quadro_deitado_nao_corta():
    from lofi.video_clip import quadro
    with tempfile.TemporaryDirectory() as d:
        _clip(os.path.join(d, "clip.mp4"), "blue", 1)          # 240x426 (em pé)
        im = quadro({"start": 0, "video_clip": "clip.mp4"}, 0.5, d, (1920, 1080))
        assert im.size == (1920, 1080)
        centro, lateral = im.getpixel((960, 540)), im.getpixel((40, 540))
        assert centro[2] > 200                                  # o clipe inteiro no centro
        assert lateral[2] < centro[2] * 0.6                     # laterais: o próprio quadro escurecido
