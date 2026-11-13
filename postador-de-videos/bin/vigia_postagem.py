"""vigia_postagem.py — avisa NA HORA quando a postagem cai abaixo do normal ou o MESMO erro se repete (04/11 dona: "antes
eram postados muitos vídeos por dia ... os últimos 2 dias caiu; por que o sistema não anunciou os problemas?").

O que faltava: o aviso diário só dizia "51 contas sem postar hoje" (igual todo dia). Ninguém viu que desde 01/11 TODO post
pelas máquinas falhava com o mesmo erro (int('') do 1080p: 9, 42, 37 vezes/dia) nem que o Instagram foi de ~40 pra 7.

1) Ritmo: posts de hoje até agora x MEDIANA dos últimos 7 dias até a mesma hora (ledgers do TikTok e do Instagram;
   PUBLICADO das solares). Abaixo de 50% (com mínimo esperado de 5) = aviso importante.
2) Erro repetido: o mesmo motivo (sem números) 5+ vezes nas últimas 6 h dos logs do TikTok/Instagram = aviso importante.
Chamado pela PostagemContinua (de hora em hora). O portão (video-fila\\avisos.py) segura o repetido por 12 h.
    python vigia_postagem.py [--simular]
"""
import json
import re
import statistics
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

LOGS = Path(r"D:\postador-de-videos\logs")
SOLAR_LOGS = Path(r"D:\ms-energy\logs")


def _ledger(nome):
    try:
        d = json.loads((LOGS / nome).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return d if isinstance(d, list) else []


def ritmo(posts, agora):
    """(hoje_ate_agora, mediana_7d_ate_a_mesma_hora)."""
    hm = agora.strftime("%H:%M:%S")
    por_dia = Counter()
    for p in posts:
        ts = str(p.get("timestamp", ""))
        if len(ts) >= 19 and ts[11:19] <= hm:
            por_dia[ts[:10]] += 1
    hoje = por_dia.get(agora.date().isoformat(), 0)
    antes = [por_dia.get((agora.date() - timedelta(days=i)).isoformat(), 0) for i in range(1, 8)]
    return hoje, statistics.median(antes)


def solares(agora):
    """PUBLICADO das solares hoje até agora x mediana dos 7 dias (os logs têm só a hora; o dia vem do cabeçalho)."""
    por_dia = Counter()
    for f in SOLAR_LOGS.glob("*.log"):
        if not re.match(r"(reel|carrossel)", f.name):
            continue
        dia = None
        try:
            for linha in f.read_text(encoding="utf-8", errors="ignore").splitlines():
                m = re.match(r"\[(\d\d)/(\d\d)/(\d{4})", linha)
                if m:
                    dia = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
                if dia and "PUBLICADO" in linha:
                    h = re.match(r"\[(\d\d:\d\d:\d\d)\]", linha)
                    if h and h.group(1) <= agora.strftime("%H:%M:%S"):
                        por_dia[dia] += 1
        except OSError:
            continue
    hoje = por_dia.get(agora.date().isoformat(), 0)
    antes = [por_dia.get((agora.date() - timedelta(days=i)).isoformat(), 0) for i in range(1, 8)]
    return hoje, statistics.median(antes)


def erros_repetidos(agora, janela_h=6, minimo=5):
    ini = agora - timedelta(hours=janela_h)
    desde = ini.strftime("%H:%M:%S") if ini.date() == agora.date() else "00:00:00"  # o log é do dia: não cruza 0h
    out = []
    for plat in ("tiktok", "instagram"):
        f = LOGS / f"{plat}_{agora:%Y%m%d}.log"
        if not f.exists():
            continue
        c = Counter()
        for linha in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            h = re.match(r"\[(\d\d:\d\d:\d\d)\]", linha)
            m = re.search(r"ERRO \([^)]*\): (.+)", linha)
            if h and m and h.group(1) >= desde:
                c[re.sub(r"\d+", "N", m.group(1))[:90]] += 1
        out += [(plat, motivo, n) for motivo, n in c.most_common(3) if n >= minimo]
    return out


def main(simular=False):
    agora = datetime.now()
    alertas = []
    for nome, (hoje, normal) in (("TikTok", ritmo(_ledger("tiktok_auto_posted.json"), agora)),
                                 ("Instagram", ritmo(_ledger("instagram_auto_posted.json"), agora)),
                                 ("Solares", solares(agora))):
        if normal >= 5 and hoje < 0.5 * normal:
            alertas.append(f"⚠️ {nome}: só {hoje} posts até agora ({agora:%H:%M}); o normal até esta hora é ~{normal:.0f}")
    for plat, motivo, n in erros_repetidos(agora):
        alertas.append(f"⚠️ {plat}: o MESMO erro {n}x nas últimas 6 h — {motivo}")
    for a in alertas:
        print(a)
    if alertas and not simular:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar("<b>Vigia da postagem</b>\n" + "\n".join(alertas), "vigia-postagem", importante=True)
    if not alertas:
        print("postagem no ritmo normal, sem erro repetido")


if __name__ == "__main__":
    main(simular="--simular" in sys.argv)
