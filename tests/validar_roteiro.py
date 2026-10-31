"""Valida o roteiro (epNN_roteiro.md) antes de entregar ao usuário.

    python3 tests/validar_roteiro.py series/dia-zero/ep03_roteiro.md [--final]
Regras: gancho no início, abertura com carimbo, 12–20 cenas, pergunta A/B + "CONTINUA NO EPISÓDIO"
(ou "FIM" no último), narração ElevenLabs por personagem, legendas com até 4 palavras por pedaço, duração 2–3 min.
"""
import re, sys

def validar(txt, final=False):
    erros, avisos = [], []
    up = txt.upper()
    if "GANCHO" not in up: erros.append("falta a CENA 0 · GANCHO")
    if "A MAIORIA ESCOLHEU" not in up and "EPISÓDIO 1/" not in up: erros.append("falta o carimbo 'A MAIORIA ESCOLHEU'")
    cenas = set(int(n) for n in re.findall(r"CENA\s+(\d+)", up) if int(n) > 0)
    if not (12 <= len(cenas) <= 20): erros.append(f"{len(cenas)} cenas (padrão 12–20)")
    if final:
        if "FIM" not in up: erros.append("último episódio sem 'FIM'")
    else:
        if not re.search(r"\bA\)", txt) or not re.search(r"\bB\)", txt): erros.append("falta a pergunta com opções A) e B)")
        if "CONTINUA NO EPISÓDIO" not in up: erros.append("falta 'CONTINUA NO EPISÓDIO'")
    if "ELEVENLABS" not in up: erros.append("falta a narração para o ElevenLabs")
    if not re.search(r"\[(whispers|sighs|nervous|pause|scared|firm|angry|crying|breathing heavily)", txt, re.I):
        avisos.append("narração sem tags de voz em inglês")
    for m in re.finditer(r"LEGENDA[^:\n]*:\s*(.+)", txt, re.I):
        for piece in re.split(r"\s*/\s*", m.group(1)):
            if len(piece.split()) > 4: avisos.append(f"legenda com mais de 4 palavras: '{piece.strip()}'")
    tempos = [float(x) for x in re.findall(r"(\d+(?:[.,]\d+)?)\s*s\b", txt.replace(",", "."))]
    if tempos and not (110 <= max(tempos) <= 190): avisos.append(f"maior tempo citado {max(tempos):.0f}s (esperado 120–180 s)")
    return erros, avisos

if __name__ == "__main__":
    e, a = validar(open(sys.argv[1], encoding="utf-8").read(), "--final" in sys.argv)
    for x in e: print("[ERRO]", x)
    for x in a: print("[AVISO]", x)
    print("OK" if not e else f"{len(e)} erro(s)")
    sys.exit(1 if e else 0)
