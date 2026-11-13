#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""postar_recaps_viral.py — Posta recaps grandes com títulos/desc/hashtags virais.

Coleta de:
1. D:/recapd-ambientes/producao/postados/anime/anime/ (recaps com nomes reais)
2. D:/hipercool-materiais/animes recap/ (candidates com MP4)

Round-robin nos canais manga/anime vivos, maiores primeiro.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PY_EXE = Path(r"D:\veo\venv\Scripts\python.exe")
POSTER = Path(r"D:\postador-de-videos\bin\youtube_poster.py")
CREDS = Path(r"D:\credenciais-canais\youtube_canais.json")
RECAPD_ANIME = Path(r"D:\recapd-ambientes\producao\postados\anime\anime")
RECAPS_MATERIAIS = Path(r"D:\hipercool-materiais\animes recap")
POSTADOS_DIR = Path(r"D:\hipercool-materiais\_postados\recaps")
LOG_FILE = Path(r"D:\postador-de-videos\logs\postar_recaps_viral.log")

DEAD = {
    "fabio com ia", "enpresainovare (financeiro",
    "emersonjosiel1995( motivação", "emersonjosiel1995nov(motivação",
    "nova conta de manga br",
    "InovareManhwaVerse", "inovaremanhwabr",
    "Inovaremanhwaversethai", "@Inovaremanhwaversethai",
}

VIRAL_TITLES = {
    "He_Accidentally_Reincarnated_As_A_Lv_1_S": [
        "Ele REENCARNA como Level 1 e CHOCA Todos com Poder Oculto",
        "Ninguém Acreditava Nele... Até Ele Revelar SEU VERDADEIRO PODER",
    ],
    "He_was_Bullied_As_the_Weakest_E_Rank_Hun": [
        "O Caçador Rank E que HUMILHOU os Rank S | Recap Completo",
        "TODOS Zombavam do Rank E... Até Ele Despertar ESSE PODER",
    ],
    "Boy_is_Reincarnated_As_The_Weakest_F_Ran": [
        "Garoto Renasce como Rank F e se TORNOU O MAIS FORTE",
        "De Rank F a LENDA: O Recap que Vai Deixar Você Sem Palavras",
    ],
    "Nasceu_Sem_Talento_Magico": [
        "Nasceu SEM TALENTO Mágico Mas se Tornou o MAIS TEMIDO",
        "Sem Nenhum Poder... Ele Derrotou o Mago Supremo | Recap",
    ],
    "BLACK_CLOVER_IN_37_MINUTES": [
        "TODA a História de Black Clover em 37 Minutos ÉPICOS",
        "BLACK CLOVER Completo: Do Zero ao Wizard King | Mega Recap",
    ],
    "CYBERPUNK__EDGERUNNERS_IS_RUTHLESS": [
        "Cyberpunk Edgerunners: O Recap Mais BRUTAL do Ano",
        "Por Que Cyberpunk Edgerunners DESTRUIU Todo Mundo",
    ],
    "He_Was_The_Worst_In_His_Class_Until_He_U": [
        "Era o PIOR da Turma... Até Descobrir um Poder PROIBIDO",
        "O Mais FRACO Desperta o Poder que NINGUÉM Queria | Recap",
    ],
    "SPACE_KING_1___Pilot": [
        "Abandonado no Espaço: Ele Construiu um IMPÉRIO Intergalático",
        "SPACE KING: De Náufrago Espacial a Rei do Universo",
    ],
    "Three_Kingdoms___OverSimplified": [
        "Os 3 REINOS Explicados de Forma que Você NUNCA VIU",
        "Três Reinos: A Guerra MAIS ÉPICA da China Antiga | Recap",
    ],
    "Elemental_Explained_By_An_Asian": [
        "Elemental EXPLICADO de Forma INÉDITA e Hilária",
        "Você Nunca Viu Elemental Sendo Explicado ASSIM",
    ],
    "Book_of_Ruth_Summary__A_Complete_Animate": [
        "A História de Rute: O Recap Animado MAIS EMOCIONANTE",
        "Rute Completo: Uma Jornada que Vai TOCAR Seu Coração",
    ],
    "Moist_Meter___Cyberpunk_Edgerunners": [
        "Cyberpunk Edgerunners é REALMENTE Tão Bom Assim? | Análise",
        "A Verdade BRUTAL Sobre Cyberpunk Edgerunners",
    ],
    "Anime_vs_The_Rumbling": [
        "O ESTRONDO: A Cena que PARALIZOU o Mundo do Anime",
        "Attack on Titan vs The Rumbling: O Momento MAIS TENSO",
    ],
    "The_Ultimate__KPop_Demon_Hunters__Recap": [
        "Caçadores de Demônios K-Pop: O Recap MAIS INSANO do Ano",
        "K-Pop + Caça de Demônios = O Anime que NINGUÉM Esperava",
    ],
    "The_myth_behind_the_Chinese_zodiac___Meg": [
        "O Mito do Zodíaco Chinês: A Verdade que NINGUÉM Conta",
        "Por Que o Gato NÃO Está no Zodíaco Chinês? | Revelado",
    ],
    # Candidatos com ID (sem nome no dir)
    "rOiI3e6WX3w": [
        "Ela RENASCE 18 Anos no Passado e FAZ o Inimigo se APAIXONAR",
        "Voltou no Tempo e Transformou Seu Pior INIMIGO em ESCRAVO do Amor",
    ],
    "_aDj2Re1xao": [
        "Todos Acham que Ele é FRACO... Mas Ele é o ASSASSINO Mais FORTE",
        "O Assassino que FINGIU ser Fraquinho e CHOCOU o Mundo",
    ],
    "KhuAegaFX4E": [
        "Blue Period em 10 Minutos: A Jornada de Arte MAIS INTENSA",
        "De Estudante ENTEDIADO a Artista GENIAL | Blue Period Recap",
    ],
}

