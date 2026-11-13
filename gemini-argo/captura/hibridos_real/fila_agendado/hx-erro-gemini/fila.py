"""Decide se a fila do hipercool pode subir um vídeo agora no canal de uma língua (trecho de bin/fila.py)."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

POSTAGEM_IDIOMAS = {"intervalo_h": 2, "max_dia": 3, "parado_h": 24}


def pode_postar(info, ups, agora_la=None, teto=None):
    """(pode, motivo) pra subir agora no canal da língua. Canal sem nada há mais de parado_h: sai já.
    Senão só no horário de pico do país (hora de lá), intervalo_h depois do último e até max_dia por dia.
    ups = horários de publicação (com fuso) de tudo que subiu ou está agendado no canal, em ordem.
    teto = teto real do canal no postador (quando vem, vale no lugar do max_dia)."""
    p = {**POSTAGEM_IDIOMAS, **{c: info[c] for c in ("intervalo_h", "max_dia", "parado_h") if c in info}}
    if teto is not None:
        p["max_dia"] = int(teto)
    agora_la = agora_la or datetime.now(ZoneInfo(info.get("fuso", "UTC")))
    ups = sorted(ups)
    # "último upload" é o último JÁ PUBLICADO: um agendado pro futuro dava "agora - ups[-1]" negativo, sempre menor
    # que o intervalo, e o canal ficava preso até a data agendada. O teto do dia continua contando os agendados de hoje.
    passados = [u for u in ups if u <= agora_la]
    if not passados or agora_la - passados[-1] > timedelta(hours=p["parado_h"]):
        return True, "canal parado, sai já"
    if agora_la - passados[-1] < timedelta(hours=p["intervalo_h"]):
        return False, f"último há {(agora_la - passados[-1]).total_seconds() / 3600:.1f} h"
    hoje = sum(1 for u in ups if u.astimezone(agora_la.tzinfo).date() == agora_la.date())
    if hoje >= p["max_dia"]:
        return False, f"já subiram {hoje} hoje"
    ini, fim = info.get("pico", [17, 22])
    if not ini <= agora_la.hour < fim:
        return False, f"fora do pico ({agora_la:%H:%M} lá, pico {ini}h-{fim}h)"
    return True, f"pico ({agora_la:%H:%M} lá)"
