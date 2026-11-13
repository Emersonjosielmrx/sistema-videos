# -*- coding: utf-8 -*-
"""SerpAPI - pesquisa de tendencias."""
import json
import urllib.request
import urllib.parse
from config import SERP_API_KEY


def search_trends(query, num_results=10):
    """Pesquisa no Google via SerpAPI."""
    if not SERP_API_KEY:
        print("[serp] sem API key, pulando")
        return []
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google",
        "num": num_results,
        "hl": "pt",
        "gl": "br",
    }
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=20)
        data = json.loads(resp.read())
        results = []
        for item in data.get("organic_results", []):
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
            })
        return results
    except Exception as e:
        print(f"[serp] erro: {e}")
        return []


def search_google_trends(topic):
    """Pesquisa Google Trends via SerpAPI."""
    if not SERP_API_KEY:
        return []
    params = {
        "q": topic,
        "api_key": SERP_API_KEY,
        "engine": "google_trends",
        "data_type": "TIMESERIES",
        "geo": "BR",
    }
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=20)
        data = json.loads(resp.read())
        return data.get("interest_over_time", {}).get("timeline_data", [])
    except Exception as e:
        print(f"[serp] erro trends: {e}")
        return []
