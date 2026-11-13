# -*- coding: utf-8 -*-
"""Orquestrador da Fabrica Viral.

Modos:
  --once        Gera 1 video (criacao ou replica alternando)
  --loop        Loop infinito com intervalo configuravel
  --criacao     Forca modo criacao original
  --replica     Forca modo replica viral
  --canal NOME  Forca canal especifico
"""
import sys
import time
import json
import random
import urllib.request
import urllib.error
import argparse
from pathlib import Path

from config import VEO_API_URL, VEO_API_TOKEN, INTERVALO_GERACAO, VIDEOS_DIR
from agentes import pipeline_criacao, pipeline_replica, CANAIS
from db_local import add_video, update_video, get_pending_videos, get_stats


def enviar_veo(prompt):
    """Envia prompt pro Veo API e retorna job_id."""
    payload = json.dumps({"prompt": prompt, "aspect": "9:16"}).encode()
    headers = {"Content-Type": "application/json"}
    if VEO_API_TOKEN:
        headers["Authorization"] = f"Bearer {VEO_API_TOKEN}"
    req = urllib.request.Request(
        f"{VEO_API_URL}/v1/jobs", data=payload, headers=headers, method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        return data.get("job_id")
    except Exception as e:
        print(f"[orq] erro ao enviar pro Veo: {e}")
        return None


def poll_veo(job_id, timeout=900, interval=30):
    """Poll ate o video ficar pronto. Tolera 404 transitorio (server reiniciou)."""
    headers = {}
    if VEO_API_TOKEN:
        headers["Authorization"] = f"Bearer {VEO_API_TOKEN}"
    deadline = time.time() + timeout
    consecutive_404 = 0
    MAX_404 = 5  # desiste apos 5 seguidos (server morreu de vez)
    while time.time() < deadline:
        try:
            req = urllib.request.Request(
                f"{VEO_API_URL}/v1/jobs/{job_id}", headers=headers
            )
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            status = data.get("status", "")
            consecutive_404 = 0
            if status == "done":
                return data
            if status == "error":
                print(f"[orq] Veo erro: {data.get('error', '?')}")
                return None
            remaining = int(deadline - time.time())
            print(f"[orq] Veo {status}... ({remaining}s restantes)")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                consecutive_404 += 1
                print(f"[orq] 404 ({consecutive_404}/{MAX_404}) — server pode ter reiniciado")
                if consecutive_404 >= MAX_404:
                    print("[orq] muitos 404 seguidos, desistindo")
                    return None
                time.sleep(min(interval * 2, 60))
                continue
            print(f"[orq] erro poll: {e}")
        except Exception as e:
            print(f"[orq] erro poll: {e}")
        time.sleep(interval)
    print("[orq] timeout esperando Veo")
    return None


def baixar_video(job_id):
    """Baixa o mp4 do Veo."""
    headers = {}
    if VEO_API_TOKEN:
        headers["Authorization"] = f"Bearer {VEO_API_TOKEN}"
    url = f"{VEO_API_URL}/v1/jobs/{job_id}/video"
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=60)
        out_path = VIDEOS_DIR / f"{job_id}.mp4"
        out_path.write_bytes(resp.read())
        size = out_path.stat().st_size
        if size > 10000:
            print(f"[orq] Video salvo: {out_path} ({size/1024/1024:.1f} MB)")
            return str(out_path)
        else:
            print(f"[orq] Video muito pequeno: {size} bytes")
            out_path.unlink()
            return None
    except Exception as e:
        print(f"[orq] erro download: {e}")
        return None


def gerar_um(modo=None, canal_nome=None):
    """Gera 1 video completo (prompt -> Veo -> download)."""
    canal = None
    if canal_nome:
        canal = next((c for c in CANAIS if c["nome"].lower() == canal_nome.lower()), None)

    # Decide modo
    if not modo:
        modo = random.choice(["criacao", "replica"])

    print(f"\n{'='*60}")
    print(f"[orq] Modo: {modo.upper()}")
    print(f"{'='*60}")

    # Gerar prompt
    if modo == "criacao":
        resultado = pipeline_criacao(canal)
    else:
        resultado = pipeline_replica(canal=canal)

    if not resultado or not resultado.get("prompt_video"):
        print("[orq] Falha na geracao do prompt")
        return None

    print(f"[orq] Titulo: {resultado['titulo'][:80]}")
    print(f"[orq] Prompt: {resultado['prompt_video'][:120]}...")

    # Salvar no banco
    db_id = add_video(
        canal=resultado.get("canal", ""),
        modo=resultado["modo"],
        titulo=resultado["titulo"],
        prompt_video=resultado["prompt_video"],
        source_url=resultado.get("source_url", ""),
        source_titulo=resultado.get("source_titulo", ""),
    )

    # Enviar pro Veo
    print("[orq] Enviando pro Veo API...")
    veo_job = enviar_veo(resultado["prompt_video"])
    if not veo_job:
        update_video(db_id, status="error", error="falha ao enviar pro Veo")
        return None

    update_video(db_id, veo_job_id=veo_job, status="rendering", started_at=time.time())
    print(f"[orq] Veo job: {veo_job}")

    # Poll
    veo_result = poll_veo(veo_job)
    if not veo_result:
        update_video(db_id, status="error", error="timeout ou erro no Veo")
        return None

    # Download
    video_path = baixar_video(veo_job)
    if video_path:
        update_video(db_id, status="done", video_path=video_path, finished_at=time.time())
        print(f"[orq] SUCESSO! Video pronto: {video_path}")
        return {"db_id": db_id, "video_path": video_path, "titulo": resultado["titulo"]}
    else:
        update_video(db_id, status="error", error="falha no download")
        return None


def loop(modo=None, canal_nome=None):
    """Loop infinito gerando videos."""
    print(f"[orq] Iniciando loop (intervalo: {INTERVALO_GERACAO}s)")
    stats = get_stats()
    print(f"[orq] Stats: {stats}")

    while True:
        try:
            result = gerar_um(modo=modo, canal_nome=canal_nome)
            if result:
                print(f"[orq] Video #{get_stats()['done']} concluido!")
            else:
                print("[orq] Falha nesta iteracao, continuando...")
        except Exception as e:
            print(f"[orq] ERRO: {e}")

        print(f"[orq] Aguardando {INTERVALO_GERACAO}s...")
        time.sleep(INTERVALO_GERACAO)


def main():
    parser = argparse.ArgumentParser(description="Fabrica Viral - Orquestrador")
    parser.add_argument("--once", action="store_true", help="Gera 1 video e sai")
    parser.add_argument("--loop", action="store_true", help="Loop infinito")
    parser.add_argument("--criacao", action="store_true", help="Modo criacao original")
    parser.add_argument("--replica", action="store_true", help="Modo replica viral")
    parser.add_argument("--canal", type=str, help="Nome do canal")
    args = parser.parse_args()

    modo = None
    if args.criacao:
        modo = "criacao"
    elif args.replica:
        modo = "replica"

    if args.loop:
        loop(modo=modo, canal_nome=args.canal)
    else:
        gerar_um(modo=modo, canal_nome=args.canal)


if __name__ == "__main__":
    main()