"""
account_health.py — Monitoramento de saúde por conta.

Rastreia falhas, detecta sinais de ban/restrição,
e gerencia pausa automática por conta (15min após 3 falhas seguidas).
"""
import json
import os
import time
from datetime import datetime, timedelta
from .logger import log

HEALTH_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "account_health.json")
CONSECUTIVE_FAIL_LIMIT = 3
COOLDOWN_SECONDS = 900  # 15 minutos
BAN_SIGNALS = [
    "sign in",
    "unusual traffic",
    "verify you're not a robot",
    "your account has been suspended",
    "this account has been terminated",
    "confirm your identity",
    "action isn't allowed",
    "couldn't perform this action",
    "turned off for this video",
    "learn more about our community guidelines",
]


def _load_health():
    try:
        with open(HEALTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_health(data):
    os.makedirs(os.path.dirname(HEALTH_FILE), exist_ok=True)
    with open(HEALTH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def report_success(account: str):
    """Registra sucesso — reseta contador de falhas consecutivas."""
    health = _load_health()
    if account not in health:
        health[account] = {}
    health[account]["consecutive_fails"] = 0
    health[account]["last_success"] = datetime.now().isoformat()
    health[account]["total_successes"] = health[account].get("total_successes", 0) + 1
    _save_health(health)


def report_failure(account: str, error_text: str = ""):
    """Registra falha — incrementa contador e aplica cooldown se necessário."""
    health = _load_health()
    if account not in health:
        health[account] = {}

    consecutive = health[account].get("consecutive_fails", 0) + 1
    health[account]["consecutive_fails"] = consecutive
    health[account]["last_failure"] = datetime.now().isoformat()
    health[account]["last_error"] = error_text[:200]
    health[account]["total_failures"] = health[account].get("total_failures", 0) + 1

    ban_detected = detect_ban_signal(error_text)
    if ban_detected:
        health[account]["ban_signal"] = ban_detected
        health[account]["ban_detected_at"] = datetime.now().isoformat()
        cooldown_until = datetime.now() + timedelta(seconds=COOLDOWN_SECONDS * 4)
        health[account]["cooldown_until"] = cooldown_until.isoformat()
        ban_cd_min = (COOLDOWN_SECONDS * 4) // 60
        log(f"[HEALTH] BAN SIGNAL em {account}: '{ban_detected}' — cooldown {ban_cd_min}min")
    elif consecutive >= CONSECUTIVE_FAIL_LIMIT:
        cooldown_until = datetime.now() + timedelta(seconds=COOLDOWN_SECONDS)
        health[account]["cooldown_until"] = cooldown_until.isoformat()
        cd_min = COOLDOWN_SECONDS // 60
        log(f"[HEALTH] {account} com {consecutive} falhas seguidas — cooldown {cd_min}min")

    _save_health(health)


def detect_ban_signal(text: str) -> str | None:
    """Verifica se o texto contém sinais de ban/restrição."""
    text_lower = text.lower()
    for signal in BAN_SIGNALS:
        if signal in text_lower:
            return signal
    return None


def is_account_healthy(account: str) -> bool:
    """Verifica se a conta pode operar agora (não está em cooldown)."""
    health = _load_health()
    acc = health.get(account, {})
    cooldown_until = acc.get("cooldown_until")
    if not cooldown_until:
        return True
    try:
        until = datetime.fromisoformat(cooldown_until)
        if datetime.now() >= until:
            acc.pop("cooldown_until", None)
            acc["consecutive_fails"] = 0
            health[account] = acc
            _save_health(health)
            return True
        return False
    except (ValueError, TypeError):
        return True


def get_unhealthy_accounts() -> list[str]:
    """Retorna lista de contas em cooldown."""
    health = _load_health()
    unhealthy = []
    for acc, data in health.items():
        cooldown_until = data.get("cooldown_until")
        if cooldown_until:
            try:
                until = datetime.fromisoformat(cooldown_until)
                if datetime.now() < until:
                    unhealthy.append(acc)
            except (ValueError, TypeError):
                pass
    return unhealthy


def get_health_summary() -> dict:
    """Retorna resumo geral de saúde de todas as contas."""
    health = _load_health()
    total = len(health)
    healthy_count = 0
    unhealthy_count = 0
    ban_count = 0

    for acc, data in health.items():
        if is_account_healthy(acc):
            healthy_count += 1
        else:
            unhealthy_count += 1
        if data.get("ban_signal"):
            ban_count += 1

    return {
        "total_accounts": total,
        "healthy": healthy_count,
        "unhealthy": unhealthy_count,
        "ban_signals_detected": ban_count,
        "accounts": health,
    }


def clear_cooldown(account: str):
    """Remove cooldown manualmente de uma conta."""
    health = _load_health()
    if account in health:
        health[account].pop("cooldown_until", None)
        health[account]["consecutive_fails"] = 0
        _save_health(health)
        log(f"[HEALTH] Cooldown removido de {account}")
