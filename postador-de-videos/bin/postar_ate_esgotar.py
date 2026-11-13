#!/usr/bin/env python3
"""
Posta vídeos nos canais até CADA UM dar erro individualmente.
Usa todas as fontes de vídeo disponíveis. Move postados para postados/.
"""
import os
import json
import shutil
import subprocess
from pathlib import Path

POSTADOS_DIR = Path(r"D:\hipercool-materiais\_postados\vo3")
PY_EXE = Path(r"D:\hipercool-videos\venv\Scripts\python.exe")
POSTER_SCRIPT = Path(r"D:\postador-de-videos\bin\youtube_poster.py")
CREDS_FILE = Path(r"D:\credenciais-canais\youtube_canais.json")

SKIP = {
    "emersonjosiel1995( motivação",
    "emersonjosiel1995nov(motivação",
    "enpresainovare (financeiro",
    "fabio com ia",
    "inovare recap manga",
    "nova conta de manga br",
}

def carregar_canais():
    with open(CREDS_FILE, "r", encoding="utf-8") as f:
        canais = json.load(f)
    validos = [c for c in canais if c.get("nome", "") not in SKIP]
    print(f"Canais validos: {len(validos)} (pulando {len(canais)-len(validos)} mortos)")
    return validos

def get_todos_videos():
    """Coleta videos de TODAS as fontes disponiveis."""
    videos = []
    fontes = [
        Path(r"D:\openclaw-videos\videos-produzidos-v2"),
        Path(r"D:\openclaw-videos\videos-produzidos"),
        Path(r"D:\hipercool-inferior-fix\roteador-veo-api-fake\videos\api_jobs"),
    ]
    for pasta in fontes:
        if pasta.exists():
            for v in sorted(pasta.glob("*.mp4")):
                if v.stat().st_size > 50000:  # ignora arquivos tiny/corrompidos
                    videos.append(v)
    print(f"Total de videos disponiveis: {len(videos)}")
    return videos

def gerar_titulo(video_path):
    nome = video_path.stem.replace("_broll", "").replace("_", " ")
    # Remove prefixos hash
    partes = nome.split(" ", 1)
    if len(partes) > 1 and len(partes[0]) > 10:
        nome = partes[1]
    titulo = f"Tutorial IA - {nome.title()}"
    if len(titulo) > 95:
        titulo = titulo[:95] + "..."
    return titulo

def postar_video(canal, video_path):
    """Tenta postar 1 video. Retorna: 'ok', 'limit', 'dead', 'error'"""
    titulo = gerar_titulo(video_path)
    desc = f"{titulo}\n\n#IA #Automacao #Tutorial #n8n #Python"
    env = dict(os.environ, PYTHONUTF8="1")
    cmd = [
        str(PY_EXE), str(POSTER_SCRIPT),
        "--video", str(video_path),
        "--titulo", titulo,
        "--descricao", desc,
        "--canal", str(canal.get("id")),
        "--privacy", "private"
    ]
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
        out = r.stdout + (r.stderr or "")
        if r.returncode == 0 and ("Upload Completo" in out or "https://youtu.be" in out):
            return "ok"
        if "uploadLimitExceeded" in out or "rateLimitExceeded" in out or "quotaExceeded" in out:
            return "limit"
        if "invalid_grant" in out or "authenticatedUserAccountSuspended" in out or "invalid_client" in out:
            return "dead"
        # Print erro pra debug
        for linha in out.splitlines():
            if "ERRO" in linha.upper() or "error" in linha.lower():
                print(f"      ! {linha.strip()[:120]}")
                break
        return "error"
    except subprocess.TimeoutExpired:
        return "timeout"

def main():
    POSTADOS_DIR.mkdir(parents=True, exist_ok=True)
    canais = carregar_canais()
    videos = get_todos_videos()

    if not videos:
        print("Sem videos!")
        return

    video_idx = 0
    resultados = {}

    for canal in canais:
        cnome = canal.get("nome", canal.get("id"))
        print(f"\n{'='*50}")
        print(f"CANAL: {cnome}")
        print(f"{'='*50}")

        contagem = 0
        erros_seguidos = 0

        while video_idx < len(videos):
            video_path = videos[video_idx]
            print(f"  [{contagem+1}] {video_path.name[:55]}...", end=" ")

            resultado = postar_video(canal, video_path)

            if resultado == "ok":
                contagem += 1
                erros_seguidos = 0
                print(f"OK")
                # Move pra postados
                dest = POSTADOS_DIR / video_path.name
                if dest.exists():
                    dest = POSTADOS_DIR / f"{video_path.stem}_{contagem}{video_path.suffix}"
                try:
                    shutil.move(str(video_path), str(dest))
                except Exception:
                    pass
                video_idx += 1

            elif resultado == "limit":
                print(f"LIMITE! (postou {contagem})")
                break

            elif resultado == "dead":
                print(f"MORTO/EXPIRADO")
                break

            elif resultado == "timeout":
                erros_seguidos += 1
                print(f"TIMEOUT")
                if erros_seguidos >= 2:
                    print(f"  -> 2 timeouts seguidos, pulando canal")
                    break
                video_idx += 1

            else:
                erros_seguidos += 1
                print(f"ERRO")
                if erros_seguidos >= 3:
                    print(f"  -> 3 erros seguidos, pulando canal")
                    break
                # Tenta proximo video no mesmo canal
                video_idx += 1

        resultados[cnome] = contagem
        if video_idx >= len(videos):
            print("\n*** ACABARAM OS VIDEOS ***")
            break

    # Resumo
    print(f"\n{'='*60}")
    print("RESUMO FINAL — LIMITE REAL POR CANAL:")
    print(f"{'='*60}")
    total = 0
    for nome, qtd in sorted(resultados.items(), key=lambda x: -x[1]):
        status = f"{qtd} videos" if qtd > 0 else "0 (morto/limite previo)"
        total += qtd
        print(f"  {nome[:42]:42s} | {status}")
    print(f"\n  TOTAL POSTADOS HOJE: {total}")
    print(f"  Videos restantes: {len(videos) - video_idx}")

if __name__ == "__main__":
    main()
