"""pc2_recapd.py — o lado de cá do PC2 para o recap de anime (dono 17/10/2026: "o noturno deve passar para o PC2 e
usar o Google Drive lá pra não ocupar o disco; mudar de modo noturno pra modo OCIOSO: medir a máquina e começar uma
produção sempre que possível"; "deveria atualizar automaticamente, o hipercool já tem script que faz isso").

Cópia adaptada de D:\\hipercool-videos\\bin\\pc2.py (sincronizar_bin / rodando). Só mexe em C:\\recapd-e-animes do PC2
(única pasta liberada pelo dono lá; o resto do PC2 é do hipercool — NUNCA matar pythonw lá).

    python pc2_recapd.py sync      # manda pro PC2 o bin/ do recapd que mudou (tamanho/data)
    python pc2_recapd.py medir     # o PC2 está ocioso? (CPU, RAM, disco, render do hipercool/anime rodando)
"""
import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HOST = "pc2"
BIN = Path(r"D:\recapd-ambientes\producao\bin")
R_BIN = "C:/recapd-e-animes/bin"
# limites do modo ocioso: só começa render no PC2 se TUDO isto valer
CPU_MAX = 40          # % médio
RAM_MIN_GB = 4
DISCO_MIN_GB = 8
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _ssh(cmd, timeout=120, entrada=None):
    return subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOST, cmd], input=entrada,
                          capture_output=True, timeout=timeout, creationflags=_SEM_JANELA)


def _ps(script, timeout=120):
    r = _ssh("powershell -NoProfile -EncodedCommand " + base64.b64encode(script.encode("utf-16-le")).decode(),
             timeout=timeout)
    return r.returncode, (r.stdout or b"").decode("utf-8", "replace")


def _bin_local():
    out = {}
    for p in BIN.iterdir():
        n = p.name
        # "_" = rascunho; _whisper_sub.py é exceção (o anime_fetch roda ele pro Whisper: sem ele o PC2 ficava sem transcrição)
        if not p.is_file() or (n.startswith("_") and n != "_whisper_sub.py") or ".bak" in n or ".bkp" in n or not n.endswith((".py", ".json", ".ps1", ".bat")):
            continue
        st = p.stat()
        out[n] = (st.st_size, int(st.st_mtime))
    return out


def _bin_remoto():
    rc, txt = _ps("Get-ChildItem -LiteralPath 'C:\\recapd-e-animes\\bin' -File | ForEach-Object "
                  "{ $_.Name + '|' + $_.Length + '|' + [int64]($_.LastWriteTimeUtc - [datetime]'1970-01-01').TotalSeconds }")
    if rc != 0:
        return None
    out = {}
    for l in txt.splitlines():
        p = l.strip().split("|")
        if len(p) == 3 and p[1].isdigit():
            out[p[0]] = (int(p[1]), int(p[2]))
    return out


def sincronizar_bin():
    """(ok, recado). Arquivo novo ou com tamanho/data diferente vai por tar dentro do ssh (o tar preserva a data,
    então a rodada seguinte não copia de novo). Nunca entra config/, secrets/, workspace/."""
    local, remoto = _bin_local(), _bin_remoto()
    if remoto is None:
        return False, "pc2: não consegui listar C:\\recapd-e-animes\\bin"
    mudou = sorted(n for n, (tam, data) in local.items()
                   if n not in remoto or remoto[n][0] != tam or data > remoto[n][1] + 2)
    if not mudou:
        return True, f"pc2: bin já igual ({len(local)} conferidos)"
    lista = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8", newline="\n")
    lista.write("".join(n + "\n" for n in mudou))
    lista.close()
    try:
        tar = subprocess.Popen(["tar", "-cf", "-", "-C", str(BIN), "-T", lista.name], stdout=subprocess.PIPE,
                               creationflags=_SEM_JANELA)
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", HOST, f"tar -xf - -C {R_BIN}"], stdin=tar.stdout,
                           capture_output=True, timeout=1800, creationflags=_SEM_JANELA)
        tar.stdout.close()
        ok = tar.wait() == 0 and r.returncode == 0
    finally:
        Path(lista.name).unlink(missing_ok=True)
    return ok, f"pc2: {len(mudou)} arquivos {'atualizados' if ok else 'FALHOU copiar'} ({', '.join(mudou[:10])})"


def medir():
    """{"ocioso": bool, "motivo": str, cpu, ram_gb, disco_gb, renders}. 18/10: é o medidor ÚNICO (maquinas.medir("pc2"),
    mesmos limites: CPU 40%, RAM 4 GB, disco C: 8 GB, render de hipercool/anime lá ou vez reservada pro PC2)."""
    import maquinas
    return maquinas.medir(HOST)


if __name__ == "__main__":
    acao = sys.argv[1] if len(sys.argv) > 1 else "medir"
    if acao == "sync":
        print(sincronizar_bin()[1])
    else:
        print(json.dumps(medir(), ensure_ascii=False))
