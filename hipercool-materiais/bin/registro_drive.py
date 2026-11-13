"""registro_drive.py — cada arquivo que sai do PC pro Google Drive fica anotado NA PASTA de onde saiu, em _NO_DRIVE.md
(dona 25/10/2026: "tem que documentar na pasta tudo que foi movido pro Drive; o script tem que fazer isso sempre").
Uma linha por arquivo: quando, nome, tamanho, caminho no Drive, quem mandou. O mapa geral continua em
D:\\video-fila\\MAPA_DRIVE.md (totais por pasta); este é o detalhe, junto do arquivo que sumiu.

Quem chama anotar() depois de cada envio confirmado: manhwa-react\\scripts\\backup_drive.py, fontes_drive.py (e o
anime\\limpar_source.py através dele), vozes_drive.py e amostras_drive.py.

    python registro_drive.py reconstruir   # anota o que já tinha ido antes deste registro existir
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ARQ = "_NO_DRIVE.md"
RCLONE = r"D:\tools\rclone.exe"
CABECALHO = """# No Google Drive

Arquivos desta pasta que foram pro Google Drive (anotado sozinho por D:\\hipercool-materiais\\bin\\registro_drive.py).
Trazer de volta um arquivo: `D:\\tools\\rclone.exe copyto "<no Drive>" "<esta pasta>\\<arquivo>"`
(ou drive.google.com, conta do rclone `manhwa-drive`, mesmo caminho sem o `manhwa-drive:`).

| quando | arquivo | MB | no Drive | quem mandou |
|---|---|---:|---|---|
"""


def anotar(local, drive, tamanho, quem, quando=None):
    """Acrescenta a linha no _NO_DRIVE.md da pasta do arquivo. Nunca levanta erro (o envio já aconteceu)."""
    try:
        local = Path(local)
        if not local.parent.is_dir():
            return  # a pasta inteira já não existe: não recria (a fila acharia que é item novo)
        md = local.parent / ARQ
        texto = md.read_text(encoding="utf-8") if md.exists() else CABECALHO
        if f"| {local.name} |" in texto and f"`{drive}`" in texto:
            return  # já anotado (reconstruir rodado de novo)
        quando = quando or time.strftime("%Y-%m-%d %H:%M")
        texto += f"| {quando} | {local.name} | {tamanho / 1e6:.1f} | `{drive}` | {quem} |\n"
        md.write_text(texto, encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        print(f"registro_drive: não anotou {local}: {type(e).__name__}: {e}", flush=True)


def _lsjson(remoto):
    # 02/11: --fast-list = poucas chamadas ao Drive (o cliente público do rclone estourava RATE_LIMIT_EXCEEDED)
    r = subprocess.run([RCLONE, "lsjson", "-R", "--fast-list", "--files-only", "--no-mimetype", remoto], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=3600, creationflags=0x08000000)
    return json.loads(r.stdout or "[]") if r.returncode == 0 else []


def reconstruir():
    """O que já estava no Drive antes do registro: manifesto do backup_drive + listagem das pastas espelhadas."""
    n = 0
    man = Path(r"D:\manhwa-react\logs\backup_drive.jsonl")
    if man.exists():
        for linha in man.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(linha)
            except ValueError:
                continue
            if r.get("drive") and r.get("local") and not Path(r["local"]).exists():
                anotar(r["local"], r["drive"], r.get("bytes") or 0, "backup_drive.py", (r.get("em") or "")[:16].replace("T", " "))
                n += 1
    base = "manhwa-drive:videos-backup/hipercool-materiais"
    for sub in ("anime", "models/rvc/vozes", "amostras_voz"):
        local_raiz = Path(r"D:\hipercool-materiais") / Path(sub)
        quem = {"anime": "fontes_drive.py", "models/rvc/vozes": "vozes_drive.py"}.get(sub, "amostras_drive.py")
        for it in _lsjson(f"{base}/{sub}"):
            local = local_raiz / Path(it["Path"])
            if not local.exists():
                anotar(local, f"{base}/{sub}/{it['Path']}", it.get("Size") or 0, quem,
                       (it.get("ModTime") or "")[:16].replace("T", " "))
                n += 1
    print(f"registro_drive: {n} arquivo(s) conferidos no registro das pastas", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.argv[1:2] == ["reconstruir"]:
        reconstruir()
    else:
        print(__doc__)
