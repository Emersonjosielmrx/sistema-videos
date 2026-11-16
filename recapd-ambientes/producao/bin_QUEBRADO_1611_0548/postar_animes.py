import json
import os
import subprocess
import time
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Canais de animes puros / IA em português
CANAIS = [
    "repost canalanimescomia", 
    "YouTube inovaremanhwaverseesp"
]

ROOT_DIR = Path("d:/recapd-ambientes/producao")
VIDEOS_DIR = ROOT_DIR / "workspace/anime"
POSTADOS_LOG = ROOT_DIR / "logs/videos_postados.json"
POSTER = "D:/recapd-ambientes/producao/venv/Scripts/python.exe"
YOUTUBE_POSTER = str(Path(__file__).resolve().parent / "youtube_poster.py")

def carregar_postados():
    if Path(POSTADOS_LOG).exists():
        with open(POSTADOS_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def arquivar(video_path):
    """Move o vídeo recem-postado pra <raiz>/postados/anime/... pra nao misturar com originais.
    Depois, apaga a pasta de origem inteira (com roteiro.txt, clipes_landscape/, source.mp4, ...)
    pra nao acumular pasta vazia/lixo no workspace. Exceção: se o destino da pasta original
    NAF for workspace/anime (ex: postar direto de /d/downloads/agendar), NAO apaga.
    """
    import shutil
    p = str(video_path)
    pasta_origem = Path(p).parent
    # Só apaga a pasta de origem se ela estiver dentro de workspace/anime
    em_workspace_anime = False
    try:
        rel = pasta_origem.relative_to(VIDEOS_DIR)
        em_workspace_anime = True
    except ValueError:
        rel = None
    # Move o mp4
    try:
        rel_full = Path(p).relative_to(ROOT_DIR)
    except ValueError:
        return
    dest = ROOT_DIR / 'postados' / 'anime' / Path(*rel_full.parts[1:])  # tira o 'anime' do comeco
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        try: Path(p).unlink()
        except: pass
    else:
        try: shutil.move(p, str(dest))
        except: pass
    # Apaga pasta de origem (só workspace/anime) — depois de mover o mp4
    if em_workspace_anime:
        try:
            shutil.rmtree(pasta_origem)
        except Exception as e:
            print(f"      ! nao foi possivel apagar pasta de origem: {e}")

def salvar_postado(video_path):
    postados = carregar_postados()
    postados.append(str(video_path))
    Path(POSTADOS_LOG).parent.mkdir(exist_ok=True, parents=True)
    with open(POSTADOS_LOG, "w", encoding="utf-8") as f:
        json.dump(postados, f, indent=4)
    arquivar(video_path)

def listar_videos_prontos():
    prontos = []
    # No projeto de animes a saida padrao do pipeline eh final_anime_short.mp4 na pasta de cada um 
    for path in VIDEOS_DIR.rglob("final_anime_short.mp4"):
        prontos.append(path)
            
    return prontos

def postar_video(video_path, canal):
    folder_name = video_path.parent.name
    # Pega um pedaço do nome da pasta (que é o titulo do recap) p/ servir de titulo
    nome = folder_name.split("_", 1)[-1].replace("_", " ").strip()
    if len(nome) < 5: nome = "Resumo Animado"
    
    # Limita tamanho pra n dar pau no youtube
    nome = (nome[:60] + '..') if len(nome) > 60 else nome
    
    titulo = f"{nome} #shorts #anime"
    tags = "anime,resumo,recap,otaku,animação,ia" 
    
    print(f"Postando {video_path.name} ({titulo}) no canal '{canal}'...")
    
    cmd = [
        POSTER, 
        YOUTUBE_POSTER, 
        "--video", str(video_path), 
        "--titulo", titulo,
        "--descricao", f"Inscreva-se para mais resumos de animes e animações incríveis!\n\n#{tags.replace(',', ' #')}",
        "--tags", tags,
        "--canal", canal
    ] 
    
    try:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if "Video id" in proc.stdout or "Upload resumable concluido!" in proc.stdout or "id" in proc.stdout.lower() or proc.returncode == 0:
            print(f"Sucesso. STDOUT: {proc.stdout}")
            salvar_postado(video_path)
            return True
        elif "uploadLimitExceeded" in proc.stderr or "uploadLimitExceeded" in proc.stdout:
            print(f"Limite de upload atingido no canal '{canal}'. Pulando este vídeo.")
            return False  # não salva —下次 tenta o próximo canal
        else:
            print(f"Falha na postagem:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
            return False
    except Exception as e:
        print(f"Erro ao executar youtube_poster: {e}")
        return False

def main():
    prontos = set(listar_videos_prontos())
    postados = set(Path(p) for p in carregar_postados())

    nao_postados = list(prontos - postados)

    if not nao_postados:
        print("Nenhum vídeo novo para postar.")
        return

    nao_postados.sort(key=lambda x: str(x))

    # Rotaciona canais
    idx_canal = len(postados) % len(CANAIS)
    canal_alvo = CANAIS[idx_canal]

    video_alvo = nao_postados[0]

    print(f"Encontrados {len(nao_postados)} vídeos novos do recaps de animes. Postando 1 short agora...")

    if postar_video(video_alvo, canal_alvo):
        print("Finalizado com sucesso. Próxima rodada postará o próximo.")
    else:
        # Canal bloqueou — tenta o próximo canal
        proximo_idx = (idx_canal + 1) % len(CANAIS)
        canal_backup = CANAIS[proximo_idx]
        print(f"Tentando canal backup: {canal_backup}...")
        if postar_video(video_alvo, canal_backup):
            print("Sucesso no canal backup.")
        else:
            # Ambos falharam — marca como tentado pra não travar
            salvar_postado(video_alvo)
            print("Ambos canais falharam. Marcando como tentado.")

if __name__ == "__main__":
    main()
