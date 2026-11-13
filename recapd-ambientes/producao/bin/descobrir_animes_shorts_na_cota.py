from pathlib import Path
from anime_auto import processar_video
import json

root = Path("d:/recapd-ambientes/producao")
base_anime = root / "workspace/anime"

prontos = list(base_anime.rglob("final_anime_short.mp4"))
print(f"Total shorts de animes prontos encontrados: {len(prontos)}")
for t in prontos:
    print(t)
