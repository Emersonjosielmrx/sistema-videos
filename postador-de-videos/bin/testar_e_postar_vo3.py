#!/usr/bin/env python3
"""
Testa as postagens de vídeos V03 (OpenClaw) canal a canal e os move.
"""
import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# Diretórios
VIDEOS_DIR = Path(r"D:\openclaw-videos\videos-produzidos-v2")
ROTEIROS_DIR = Path(r"D:\openclaw-videos\roteiros")
# Destino central unico de todos os postados (por categoria)
POSTADOS_DIR = Path(r"D:\hipercool-materiais\_postados\vo3")

# Caminhos dos Executáveis e Configs
PY_EXE = Path(r"D:\hipercool-videos\venv\Scripts\python.exe")
POSTER_SCRIPT = Path(r"D:\postador-de-videos\bin\youtube_poster.py")
CREDS_FILE = Path(r"D:\credenciais-canais\youtube_canais.json")

def carregar_canais():
    with open(CREDS_FILE, "r", encoding="utf-8") as f:
        canais = json.load(f)
    print(f"Total de canais disponíveis no JSON: {len(canais)}")
    return canais

def get_broll_videos():
    videos = []
    if not VIDEOS_DIR.exists():
        return videos
    for v in VIDEOS_DIR.glob("*.mp4"):
        nome_base = v.stem.replace("_broll", "")
        # Checa se o roteiro.md existe.
        md_file = ROTEIROS_DIR / f"{nome_base}.md"
        if md_file.exists():
            videos.append((v, md_file))
    return sorted(videos)

def limpar_angle_brackets(txt):
    """YouTube recusa descrições com < ou > (causa HTTP 400 invalidDescription)"""
    return txt.replace('<', '〈').replace('>', '〉')

def ler_roteiro(md_path):
    titulo = "Sem Título - Tutorial de IA"
    descricao = ""
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            linhas = f.readlines()
            for l in linhas:
                if l.startswith("# "):
                    titulo = l.replace("#", "").strip()
                    break
            descricao = "".join(linhas)
            if len(titulo) > 95:
                titulo = titulo[:95] + "..."
    except Exception as e:
        print(f"Erro lendo roteiro {md_path.name}: {e}")
    return limpar_angle_brackets(titulo), limpar_angle_brackets(descricao)

def testar_postagem():
    POSTADOS_DIR.mkdir(parents=True, exist_ok=True)
    
    canais = carregar_canais()
    videos = get_broll_videos()
    
    if not videos:
        print("Nenhum vídeo com roteiro encontrado!")
        return

    print(f"Total de {len(videos)} vídeos alinhados a roteiros.")

    env = dict(os.environ, PYTHONUTF8="1")
    
    videos_para_testar = videos[:len(canais)]

    print("\nIniciando testes de postagem do V03 nos canais da API:")
    
    # Loop em todos os canais/vídeos disponíveis!
    for indice, (video_path, md_path) in enumerate(videos_para_testar):

        canal = canais[indice]
        canal_nome = canal.get("nome", canal.get("id"))
        
        # Pula canais mortos sabidos
        if canal_nome in ["emersonjosiel1995nov", "enpresainovare", "fabio com ia"]:
            print(f"[{indice}] Pulo do Canal Morto: {canal_nome}")
            continue
            
        print(f"[{indice}] Canal: {canal_nome} | Vídeo: {video_path.name}")
        
        titulo, descricao = ler_roteiro(md_path)
        
        cmd = [
            str(PY_EXE), str(POSTER_SCRIPT),
            "--video", str(video_path),
            "--titulo", titulo,
            "--descricao", descricao,
            "--canal", str(canal.get("id", canal_nome)),
            "--privacy", "private"
        ]

        try:
            r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
            stdout_txt = r.stdout
            if r.returncode == 0 and ("Upload Completo" in stdout_txt or "https://youtu.be" in stdout_txt):
                print(f" -> [SUCESSO] Postado no canal {canal_nome}!")
                
                d_video_move = POSTADOS_DIR / video_path.name
                d_md_move = POSTADOS_DIR / md_path.name
                
                try:
                    shutil.move(str(video_path), str(d_video_move))
                    shutil.move(str(md_path), str(d_md_move))
                    print(f" -> Movido para {POSTADOS_DIR.name}/")
                except Exception as e:
                    print(f" -> [ERRO] falha ao mover: {e}")
            else:
                print(f" -> [FALHA] Código {r.returncode}")
                # Print API JSON errors
                for linha in stdout_txt.splitlines() + (r.stderr.splitlines() if r.stderr else []):
                    if "ERRO 4" in linha.upper() or "error" in linha.lower() or "suspen" in linha.lower():
                        print(f"    ! {linha.strip()}")
        except subprocess.TimeoutExpired:
            print(f" -> [FALHA] Timeout no envio!")
            
if __name__ == "__main__":
    testar_postagem()
