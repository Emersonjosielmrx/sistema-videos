"""Busca views de videos via scraping da pagina publica (fallback sem API key)."""
import sys
import json
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_video_views(video_id):
    """Extrai view count da pagina publica do YouTube."""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Procura por "viewCount":"NUMBER" no HTML
        match = re.search(r'"viewCount":"(\d+)"', response.text)
        if match:
            views = int(match.group(1))
            return {"video_id": video_id, "views": views, "error": None}
        else:
            # Tenta outro padrao
            match2 = re.search(r'{"viewCount":{"simpleText":"([\d,\.]+)', response.text)
            if match2:
                views_str = match2.group(1).replace(",", "").replace(".", "")
                views = int(views_str) if views_str.isdigit() else 0
                return {"video_id": video_id, "views": views, "error": None}

            return {"video_id": video_id, "views": 0, "error": "view count not found"}
    except Exception as e:
        return {"video_id": video_id, "views": 0, "error": str(e)}

if __name__ == "__main__":
    video_ids = [line.strip() for line in sys.stdin if line.strip()]

    if not video_ids:
        print(json.dumps({"error": "No video IDs provided"}), file=sys.stderr)
        sys.exit(1)

    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(get_video_views, vid): vid for vid in video_ids}
        for future in as_completed(futures):
            results.append(future.result())

    # Sort by video_id order
    results.sort(key=lambda x: video_ids.index(x["video_id"]))

    print(json.dumps(results, ensure_ascii=False, indent=2))
