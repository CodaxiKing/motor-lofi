"""Uso: python3 tools/diretor.py roteiro.txt [saida.json]"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lofi.director import suggest_shots
if __name__ == "__main__":
    if len(sys.argv) not in (2, 3): raise SystemExit("Uso: python3 tools/diretor.py roteiro.txt [saida.json]")
    output = json.dumps(suggest_shots(Path(sys.argv[1]).read_text(encoding="utf-8")), ensure_ascii=False, indent=2)
    if len(sys.argv) == 3: Path(sys.argv[2]).write_text(output + "\n", encoding="utf-8")
    else: print(output)