HASHTAGS_POOL = {
    "anime": "#anime #recap #animerecap #otaku #viral #fyp #animeedit #animefans #animelover #weeb",
    "manhwa": "#manhwa #manhwarecap #webtoon #recap #viral #fyp #manhwaedit #comics #kdrama",
    "default": "#anime #recap #viral #fyp #animeedit #otaku #animelover #weeb #animefans #trending",
}


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def carregar_canais_manga():
    cred = json.loads(CREDS.read_text(encoding="utf-8"))
    dead_lower = {d.lower() for d in DEAD}
    vivos = [c for c in cred if c["nome"].lower() not in dead_lower and c.get("tem_upload")]
    manga = [c["nome"] for c in vivos if any(k in c["nome"].lower() for k in ("manga", "manhwa", "anime"))]
    return manga


def extrair_chave_anime(dirname):
    name = dirname.rstrip("/")
    m = re.match(r'^[A-Za-z0-9_-]{11}_(.+)$', name)
    if m:
        rest = m.group(1)
        if rest == "candidate":
            return name.replace("_candidate", "")
        return rest
    parts = name.split("_", 1)
    if len(parts) > 1 and parts[1] != "candidate":
        return parts[1]
    return parts[0].replace("_candidate", "")


def gerar_titulo_viral(chave, idx=0):
    titulos = VIRAL_TITLES.get(chave)
    if titulos:
        return titulos[idx % len(titulos)]
    slug = chave.replace("_", " ").strip()
    slug = re.sub(r'\s+', ' ', slug).title()
    return f"{slug}: O Recap que Vai MUDAR Sua Visão | Anime Recap"


def gerar_descricao_viral(titulo, tipo="anime"):
    gancho = (
        "Se INSCREVA e ATIVE o SINO pra não perder os próximos recaps! "
        "Esse vídeo vai te fazer QUERER ASSISTIR o original AGORA."
    )
    hashtags = HASHTAGS_POOL.get(tipo, HASHTAGS_POOL["default"])
    return (
        f"{titulo}\n\n"
        f"{gancho}\n\n"
        f"Recap completo, dublado e editado com efeitos CINEMATOGRÁFICOS.\n"
        f"Compartilhe com amigos que amam anime/manhwa!\n\n"
        f"{hashtags}\n\n"
        f"© Créditos ao autor original da obra."
    )


def gerar_tags(tipo="anime"):
    base = ["anime", "recap", "anime recap", "viral", "otaku", "fyp", "trending"]
    if tipo == "manhwa":
        base += ["manhwa", "manhwa recap", "webtoon", "kdrama", "comics"]
    else:
        base += ["anime edit", "anime fans", "weeb", "anime lover"]
    return base


def coletar_recaps():
    itens = []

    if RECAPD_ANIME.exists():
        for d in RECAPD_ANIME.iterdir():
            if not d.is_dir():
                continue
            mp4s = list(d.glob("final_anime_deitado*.mp4"))
            if not mp4s:
                mp4s = list(d.glob("*.mp4"))
            if not mp4s:
                continue
            mp4 = max(mp4s, key=lambda f: f.stat().st_size)
            chave = extrair_chave_anime(d.name)
            tipo = "manhwa" if any(k in d.name.lower() for k in ("manhwa", "reincarn", "rank", "bullied", "weakest")) else "anime"
            titulo = gerar_titulo_viral(chave)
            itens.append({
                "arquivo": str(mp4),
                "titulo": titulo[:100],
                "descricao": gerar_descricao_viral(titulo, tipo),
                "tags": gerar_tags(tipo),
                "categoria": "recap",
                "tipo": tipo,
                "tamanho": mp4.stat().st_size,
                "chave": chave,
                "source_dir": str(d),
            })

    if RECAPS_MATERIAIS.exists():
        for d in RECAPS_MATERIAIS.iterdir():
            if not d.is_dir() or d.name.startswith("_"):
                continue
            mp4s = list(d.glob("*.mp4"))
            if not mp4s:
                continue
            mp4 = max(mp4s, key=lambda f: f.stat().st_size)
            vid_id = d.name.replace("_candidate", "").strip("_")
            chave = vid_id
            tipo = "manhwa" if chave in ("rOiI3e6WX3w", "_aDj2Re1xao") else "anime"
            titulo = gerar_titulo_viral(chave)
            itens.append({
                "arquivo": str(mp4),
                "titulo": titulo[:100],
                "descricao": gerar_descricao_viral(titulo, tipo),
                "tags": gerar_tags(tipo),
                "categoria": "recap",
                "tipo": tipo,
                "tamanho": mp4.stat().st_size,
                "chave": chave,
                "source_dir": str(d),
            })

    itens.sort(key=lambda x: x["tamanho"], reverse=True)
    return itens


