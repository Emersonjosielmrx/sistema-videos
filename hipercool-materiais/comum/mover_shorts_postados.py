r"""mover_shorts_postados.py — sobe pro Drive os Shorts de parceiro JÁ POSTADOS e só então apaga do PC (10/11/2026).

Dona 10/11: "mova pra o drive os já postados". Os 1.441 Shorts postados de animes recap\shorts não saíam porque o
BackupDriveVideos sobe só 1-10 por hora (cota da chave pública do Drive). Aqui sobe em LOTE (rclone copy com
--files-from), confere (rclone check --one-way --size-only) e apaga do PC SÓ o video.mp4 que bateu no Drive.
Os jsons/capa da pasta ficam (pequenos; o postador ainda lê). Não-postados NUNCA saem (são a fila).

Postado = a pasta aparece no D:\postador-de-videos\logs\uploads_ledger.jsonl (mesmo teste da análise de 10/11).
Destino: manhwa-drive:videos-backup/parceiro/_postados_lote_1011/<pasta>/video.mp4

    python mover_shorts_postados.py [--max N] [--so-listar]
Retomável: o que já subiu e conferiu é pulado; log em D:\tmp\mover_shorts_postados.log
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(r"D:\hipercool-materiais\animes recap\shorts")
LEDGER = Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl")
RCLONE = r"D:\tools\rclone.exe"
DESTINO = "manhwa-drive:videos-backup/parceiro/_postados_lote_1011"
LOG = Path(r"D:\tmp\mover_shorts_postados.log")
LISTA = Path(r"D:\tmp\mover_shorts_lista.txt")


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def postados():
    nomes = set()
    for linha in LEDGER.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        c = d.get("caminho") or ""
        if "animes recap" in c and "shorts" in c:
            nomes.add(Path(c).parent.name.lower())
    return nomes


def rc(*args, timeout=7200):
    r = subprocess.run([RCLONE, *args, "--tpslimit", "4", "--tpslimit-burst", "4", "--retries", "5",
                        "--low-level-retries", "20"], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, creationflags=0x08000000)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    maximo = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10 ** 9
    ja = postados()
    alvo = [p for p in sorted(BASE.iterdir()) if p.is_dir() and p.name.lower() in ja and (p / "video.mp4").exists()]
    alvo = alvo[:maximo]
    tam = sum((p / "video.mp4").stat().st_size for p in alvo)
    log(f"{len(alvo)} Shorts postados com video.mp4 no PC ({tam / 1e9:.1f} GB)")
    if "--so-listar" in sys.argv or not alvo:
        return
    LISTA.write_text("\n".join(f"{p.name}/video.mp4" for p in alvo) + "\n", encoding="utf-8")
    rcode, saida = rc("copy", str(BASE), DESTINO, "--files-from", str(LISTA), "--transfers", "4")
    log(f"copy rc={rcode} {saida.strip()[-300:]}")
    # 10/11: o "rclone check --files-from" passou de 25 min com a cota do Drive (morto antes de gravar — nada apagado).
    # Conferência por 1 listagem só do destino: mesmo caminho + mesmo tamanho em bytes = subiu inteiro.
    rcode, saida = rc("lsjson", DESTINO, "-R", "--files-only", "--no-mimetype", "--no-modtime")
    log(f"lsjson rc={rcode}")
    no_drive = {}
    if rcode == 0:
        try:
            no_drive = {x["Path"].replace("\\", "/"): x["Size"] for x in json.loads(saida[saida.index("["):])}
        except (ValueError, KeyError):
            no_drive = {}
    ok = {f"{p.name}/video.mp4" for p in alvo
          if no_drive.get(f"{p.name}/video.mp4") == (p / "video.mp4").stat().st_size}
    apagados = liberado = 0
    for p in alvo:
        rel = f"{p.name}/video.mp4"
        if rel in ok:
            v = p / "video.mp4"
            liberado += v.stat().st_size
            v.unlink()
            (p / "_NO_DRIVE.txt").write_text(f"{DESTINO}/{rel}\n", encoding="utf-8")
            apagados += 1
    log(f"apagados {apagados} de {len(alvo)} (só os conferidos), {liberado / 1e9:.1f} GB liberados; "
        f"{len(alvo) - apagados} ficam no PC (não conferidos: roda de novo depois)")


if __name__ == "__main__":
    main()
