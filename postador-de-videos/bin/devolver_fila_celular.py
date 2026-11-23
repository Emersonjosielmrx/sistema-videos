"""devolver_fila_celular.py — 23/11: a fila dos celulares está PARADA desde 17/11 (fila_celulares\\PARAR.txt) e o
youtube_web_poster seguiu mandando Shorts pra lá e gravando posted_url="fila_celular:..." no postar.json — o Short
ficava "postado" sem nunca ter saído (180 presos). Este script devolve cada um à fila normal do PC:
  - tira posted_url/agendado_para/canal_postado do postar.json da pasta ORIGINAL (só se o posted_url é o desta fila)
  - move o pedido de fila_celulares\\pendentes pra fila_celulares\\devolvidos_23nov (não apaga) e a cópia do vídeo
    da fila (videos\\<id>.mp4) é apagada só se o original ainda existir (ou o _NO_DRIVE.txt disser que está no Drive)
  - registra cada um em logs\\devolver_fila_celular.jsonl
    python devolver_fila_celular.py            # ensaio
    python devolver_fila_celular.py --fazer
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

FILA = Path(r"D:\projeto celular sub controle\fila_celulares")
DEST = FILA / "devolvidos_23nov"
LOG = Path(r"D:\postador-de-videos\logs\devolver_fila_celular.jsonl")


def main(fazer):
    n_ok = n_pula = 0
    motivos = {}
    for pedido in sorted((FILA / "pendentes").glob("*.json")):
        try:
            d = json.loads(pedido.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        orig = Path(d.get("video_original") or "")
        pj = orig.parent / "postar.json"
        chave = f"fila_celular:{pedido.name}"
        motivo = None
        if not pj.exists():
            motivo = "sem postar.json na pasta original"
        else:
            try:
                p = json.loads(pj.read_text("utf-8"))
            except (OSError, ValueError):
                p, motivo = {}, "postar.json ilegível"
            if not motivo and str(p.get("posted_url") or "") != chave:
                motivo = f"posted_url é outro ({str(p.get('posted_url'))[:40]})"
        if motivo:
            n_pula += 1
            motivos[motivo.split(" (")[0]] = motivos.get(motivo.split(" (")[0], 0) + 1
            continue
        n_ok += 1
        if not fazer:
            continue
        for k in ("posted_url", "agendado_para", "canal_postado", "posted_at"):
            p.pop(k, None)
        p["devolvido_fila_celular"] = datetime.now().isoformat(timespec="seconds")
        tmp = pj.with_suffix(".tmp")
        tmp.write_text(json.dumps(p, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(pj)
        DEST.mkdir(exist_ok=True)
        shutil.move(str(pedido), str(DEST / pedido.name))
        copia = Path(d.get("video") or "")
        if copia.is_file() and (orig.is_file() or (orig.parent / "_NO_DRIVE.txt").exists()):
            copia.unlink()
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), "pedido": pedido.name,
                                "pasta": str(orig.parent), "canal": d.get("canal")}, ensure_ascii=False) + "\n")
    print(f"{'devolvidos' if fazer else '[ensaio] devolveria'}: {n_ok} | pulados: {n_pula} {motivos}")


if __name__ == "__main__":
    main("--fazer" in sys.argv)
