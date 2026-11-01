"""Uso: python3 tools/validar_continuidade.py episodio.json"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lofi.continuity import validate_episode
if __name__=='__main__':
    problems=validate_episode(sys.argv[1]);print('\n'.join(problems) if problems else 'Continuidade: OK')
    raise SystemExit(bool(problems))
