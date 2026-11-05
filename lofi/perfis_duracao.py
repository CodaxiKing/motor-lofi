"""Perfis editoriais de duração; não representam limites das plataformas."""
import re
import math
from pathlib import Path


PERFIS = {
    "curto": {"min_s": 90, "max_s": 120, "min_cenas": 9},
    "medio": {"min_s": 120, "max_s": 180, "min_cenas": 12},
    "longo": {"min_s": 180, "max_s": 300, "min_cenas": 18},
    "tradicional": {"min_s": 90, "max_s": None, "min_cenas": 12},
}


def planejar(nome, duracao=None, estimativa=0):
    """Contrato compartilhado pelos produtores; sem inventar conteúdo para preencher tempo."""
    _, regras = selecionar('', perfil=nome)
    alvo = max(regras['min_s'], estimativa) if duracao is None else duracao
    if isinstance(alvo, bool) or not isinstance(alvo, (int, float)) or not math.isfinite(alvo):
        raise ValueError('Duração deve ser um número finito')
    if alvo < regras['min_s'] or (regras['max_s'] and alvo > regras['max_s']):
        raise ValueError(f'Duração {alvo:g}s fora do perfil {nome}: {regras}')
    return dict(regras, nome=nome, alvo_s=alvo)


def selecionar(txt, caminho=None, perfil=None):
    """Precedência: argumento > roteiro > bíblia > tradicional (legado)."""
    fontes = [txt]
    if caminho:
        biblia = Path(caminho).resolve().parent / "biblia.md"
        if biblia.is_file():
            fontes.append(biblia.read_text(encoding="utf-8"))
    if perfil is None:
        for fonte in fontes:
            m = re.search(r"^\s*(?:\*\*)?Perfil de dura[çc][ãa]o(?:\*\*)?\s*:\s*(?:\*\*)?([^\s*]+)", fonte, re.M | re.I)
            if m:
                perfil = m.group(1).lower()
                break
    perfil = perfil or "tradicional"
    if perfil not in PERFIS:
        raise ValueError(f"perfil de duração '{perfil}' inválido; use {', '.join(PERFIS)}")
    return perfil, PERFIS[perfil]


def conferir_duracao(txt, nome, perfil):
    """Usa fim das cenas; referências a segundos na fala não estendem o vídeo."""
    from .ritmo import cenas
    timeline = cenas(txt)
    tempos = [c[2] for c in timeline]
    if nome == "tradicional":
        # Compatibilidade com os roteiros anteriores aos perfis.
        tempos = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*s\b", re.sub(r"(\d),(\d)", r"\1.\2", txt))]
    if not tempos:
        return ["duração não verificável: use cenas com tempos (## CENA 1 — 0 s a 15 s)"] if nome != "tradicional" else []
    duracao = max(tempos)
    minimo, maximo = perfil["min_s"], perfil["max_s"]
    if duracao < minimo or (maximo is not None and duracao > maximo):
        faixa = f"{minimo}–{maximo} s" if maximo is not None else f"no mínimo {minimo} s"
        return [f"duração {duracao:g} s fora do perfil {nome}: esperado {faixa}"]
    return []
