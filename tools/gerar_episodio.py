"""Gera roteiro técnico a partir de texto: python tools/gerar_episodio.py historia.txt episodio.json"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lofi.autodirect import write_episode

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Gera episódio técnico editável a partir de história')
    p.add_argument('story')
    p.add_argument('output')
    p.add_argument('--title', default='NOVA SÉRIE')
    p.add_argument('--actor', default='roberta')
    p.add_argument('--scene', default='apartamento')
    p.add_argument('--profile', default='lofi_classic')
    p.add_argument('--duration', type=float)
    args = p.parse_args()
    spec = write_episode(args.story, args.output, title=args.title, actor=args.actor,
                         scene=args.scene, visual_profile=args.profile, duration=args.duration)
    print(f"Gerados {len(spec['shots'])} planos em {args.output} ({spec['total']}s)")
