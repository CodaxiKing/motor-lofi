"""Planejamento de atuação: ações, emoções e ritmo para o rig existente."""
import re

# Verbos no presente, passado, gerúndio e plural (roteiros costumam vir no presente: "João corre").
# Fronteira de palavra evita falsos positivos: "corredor", "segundo andar", "você está segura".
_A = r"(?:a|am|ou|aram|ando)"          # 1ª conjugação: anda, andam, andou, andaram, andando
_E = r"(?:e|em|eu|eram|endo)"          # 2ª conjugação: corre, correm, correu, correram, correndo
ACTION_RULES = (
    (r'\babrac(?:a|ou|ando)\b|\babraç(?:a|ou|ando)\b', 'hug', 'idle', 'happy'),
    (r'\babr(?:e|iu|indo)\b.*porta', 'open_door', 'idle', 'neutral'),
    (r'\bempurr(?:a|ou|ando)\b', 'push', 'idle', 'angry'),
    (rf"\bbat{_E}\b|batid|\btoc{_A} (?:a|na) porta", "knock", "idle", "tense"),
    (rf"\bcorr{_E}\b|\bfog(?:e|em)\b|\bfug(?:iu|iram|indo)\b|\bdispar{_A}\b", "run", "run", "fear"),
    (rf"\b(?:caminh|and|aproxim){_A}\b|passos", "walk", "walk", "neutral"),
    (rf"\b(?:apont|indic|mostr){_A}\b", "point", "idle", "neutral"),
    (rf"\bescond{_E}\b|\b(?:agach|abaix){_A}\b", "hide", "hide", "fear"),
    (rf"\bsent{_A}\b|\bsentad[ao]s?\b", "sit", "sit", "neutral"),
    (rf"\b(?:peg|agarr){_A}\b|\bsegur(?:am|ou|aram|ando)\b|\bsegura (?:a|o|um|uma|firme)\b", "hold", "idle", "neutral"),
    (rf"celular|telefone|\blig(?:ou|aram|ando)\b|\bliga para\b", "phone", "idle", "neutral"),
    (rf"\b(?:olh|observ|espi){_A}\b", "idle", "idle", "neutral"),
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
    prop = next((p for pat, p in ((r'\bchave\b', 'key'), (r'\blanterna\b', 'flashlight'),
                (r'\bcelular|telefone\b', 'phone'), (r'\brádio\b', 'radio'))
                if re.search(pat, lower) and action[0] in ('hold', 'phone', 'open_door')), None)
    return {'pose': action[0], 'movement': action[1], 'emotion': emotion, 'prop': prop,
            'look': -15 if re.search(rf'\bespi{_A}\b|\bescond{_E}\b|baixo', lower) else 0,
            'intensity': 'high' if emotion in ('fear', 'angry') else 'normal'}
