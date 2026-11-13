#!/usr/bin/env python3
r"""Responde "5.5" no bot do Opus (Telegram): crédito do Opus 5.5 (contas CC no OmniRoute) agora.
Lê pelo D:\sentinela_credito.py --provider cc e manda pelo portão avisos.py (origem opus-monitor = bot do Opus, sem
reescrita). Chamado pelo notificar_telegram.py (dona 27/10: "ponha os 3 no bot opus": Opus 4.6, Opus 5.5 e Argon).
"""
import json
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, r"D:\video-fila")
import avisos  # noqa: E402

PY = r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe"


def main():
    agora = datetime.now()
    try:
        r = subprocess.run([PY, "-X", "utf8", r"D:\sentinela_credito.py", "--provider", "cc"], cwd="D:\\",
                           capture_output=True, text=True, encoding="utf-8", timeout=150)
        dados = json.loads(r.stdout)
        p = dados[0] if isinstance(dados, list) else dados
    except Exception as e:  # noqa: BLE001
        avisos.enviar(f"Não consegui ler o crédito do Opus 5.5 agora ({type(e).__name__}).", "opus-monitor",
                      importante=True, chave=f"opus55-comando-erro:{agora.isoformat()}")
        return
    com = p.get("com_credito", 0)
    if com:
        msg = f"<b>Opus 5.5 com crédito</b> ({agora:%H:%M})\n{com} de {p.get('contas')} conta(s) com crédito agora."
    else:
        volta = p.get("proxima_volta") or (p.get("voltas") or [None])[0]
        quando = (datetime.fromisoformat(volta.replace("Z", "+00:00")).astimezone().strftime("%d/%m às %H:%M")
                  if volta else "sem previsão")
        msg = f"<b>Opus 5.5 sem crédito</b> ({agora:%H:%M})\nVolta {quando}."
    avisos.enviar(msg, "opus-monitor", importante=True, chave=f"opus55-comando:{agora.isoformat()}")
    print(msg)


if __name__ == "__main__":
    main()
