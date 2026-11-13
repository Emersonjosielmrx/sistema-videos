"""Busca estatísticas (views, likes, comments) de vídeos do YouTube."""
import sys
import json
from googleapiclient.discovery import build
from pathlib import Path

# API key do YouTube (sem OAuth, só leitura pública)
# Precisa estar em D:\credenciais-canais\youtube_api_key.txt
API_KEY_FILE = Path(r"D:\credenciais-canais\youtube_api_key.txt")

def get_video_stats(video_ids):
    """Retorna stats de uma lista de video IDs."""
    if not API_KEY_FILE.exists():
        print("ERRO: Arquivo de API key não encontrado:", API_KEY_FILE, file=sys.stderr)
        print("Crie o arquivo com uma API key do YouTube Data API v3", file=sys.stderr)
        sys.exit(1)

    api_key = API_KEY_FILE.read_text(encoding="utf-8").strip()
    youtube = build("youtube", "v3", developerKey=api_key)

    # API aceita até 50 IDs por request
    results = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        response = youtube.videos().list(
            part="statistics,snippet",
            id=",".join(batch)
        ).execute()

        for item in response.get("items", []):
            video_id = item["id"]
            stats = item["statistics"]
            snippet = item["snippet"]
            results.append({
                "video_id": video_id,
                "title": snippet["title"],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
            })

    return results

if __name__ == "__main__":
    # Le video IDs do stdin (um por linha)
    video_ids = [line.strip() for line in sys.stdin if line.strip()]

    if not video_ids:
        print("ERRO: Nenhum video ID fornecido via stdin", file=sys.stderr)
        sys.exit(1)

    stats = get_video_stats(video_ids)

    # Output como JSON
    print(json.dumps(stats, ensure_ascii=False, indent=2))
