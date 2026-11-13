#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""calcular_proximo_horario.py — Calcula próximo horário de postagem em BRT (UTC-3).

Retorna timestamp RFC 3339 para agendamento no YouTube.
"""
import sys
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def calcular_proximo_horario(offset_horas=2, timezone_offset=-3):
    """Calcula próximo horário de postagem.

    Args:
        offset_horas: quantas horas no futuro agendar (padrão 2h)
        timezone_offset: offset do timezone em horas (padrão -3 para BRT)

    Returns:
        String RFC 3339 em UTC (ex: '2026-10-07T21:00:00.000Z')
    """
    # Timezone BRT (UTC-3)
    tz = timezone(timedelta(hours=timezone_offset))

    # Hora atual em BRT
    now_brt = datetime.now(tz)

    # Adiciona offset
    proximo_horario_brt = now_brt + timedelta(hours=offset_horas)

    # Converte para UTC (YouTube API requer UTC)
    proximo_horario_utc = proximo_horario_brt.astimezone(timezone.utc)

    # Formata como RFC 3339
    rfc3339 = proximo_horario_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    print(f"[calcular] Agora (BRT): {now_brt.strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)
    print(f"[calcular] Próximo horário (BRT): {proximo_horario_brt.strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)
    print(f"[calcular] Próximo horário (UTC): {rfc3339}", file=sys.stderr)

    return rfc3339


if __name__ == "__main__":
    offset = 2  # padrão: 2 horas no futuro

    if len(sys.argv) > 1:
        try:
            offset = int(sys.argv[1])
        except ValueError:
            print(f"[calcular] AVISO: offset inválido '{sys.argv[1]}', usando padrão 2h", file=sys.stderr)

    rfc3339 = calcular_proximo_horario(offset)
    print(rfc3339)  # stdout: timestamp para uso em scripts
