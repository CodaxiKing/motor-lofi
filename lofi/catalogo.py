"""Catálogo de tudo que o motor aceita, lido direto do código (fonte única para SPEC, skills e validador).

    python3 -m lofi.catalogo          -> imprime em markdown
    python3 -m lofi.catalogo --json   -> imprime em JSON
    python3 -m lofi.catalogo --md CATALOGO.md   -> regrava o arquivo (o CI confere se está em dia)
"""
import sys, json

TRANSITIONS = ["cut", "whip", "flash", "fade", "zoom", "glitch", "dip"]
VIEWS = ["front", "back", "side", "3q"]
WEATHER = {"rain": ["forte", "normal", "fraca", "nenhuma"], "time": ["dia", "entardecer", "amanhecer", "madrugada", "noite"]}
PROPS = ["radio", "flashlight", "phone", "handset", "key", "bag"]
BODIES = ["child", "old", "tall", "fat", "thin"]


def catalogo():
    from . import scenes, rig, detail, audio
    return {
        "cenarios": sorted(scenes.REGISTRY),
        "personagens": sorted(rig.CHARS),
        "poses": sorted(rig.POSES),
        "emocoes": sorted(rig.EMOTIONS),
        "vistas": VIEWS,
        "detalhes": sorted({s for s in detail.SUBJECTS if s.isascii()}),
        "sons": sorted(audio.SFX),
        "sons_com_duracao": sorted(audio.DURATION_SFX),
        "transicoes": TRANSITIONS,
        "acusticas": sorted(set(audio.ACOUSTICS) | {"abafado", "aberto"}),
        "objetos": PROPS,
        "corpos": BODIES,
        "clima": WEATHER,
    }


TITULOS = [("cenarios", "Cenários"), ("personagens", "Personagens prontos"), ("poses", "Poses"), ("emocoes", "Emoções"),
           ("vistas", "Vistas"), ("detalhes", "Planos de detalhe (`subject`)"), ("sons", "Sons (`sfx.name`)"),
           ("sons_com_duracao", "Sons que aceitam `dur`"), ("transicoes", "Transições"), ("acusticas", "Acústicas"),
           ("objetos", "Objetos na mão (`prop`)"), ("corpos", "Corpos (`body`)")]


def markdown(c):
    out = ["# Catálogo do motor", "",
           "Gerado por `python3 -m lofi.catalogo --md CATALOGO.md` a partir do código. Não edite à mão.", ""]
    for k, t in TITULOS:
        out += [f"**{t}** ({len(c[k])}): " + ", ".join(f"`{x}`" for x in c[k]), ""]
    out += ["**Clima:** `rain` = " + ", ".join(f"`{x}`" for x in c["clima"]["rain"]) +
            " · `time` = " + ", ".join(f"`{x}`" for x in c["clima"]["time"]) + " · `fog` e `snow` de 0 a 1", ""]
    from .mapa import MAPA
    out += ["## Marcas de posição por cenário", "",
            "Use no ator: `\"mark\": \"porta\"` (ou `[[0, \"fundo\"], [3, \"frente\"]]` para andar entre marcas). "
            "Imagem com todas: [`examples/mapa_cenarios.png`](examples/mapa_cenarios.png).", ""]
    for cena, m in MAPA.items():
        itens = [f"`{n}`" + (f" ({v['nota']})" if v.get("nota") else "") for n, v in m["marcas"].items()]
        out += [f"- **{cena if cena != '_travelling' else 'travelling (qualquer cenário com \"travelling\")'}:** " + ", ".join(itens)]
    out += ["", "## Travelling lateral (o cenário passa)", "",
            "No plano: `\"travelling\": 320` (px/s; positivo = eles vão para a direita) ou `{\"speed\": 320, \"frente\": true}`. "
            "Os personagens ficam no lugar correndo/andando (`walk`, `run`, `facing` no sentido do movimento) e o cenário rola: "
            "cidade (rua, rua_amanhecer, entrada_metro, posto, telhado), mata (floresta), túnel (metro), esgoto, ponte e "
            "interno (corredor, hospital, escola, delegacia, mercado, igreja, casa). Use as marcas de travelling acima.", ""]
    out += ["", "## Partes do corpo (mão e braço do personagem)", "",
            "Em rádio e planos de detalhe, `\"hand\": \"roberta\"` desenha o braço com a manga e a pele da ficha do personagem; "
            "`{\"of\": \"rafa\", \"at\": \"antena\"}` escolhe a posição; `false` tira a mão. No `olho`, a pele em volta é a do personagem.", ""]
    from .partes import POSICOES
    for cena, ps in POSICOES.items():
        out += [f"- **{cena}:** " + ", ".join(f"`{n}` ({p['nota']})" for n, p in ps.items())]
    out += [""]
    return "\n".join(out)


if __name__ == "__main__":
    c = catalogo()
    if "--json" in sys.argv: print(json.dumps(c, ensure_ascii=False, indent=1))
    elif "--md" in sys.argv:
        open(sys.argv[sys.argv.index("--md") + 1], "w", encoding="utf-8").write(markdown(c))
    else: print(markdown(c))
