r"""reserva_shorts_drive.py — Shorts prontos e NÃO postados que passam de 7 dias de reserva vão pro Drive (12/11, dona:
"sim, pode mandar as reservas pra lá"). Fila tinha 633 Shorts / 17 GB no PC e o disco segurava a postagem dos longos.

Por canal: guarda no PC os N mais VELHOS (o postador posta do mais velho pro mais novo), com N = 7 x por_dia do canal
(config/parceiro.json; mín. 7). O resto sobe pro Drive (rclone copy + conferência por tamanho) e só então o video.mp4
sai do PC. Deixa _NO_DRIVE.txt com o caminho; o postador traz de volta na hora de postar (catalogo.baixar / igual aos
postados). Shorts marcados "dispensada"/"reprovado" (não vão subir) também vão, sem limite.
Só mídia sai; jsons, capa e textos ficam. RESERVA_SHORTS_DRIVE=0 desliga.

    python reserva_shorts_drive.py --simular
    python reserva_shorts_drive.py
"""
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mover_shorts_postados as msp  # noqa: E402  (mesma base, mesmo teste de "postado", mesmo rclone)

DESTINO = "manhwa-drive:videos-backup/parceiro/_reserva_1112"
PARCEIRO = Path(r"D:\recapd-ambientes\producao\config\parceiro.json")
LOG = Path(r"D:\tmp\reserva_shorts_drive.log")
LISTA = Path(r"D:\tmp\reserva_shorts_lista.txt")
DIAS = 7


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    print(linha, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _meta(p):
    for nome in ("postar.json", "metadata.json"):
        try:
            return json.loads((p / nome).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
    return {}


def main(simular):
    if os.environ.get("RESERVA_SHORTS_DRIVE", "1") == "0":
        return
    cfg = json.loads(PARCEIRO.read_text(encoding="utf-8"))
    por_dia = {d["canal"]: d.get("por_dia", 1) for d in cfg.get("pt", [])}
    por_dia.update({d["canal"]: d.get("por_dia", 1) for d in (cfg.get("idiomas") or {}).values()})
    ja = msp.postados()
    por_canal, sair = defaultdict(list), []
    for p in msp.BASE.iterdir():
        v = p / "video.mp4"
        if not p.is_dir() or p.name.lower() in ja or not v.exists():
            continue
        m = _meta(p)
        rev = str(m.get("revisao") or m.get("estado") or "")
        # "dispensada" = pulou a trava de nudez e ESTÁ pronto pra postar (fila normal); só reprovado não sobe nunca
        if rev.startswith("reprovado"):
            sair.append(p)
            continue
        por_canal[str(m.get("canal") or "?")].append(p)
    for canal, pastas in por_canal.items():
        fica = max(DIAS, DIAS * int(por_dia.get(canal, 1)))
        pastas.sort(key=lambda p: (p / "video.mp4").stat().st_mtime)  # mais velho primeiro = posta antes
        sair += pastas[fica:]
    tam = sum((p / "video.mp4").stat().st_size for p in sair)
    log(f"{len(sair)} Shorts fora da reserva de {DIAS} dias ({tam / 1e9:.1f} GB) — "
        f"{sum(len(v) for v in por_canal.values())} na fila em {len(por_canal)} canais")
    if simular or not sair:
        return
    LISTA.write_text("\n".join(f"{p.name}/video.mp4" for p in sair) + "\n", encoding="utf-8")
    rc, saida = msp.rc("copy", str(msp.BASE), DESTINO, "--files-from", str(LISTA), "--transfers", "4")
    log(f"copy rc={rc} {saida.strip()[-200:]}")
    rc, saida = msp.rc("lsjson", DESTINO, "-R", "--files-only", "--no-mimetype", "--no-modtime")
    no_drive = {}
    if rc == 0:
        try:
            no_drive = {x["Path"].replace("\\", "/"): x["Size"] for x in json.loads(saida[saida.index("["):])}
        except (ValueError, KeyError):
            no_drive = {}
    liberado = n = 0
    for p in sair:
        rel, v = f"{p.name}/video.mp4", p / "video.mp4"
        if not v.exists():  # 12/11: o postador subiu/moveu este Short durante a cópia — nada a fazer
            continue
        if no_drive.get(rel) == v.stat().st_size:
            liberado += v.stat().st_size
            v.unlink()
            (p / "_NO_DRIVE.txt").write_text(f"{DESTINO}/{rel}\n", encoding="utf-8")
            n += 1
    log(f"no Drive e fora do PC: {n} de {len(sair)}, {liberado / 1e9:.1f} GB liberados")


if __name__ == "__main__":
    main("--simular" in sys.argv)
