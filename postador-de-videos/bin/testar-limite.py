#!/usr/bin/env python3
"""testar-limite.py — Mede o LIMITE DIÁRIO REAL de upload de canais (empírico).

Empurra uploads privados num canal até o YouTube recusar com uploadLimitExceeded,
contando quantos passaram. Descobre o máximo real por conta/dia (não por doc).

Uso: python bin/testar-limite.py <id_canal1> <id_canal2> ...
     (sem args usa 3 canais de amostra)

Os vídeos criados vão pra _LEIA_POSTAR_VIDEOS/testar_limite_resultado.json e o
apagar-testes.py limpa junto.
"""
import json
import sys
import time
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import youtube_poster as yp  # noqa: E402

TEST_VIDEO = r"D:/hipercool-producao/workspace/shorts/the-meek-cat-cap3/the-meek-cat_cap3_parte07.mp4"
MAX_TENTATIVAS = 20  # trava de segurança
AMOSTRA_PADRAO = ["n6w2HCpYQI6i63cu", "NdHuOLpVF21th3YZ", "0RW4rz4ekPpkPcZx"]
OUT = (Path(__file__).resolve().parent.parent /
       "_LEIA_POSTAR_VIDEOS" / "testar_limite_resultado.json")


def reason_of(e):
    if isinstance(e, urllib.error.HTTPError):
        try:
            return json.loads(e.read().decode("utf-8", "replace"))["error"]["errors"][0]["reason"]
        except Exception:
            return f"HTTP {e.code}"
    return str(e)[:60]


def main():
    ids = sys.argv[1:] or AMOSTRA_PADRAO
    canais = {c["id"]: c for c in yp._load_canais()}
    criados = []
    resumo = []

    for cid in ids:
        canal = canais.get(cid)
        if not canal:
            print(f"?? id desconhecido: {cid}", flush=True)
            continue
        nome = canal["nome"].strip()
        print(f"\n==== {nome} ({cid}) ====", flush=True)
        sucessos = 0
        motivo = "atingiu MAX_TENTATIVAS (não travou)"
        for n in range(1, MAX_TENTATIVAS + 1):
            try:
                vid = yp.upload(TEST_VIDEO, "TESTE LIMITE - APAGAR",
                                "teste limite diario", ["teste"], canal,
                                privacy="private")
                sucessos += 1
                criados.append({"nome": nome, "id": cid, "status": "POSTOU",
                                "info": f"https://youtu.be/{vid}"})
                print(f"  upload agora #{sucessos} OK  ({vid})", flush=True)
            except Exception as e:  # noqa
                motivo = reason_of(e)
                print(f"  PAROU na tentativa #{sucessos + 1}  ->  {motivo}", flush=True)
                break
            time.sleep(0.6)
        total = sucessos + 1  # +1 do teste de canais feito antes hoje
        print(f"  >>> {nome}: {sucessos} agora + 1 (teste anterior) "
              f"= ~{total} uploads hoje antes de travar  [{motivo}]", flush=True)
        resumo.append((nome, sucessos, total, motivo))

    # salva ids criados p/ limpeza
    OUT.write_text(json.dumps(criados, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n==================== RESUMO LIMITE REAL ====================")
    for nome, ag, tot, mot in resumo:
        print(f"  {nome[:34]:34} ~{tot:2} uploads/dia  ({mot})")
    print(f"\n{len(criados)} vídeos de teste criados (limpar com apagar-testes.py)")


if __name__ == "__main__":
    main()
