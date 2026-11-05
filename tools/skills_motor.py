"""Integração local das skills: inventário, brief criativo e exportação de avaliações."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lofi.skill_bridge import listar, contexto, converter_evals


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('listar')
    a = sub.add_parser('contexto')
    a.add_argument('serie'); a.add_argument('--episode', type=int, required=True)
    a.add_argument('--skill', choices=['video-script', 'canvas-design'], default='video-script')
    a.add_argument('--duration-profile'); a.add_argument('--duration', type=float)
    a = sub.add_parser('evals')
    a.add_argument('--source'); a.add_argument('--skill-name', default='serie-lofi-interativa')
    args = parser.parse_args(argv)
    if args.command == 'listar': resultado = listar()
    elif args.command == 'evals': resultado = converter_evals(args.source, args.skill_name)
    else: resultado = contexto(args.serie, args.episode, skill=args.skill,
                              perfil=args.duration_profile, duracao=args.duration)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return resultado


if __name__ == '__main__': main()
