r"""recuperar_falsos_mudos.py — devolve à fila os Shorts descartados como "mudos" que NÃO eram mudos (13/11/2026).

De 31/10 a 13/11 a conferência do áudio (conferir_audio.py) lia a transcrição VAZIA do Groq fora do ar como "0 palavras
= quase nada se ouve"; o descartar_segurados.py mandava o vídeo pro Drive (videos-backup/parceiro/nao-usados). Este
script, pra cada ficha com conferido_audio "0 palavras":
  1. traz o video.mp4 de volta do Drive (1 por vez);
  2. OUVE de novo com a conferência corrigida (Groq; se vier vazio, mede o som e usa o Whisper local);
  3. ok=True  -> ficha volta a "pronto" (revisão limpa) e entra na fila normal de postagem;
     ok=False -> continua descartado (o vídeo volta pro Drive) com o motivo novo;
     ok=None  -> não mexe (não deu pra conferir agora).
Nunca devolve fonte que já saiu em outro canal (regra "nunca o mesmo vídeo em 2 canais").

    python recuperar_falsos_mudos.py --simular      # só lista
    python recuperar_falsos_mudos.py [--max 20]
"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
RCLONE = r"D:\tools\rclone.exe"
DRIVE = "manhwa-drive:videos-backup/parceiro/nao-usados"
# o vídeo segurado pode estar em: nao-usados (descartar_segurados), _segurados_1211 (limpeza de disco de 12/11) ou
# _reserva_1112 (reserva_shorts_drive)
PASTAS = ["manhwa-drive:videos-backup/parceiro/nao-usados", "manhwa-drive:videos-backup/parceiro/_segurados_1211",
          "manhwa-drive:videos-backup/parceiro/_reserva_1112"]
LOG = Path(r"D:\tmp\recuperar_falsos_mudos.log")


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    print(linha, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    simular = "--simular" in sys.argv
    maximo = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 999
    import conferir_audio
    import parceiro_diario as p
    c = p.cfg()
    its = p.itens(c)
    postadas = p._fontes_postadas(its)
    n = {"voltou": 0, "mudo mesmo": 0, "outro defeito": 0, "não conferi": 0, "fonte já postada": 0, "sem vídeo no Drive": 0}
    feitos = 0
    for x in its:
        ca = x["d"].get("conferido_audio") or {}
        if not (x["estado"] in ("esperando", "reprovado") and ca.get("ok") is False and ca.get("palavras") == 0
                and "quase nada se ouve" in str(ca.get("motivo"))):
            continue
        pasta = x["pj"].parent
        f_id = p._id_fonte(x["fonte"]) or ""
        if any(f_id in por and por[f_id] != x["canal"] for por in postadas.values()):
            n["fonte já postada"] += 1
            continue
        if feitos >= maximo:
            break
        feitos += 1
        if simular:
            log(f"[simular] conferiria {pasta.name}")
            continue
        veio_do_drive = False
        if not x["mp4"].exists():
            origem = None
            for raiz in PASTAS:
                r = subprocess.run([RCLONE, "copyto", f"{raiz}/{pasta.name}/{x['mp4'].name}", str(x["mp4"]), "--retries", "2"],
                                   capture_output=True, text=True, timeout=900, creationflags=0x08000000)
                if x["mp4"].exists():
                    origem = raiz
                    break
            if not x["mp4"].exists():
                n["sem vídeo no Drive"] += 1
                log(f"{pasta.name}: vídeo não veio do Drive ({(r.stderr or '')[-80:].strip()})")
                continue
            veio_do_drive = True
        r = conferir_audio.ouvir(pasta)
        d = json.loads(x["pj"].read_text(encoding="utf-8"))
        if r.get("ok") is True:
            d["conferido_audio"] = r
            d["pronto"] = True
            d["revisao"] = "aprovado"
            d["_recuperado_13nov"] = ("estava descartado como 'áudio mudo' por transcrição vazia do Groq; ouvido de novo: "
                                      f"{r.get('palavras')} palavras")
            d.pop("descartado_em", None)
            x["pj"].write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            if veio_do_drive:  # tira a cópia de "não usados" (o vídeo voltou a valer)
                subprocess.run([RCLONE, "purge", f"{origem}/{pasta.name}"], capture_output=True, timeout=300,
                               creationflags=0x08000000)
            n["voltou"] += 1
            log(f"{pasta.name}: VOLTOU pra fila ({r.get('palavras')} palavras em {r.get('duracao_s')} s) — «{r.get('ouvido', '')[:70]}»")
        elif r.get("ok") is False:
            d["conferido_audio"] = r
            x["pj"].write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            chave = "mudo mesmo" if "quase nada se ouve" in str(r.get("motivo")) else "outro defeito"
            n[chave] += 1
            log(f"{pasta.name}: continua descartado — {r.get('motivo')}")
            if veio_do_drive:
                x["mp4"].unlink(missing_ok=True)  # a cópia do Drive continua lá
        else:
            n["não conferi"] += 1
            log(f"{pasta.name}: não conferi agora ({r.get('motivo')}) — fica como está")
            if veio_do_drive:
                x["mp4"].unlink(missing_ok=True)
        time.sleep(1)
    log("RESUMO: " + ", ".join(f"{k} {v}" for k, v in n.items()))


if __name__ == "__main__":
    main()
