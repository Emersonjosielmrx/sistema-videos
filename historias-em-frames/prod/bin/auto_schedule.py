# -*- coding: utf-8 -*-
"""auto_schedule.py — Auto-schedule de postagem apos geracao.

Apos gerar video + shorts, adiciona automaticamente na posting_queue.json
com slots de horario otimos. Integra com o montar_fila existente.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_DIR = Path(__file__).resolve().parent.parent
from hp_common import VIDEOS_DIR  # noqa: E402  (hipercool-materiais)
QUEUE_FILE = PROJECT_DIR / "workspace" / "posting_queue.json"
SHORTS_DIR = VIDEOS_DIR / "_shorts"

# Slots de horario ideal pra postar (BRT) — picos de engajamento YT Brasil
POSTING_SLOTS = ["06:40", "09:00", "12:00", "15:00", "18:00", "20:00"]
MAX_PER_DAY = int(os.environ.get("MAX_POSTS_PER_DAY", "6"))


def _load_queue():
    """Carrega a fila de postagem existente."""
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_queue(queue):
    """Salva a fila de postagem."""
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")


def _next_available_slot(queue):
    """Calcula o proximo slot disponivel baseado na fila existente."""
    now = datetime.now()

    # Ver quais slots ja estao ocupados
    occupied_dates = set()
    for item in queue:
        if item.get("scheduled_at"):
            occupied_dates.add(item["scheduled_at"][:16])  # YYYY-MM-DDTHH:MM

    # Encontrar proximo slot livre
    check_date = now
    for day_offset in range(14):  # Buscar ate 14 dias na frente
        date = now + timedelta(days=day_offset)
        date_str = date.strftime("%Y-%m-%d")

        # Contar quantos ja tem nesse dia
        day_count = sum(1 for item in queue
                       if item.get("scheduled_at", "").startswith(date_str))

        if day_count >= MAX_PER_DAY:
            continue

        for slot in POSTING_SLOTS:
            slot_dt = datetime.strptime(f"{date_str} {slot}", "%Y-%m-%d %H:%M")
            if slot_dt <= now:
                continue
            slot_key = slot_dt.strftime("%Y-%m-%dT%H:%M")
            if slot_key not in occupied_dates:
                return slot_dt.isoformat()

    # Fallback: 1 dia apos o ultimo item
    if queue:
        last = queue[-1].get("scheduled_at", now.isoformat())
        try:
            last_dt = datetime.fromisoformat(last)
            return (last_dt + timedelta(hours=3)).isoformat()
        except Exception:
            pass

    return (now + timedelta(hours=1)).isoformat()


def schedule_video(video_path, meta=None):
    """Adiciona um video a fila de postagem com slot otimo.

    Args:
        video_path: Path do video gerado
        meta: dict com metadata (titulo, genero, hashtags, etc)

    Returns:
        dict com info do agendamento ou None se falhou
    """
    video_path = Path(video_path)
    if not video_path.exists():
        return None

    meta = meta or {}
    queue = _load_queue()

    # Verificar se ja esta na fila
    for item in queue:
        if item.get("video") == str(video_path):
            return None  # Ja agendado

    slot = _next_available_slot(queue)

    entry = {
        "video": str(video_path),
        "titulo": meta.get("titulo_viral", meta.get("titulo", video_path.stem)),
        "genero": meta.get("genero", ""),
        "hashtags": meta.get("hashtags", ""),
        "description": meta.get("description", ""),
        "scheduled_at": slot,
        "status": "queued",
        "type": "long" if "short" not in str(video_path).lower() else "short",
        "size_mb": round(video_path.stat().st_size / (1024 * 1024), 1),
        "added_at": datetime.now().isoformat(),
    }

    queue.append(entry)
    _save_queue(queue)

    return entry


def schedule_shorts(shorts_dir, meta=None):
    """Agenda todos os shorts de um diretorio na fila.

    Shorts sao intercalados com videos longos (1 short entre cada longo).
    """
    shorts_dir = Path(shorts_dir)
    if not shorts_dir.exists():
        return []

    scheduled = []
    shorts = sorted(shorts_dir.glob("*.mp4"))

    for short in shorts:
        entry = schedule_video(short, meta={
            **(meta or {}),
            "titulo_viral": f"{(meta or {}).get('titulo', '')} (Parte {len(scheduled)+1})",
        })
        if entry:
            entry["type"] = "short"
            scheduled.append(entry)

    if scheduled:
        _save_queue(_load_queue())  # Garantir persist

    return scheduled


def auto_schedule_after_pipeline(video_path, shorts_dir=None, meta=None):
    """Funcao principal chamada pelo pipeline apos geracao.

    Agenda o video longo + todos os shorts derivados.
    Retorna resumo do agendamento.
    """
    results = {"video": None, "shorts": []}

    # Agendar video principal
    entry = schedule_video(video_path, meta)
    if entry:
        results["video"] = entry

    # Agendar shorts se existirem
    if shorts_dir and Path(shorts_dir).exists():
        results["shorts"] = schedule_shorts(shorts_dir, meta)

    return results
