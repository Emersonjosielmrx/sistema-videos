r"""github_agora.py — manda AGORA pro GitHub só os arquivos que acabei de mexer (13/11/2026).

Dona 13/11: "quando alterar arquivos já altere também o mesmo arquivo no GitHub imediatamente; tem outro agente
trabalhando lá e é importante manter vocês 2 sincronizados". O salvar_github.py remonta os 35 projetos (~25 min):
não serve pra "imediatamente". Este manda só os caminhos pedidos, em segundos, com a MESMA limpeza de segredos.

    python github_agora.py "mensagem curta" D:\caminho\arquivo1.py D:\caminho\arquivo2.json ...
    python github_agora.py --desde 60 "mensagem"      # tudo que mudou nos projetos nos últimos 60 min

Regras (as mesmas do salvar_github): só extensão de código/texto, < 2 MB, fora de pasta proibida (secrets, cofre,
perfis...); o conteúdo passa por limpar(); cada arquivo é varrido de novo e NÃO vai se sobrou cara de segredo.
Antes de enviar faz `git pull --rebase` (o agente online pode ter mexido no main); conflito = não envia e avisa.
Arquivo apagado no D: sai do repositório. Log: D:\tmp\github_agora.log.
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import salvar_github as sg  # noqa: E402

LOG = Path(r"D:\tmp\github_agora.log")


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")
    if sys.stdout:
        try:
            print(linha, flush=True)
        except (OSError, ValueError):
            pass


def _rel(p):
    """Caminho no repositório (projeto/…, raiz_D/… ou os recados na raiz) ou None se o arquivo não é espelhado."""
    p = Path(p).resolve()
    partes = p.parts
    if len(partes) < 2 or partes[0].upper() != "D:\\":
        return None
    if partes[1:3] == ("video-fila", "agentes") and p.name in sg.RECADOS_RAIZ:
        return Path(p.name)
    if len(partes) == 2:
        return Path("raiz_D") / p.name if p.name in sg.RAIZ_SOLTOS else None
    if partes[1] not in sg.PROJETOS:
        return None
    # mesmas regras de pasta do espelho completo: nenhuma pasta do caminho pode ser proibida
    pai = Path("D:/") / partes[1]
    for d in partes[2:-1]:
        if not sg._pasta_vai(str(pai), d):
            return None
        pai = pai / d
    return Path(*partes[1:])


def recentes(minutos):
    """Arquivos dos projetos mexidos nos últimos N minutos (mesma varredura do espelho, só olhando a data)."""
    corte = time.time() - minutos * 60
    out = []
    for proj in sg.PROJETOS:
        raiz = Path("D:/") / proj
        if not raiz.is_dir():
            continue
        for r, ds, fs in os.walk(raiz):
            if sg.MARCA_PERFIL & set(fs):
                ds[:] = []
                continue
            ds[:] = [d for d in ds if sg._pasta_vai(r, d)]
            for f in fs:
                c = os.path.join(r, f)
                try:
                    if os.path.getmtime(c) >= corte and sg._vai(c, f):
                        out.append(c)
                except OSError:
                    pass
    return out


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    if os.environ.get("SALVAR_GITHUB", "1") == "0":
        return 0
    if args[:1] == ["--desde"]:
        caminhos, msg = recentes(int(args[1])), (args[2] if len(args) > 2 else "arquivos alterados")
    else:
        if len(args) < 2:
            print(__doc__)
            return 2
        msg, caminhos = args[0], args[1:]
    if not (sg.DESTINO / ".git").exists():
        log("repositório local não existe — rode o salvar_github.py uma vez")
        return 1
    foi, fora, barrados = [], [], []
    for c in caminhos:
        p = Path(c)
        rel = _rel(p)
        if rel is None or (p.exists() and not sg._vai(str(p), p.name)):
            fora.append(p.name)
            continue
        dst = sg.DESTINO / rel
        if not p.exists():  # apagado no D: sai da cópia
            if dst.exists():
                dst.unlink()
                foi.append(str(rel).replace("\\", "/"))
            continue
        try:
            limpo = sg.limpar(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            fora.append(p.name)
            continue
        m = sg.SOBROU.search(limpo) or (sg.SOBROU_PUBLICO.search(limpo) if sg.LIMPEZA_EXTRA else None)
        if m:
            barrados.append(f"{rel}: {m.group(0)[:10]}…")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or dst.read_text(encoding="utf-8", errors="replace") != limpo:
            dst.write_text(limpo, encoding="utf-8")
        foi.append(str(rel).replace("\\", "/"))
    if barrados:
        log(f"BARRADOS (cara de segredo, NÃO enviados): {'; '.join(barrados[:8])}")
    if not foi:
        log(f"nada a enviar ({len(fora)} fora do espelho: {', '.join(fora[:6])})")
        return 0 if not barrados else 3
    sg.git("add", "--", *foi)
    if not sg.git("status", "--porcelain", "--", *foi).strip():
        log(f"{len(foi)} arquivo(s) já iguais no repositório")
        return 0
    sg.git("commit", "-q", "-m", f"{msg} ({datetime.now():%d/%m %H:%M})", "--", *foi)
    try:
        sg.git("pull", "--rebase", "--autostash", "-q", "origin", "main")
    except RuntimeError as e:
        sg.git("rebase", "--abort", ok=True)
        log(f"[!] o main do GitHub mudou e não deu pra juntar sozinho — commit ficou local, NÃO enviado: {str(e)[-160:]}")
        return 4
    sg.git("push", "-q", "origin", "main")
    log(f"enviado ({len(foi)}): {', '.join(foi[:8])}{'…' if len(foi) > 8 else ''} — {msg}")
    return 0 if not barrados else 3


if __name__ == "__main__":
    sys.exit(main())
