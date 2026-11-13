"""
stats.py — Dashboard de estatísticas do bot de engajamento.

Uso:
    python -m engage_modules.stats
    ou: from engage_modules.stats import print_stats; print_stats()
"""
import json
from datetime import date, datetime
from pathlib import Path
from collections import Counter

from .config import PROGRESS_FILE, CONFIG_FILE, BASE_DIR
from .progress import load_progress

import sys
sys.path.append(str(BASE_DIR / "shared"))
from google_session import PORT_MAP


def get_stats():
    """Retorna dict com todas as métricas do bot."""
    progress = load_progress()
    today_str = date.today().isoformat()

    total_engagements = 0
    today_engagements = 0
    acc_today = Counter()
    acc_total = Counter()
    channel_today = Counter()
    channel_total = Counter()
    likes_today = 0
    comments_today = 0
    subs_today = 0
    errors_today = 0
    hourly_distribution = Counter()
    action_types_today = Counter()
    shorts_today = 0
    videos_today = 0

    for vid_key, v in progress.items():
        ch = v.get("channel", "unknown")
        engaged = v.get("engaged_by", [])
        total_engagements += len(engaged)

        for a in v.get("actions", []):
            acc = a.get("acc", "")
            ts = a.get("ts", "")
            acc_total[acc] += 1
            channel_total[ch] += 1

            if ts.startswith(today_str):
                today_engagements += 1
                acc_today[acc] += 1
                channel_today[ch] += 1
                if a.get("liked"):
                    likes_today += 1
                    action_types_today["like"] += 1
                if a.get("commented"):
                    comments_today += 1
                    action_types_today["comment"] += 1
                if a.get("subscribed"):
                    subs_today += 1
                    action_types_today["subscribe"] += 1
                try:
                    hour = int(ts[11:13])
                    hourly_distribution[hour] += 1
                except (ValueError, IndexError):
                    pass
                if "/shorts/" in vid_key:
                    shorts_today += 1
                else:
                    videos_today += 1

    # Contas banidas
    banned = set()
    dead_file = BASE_DIR / "dead_accounts.txt"
    if dead_file.exists():
        banned = set(dead_file.read_text("utf-8").splitlines())

    # Config atual
    cfg = {}
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text("utf-8"))
        except: pass

    # Videos totais
    total_videos = len(progress)
    fully_engaged = sum(1 for v in progress.values() if len(v.get("engaged_by", [])) >= len(PORT_MAP))

    # Account health
    health_data = {}
    health_file = BASE_DIR / "data" / "account_health.json"
    if health_file.exists():
        try:
            health_data = json.loads(health_file.read_text("utf-8"))
        except: pass

    accounts_in_cooldown = []
    accounts_with_ban_signal = []
    total_successes = 0
    total_failures = 0
    for acc, data in health_data.items():
        total_successes += data.get("total_successes", 0)
        total_failures += data.get("total_failures", 0)
        cooldown = data.get("cooldown_until")
        if cooldown:
            try:
                if datetime.fromisoformat(cooldown) > datetime.now():
                    accounts_in_cooldown.append(acc)
            except: pass
        if data.get("ban_signal"):
            accounts_with_ban_signal.append(acc)

    success_rate = (total_successes / max(1, total_successes + total_failures)) * 100

    # Proxy status
    proxy_status = "desconhecido"
    try:
        from .browser import _proxy_status, _healthy_proxies, _runtime_blacklist, PROXIES
        proxy_status = _proxy_status
        proxy_healthy = len(_healthy_proxies)
        proxy_total = len(PROXIES)
        proxy_blacklisted = len(_runtime_blacklist)
    except:
        proxy_healthy = 0
        proxy_total = 0
        proxy_blacklisted = 0

    return {
        "total_engagements": total_engagements,
        "today_engagements": today_engagements,
        "likes_today": likes_today,
        "comments_today": comments_today,
        "subs_today": subs_today,
        "shorts_today": shorts_today,
        "videos_today": videos_today,
        "total_videos": total_videos,
        "fully_engaged_videos": fully_engaged,
        "accounts_active": len(PORT_MAP) - len(banned),
        "accounts_banned": len(banned),
        "accounts_in_cooldown": len(accounts_in_cooldown),
        "accounts_with_ban_signal": len(accounts_with_ban_signal),
        "banned_list": sorted(banned),
        "cooldown_list": accounts_in_cooldown,
        "top_accounts_today": acc_today.most_common(10),
        "top_channels_today": channel_today.most_common(10),
        "hourly_distribution": dict(sorted(hourly_distribution.items())),
        "success_rate": round(success_rate, 1),
        "total_successes": total_successes,
        "total_failures": total_failures,
        "proxy_status": proxy_status,
        "proxy_healthy": proxy_healthy,
        "proxy_total": proxy_total,
        "proxy_blacklisted": proxy_blacklisted,
        "config": cfg,
        "paused": cfg.get("paused", False),
    }


