"""Pipeline offline: roteiro -> JSON editável + manifesto de assets.

Uso: python3 tools/produzir.py roteiro.txt saida/ep01.json --profile horror_illustrated
Render: python3 -m lofi.render saida/ep01.json --test 2
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lofi.autodirect import write_episode
from lofi.asset_plan import write_asset_manifest

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('story'); parser.add_argument('output')
    parser.add_argument('--profile', default='horror_illustrated')
    parser.add_argument('--actor', default='roberta')
    parser.add_argument('--scene', default='apartamento')
    parser.add_argument('--duration', type=float)
    args = parser.parse_args()
    episode = write_episode(args.story, args.output, actor=args.actor,
                            scene=args.scene, visual_profile=args.profile,
                            duration=args.duration)
    manifest = str(Path(args.output).with_suffix('.assets.json'))
    write_asset_manifest(episode, manifest)
    print(f'Episódio: {args.output} ({len(episode["shots"])} planos)')
    print(f'Manifesto: {manifest}')
