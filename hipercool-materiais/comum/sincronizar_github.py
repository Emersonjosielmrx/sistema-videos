r"""sincronizar_github.py — junta no D: o que o agente online mudou no GitHub, sem perder o que mudou aqui (13/11, dona:
"sincronize com os arquivos do GitHub; o modelo daqui e o de lá melhoraram muita coisa; veja o que mudou em cada
arquivo e quais alteraram os mesmos, e mescle").

Para cada arquivo que o ramo do agente mudou em relação à BASE (o commit do nosso último envio):
  - só lá mudou (o D: ainda igual à base)        -> aplica a versão de lá no D:
  - só aqui mudou (lá igual à base)              -> não mexe
  - os dois mudaram                               -> mescla de 3 vias (git merge-file): sem conflito = aplica; com
                                                     conflito = NÃO aplica, deixa <arquivo>.conflito no D: e lista
  - igual dos dois lados                          -> nada
Antes de gravar, guarda o original em <arquivo>.antes_sync_<data>. Arquivo com <SEGREDO_REMOVIDO> NUNCA vai pro D:
direto (a versão de lá tem as chaves tiradas): só a mescla 3 vias, que mantém as chaves do D:.

    python sincronizar_github.py <ramo> --ver     # só mostra
    python sincronizar_github.py <ramo>           # aplica
"""
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

REPO = Path(r"D:\github_sistema")
D = Path("D:/")
LOG = Path(r"D:\tmp\sincronizar_github.log")


def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True, encoding="utf-8",
                          errors="replace").stdout


def mostrar(rev, caminho):
    r = subprocess.run(["git", "-C", str(REPO), "show", f"{rev}:{caminho}"], capture_output=True)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None


def log(m):
    print(m, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M}] {m}\n")


def main(ramo, ver):
    base = git("merge-base", "main", f"origin/{ramo}").strip()
    arquivos = [l for l in git("diff", "--name-only", base, f"origin/{ramo}").splitlines() if l.strip()]
    tag = datetime.now().strftime("%m%d_%H%M")
    res = {"só lá (aplicado)": [], "mesclado": [], "conflito": [], "só aqui (mantido)": [], "igual": [], "novo": []}
    for rel in arquivos:
        d_arq = D / rel
        base_txt, la_txt = mostrar(base, rel), mostrar(f"origin/{ramo}", rel)
        if la_txt is None:
            continue
        aqui_txt = d_arq.read_text(encoding="utf-8", errors="replace") if d_arq.exists() else None
        if aqui_txt is None:
            res["novo"].append(rel)
            if not ver and "<SEGREDO_REMOVIDO>" not in la_txt:
                d_arq.parent.mkdir(parents=True, exist_ok=True)
                d_arq.write_text(la_txt, encoding="utf-8")
            continue
        # a base do GitHub tem as chaves tiradas: compara sem isso
        if aqui_txt == la_txt:
            res["igual"].append(rel)
            continue
        if base_txt is not None and aqui_txt == base_txt and "<SEGREDO_REMOVIDO>" not in la_txt:
            res["só lá (aplicado)"].append(rel)
            if not ver:
                (d_arq.parent / (d_arq.name + f".antes_sync_{tag}")).write_text(aqui_txt, encoding="utf-8")
                d_arq.write_text(la_txt, encoding="utf-8")
            continue
        if base_txt is not None and la_txt == base_txt:
            res["só aqui (mantido)"].append(rel)
            continue
        with tempfile.TemporaryDirectory() as t:
            a, b, c = Path(t, "aqui"), Path(t, "base"), Path(t, "la")
            a.write_text(aqui_txt, encoding="utf-8")
            b.write_text(base_txt or "", encoding="utf-8")
            c.write_text(la_txt, encoding="utf-8")
            r = subprocess.run(["git", "merge-file", "-p", "-L", "D:", "-L", "base", "-L", "github", str(a), str(b),
                                str(c)], capture_output=True)
            junto = r.stdout.decode("utf-8", "replace")
        if r.returncode == 0 and "<SEGREDO_REMOVIDO>" not in junto.replace(aqui_txt, ""):
            res["mesclado"].append(rel)
            if not ver:
                (d_arq.parent / (d_arq.name + f".antes_sync_{tag}")).write_text(aqui_txt, encoding="utf-8")
                d_arq.write_text(junto, encoding="utf-8")
        else:
            res["conflito"].append(rel)
            if not ver:
                (d_arq.parent / (d_arq.name + f".conflito_{tag}")).write_text(junto, encoding="utf-8")
    for k, v in res.items():
        log(f"{k}: {len(v)}" + ("".join(f"\n   - {x}" for x in v) if v and k != "igual" else ""))
    return res


if __name__ == "__main__":
    main(sys.argv[1], "--ver" in sys.argv)
