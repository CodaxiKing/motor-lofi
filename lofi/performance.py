"""Planejamento de atuação: ações, emoções e ritmo para o rig existente."""
import re

ACTION_RULES = (
    (r"bateu|batid|tocou a porta", "knock", "idle", "tense"),
    (r"correu|correndo|fugiu|fugindo|disparou", "run", "run", "fear"),
    (r"caminhou|andou|aproximou|passos", "walk", "walk", "neutral"),
    (r"apontou|indicou|mostrou", "point", "idle", "neutral"),
    (r"escondeu|agachou|abaixou", "hide", "hide", "fear"),
    (r"sentou|sentada|sentado", "sit", "sit", "neutral"),
    (r"segurou|pegou|agarrou", "hold", "idle", "neutral"),
    (r"celular|telefone|ligou", "phone", "idle", "neutral"),
    (r"olhou|observou|espiou", "idle", "idle", "neutral"),
)
EMOTION_RULES = ((r"medo|pânico|apavor|assust|terror", "fear"),
                 (r"chor|triste|luto", "sad"),
                 (r"raiva|furios|grit", "angry"),
                 (r"sorr|alegr|feliz", "happy"))

def plan_performance(text):
    """Plano de atuação determinístico. Mantém o rig e não inventa áudio."""
    if not isinstance(text, str):
        raise TypeError('text deve ser str')
    lower = text.lower()
    action = next(((pose, movement, default) for pat, pose, movement, default in ACTION_RULES
                   if re.search(pat, lower)), ('idle', 'idle', 'neutral'))
    emotion = next((emo for pat, emo in EMOTION_RULES if re.search(pat, lower)), action[2])
    return {'pose': action[0], 'movement': action[1], 'emotion': emotion,
            'look': -15 if re.search(r'espiou|escondeu|baixo', lower) else 0,
            'intensity': 'high' if emotion in ('fear', 'angry') else 'normal'}
