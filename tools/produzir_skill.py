"""CLI para skill: preparar, voz, status; ações pagas exigem --provider elevenlabs explícito."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lofi.production import prepare, generate_narration, status

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='action',required=True)
 a=sub.add_parser('preparar');a.add_argument('story');a.add_argument('episode');a.add_argument('--profile',default='horror_illustrated');a.add_argument('--actor',default='roberta');a.add_argument('--scene',default='apartamento')
 v=sub.add_parser('voz');v.add_argument('story');v.add_argument('output');v.add_argument('--provider',choices=['piper','elevenlabs'],default='piper');v.add_argument('--model');v.add_argument('--voice')
 s=sub.add_parser('status');s.add_argument('story');s.add_argument('episode')
 args=p.parse_args(argv)
 if args.action=='preparar': result=prepare(args.story,args.episode,profile=args.profile,actor=args.actor,scene=args.scene)
 elif args.action=='voz':result={'audio':generate_narration(args.story,args.output,provider=args.provider,model=args.model,voice=args.voice)}
 else:result=status(args.story,args.episode)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
