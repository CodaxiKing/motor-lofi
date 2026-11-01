"""CLI offline da skill Motor Lo-Fi Studio. Sem MCP obrigatório."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lofi.studio import detect_capabilities, initialize_series, plan_episode, quality_report, commit_continuity

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('ambiente')
    a = sub.add_parser('iniciar'); a.add_argument('series_dir'); a.add_argument('--title', required=True); a.add_argument('--profile', default='horror_illustrated')
    a = sub.add_parser('planejar'); a.add_argument('story'); a.add_argument('series_dir'); a.add_argument('--episode', type=int, default=1); a.add_argument('--branch'); a.add_argument('--actor', default='roberta'); a.add_argument('--scene', default='apartamento'); a.add_argument('--mode', choices=['automatic','professional','hybrid'], default='hybrid'); a.add_argument('--duration', type=float)
    a = sub.add_parser('revisar'); a.add_argument('episode')
    a = sub.add_parser('confirmar'); a.add_argument('series_dir'); a.add_argument('--episode', type=int, required=True); a.add_argument('--fact', action='append'); a.add_argument('--thread', action='append'); a.add_argument('--choice')
    args = p.parse_args(argv)
    if args.command == 'ambiente': out = detect_capabilities()
    elif args.command == 'iniciar': out = initialize_series(args.series_dir, args.title, visual_style=args.profile)
    elif args.command == 'planejar': out = plan_episode(Path(args.story).read_text(encoding='utf-8'), series_dir=args.series_dir, episode_number=args.episode, branch=args.branch, actor=args.actor, scene=args.scene, mode=args.mode, duration=args.duration)
    elif args.command == 'revisar':
        ep = Path(args.episode)
        out = quality_report(json.loads(ep.read_text(encoding='utf-8')), episode_path=ep)
    else: out = commit_continuity(args.series_dir, episode_number=args.episode, facts=args.fact, open_threads=args.thread, choice=args.choice)
    print(json.dumps(out, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
