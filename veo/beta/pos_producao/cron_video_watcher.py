"""cron_video_watcher: detecta MP4 novo em cron_shorts/.

Uso: python -m pos_producao.cron_video_watcher
Log: D:/veo/beta/pos_producao/cron_logs/cron_video_watcher.jsonl
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone

_BASE = Path(r"D:/veo/beta")
_SRC = _BASE / "videos" / "cron_shorts"
_OUT = _BASE / "videos_pos" / "cron_shorts"
_LOGS = _BASE / "pos_producao" / "cron_logs"
_LOGS.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOGS / "cron_video_watcher.jsonl"

# Modo backlog: processa TODO video sem pos-producao feita, nao so os recentes.
# A janela de tempo antiga (WINDOW_MIN=10) fazia o watcher ignorar o backlog
# inteiro quando o Veo nao gerava nada novo nos ultimos 10 min. Agora "novo" =
# qualquer mp4 na origem cuja saida em videos_pos nao existe ou esta desatualizada.
WINDOW_MIN = None  # None = sem janela (pega backlog inteiro)


def _log(obj: dict):
    obj["ts"] = datetime.now(timezone.utc).isoformat()
    obj["agente"] = "cron_video_watcher"
    line = json.dumps(obj, ensure_ascii=False)
    with _LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def run():
    if not _SRC.exists():
        _log({"acao": "scan", "status": "erro", "detalhes": f"src nao existe: {_SRC}"})
        return
    cutoff = None if WINDOW_MIN is None else time.time() - WINDOW_MIN * 60
    novos = []
    # mais recente primeiro: conteudo novo sai na frente do backlog antigo
    for mp4 in sorted(_SRC.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
        # exclui arquivos de teste (_test_, _orig_)
        if mp4.stem.startswith("_"):
            continue
        # ja processado? (saida existe e esta atualizada)
        out_mp4 = _OUT / mp4.name
        if out_mp4.exists() and out_mp4.stat().st_mtime >= mp4.stat().st_mtime:
            continue
        # janela de tempo so filtra se WINDOW_MIN estiver definido
        if cutoff is not None and mp4.stat().st_mtime < cutoff:
            continue
        novos.append({"stem": mp4.stem, "path": str(mp4),
                      "mtime": mp4.stat().st_mtime,
                      "size_mb": round(mp4.stat().st_size / 1024 / 1024, 2)})
    _log({"acao": "scan", "status": "ok",
          "detalhes": {"src": str(_SRC), "novos": novos, "qtd": len(novos)}})


if __name__ == "__main__":
    run()