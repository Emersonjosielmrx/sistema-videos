"""
timezone.py — Horário de pico por idioma/fuso.

Cada canal tem um público em fuso específico.
Engajar no horário de pico da audiência aumenta visibilidade.
"""
from datetime import datetime, timezone, timedelta


# Fuso horário de pico por idioma (UTC offset + range de horário ideal)
PEAK_HOURS = {
    "pt": {"utc_offset": -3, "start": 18, "end": 23},   # Brasil: 18h-23h BRT
    "en": {"utc_offset": -5, "start": 17, "end": 22},   # US East: 5pm-10pm
    "es": {"utc_offset": -5, "start": 18, "end": 23},   # Latam
    "fr": {"utc_offset": 1, "start": 18, "end": 23},    # Paris
    "it": {"utc_offset": 1, "start": 18, "end": 23},    # Roma
    "th": {"utc_offset": 7, "start": 18, "end": 23},    # Bangkok
    "vi": {"utc_offset": 7, "start": 18, "end": 23},    # Hanoi
    "hi": {"utc_offset": 5.5, "start": 19, "end": 23},  # Mumbai
    "ru": {"utc_offset": 3, "start": 18, "end": 23},    # Moscou
    "id": {"utc_offset": 7, "start": 18, "end": 23},    # Jakarta
}


def is_peak_hour(lang):
    """
    Retorna True se agora é horário de pico pra o público desse idioma.
    Se o idioma não tiver config, retorna True (sempre engaja).
    """
    peak = PEAK_HOURS.get(lang)
    if not peak:
        return True

    utc_now = datetime.now(timezone.utc)
    offset = timedelta(hours=peak["utc_offset"])
    local_hour = (utc_now + offset).hour

    start = peak["start"]
    end = peak["end"]

    if start <= end:
        return start <= local_hour <= end
    else:
        return local_hour >= start or local_hour <= end


def get_priority_multiplier(lang):
    """
    Retorna multiplicador de prioridade baseado no horário.
    Pico = 3x mais chance de ser selecionado na fila.
    Fora de pico = 1x (normal).
    """
    return 3.0 if is_peak_hour(lang) else 1.0
