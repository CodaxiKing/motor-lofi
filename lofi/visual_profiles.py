"""Perfis visuais opcionais; o perfil padrão preserva a imagem original."""
from dataclasses import dataclass, replace
from math import isfinite
from PIL import Image, ImageEnhance, ImageFilter

@dataclass(frozen=True)
class VisualProfile:
    name: str = "lofi_classic"
    saturation: float = 1.0
    contrast: float = 1.0
    brightness: float = 1.0
    shadow_strength: float = 0.0
    texture_strength: float = 0.0

    def __post_init__(self):
        for field in ("saturation", "contrast", "brightness", "shadow_strength", "texture_strength"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or not 0 <= value <= 3:
                raise ValueError(f"{field} deve ser finito entre 0 e 3")

PROFILES = {
    "lofi_classic": VisualProfile(),
    "cartoon_dark": VisualProfile("cartoon_dark", .83, 1.16, .91, .12, .07),
    "horror_illustrated": VisualProfile("horror_illustrated", .69, 1.32, .83, .19, .12),
    "cinematic_cartoon": VisualProfile("cinematic_cartoon", 1.09, 1.14, 1.02, .08, .05),
}

def resolve_profile(name="lofi_classic", overrides=None):
    if name not in PROFILES:
        raise ValueError(f"Perfil desconhecido: {name}. Opções: {', '.join(PROFILES)}")
    overrides = dict(overrides or {})
    unknown = set(overrides) - (set(VisualProfile.__dataclass_fields__) - {"name"})
    if unknown:
        raise ValueError(f"Campos inválidos: {', '.join(sorted(unknown))}")
    return replace(PROFILES[name], **overrides)

def apply_profile(img, profile):
    if profile == PROFILES["lofi_classic"]:
        return img
    out = ImageEnhance.Color(img).enhance(profile.saturation)
    out = ImageEnhance.Contrast(out).enhance(profile.contrast)
    out = ImageEnhance.Brightness(out).enhance(profile.brightness)
    if profile.shadow_strength:
        dark = ImageEnhance.Brightness(out).enhance(max(.05, 1 - profile.shadow_strength))
        out = Image.blend(out, dark, min(1, profile.shadow_strength))
    if profile.texture_strength:
        sharp = out.filter(ImageFilter.UnsharpMask(radius=1.6, percent=75))
        out = Image.blend(out, sharp, min(1, profile.texture_strength))
    return out
