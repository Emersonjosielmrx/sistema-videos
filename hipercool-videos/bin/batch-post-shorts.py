#!/usr/bin/env python3
"""batch-post-shorts.py — Posta múltiplos Shorts no YouTube via n8n.

Uso:
    python bin/batch-post-shorts.py --shorts-dir workspace/shorts/the-meek-cat-cap2 \
        --meta workspace/shorts/the-meek-cat-cap2/meta_shorts.json \
        --canal "hipercool-postar" [--dry-run]

Processo:
    Para cada Short (em ordem):
    1. Sobe no catbox.moe
    2. Envia pro webhook n8n com metadados
    3. Agenda pra horário nobre (espaçado 15min entre partes)
"""
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "bin"))

# Horário nobre BR
BRT = timezone(timedelta(hours=-3))
PEAK_HOURS_BRT = [18, 19, 20, 21]
SLOT_INTERVAL = 15  # minutos entre cada parte


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def kc(service):
    try:
        return subprocess.run(["security", "find-generic-password", "-s", service, "-w"],
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""


def _upload_host(video_path):
    """Sobe pro tmpfiles.org (catbox está instável), retorna URL direta de download."""
    # tmpfiles.org: upload -> retorna URL de página -> converter pra /dl/ pra download direto
    r = subprocess.run(["curl", "-s", "-m", "600", "-F", f"file=@{video_path}",
                        "https://tmpfiles.org/api/v1/upload"],
                       capture_output=True, text=True)
    try:
        import json as _j
        data = _j.loads(r.stdout)
        if data.get("status") == "success":
            page_url = data["data"]["url"]
            # Converter https://tmpfiles.org/XXXX/file.mp4 -> https://tmpfiles.org/dl/XXXX/file.mp4
            dl_url = page_url.replace("tmpfiles.org/", "tmpfiles.org/dl/", 1)
            return dl_url
    except Exception:
        pass
    return None


def schedule_slots(total, interval_min=15):
    """Gera slots de horário espaçados no próximo horário nobre."""
    now = datetime.now(BRT)
    slots = []
    for h in PEAK_HOURS_BRT:
        t = datetime(now.year, now.month, now.day, h, 0, tzinfo=BRT)
        if t > now + timedelta(minutes=10):
            slots.append(t)
    if not slots:
        # Amanhã
        tomorrow = now + timedelta(days=1)
        for h in PEAK_HOURS_BRT:
            slots.append(datetime(tomorrow.year, tomorrow.month, tomorrow.day, h, 0, tzinfo=BRT))

    # Distribuir os slots com intervalo
    result = []
    for i in range(total):
        slot_idx = i // (60 // interval_min)  # quantos cabem por hora
        minute_offset = (i % (60 // interval_min)) * interval_min
        if slot_idx < len(slots):
            t = slots[slot_idx] + timedelta(minutes=minute_offset)
        else:
            t = slots[-1] + timedelta(hours=1) + timedelta(minutes=minute_offset)
        result.append(t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    return result


def post_short(video_path, meta_entry, webhook_url, publish_at, dry_run=False):
    """Posta um Short: upload catbox -> webhook n8n."""
    video_path = Path(video_path)
    if not video_path.exists():
        log(f"  [X] Vídeo não existe: {video_path}")
        return False

    # Upload
    log(f"  Subindo pro catbox... ({video_path.name})")
    vurl = _upload_host(video_path)
    if not vurl:
        log(f"  [X] Falha no upload")
        return False
    log(f"  [OK] URL: {vurl}")

    meta = meta_entry.get("pt", meta_entry)
    tags = ",".join(meta.get("tags", [])) if isinstance(meta.get("tags"), list) else meta.get("tags", "")

    body = {
        "video_url": vurl,
        "title": meta.get("title", ""),
        "description": meta.get("description", ""),
        "tags": tags,
        "publishAt": publish_at,
        "formato": "vertical",
    }

    if dry_run:
        log(f"  [OK] [DRY-RUN] Enviaria: {meta['title'][:50]}... às {publish_at}")
        return True

    req = urllib.request.Request(webhook_url, data=json.dumps(body).encode(),
                                 method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            resp = r.read().decode(errors="replace")[:200]
            log(f"  ✅ Postado: {r.status} — {resp}")
            return True
    except Exception as e:
        log(f"  [X] Webhook falhou: {e}")
        return False

    return True


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--shorts-dir", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--canal", default="hipercool-postar", help="Webhook path")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    shorts_dir = Path(args.shorts_dir)
    meta_path = Path(args.meta)
    meta_all = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    # Log de já postados (evita duplicatas em re-runs)
    posted_log = shorts_dir / ".posted.json"
    posted = json.loads(posted_log.read_text()) if posted_log.exists() else {}

    # Listar arquivos .mp4 ordenados por parte
    videos = sorted(shorts_dir.glob("*.mp4"),
                    key=lambda p: int(''.join(filter(str.isdigit, p.stem.split('_')[-1])) or '0'))

    # Filtrar só os que têm meta
    videos = [v for v in videos]
    total = len(videos)
    log(f"📤 Postando {total} Shorts")

    # Pular já postados
    to_post = [v for v in videos if v.name not in posted]
    if len(to_post) < total:
        log(f"  ⏭ {total - len(to_post)} já postados anteriormente, pulando")

    # Gerar slots de horário
    slots = schedule_slots(len(to_post), SLOT_INTERVAL)
    base = kc("n8n-api-endpoint") or "https://console.inovareinteligenciaartificial.com"
    webhook = f"{base}/webhook/{args.canal}"

    success = 0
    for i, video in enumerate(to_post):
        part_key = None
        for k in meta_all:
            if k in video.stem or video.stem in k:
                part_key = k
                break
        if not part_key:
            part_num = int(''.join(filter(str.isdigit, video.stem.split('_')[-1])) or '0')
            part_key = f"part_{part_num:02d}"

        meta_entry = meta_all.get(part_key, {})

        # Fallback: gerar na hora
        if not meta_entry:
            part_num = i + 1
            meta_entry = {
                "pt": {
                    "title": f"The Meek Cat Cap.2 | {part_num}/{total} 🔥",
                    "description": f"Parte {part_num} de {total} do Capítulo 2.\n\n#Manhwa #Recap",
                    "tags": ["The Meek Cat", "manhwa", "recap", f"parte {part_num}"]
                }
            }

        log(f"\n[{i+1}/{len(to_post)}] {video.name} -> slot {slots[i]}")
        ok = post_short(video, meta_entry, webhook, slots[i], args.dry_run)
        if ok:
            success += 1
            # Registrar como postado
            posted[video.name] = {"slot": slots[i], "posted_at": datetime.now().isoformat()}
            posted_log.write_text(json.dumps(posted, indent=2))

        # Pausa entre uploads
        if i < len(to_post) - 1 and not args.dry_run:
            time.sleep(2)

    log(f"\n{'='*50}")
    log(f"✅ {success}/{len(to_post)} Shorts postados!")
    if args.dry_run:
        log(f"DRY-RUN: Use sem --dry-run pra postar de verdade")


if __name__ == "__main__":
    main()
