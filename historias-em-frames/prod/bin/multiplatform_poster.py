# -*- coding: utf-8 -*-
"""multiplatform_poster.py - Postagem em multiplas plataformas.

YouTube (direto via API), Instagram/Facebook (via n8n webhook).
TikTok marcado como bloqueado (anti-bot).
"""
import json
import os
import time
import urllib.request
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log

POSTED_LOG = PROJECT_DIR / "logs" / "multiplatform_posted.json"
POSTED_LOG.parent.mkdir(parents=True, exist_ok=True)

PLATFORM_CONFIG = {
    "youtube": {
        "enabled": True,
        "method": "api",
        "max_title": 100,
        "max_description": 5000,
        "max_tags": 500,
    },
    "instagram": {
        "enabled": True,
        "method": "n8n",
        "webhook_env": "N8N_INSTAGRAM_WEBHOOK",
        "max_title": 0,
        "max_description": 2200,
        "max_tags": 30,
    },
    "facebook": {
        "enabled": True,
        "method": "n8n",
        "webhook_env": "N8N_FACEBOOK_WEBHOOK",
        "max_title": 0,
        "max_description": 63206,
        "max_tags": 0,
    },
    "tiktok": {
        "enabled": False,
        "method": "blocked",
        "reason": "Anti-bot detection blocks automated uploads",
    },
}


def _load_posted():
    if POSTED_LOG.exists():
        return json.loads(POSTED_LOG.read_text(encoding="utf-8"))
    return []


def _save_posted(records):
    POSTED_LOG.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def _post_n8n(webhook_url, payload):
    """Envia payload pra webhook n8n."""
    try:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            webhook_url, data=body,
            headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status == 200
    except Exception as e:
        log(f"  multiplatform: n8n webhook falhou - {e}")
        return False


def adapt_metadata(titulo, descricao, tags, platform):
    """Adapta metadados pro limite de cada plataforma."""
    config = PLATFORM_CONFIG.get(platform, {})
    max_title = config.get("max_title", 100)
    max_desc = config.get("max_description", 2200)
    max_tags_count = config.get("max_tags", 30)

    adapted_title = titulo[:max_title] if max_title else titulo
    adapted_desc = descricao[:max_desc] if max_desc else descricao

    if isinstance(tags, list):
        if platform == "instagram":
            adapted_tags = [f"#{t.replace(' ', '')}" for t in tags[:max_tags_count]]
        else:
            adapted_tags = tags[:max_tags_count] if max_tags_count else tags
    else:
        adapted_tags = tags

    return {"titulo": adapted_title, "descricao": adapted_desc, "tags": adapted_tags}


def post_everywhere(video_path, metadata, platforms=None, dry_run=False):
    """Posta video em todas as plataformas habilitadas.

    Args:
        video_path: caminho do MP4
        metadata: dict com titulo, descricao, tags, genero
        platforms: lista de plataformas (None = todas habilitadas)
        dry_run: se True, simula sem postar

    Returns:
        dict {platform: {status, error?}}
    """
    if platforms is None:
        platforms = [p for p, cfg in PLATFORM_CONFIG.items() if cfg.get("enabled")]

    results = {}
    posted = _load_posted()

    for platform in platforms:
        config = PLATFORM_CONFIG.get(platform)
        if not config or not config.get("enabled"):
            results[platform] = {"status": "disabled"}
            continue

        adapted = adapt_metadata(
            metadata.get("titulo", ""),
            metadata.get("descricao", ""),
            metadata.get("tags", []),
            platform
        )

        if dry_run:
            results[platform] = {"status": "dry_run", "metadata": adapted}
            log(f"  multiplatform: [DRY] {platform} - {adapted['titulo'][:50]}")
            continue

        if config["method"] == "api" and platform == "youtube":
            try:
                import youtube_poster
                result = youtube_poster.upload(
                    str(video_path),
                    adapted["titulo"],
                    adapted["descricao"],
                    adapted["tags"],
                    canal=metadata.get("canal", "default"),
                )
                results[platform] = {"status": "ok" if result else "failed"}
            except Exception as e:
                results[platform] = {"status": "error", "error": str(e)}

        elif config["method"] == "n8n":
            webhook_url = os.environ.get(config.get("webhook_env", ""), "")
            if not webhook_url:
                results[platform] = {"status": "no_webhook", "error": f"env {config['webhook_env']} not set"}
                continue

            payload = {
                "video_path": str(video_path),
                "titulo": adapted["titulo"],
                "descricao": adapted["descricao"],
                "tags": adapted["tags"],
                "platform": platform,
            }
            success = _post_n8n(webhook_url, payload)
            results[platform] = {"status": "ok" if success else "failed"}

        else:
            results[platform] = {"status": "blocked", "reason": config.get("reason", "")}

        if results[platform].get("status") == "ok":
            posted.append({
                "video": str(video_path),
                "platform": platform,
                "titulo": adapted["titulo"],
                "posted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            })

    _save_posted(posted)

    ok = sum(1 for r in results.values() if r.get("status") == "ok")
    log(f"  multiplatform: {ok}/{len(platforms)} plataformas OK")
    return results
