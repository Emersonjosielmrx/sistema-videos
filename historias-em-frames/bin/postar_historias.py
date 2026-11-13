import json
import os
import subprocess
import time
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Canais variados para postar terror e superação
CANAIS = [
    "raiz3 emersonjosielmrx1995(curiosidade", 
    "raiz fabricadeautomacoes0(ia pro"
]

ROOT_DIR = Path(__file__).resolve().parent.parent
# saida configuravel por pista (mesma env do hp_common); fallback local
from hp_common import VIDEOS_DIR  # noqa: E402  (hipercool-materiais; HEF_VIDEOS_DIR ainda vale)
POSTADOS_LOG = ROOT_DIR / "logs/videos_postados.json"
# venv e poster da PROPRIA pista (sem depender de outro projeto)
_local_py = ROOT_DIR / "venv" / "Scripts" / "python.exe"
POSTER = str(_local_py) if _local_py.exists() else sys.executable
YOUTUBE_POSTER = str(ROOT_DIR / "bin" / "youtube_poster.py")

def carregar_postados():
    if Path(POSTADOS_LOG).exists():
        with open(POSTADOS_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def arquivar(video_path):
    """Move o vídeo recem-postado para <raiz>/postados/<categoria>/... pra nao misturar com originais."""
    import shutil
    p = str(video_path)
    rel = None
    try:
        rel = Path(p).relative_to(ROOT_DIR)
    except ValueError:
        return
    parts = rel.parts
    # achar categoria
    cats = ['terror', 'misterio', 'comedia', 'romance', 'drama',
            'superacao', 'motivacional', 'religioso', 'fantasia']
    cat = next((c for c in cats if c in parts), 'outros')
    try:
        idx = parts.index(cat)
        sufixo = Path(*parts[idx+1:])
    except ValueError:
        sufixo = Path(p).name
    # destino central unico de todos os postados (categoria historias-em-frames, subpasta = genero)
    dest = Path(r"D:\hipercool-materiais\_postados\historias-em-frames") / cat / sufixo
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        try: Path(p).unlink()
        except: pass
    else:
        try: shutil.move(p, str(dest))
        except: pass

def salvar_postado(video_path):
    postados = carregar_postados()
    postados.append(str(video_path))
    Path(POSTADOS_LOG).parent.mkdir(exist_ok=True, parents=True)
    with open(POSTADOS_LOG, "w", encoding="utf-8") as f:
        json.dump(postados, f, indent=4)
    # Arquiva no disco pra nao misturar com os ainda-pendentes
    arquivar(video_path)

def listar_videos_prontos():
    prontos = []
    # Usar _ULTIMO.mp4 (limpo sem marca d'água de teste) ou o arquivo aprovado
    for path in VIDEOS_DIR.rglob("*_FINAL_ULTIMO.mp4"):
        if "_quarantine" not in str(path):
            prontos.append(path)
            
    for path in VIDEOS_DIR.rglob("*_APROVADO_*.mp4"):
        if "_quarantine" not in str(path):
            prontos.append(path)
            
    return prontos

def postar_video(video_path, canal):
    print(f"Postando {video_path.name} no canal '{canal}'...")
    
    tags = "história,superação,motivação,ia,animação" if "superacao" in str(video_path).lower() else "terror,assustador,história,ia,creepypasta"
    titulo = "Uma história de " + ("Superação Incrível #shorts" if "superacao" in str(video_path).lower() else "Terror Perturbadora #shorts")
    
    cmd = [
        POSTER, 
        YOUTUBE_POSTER, 
        "--video", str(video_path), 
        "--titulo", titulo,
        "--descricao", f"Se inscreva para mais conteúdos! #shorts #{tags.replace(',', ' #')}",
        "--tags", tags,
        "--canal", canal
    ] 
    
    try:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if "Video id" in proc.stdout or "Upload resumable concluido!" in proc.stdout or proc.returncode == 0:
            print(f"Sucesso. STDOUT: {proc.stdout}")
            salvar_postado(video_path)
            return True
        elif "uploadLimitExceeded" in proc.stderr or "uploadLimitExceeded" in proc.stdout or "rateLimitExceeded" in proc.stderr or "rateLimitExceeded" in proc.stdout:
            print(f"Limite de upload/rate atingido. Aguardar ~24h.")
            return False
        else:
            print(f"Falha:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
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
        
    nao_postados.sort(key=str) # pra ficar deterministico mas vc testa em ordem
    
    # Rotaciona canais baseado em quanntos ja foram postados
    idx_canal = len(postados) % len(CANAIS)
    canal_alvo = CANAIS[idx_canal]
    
    # Pega o primeiro e posta
    video_alvo = nao_postados[0]
    
    print(f"Encontrados {len(nao_postados)} vídeos novos. Postando 1 agora...")

    if postar_video(video_alvo, canal_alvo):
        print("Finalizado com sucesso. Próxima rodada postará o próximo.")
    else:
        proximo_idx = (idx_canal + 1) % len(CANAIS)
        canal_backup = CANAIS[proximo_idx]
        print(f"Tentando canal backup: {canal_backup}...")
        if postar_video(video_alvo, canal_backup):
            print("Sucesso no canal backup.")
        else:
            print("Ambos canais falharam.")

if __name__ == "__main__":
    main()
