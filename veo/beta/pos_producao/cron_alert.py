"""cron_alert: agrega logs da ultima hora e gera ALERTA.txt se necessario.

Uso: python -m pos_producao.cron_alert
Log: D:/veo/beta/pos_producao/cron_logs/cron_alert.jsonl
Saida: D:/veo/beta/ALERTA.txt (se houver alerta)

Triggers:
  - qualquer 'status=erro' nas ultimas 1h
  - mais de 5 'status=warn'
  - cron_quarantine moveu algum arquivo
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

_BASE = Path(r"D:/veo/beta")
_LOGS = _BASE / "pos_producao" / "cron_logs"
_ALERT_FILE = _BASE / "ALERTA.txt"
_LOG_FILE = _LOGS / "cron_alert.jsonl"

WINDOW_MIN = 60


def _log(obj: dict):
    obj["ts"] = datetime.now(timezone.utc).isoformat()
    obj["agente"] = "cron_alert"
    line = json.dumps(obj, ensure_ascii=False)
    with _LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def run():
    cutoff = time.time() - WINDOW_MIN * 60
    erros = []
    warns = []
    quarentine = []
    outros = []
    if _LOGS.exists():
        for jsonl in _LOGS.glob("cron_*.jsonl"):
            if jsonl.name == "cron_alert.jsonl":
                continue
            for line in jsonl.read_text(encoding="utf-8").splitlines():
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                ts = datetime.fromisoformat(obj["ts"]).timestamp()
                if ts < cutoff:
                    continue
                status = obj.get("status")
                agente = obj.get("agente")
                if status == "erro":
                    erros.append((agente, obj))
                elif status == "warn":
                    warns.append((agente, obj))
                    if agente == "cron_quarantine":
                        det = obj.get("detalhes") or {}
                        quarentine.extend(det.get("quarentine") or [])
                else:
                    outros.append((agente, obj))

    triggers = []
    if erros:
        triggers.append(f"{len(erros)} ERRO(S)")
    if len(warns) > 5:
        triggers.append(f"{len(warns)} avisos (limite 5)")
    if quarentine:
        triggers.append(f"{len(quarentine)} video(s) quarentine: {quarentine}")

    if triggers:
        linhas = [
            "ALERTA MODO PRODUCAO",
            f"Janela: ultimas {WINDOW_MIN} min",
            f"Triggers: {', '.join(triggers)}",
            "",
            "ULTIMOS ERROS:",
        ]
        for agente, obj in erros[-5:]:
            linhas.append(f"  [{agente}] {json.dumps(obj.get('detalhes') or {}, ensure_ascii=False)[:200]}")
        linhas.append("")
        linhas.append("ACOES: agente da manha - investigar e ajustar pipeline")
        _ALERT_FILE.write_text("\n".join(linhas), encoding="utf-8")
        _log({"acao": "alert", "status": "alerta",
              "detalhes": {"triggers": triggers,
                           "qtd_erros": len(erros),
                           "qtd_warns": len(warns),
                           "quarentine": quarentine}})
    else:
        # se nao ha trigger, remove ALERTA.txt se existir
        if _ALERT_FILE.exists():
            _ALERT_FILE.unlink()
        _log({"acao": "alert", "status": "ok",
              "detalhes": {"qtd_erros": len(erros),
                           "qtd_warns": len(warns),
                           "total_eventos": len(erros) + len(warns) + len(outros)}})


if __name__ == "__main__":
    run()