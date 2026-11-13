# -*- coding: utf-8 -*-
"""Cliente de metricas: busca views/likes de videos postados em varias plataformas.

Plataformas suportadas:
- YouTube Shorts (via YouTube Data API v3 - requer API key)
- TikTok (via scraping da pagina publica - com cuidado)
- Instagram Reels (via scraping pag publica - com cuidado)

Para usar YouTube: exporte YOUTUBE_API_KEY=AIza...
Para TikTok/IG: passar URLs explicitamente (scraping).
"""
import os, sys, json, time, urllib.request, urllib.parse, re
from datetime import datetime, timedelta

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "logs", "video_cache.json")

# YOUTUBE DATA API v3 ---------------------------------------------------
def youtube_search_video_by_title(titulo, canal_youtube, api_key=None):
    """Busca video no YouTube por titulo+canal. Retorna video_id ou None."""
    api_key = api_key or os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        return None
    try:
        q = urllib.parse.quote(f"{titulo} {canal_youtube}")
        url = f"https://www.googleapis.com/youtube/v3/search?part=id&q={q}&maxResults=5&type=video&key={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        for item in data.get("items", []):
            return item["id"]["videoId"]
    except Exception as e:
        log(f"[yt] search falhou: {e}")
    return None


def youtube_video_stats(video_id, api_key=None):
    """Retorna dict com views, likes, comments."""
    api_key = api_key or os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        return {}
    try:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if data.get("items"):
            stats = data["items"][0].get("statistics", {})
            return {
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
            }
    except Exception as e:
        log(f"[yt] stats falhou: {e}")
    return {}


# TIKTOK / INSTAGRAM (scraping simples) ---------------------------------
def _scrape_og_meta(url):
    """Extrai og:description e outros meta de uma URL publica."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        # Procura patterns comuns de views/likes
        out = {}
        # Play count
        m = re.search(r'"playCount":\s*(\d+)', html)
        if m: out["views"] = int(m.group(1))
        # Like count
        m = re.search(r'"diggCount":\s*(\d+)', html)
        if m: out["likes"] = int(m.group(1))
        # Comment count
        m = re.search(r'"commentCount":\s*(\d+)', html)
        if m: out["comments"] = int(m.group(1))
        # Share count
        m = re.search(r'"shareCount":\s*(\d+)', html)
        if m: out["shares"] = int(m.group(1))
        return out
    except Exception as e:
        log(f"[scrape] {url[:60]} falhou: {e}")
        return {}


def tiktok_metrics(url):
    """Extrai metricas de um TikTok via og tags."""
    return _scrape_og_meta(url)


def instagram_metrics(url):
    """Extrai metricas de um Instagram Reel via og tags."""
    return _scrape_og_meta(url)


# INTEGRACAO COM CACHE -------------------------------------------------
def load_cache():
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def update_cache_metrics(video_id, metrics):
    """Atualiza metricas de um video no cache."""
    cache = load_cache()
    for item in cache:
        if item["id"] == video_id:
            item["metrics"].update(metrics)
            item["metrics_updated_at"] = datetime.now().isoformat(timespec="seconds")
            # Calcula engagement rate
            v = metrics.get("views", 0)
            l = metrics.get("likes", 0)
            c = metrics.get("comments", 0)
            if v > 0:
                item["metrics"]["engagement_rate"] = round((l + c) / v * 100, 2)
            save_cache(cache)
            log(f"[metrics] {video_id}: {metrics}")
            return True
    return False


def auto_update_all(yt_api_key=None, max_yt_calls=50):
    """Atualiza metricas de todos os videos com titulo_postado no cache.

    Para cada video, se tem metricas.posted_url, busca.
    Para cada video sem metricas mas com video_path, tenta YouTube search.
    """
    cache = load_cache()
    yt_calls = 0
    for item in cache:
        if not item.get("video_path"):
            continue
        # Se ja tem URL postada
        url = (item.get("metrics") or {}).get("posted_url")
        if url:
            if "tiktok.com" in url:
                m = tiktok_metrics(url)
                if m:
                    update_cache_metrics(item["id"], m)
            elif "instagram.com" in url:
                m = instagram_metrics(url)
                if m:
                    update_cache_metrics(item["id"], m)
            elif "youtube.com" in url or "youtu.be" in url:
                m = re.search(r'(?:v=|youtu\.be/)([\w-]+)', url)
                if m and yt_calls < max_yt_calls:
                    vid = m.group(1)
                    m = youtube_video_stats(vid, api_key=yt_api_key)
                    if m:
                        update_cache_metrics(item["id"], m)
                    yt_calls += 1
                    time.sleep(0.1)
        # YouTube: tenta por titulo + canal
        elif not item.get("metrics", {}).get("views") and yt_calls < max_yt_calls:
            vid = youtube_search_video_by_title(
                item.get("fala", "")[:50],
                item.get("canal", ""),
                api_key=yt_api_key,
            )
            if vid:
                m = youtube_video_stats(vid, api_key=yt_api_key)
                if m:
                    update_cache_metrics(item["id"], m)
                yt_calls += 1
                time.sleep(0.1)


# ---------------------------------------------------------------------------
# FASE 17: Auto-update bio com link do produto (top video)
# ---------------------------------------------------------------------------
def gerar_bio(canal_nome, top_video=None, link="https://exemplo.com"):
    """Gera bio otimizada para o canal usando o top video como gancho."""
    if top_video:
        fala = top_video.get("fala", "")[:60]
        return f"🤖 {canal_nome} | Videos virais com IA 🎬\n👀 Mais visto: \"{fala}\"\n🔗 {link}"
    return f"🤖 {canal_nome} | Videos virais com IA 🎬\n🔗 {link}"


def auto_update_bio_tiktok():
    """Atualiza bio do TikTok via browser logado."""
    try:
        from selenium import webdriver
        # Para simplicidade, so mostra o que faria
        cache = load_cache()
        com_views = [c for c in cache if c.get("metrics", {}).get("views", 0) > 100]
        if not com_views:
            log("[bio] sem videos com views ainda")
            return
        top = max(com_views, key=lambda c: c["metrics"]["views"])
        canal = top.get("canal", "")
        bio = gerar_bio(canal, top)
        log(f"[bio] bio gerada para '{canal}':")
        log(f"  {bio}")
        # TODO: aplicar via Selenium no tiktok.com/edit-profile
    except Exception as e:
        log(f"[bio] falhou: {e}")


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "update":
        auto_update_all()
    elif cmd == "single":
        # metrics_client.py single VIDEO_ID URL
        vid = sys.argv[2]
        url = sys.argv[3]
        if "youtube" in url or "youtu.be" in url:
            m = re.search(r'(?:v=|youtu\.be/)([\w-]+)', url)
            if m:
                stats = youtube_video_stats(m.group(1))
            else:
                stats = {}
        elif "tiktok" in url:
            stats = tiktok_metrics(url)
        elif "instagram" in url:
            stats = instagram_metrics(url)
        else:
            stats = {}
        if stats:
            update_cache_metrics(vid, stats)
            print(f"OK: {stats}")
        else:
            print("falhou")
    elif cmd == "help":
        print("uso: metrics_client.py update")
        print("     metrics_client.py single VIDEO_ID URL")
        print("env: YOUTUBE_API_KEY=... (opcional)")
