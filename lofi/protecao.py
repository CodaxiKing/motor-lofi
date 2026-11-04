"""Arquivos travados de uma série (episódio publicado ou cânone fixo): ninguém no motor grava neles.

Arquivo da série: series/<serie>/protegidos.json
{
  "motivo": "episódio 1 publicado: cânone fixo",
  "arquivos": {"ep01.json": "<sha256>", "ep01_roteiro.md": "<sha256>"},
  "trechos": {"biblia.md": ["- EP 1: 18:50, o Léo repõe...", "| 1 | 0 | início | montado | ..."]}   # linhas que não podem mudar
}

Todo comando que grava roteiro (ganchos, validador com correção, literal --aplicar) chama `bloquear(caminho)` antes.
`conferir(pasta)` refaz os hashes e confirma que nada mudou (usado nos testes e no fim de cada tarefa).

    python3 -m lofi.protecao conferir series/o-ultimo-estoque
    python3 -m lofi.protecao travar  series/o-ultimo-estoque ep01.json ep01_roteiro.md   (grava os hashes atuais)
"""
import hashlib, json, os, sys


class Protegido(PermissionError):
    pass


def sha256(caminho):
    """Hash do conteúdo com as quebras de linha normalizadas (CRLF do Windows = LF do git/CI): o mesmo arquivo dá o
    mesmo hash em qualquer máquina; qualquer outra mudança de byte muda o hash."""
    return hashlib.sha256(open(caminho, "rb").read().replace(b"\r\n", b"\n")).hexdigest()


def _cfg(pasta):
    p = os.path.join(pasta, "protegidos.json")
    return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else None


def protegido(caminho):
    """True se o arquivo está travado na série dele."""
    caminho = os.path.abspath(caminho); cfg = _cfg(os.path.dirname(caminho))
    return bool(cfg and os.path.basename(caminho) in cfg.get("arquivos", {}))


def bloquear(caminho, novo_texto=None):
    """Levanta Protegido se `caminho` é travado, ou se `novo_texto` apaga/altera um trecho travado do arquivo."""
    caminho = os.path.abspath(caminho); cfg = _cfg(os.path.dirname(caminho))
    if not cfg: return
    nome = os.path.basename(caminho)
    if nome in cfg.get("arquivos", {}):
        raise Protegido(f"{nome} está travado ({cfg.get('motivo', 'protegidos.json')}): o motor não grava nele")
    if novo_texto is not None:
        linhas = set(novo_texto.split("\n"))
        for t in cfg.get("trechos", {}).get(nome, []):
            if t not in linhas: raise Protegido(f"{nome}: a linha travada mudou ou sumiu: {t[:70]}...")


def conferir(pasta):
    """Lista de problemas (vazia = tudo idêntico ao travado)."""
    cfg = _cfg(pasta); out = []
    if not cfg: return out
    for nome, h in cfg.get("arquivos", {}).items():
        p = os.path.join(pasta, nome)
        if not os.path.isfile(p): out.append(f"{nome}: sumiu")
        elif sha256(p) != h: out.append(f"{nome}: o conteúdo mudou (hash diferente)")
    for nome, linhas in cfg.get("trechos", {}).items():
        p = os.path.join(pasta, nome)
        txt = open(p, encoding="utf-8").read().split("\n") if os.path.isfile(p) else []
        for t in linhas:
            if t not in txt: out.append(f"{nome}: a linha travada mudou: {t[:70]}")
    return out


def travar(pasta, nomes, motivo="cânone fixo", trechos=None):
    cfg = _cfg(pasta) or {}
    cfg["motivo"] = motivo
    cfg.setdefault("arquivos", {}).update({n: sha256(os.path.join(pasta, n)) for n in nomes})
    if trechos: cfg.setdefault("trechos", {}).update(trechos)
    json.dump(cfg, open(os.path.join(pasta, "protegidos.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    return cfg


if __name__ == "__main__":
    cmd, pasta = sys.argv[1], sys.argv[2]
    if cmd == "travar": print(json.dumps(travar(pasta, sys.argv[3:]), ensure_ascii=False, indent=1))
    else:
        probs = conferir(pasta)
        print("\n".join(probs) if probs else "intacto: todos os arquivos e trechos travados estão idênticos")
        sys.exit(1 if probs else 0)
