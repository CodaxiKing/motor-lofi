"""Direção cinematográfica determinística baseada em roteiro.

Gera uma shotlist editorial; não substitui o formato técnico de lofi.render.
Sem serviços externos e sem alterações nos episódios existentes.
"""
import re
from dataclasses import dataclass

RULES = (
    (r"porta|maçaneta|chave|relógio|celular|rádio|fotografia|bilhete", "detail", "Close no objeto importante"),
    (r"medo|assust|terror|pânico|chor|triste|sussurr|trem", "close", "Aproxime a câmera para enfatizar a emoção"),
    (r"correu|corre|fug|persegu|dispar|salt|caminh", "tracking", "Acompanhe o movimento do personagem"),
    (r"silêncio|vazio|cidade|rua|floresta|prédio|horizonte|multidão", "wide", "Mostre a escala do ambiente"),
)
SOUND = re.compile(r"batid|estalo|grito|explos|tiro|alarme|siren|rangid|passos|barulho", re.I)
DANGER = re.compile(r"perig|ameaç|sangue|morr|morte|zumbi|monstro|sombra|escuro", re.I)
CALM = re.compile(r"calma|sorr|abraç|alívio|paz|segur", re.I)


def suggest_shots(script, *, target_duration=None):
    """Cria planos editoriais a partir de linhas não vazias.

    Mantém as chaves text/shot/reason do diretor anterior e acrescenta
    duração, intensidade, câmera, áudio, transição e índices. As durações
    são estimativas, não alinhamento de fala nem timestamps de áudio.
    """
    if not isinstance(script, str):
        raise TypeError("script deve ser texto")
    if target_duration is not None and (isinstance(target_duration, bool) or
            not isinstance(target_duration, (int, float)) or not 0 < target_duration <= 3600):
        raise ValueError("target_duration deve estar entre 0 e 3600 segundos")
    lines = [line.strip() for line in script.splitlines() if line.strip()]
    if not lines:
        return []
    result = []
    previous = None
    for index, line in enumerate(lines):
        kind, reason = next(((kind, reason) for pattern, kind, reason in RULES
                             if re.search(pattern, line, re.I)), ("medium", "Plano médio padrão"))
        danger = bool(DANGER.search(line))
        sound = bool(SOUND.search(line))
        intensity = "high" if danger or sound else "low" if CALM.search(line) else "medium"
        if previous == kind and kind != "detail":
            kind = {"medium": "close", "close": "medium", "wide": "medium", "tracking": "medium"}.get(kind, kind)
            reason += "; variar escala em relação ao plano anterior"
        camera = {"detail": "slow_push", "close": "slow_push", "tracking": "follow",
                  "wide": "slow_pan", "medium": "static"}[kind]
        transition = "cut" if index else "fade_in"
        if sound and index:
            transition = "hard_cut"
        duration = max(2.0, min(8.0, 1.3 + len(line.split()) / 2.8))
        result.append({"index": index + 1, "text": line, "shot": kind, "reason": reason,
                       "duration_estimate": round(duration, 2), "intensity": intensity,
                       "camera_suggestion": camera, "transition_suggestion": transition,
                       "sound_cue": "impact" if sound else "tension" if danger else None})
        previous = kind
    if target_duration is not None:
        factor = target_duration / sum(item["duration_estimate"] for item in result)
        for item in result:
            item["duration_estimate"] = round(item["duration_estimate"] * factor, 3)
    return result
