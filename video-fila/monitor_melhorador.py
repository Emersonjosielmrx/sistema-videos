"""Monitor do chat (dona 29/10): avisa no chat cada vídeo novo de cada linha e o que o melhorador central fez.
Só imprime o que importa (cada linha = 1 aviso): vídeo novo por linha, resultado de rodada, aplicado/vetado, erro."""
import json
import re
import sys
import time
from pathlib import Path

LOG = Path(r"D:\video-fila\logs\melhorador_central.log")
EST = Path(r"D:\video-fila\estado\central\estado.json")
NOVOS = re.compile(r"(\w+) [\d.]+ \(novos (\d+)")
IMPORTA = re.compile(r"rc=|APROVAD|APLICAD|desfe[iz]|central (LIGADO|DESLIGADO)|Traceback|ERRO|sem IA|nenhum modelo", re.I)
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)


def main():
    pos = LOG.stat().st_size if LOG.exists() else 0
    ultimos = {}
    while True:
        try:
            tam = LOG.stat().st_size
            if tam < pos:
                pos = 0
            if tam > pos:
                with LOG.open("rb") as f:
                    f.seek(pos)
                    novas = f.read().decode("utf-8", "replace").splitlines()
                pos = tam
                for ln in novas:
                    for linha, n in NOVOS.findall(ln):  # linha "pressão": novos por linha desde a última rodada dela
                        n = int(n)
                        if linha in ultimos and n > ultimos[linha]:
                            print(f"VÍDEO NOVO em {linha}: {n - ultimos[linha]} (agora {n} esperando o melhorador)")
                        ultimos[linha] = n
                    if IMPORTA.search(ln):
                        print(ln.strip()[:400])
        except Exception as e:  # noqa: BLE001
            print(f"monitor: erro lendo o log ({type(e).__name__}: {e})")
        time.sleep(20)


if __name__ == "__main__":
    main()