def print_stats():
    """Imprime dashboard formatado no terminal."""
    s = get_stats()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*60}")
    print(f"  MEGA ENGAGE v3 — Dashboard  [{now}]")
    print(f"{'='*60}")
    print(f"  Status: {'PAUSADO' if s['paused'] else 'RODANDO'}")
    print(f"  Contas ativas: {s['accounts_active']} | Banidas: {s['accounts_banned']} | Em cooldown: {s['accounts_in_cooldown']}")
    print(f"  Taxa de sucesso: {s['success_rate']}% ({s['total_successes']} ok / {s['total_failures']} fail)")
    print(f"{'─'*60}")
    print(f"  PROXIES:")
    print(f"    Status: {s['proxy_status'].upper()} | Vivos: {s['proxy_healthy']}/{s['proxy_total']} | Blacklist: {s['proxy_blacklisted']}")
    print(f"{'─'*60}")
    print(f"  HOJE:")
    print(f"    Ações totais: {s['today_engagements']} (vídeos: {s['videos_today']} | shorts: {s['shorts_today']})")
    print(f"    Likes: {s['likes_today']} | Comentários: {s['comments_today']} | Inscrições: {s['subs_today']}")
    print(f"{'─'*60}")
    print(f"  GERAL:")
    print(f"    Engajamentos totais: {s['total_engagements']}")
    print(f"    Vídeos rastreados: {s['total_videos']}")
    print(f"    Completos (todas contas): {s['fully_engaged_videos']}")
    print(f"{'─'*60}")

    if s["hourly_distribution"]:
        print(f"  DISTRIBUIÇÃO HORÁRIA (hoje):")
        max_val = max(s["hourly_distribution"].values()) if s["hourly_distribution"] else 1
        for hour in range(24):
            count = s["hourly_distribution"].get(hour, 0)
            bar = "█" * int((count / max(1, max_val)) * 20)
            print(f"    {hour:02d}h  {bar:20s} {count}")
        print(f"{'─'*60}")

    if s["top_accounts_today"]:
        print(f"  TOP CONTAS HOJE:")
        for acc, cnt in s["top_accounts_today"]:
            print(f"    {acc[:30]:30s} {cnt:4d} ações")
        print(f"{'─'*60}")

    if s["top_channels_today"]:
        print(f"  TOP CANAIS HOJE:")
        for ch, cnt in s["top_channels_today"]:
            print(f"    @{ch[:28]:28s} {cnt:4d} ações")
        print(f"{'─'*60}")

    if s["cooldown_list"]:
        print(f"  CONTAS EM COOLDOWN ({len(s['cooldown_list'])}):")
        for acc in s["cooldown_list"][:5]:
            print(f"    - {acc}")
        print(f"{'─'*60}")

    if s["banned_list"]:
        print(f"  CONTAS BANIDAS:")
        for acc in s["banned_list"]:
            print(f"    - {acc}")
        print(f"{'─'*60}")

    if s.get("accounts_with_ban_signal"):
        print(f"  ⚠ BAN SIGNALS DETECTADOS: {s['accounts_with_ban_signal']}")
        print(f"{'─'*60}")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    print_stats()
