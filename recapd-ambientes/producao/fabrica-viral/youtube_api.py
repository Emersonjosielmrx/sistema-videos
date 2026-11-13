# -*- coding: utf-8 -*-
"""YouTube Data API - pesquisa e estatisticas."""
import json
import urllib.request
import urllib.parse
from config import YT_API_KEY


def search_shorts(query, max_results=20, region="BR", language="pt", published_after=None):
    """Pesquisa shorts virais no YouTube."""
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoDuration": "short",
        "order": "viewCount",
        "maxResults": min(max_results, 50),
        "regionCode": region,
        "relevanceLanguage": language,
        "key": YT_API_KEY,
    }
    if published_after:
        params["publishedAfter"] = published_after

    url = "https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        results = []
        for item in data.get("items", []):
            vid = item.get("id", {}).get("videoId")
            if vid:
                results.append({
                    "video_id": vid,
                    "title": item["snippet"]["title"],
                    "channel": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                    "thumbnail": item["snippet"]["thumbnails"].get("high", {}).get("url", ""),
                    "url": f"https://www.youtube.com/shorts/{vid}",
                })
        return results
    except Exception as e:
        print(f"[youtube] erro search: {e}")
        return []


def get_video_stats(video_ids):
    """Pega estatisticas de uma lista de video IDs."""
    if isinstance(video_ids, str):
        video_ids = [video_ids]
    ids_str = ",".join(video_ids[:50])
    params = {
        "part": "snippet,statistics",
        "id": ids_str,
        "key": YT_API_KEY,
    }
    url = "https://www.googleapis.com/youtube/v3/videos?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        results = {}
        for item in data.get("items", []):
            vid = item["id"]
            stats = item.get("statistics", {})
            results[vid] = {
                "title": item["snippet"]["title"],
                "description": item["snippet"].get("description", "")[:500],
                "channel": item["snippet"]["channelTitle"],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "thumbnail": item["snippet"]["thumbnails"].get("maxres", 
                    item["snippet"]["thumbnails"].get("high", {})).get("url", ""),
            }
        return results
    except Exception as e:
        print(f"[youtube] erro stats: {e}")
        return {}


def search_trending(query, max_results=10):
    """Busca videos trending (por relevancia recente)."""
    params = {
        "part": "snippet",
        "q": query + " #shorts",
        "type": "video",
        "videoDuration": "short",
        "order": "date",
        "maxResults": max_results,
        "regionCode": "BR",
        "relevanceLanguage": "pt",
        "publishedAfter": _days_ago(7),
        "key": YT_API_KEY,
    }
    url = "https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        ids = [item["id"]["videoId"] for item in data.get("items", []) if item.get("id", {}).get("videoId")]
        if ids:
            return get_video_stats(ids)
        return {}
    except Exception as e:
        print(f"[youtube] erro trending: {e}")
        return {}


def _days_ago(n):
    from datetime import datetime, timezone, timedelta
    dt = datetime.now(timezone.utc) - timedelta(days=n)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
