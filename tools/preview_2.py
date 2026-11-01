"""Preview sem renderizar o vídeo: python3 tools/preview_2.py episodio.json 2 7 12"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lofi.render import Episode
def main():
    if len(sys.argv)<3: raise SystemExit('Uso: python3 tools/preview_2.py episodio.json segundo [segundo...]')
    ep=Episode(sys.argv[1]); out=Path(sys.argv[1]).parent/'preview_2';out.mkdir(exist_ok=True)
    for val in sys.argv[2:]:
        t=float(val)
        if not 0<=t<=ep.total: raise ValueError(f'Tempo fora do episódio: {t}')
        target=out/f'frame_{t:08.2f}.png';ep.frame(t).save(target);print(target)
if __name__=='__main__': main()
