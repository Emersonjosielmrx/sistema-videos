# -*- coding: utf-8 -*-
"""batch_post_shorts.py — Posta shorts gerados via n8n webhook.

Lê os metadata JSON de cada short e envia pro n8n que cuida do upload pro YouTube.
Suporta dry-run, delay entre posts, e log de resultados.
"""
import os
import sys
import json
import time
import argparse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hp_common import PROJECT_DIR, VIDEOS_DIR, log

SHORTS_DIR = VIDEOS_DIR / "_shorts"
N8N_WEBHOOK = os.environ.get("N8N_SHORTS_WEBHOOK", "")
POST_DELAY = int(os.environ.get("POST_DELAY", "60"))
POST_LOG = PROJECT_DIR / "logs" / "shorts_posted.json"


def _post_to_n8n(payload):
    """Envia payload pro webhook n8n."""
    if not N8N_WEBHOOK:
        return {"error": "N8N_SHORTS_WEBHOOK not set"}

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        N8N_WEBHOOK, data=body, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def _load_posted():
    """Carrega registro de shorts já postados."""
    if POST_LOG.exists():
        try:
            return json.loads(POST_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_posted(posted):
    POST_LOG.parent.mkdir(parents=True, exist_ok=True)
    POST_LOG.write_text(json.dumps(posted, ensure_ascii=False, indent=2), encoding="utf-8")


def find_shorts(directory=None):
    """Encontra todos os shorts com metadata JSON."""
    d = Path(directory) if directory else SHORTS_DIR
    shorts = []
    for meta_file in sorted(d.rglob("*.json")):
        if meta_file.name.startswith("queue"):
            continue
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            if meta.get("file") and Path(meta["file"]).exists():
                shorts.append(meta)
        except Exception:
            pass
    return shorts


def post_shorts(shorts, dry_run=False, delay=None):
    """Posta lista de shorts. Retorna resultados."""
    delay = delay if delay is not None else POST_DELAY
    posted = _load_posted()
    posted_files = {p.get("file") for p in posted}
    results = []

    pending = [s for s in shorts if s.get("file") not in posted_files]
    log(f"SHORTS: {len(pending)} pendentes de {len(shorts)} total")

    for i, short in enumerate(pending):
        log(f"  [{i+1}/{len(pending)}] {short.get('title', '?')}")

        if dry_run:
            log(f"    DRY RUN: seria postado")
            results.append({"file": short["file"], "status": "dry_run"})
            continue

        payload = {
            "title": short.get("title", ""),
            "description": short.get("description", ""),
            "file_path": short["file"],
            "hashtags": short.get("hashtags", ""),
            "part": short.get("part", 1),
        }

        resp = _post_to_n8n(payload)
        if resp.get("error"):
            log(f"    ERRO: {resp['error']}")
            results.append({"file": short["file"], "status": "error", "error": resp["error"]})
        else:
            log(f"    OK")
            record = {**short, "posted_at": time.strftime("%Y-%m-%d %H:%M"), "response": resp}
            posted.append(record)
            _save_posted(posted)
            results.append({"file": short["file"], "status": "ok"})

        if i < len(pending) - 1:
            time.sleep(delay)

    ok = sum(1 for r in results if r["status"] == "ok")
    log(f"SHORTS POSTADOS: {ok}/{len(pending)}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Batch post shorts via n8n")
    parser.add_argument("--dir", default=None, help="Diretorio com shorts")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--delay", type=int, default=POST_DELAY, help="Delay entre posts (s)")
    parser.add_argument("--webhook", default=None, help="Override n8n webhook URL")
    args = parser.parse_args()

    if args.webhook:
        global N8N_WEBHOOK
        N8N_WEBHOOK = args.webhook

    shorts = find_shorts(args.dir)
    if not shorts:
        print("Nenhum short encontrado")
        return

    results = post_shorts(shorts, dry_run=args.dry_run, delay=args.delay)
    ok = sum(1 for r in results if r["status"] == "ok")
    print(f"Resultado: {ok}/{len(results)} postados")


if __name__ == "__main__":
    main()