def postar(canal_nome, item):
    tags_str = ",".join(item["tags"]) if isinstance(item["tags"], list) else str(item["tags"])
    cmd = [
        str(PY_EXE), str(POSTER),
        "--video", item["arquivo"],
        "--titulo", item["titulo"],
        "--descricao", item["descricao"],
        "--tags", tags_str,
        "--canal", canal_nome,
        "--privacy", "public",
    ]
    env = dict(os.environ, PYTHONUTF8="1")
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True,
                           timeout=1200, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return "timeout", None
    out = (r.stdout or "") + (r.stderr or "")
    if "POSTADO:" in out or "AGENDADO:" in out:
        url = None
        for tok in out.split():
            if "youtu.be/" in tok:
                url = tok.strip()
                break
        return "ok", url
    low = out.lower()
    if "uploadlimitexceeded" in low or "quotaexceeded" in low or "ratelimitexceeded" in low:
        return "limit", None
    if "invalid_grant" in low or "suspended" in low or "invalid_client" in low or "unauthorized" in low:
        return "dead", None
    return "error", out.strip()[-400:]


def main():
    canais = carregar_canais_manga()
    log(f"Canais manga/anime vivos: {len(canais)}")
    if not canais:
        log("ERRO: nenhum canal manga/anime disponível!")
        return

    for c in canais:
        log(f"  - {c}")

    recaps = coletar_recaps()
    log(f"\nRecaps coletados: {len(recaps)} (ordenados por tamanho desc)")

    if not recaps:
        log("Nenhum recap pra postar!")
        return

    for i, r in enumerate(recaps):
        sz_mb = r["tamanho"] / 1e6
        log(f"  [{i+1}] {sz_mb:.0f}MB | {r['titulo'][:80]}")

    if "--dry-run" in sys.argv:
        log("\n=== DRY RUN — nada postado ===")
        return

    bloqueados = set()
    contagem = {}
    total_ok = 0
    total_err = 0
    canal_idx = 0

    for i, item in enumerate(recaps):
        pool = [c for c in canais if c not in bloqueados]
        if not pool:
            log("TODOS os canais manga/anime bloqueados! Parando.")
            break

        canal = pool[canal_idx % len(pool)]
        canal_idx += 1

        sz_mb = item["tamanho"] / 1e6
        log(f"\n[{i+1}/{len(recaps)}] {sz_mb:.0f}MB -> '{canal}'")
        log(f"  Titulo: {item['titulo']}")

        status, url = postar(canal, item)

        if status == "ok":
            total_ok += 1
            contagem[canal] = contagem.get(canal, 0) + 1
            log(f"  OK #{total_ok} -> {url}")
        elif status == "limit":
            bloqueados.add(canal)
            remaining = len([c for c in canais if c not in bloqueados])
            log(f"  LIMITE em '{canal}' ({remaining} canais restantes)")
            pool2 = [c for c in canais if c not in bloqueados]
            if pool2:
                canal2 = pool2[0]
                log(f"  Retry em '{canal2}'...")
                status2, url2 = postar(canal2, item)
                if status2 == "ok":
                    total_ok += 1
                    contagem[canal2] = contagem.get(canal2, 0) + 1
                    log(f"  OK #{total_ok} -> {url2}")
                elif status2 == "limit":
                    bloqueados.add(canal2)
                    log(f"  LIMITE duplo")
                else:
                    total_err += 1
                    log(f"  Erro retry: {status2}")
            else:
                log("  TODOS bloqueados!")
                break
        elif status == "dead":
            bloqueados.add(canal)
            log(f"  DEAD: '{canal}'")
        else:
            total_err += 1
            log(f"  ERRO: {url}")

        time.sleep(3)

    log("\n========== RESUMO ==========")
    log(f"Postados: {total_ok}")
    log(f"Erros:    {total_err}")
    log(f"Bloqueados: {len(bloqueados)}")
    log("Por canal:")
    for c, n in sorted(contagem.items(), key=lambda x: -x[1]):
        log(f"  {c}: {n}")
    log("============================")


if __name__ == "__main__":
    main()
