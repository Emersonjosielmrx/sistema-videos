# -*- coding: utf-8 -*-
r"""vigia_tiktok_ip.py — 12/11 (dona: "todas com proxy, mas tem que ter análise se as novas postadas nos canais top ainda
vão dar bem... altamente documentado e lembrete"). Doc: D:\postador-de-videos\docs\TIKTOK_IPS_COMPARTILHADOS.md

Desde 12/11 TODAS as contas do TikTok postam pelos 10 IPs grátis do Webshare, ~6 contas por IP (exceção da dona à regra
de 1 conta por IP, só no TikTok). Cada IP tem 1 conta BOA (as 10 de mais views, em proxy_tiktok.json "_boas").
Risco: o TikTok ligar as contas do mesmo IP e a conta morta derrubar a boa.

O que este vigia faz, 1x por dia depois da medição (tarefa TikTok_MedirViews 07:23 -> logs\tiktok_views\<data>.json):
- ganho de views de cada conta boa = views de hoje - views de ontem (só dias em que o perfil ABRIU nas 2 medições);
- normal da conta = média desse ganho nos 5 dias ANTES de 12/11 (a "linha de base", gravada na 1ª rodada);
- ganho < 50% do normal em 2 dias seguidos = QUEDA: avisa no Telegram e PAUSA as contas não-boas do mesmo IP
  ("pausada" em reuso_plataformas.json, motivo "vigia_tiktok_ip"); a boa continua.
- dia com medição falha (perfil não abriu) não conta nem a favor nem contra.
Não fala com o TikTok: só lê os arquivos da medição. Estado: logs\vigia_tiktok_ip.json. Desligar: VIGIA_TIKTOK_IP=0.

    python vigia_tiktok_ip.py            # roda (aviso + pausa se cair)
    python vigia_tiktok_ip.py --ensaio   # só mostra
"""
import json
import os
import shutil
import sys
import time
from datetime import date, timedelta
from pathlib import Path

BASE = Path(r"D:\postador-de-videos")
MEDICOES = BASE / "logs" / "tiktok_views"
MAPA = BASE / "config" / "proxy_tiktok.json"
REUSO = BASE / "config" / "reuso_plataformas.json"
ESTADO = BASE / "logs" / "vigia_tiktok_ip.json"
INICIO = date(2026, 11, 12)  # dia em que as contas passaram a dividir IP
DIAS_BASE = 5
LIMITE = 0.5        # ganho abaixo de 50% do normal...
DIAS_SEGUIDOS = 2   # ...por 2 dias seguidos = queda
MIN_NORMAL = 30     # conta que ganhava menos de 30 views/dia não dá pra julgar (ruído)


def _med(d):
    try:
        return json.loads((MEDICOES / f"{d.isoformat()}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _por_video(med, conta, cofre=None):
    """{id do vídeo: views} da medição, ou None se o perfil não abriu."""
    x = med.get(cofre or conta) or med.get(conta) or {}
    return x.get("por_video") or {} if x.get("abriu") else None


def ganho(conta, dia, cofre=None):
    """Views ganhas de dia-1 para dia, vídeo a vídeo; None se alguma das 2 medições falhou.
    12/11: NÃO usar o total do perfil — a grade carrega um nº diferente de vídeos a cada dia (37 num dia, 24 no outro)
    e o total "caía" 967 views sem cair nada. Vídeo nos 2 dias = diferença; vídeo novo (só hoje) = o que já fez."""
    a, b = _por_video(_med(dia - timedelta(days=1)), conta, cofre), _por_video(_med(dia), conta, cofre)
    if a is None or b is None:
        return None
    return sum(max(0, v - a[k]) if k in a else v for k, v in b.items())


def main(ensaio=False):
    if os.environ.get("VIGIA_TIKTOK_IP", "1") == "0":
        return
    mapa = json.loads(MAPA.read_text(encoding="utf-8"))
    boas = (mapa.get("_boas") or {}).get("contas") or {}
    if not boas:
        print("sem _boas em proxy_tiktok.json (rodar tiktok_pausar_zeradas.py --compartilhar --fazer)")
        return
    reuso = json.loads(REUSO.read_text(encoding="utf-8"))
    contas = reuso["tiktok"]["contas"]
    try:
        est = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        est = {"base": {}, "ruins": {}, "historico": []}
    hoje = date.today()
    linhas, quedas = [], []
    for conta, ip in boas.items():
        cofre = (contas.get(conta) or {}).get("cofre")
        if conta not in est["base"]:  # linha de base: média dos DIAS_BASE dias antes de virar compartilhado
            gs = [g for g in (ganho(conta, INICIO - timedelta(days=i), cofre) for i in range(1, DIAS_BASE + 1)) if g is not None]
            est["base"][conta] = round(sum(gs) / len(gs), 1) if gs else None
        normal = est["base"][conta]
        g = ganho(conta, hoje, cofre)
        if g is None:
            situ = "medição falhou hoje (não conta)"
        elif not normal or normal < MIN_NORMAL:
            situ = f"normal baixo demais pra julgar ({normal})"
        elif g < LIMITE * normal:
            est["ruins"][conta] = est["ruins"].get(conta, 0) + 1
            situ = f"ABAIXO ({est['ruins'][conta]}º dia seguido)"
            if est["ruins"][conta] >= DIAS_SEGUIDOS:
                quedas.append((conta, ip, g, normal))
        else:
            est["ruins"][conta] = 0
            situ = "ok"
        linhas.append(f"IP {ip:2d} {conta}: hoje {g if g is not None else '?'} views | normal {normal} | {situ}")
    print("\n".join(linhas))
    est["historico"] = (est.get("historico") or [])[-60:] + [{"dia": hoje.isoformat(), "linhas": linhas}]
    pausadas = []
    if quedas and not ensaio:
        h = time.strftime("%Y%m%d_%H%M")
        shutil.copy2(REUSO, REUSO.with_name(REUSO.name + f".bkp_vigia_{h}"))
        for conta, ip, g, normal in quedas:
            for c, n in mapa["contas"].items():
                if n == ip and c != conta and c in contas and not contas[c].get("pausada"):
                    contas[c]["pausada"] = f"{hoje:%d/%m}: vigia_tiktok_ip — a boa {conta} do IP {ip} caiu ({g} vs normal {normal})"
                    pausadas.append(c)
        REUSO.write_text(json.dumps(reuso, ensure_ascii=False, indent=1), encoding="utf-8")
    if not ensaio:
        ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    if quedas and not ensaio:
        try:
            sys.path.insert(0, r"D:\video-fila")
            import avisos
            txt = ("📉 <b>TikTok: conta boa caiu no IP compartilhado</b>\n"
                   + "\n".join(f"• {c} (IP {ip}): {g} views em 24 h, normal {n}" for c, ip, g, n in quedas)
                   + f"\nPausei {len(pausadas)} conta(s) que dividiam o IP com ela: {', '.join(pausadas)[:300]}"
                   + "\nDoc: D:\\postador-de-videos\\docs\\TIKTOK_IPS_COMPARTILHADOS.md")
            avisos.enviar(txt, "tiktok-views", importante=True, chave=f"vigia_ip:{hoje}:{','.join(c for c, *_ in quedas)}")
        except Exception as e:  # noqa: BLE001
            print(f"aviso falhou: {type(e).__name__}: {e}")
    return quedas


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main("--ensaio" in sys.argv)
