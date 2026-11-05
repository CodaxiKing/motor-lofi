"""Gera roteiro técnico a partir de texto: python tools/gerar_episodio.py historia.txt episodio.json"""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lofi.autodirect import write_episode
from lofi.personagens import carregar_elenco

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Gera episódio técnico editável a partir de história')
    p.add_argument('story')
    p.add_argument('output')
    p.add_argument('--title', default='NOVA SÉRIE')
    p.add_argument('--actor', default='roberta')
    p.add_argument('--scene', default='apartamento')
    p.add_argument('--profile', default='lofi_classic')
    p.add_argument('--duration', type=float)
    p.add_argument('--duration-profile', choices=['curto','medio','longo','tradicional'])
    p.add_argument('--opening', choices=['A','B','C'], default='A')
    p.add_argument('--cast', help='Elenco JSON com identidades e perfis de movimento')
    p.add_argument('--state', help='Estado físico revisado do episódio anterior')
    args = p.parse_args()
    spec = write_episode(args.story, args.output, title=args.title, actor=args.actor,
                         scene=args.scene, visual_profile=args.profile, duration=args.duration, duration_profile=args.duration_profile, opening=args.opening,
                            elenco=carregar_elenco(args.cast) if args.cast else None,
                            world_state=json.loads(Path(args.state).read_text(encoding='utf-8')) if args.state else None)
    print(f"Gerados {len(spec['shots'])} planos em {args.output} ({spec['total']}s)")
