"""Gera skills/<nome>.zip a partir de skills/<nome>/ (formato aceito nas configurações de skills do Claude).

    python3 tools/empacotar_skills.py            -> regrava os .zip que mudaram
    python3 tools/empacotar_skills.py --checar   -> só confere (código 1 se algum .zip estiver desatualizado; usado no CI)

Os zips são determinísticos (data e permissões fixas): o mesmo conteúdo sempre gera o mesmo arquivo.
"""
import os, sys, io, zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(RAIZ, "skills")
DATA = (2026, 1, 1, 0, 0, 0)


def montar(nome):
    pasta = os.path.join(SKILLS, nome)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        d = zipfile.ZipInfo(nome + "/", DATA); d.external_attr = (0o40755 << 16) | 0x10; z.writestr(d, b"")
        for raiz, dirs, arqs in os.walk(pasta):
            dirs.sort()
            for a in sorted(arqs):
                if a.startswith(".") or a.endswith(".pyc"): continue
                cam = os.path.join(raiz, a)
                info = zipfile.ZipInfo(os.path.relpath(cam, SKILLS).replace(os.sep, "/"), DATA)
                info.external_attr = 0o100644 << 16; info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, open(cam, "rb").read())
    return buf.getvalue()


def conteudo(dados):
    """Arquivos e conteúdos de um zip (ignora data e compressão) para comparar."""
    with zipfile.ZipFile(io.BytesIO(dados)) as z:
        return {n: z.read(n) for n in z.namelist() if not n.endswith("/")}


if __name__ == "__main__":
    checar = "--checar" in sys.argv
    nomes = sorted(n for n in os.listdir(SKILLS) if os.path.isfile(os.path.join(SKILLS, n, "SKILL.md")))
    falhas = []
    for nome in nomes:
        novo = montar(nome); destino = os.path.join(SKILLS, nome + ".zip")
        atual = open(destino, "rb").read() if os.path.exists(destino) else None
        igual = atual is not None and conteudo(atual) == conteudo(novo)
        if checar:
            if not igual: falhas.append(nome)
        elif not igual:
            open(destino, "wb").write(novo); print(f"atualizado: skills/{nome}.zip")
    if checar:
        for f in falhas: print(f"[ERRO] skills/{f}.zip desatualizado: rode python3 tools/empacotar_skills.py")
        print("zips em dia" if not falhas else f"{len(falhas)} zip(s) desatualizado(s)")
        sys.exit(1 if falhas else 0)
