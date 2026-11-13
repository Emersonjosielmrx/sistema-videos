#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""postar_shorts_agendado.py — Posta 1 Short do hipercool por vez, respeitando intervalo e pico.

Chamado por cron ou pela fila de postagem. Pega o próximo Short não postado do cap mais antigo
e posta se estiver dentro do pico e tiver passado o intervalo desde o último upload.
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "bin"))
from hp_common import log  # noqa: E402

CONFIG = PROJECT / "config" / "fila.json"
ESTADO = PROJECT / "workspace" / "fila_estado.json"
LEDGER_DIR = Path(r"D:\postador-de-videos\ledger")

PY = str(PROJECT / "venv" / "Scripts" / "python.exe")


def cfg():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def ler_estado():
    if not ESTADO.exists():
        return {}
    return json.loads(ESTADO.read_text(encoding="utf-8"))


def canal_pt():
    return cfg().get("canal_pt") or "inovaremanhwabr"


def ultimo_upload_canal():
    """Retorna datetime do último upload do canal pt, ou None."""
    canal = canal_pt()
    if not LEDGER_DIR.exists():
        return None

    # Lê todos os arquivos do ledger deste canal
    uploads = []
    for arq in LEDGER_DIR.glob(f"{canal}__*.json"):
        try:
            dados = json.loads(arq.read_text(encoding="utf-8"))
            if dados.get("projeto") == "manhwa-react" and dados.get("quando"):
                uploads.append(dados["quando"])
        except Exception:
            continue

    if not uploads:
        return None

    ultimo = max(uploads)
    return datetime.fromisoformat(ultimo.replace("Z", "+00:00"))


def pode_postar_agora():
    """Verifica se está no horário de pico e se já passou o intervalo desde o último upload."""
    c = cfg()
    post_cfg = c.get("postagem_pt", {})
    fuso = post_cfg.get("fuso", "America/Sao_Paulo")
    pico = post_cfg.get("pico", [18, 23])
    intervalo_h = post_cfg.get("intervalo_h", 2)

    agora = datetime.now(ZoneInfo(fuso))
    hora = agora.hour

    # Verifica se está no pico
    if not (pico[0] <= hora < pico[1]):
        log(f"Fora do pico ({pico[0]}h-{pico[1]}h): agora são {hora}h")
        return False

    # Verifica intervalo desde último upload
    ultimo_dt = ultimo_upload_canal()
    if ultimo_dt:
        ultimo_local = ultimo_dt.astimezone(ZoneInfo(fuso))
        desde = (agora - ultimo_local).total_seconds() / 3600
        if desde < intervalo_h:
            log(f"Intervalo insuficiente: {desde:.1f}h desde último upload (mín {intervalo_h}h)")
            return False

    return True


def proximo_short_nao_postado():
    """Retorna (video_completo, numero_parte) do próximo Short não postado, ou None."""
    estado = ler_estado()

    # Ordena caps por número
    caps = sorted([k for k in estado.keys() if k.startswith("the-inheritor-cap")],
                  key=lambda x: int(x.split("cap")[-1]))

    for cap_key in caps:
        cap = estado[cap_key]
        if cap.get("situacao") != "pronto":
            continue

        video_rel = cap.get("video")
        if not video_rel:
            continue

        # Acha o vídeo censurado
        video = PROJECT / "workspace" / "videos" / video_rel
        if "_CENSURADO" not in video.stem:
            # Procura a versão censurada
            base = video.stem.replace("_ULTIMO", "")
            censurado = video.parent.parent / "censurado" / f"{base}_CENSURADO_ULTIMO.mp4"
            if not censurado.exists():
                censurado = video.with_name(f"{base}_CENSURADO_ULTIMO.mp4")
            if censurado.exists():
                video = censurado

        if not video.exists():
            continue

        # Verifica quais shorts já foram postados
        meta_shorts = video.parent / "meta_shorts.json"
        if not meta_shorts.exists():
            continue

        try:
            shorts_info = json.loads(meta_shorts.read_text(encoding="utf-8"))
            num_shorts = len(shorts_info.get("shorts", []))
        except Exception:
            continue

        # Conta quantos já foram postados verificando o ledger
        postados = 0
        canal = canal_pt()
        for parte in range(1, num_shorts + 1):
            # Nome do short no ledger
            short_nome = f"the-inheritor_cap{cap_key.split('cap')[-1]}_parte{parte:02d}.mp4"
            ledger_arq = LEDGER_DIR / f"{canal}__{short_nome}.json"
            if ledger_arq.exists():
                postados += 1

        if postados < num_shorts:
            return str(video), postados + 1

    return None, None


def main():
    log("desativado em 16/10 15h: sem --max-novos ele subia todos os Shorts de uma vez. "
        "Quem posta os Shorts do cap 1 é bin/shorts_a_cada_2h.py (tarefa HipercoolShorts2h).")
    return
    force = "--force-now" in sys.argv

    if not force and not pode_postar_agora():
        return

    if force:
        log("Forçando postagem imediata (--force-now)")

    video, parte = proximo_short_nao_postado()
    if not video:
        log("Nenhum Short pendente para postar")
        return

    log(f"Postando Short parte {parte} de {Path(video).parent.parent.name}")

    cmd = [
        PY,
        str(PROJECT / "bin" / "postar_hipercool.py"),
        "--video", video,
        "--no-completo",
        "--aprovado"
    ]

    try:
        subprocess.run(cmd, check=True, cwd=PROJECT)
        log(f"✓ Short parte {parte} postado")
    except subprocess.CalledProcessError as e:
        log(f"✗ Erro ao postar: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
