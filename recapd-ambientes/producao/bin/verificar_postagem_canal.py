#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verificar_postagem_canal.py — Verifica se um canal já postou hoje via YouTube Data API.

Retorna True se já postou hoje, False caso contrário.
"""
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CREDS_FILE = Path(r"D:\credenciais-canais\youtube_canais.json")
TOKEN_URL = "<SEGREDO_REMOVIDO>"
CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def _load_canais():
    """Carrega credenciais dos canais."""
    return json.loads(CREDS_FILE.read_text(encoding="utf-8"))


def _find_canal(canais, nome_ou_id):
    """Encontra um canal por nome ou ID."""
    for c in canais:
        if c["id"] == nome_ou_id or c["nome"].strip().lower() == nome_ou_id.strip().lower():
            return c
    # match parcial pelo nome
    for c in canais:
        if nome_ou_id.strip().lower() in c["nome"].strip().lower():
            return c
    return None


def refresh_access_token(canal):
    """Troca o refresh_token por um access_token novo."""
    data = urllib.parse.urlencode({
        "client_id": canal["clientId"],
        "client_secret": canal["clientSecret"],
        "refresh_token": canal["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())["access_token"]


def obter_channel_id(access_token):
    """Obtém o channel ID do canal autenticado via YouTube Data API."""
    url = f"{CHANNELS_URL}?part=id&mine=true"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
            items = data.get("items", [])
            if items:
                return items[0]["id"]
    except Exception as e:
        print(f"[verificar] Erro ao obter channel ID: {e}", file=sys.stderr)

    return None


def verificar_postagem_hoje(canal_nome_ou_id, timezone_offset=-3):
    """Verifica se o canal já postou hoje (timezone BRT = UTC-3).

    Args:
        canal_nome_ou_id: nome ou ID do canal
        timezone_offset: offset do timezone em horas (padrão -3 para BRT)

    Returns:
        True se já postou hoje, False caso contrário
    """
    canais = _load_canais()
    canal = _find_canal(canais, canal_nome_ou_id)

    if not canal:
        print(f"[verificar] Canal não encontrado: {canal_nome_ou_id}", file=sys.stderr)
        return False

    try:
        # Renova access token
        access_token = refresh_access_token(canal)

        # Obtém channel ID
        channel_id = obter_channel_id(access_token)
        if not channel_id:
            print(f"[verificar] Não foi possível obter channel ID", file=sys.stderr)
            return False

        # Calcula início do dia de hoje em BRT (UTC-3)
        tz = timezone(timedelta(hours=timezone_offset))
        now_brt = datetime.now(tz)
        inicio_hoje = now_brt.replace(hour=0, minute=0, second=0, microsecond=0)

        # Converte para UTC (YouTube API usa UTC)
        inicio_hoje_utc = inicio_hoje.astimezone(timezone.utc)

        # Formata como RFC 3339
        published_after = inicio_hoje_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Busca vídeos publicados hoje
        params = urllib.parse.urlencode({
            "part": "id",
            "channelId": channel_id,
            "type": "video",
            "order": "date",
            "publishedAfter": published_after,
            "maxResults": 1
        })

        url = f"{SEARCH_URL}?{params}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})

        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
            items = data.get("items", [])

            # Se tem algum vídeo publicado hoje, retorna True
            ja_postou = len(items) > 0

            if ja_postou:
                print(f"[verificar] Canal '{canal['nome']}' já postou hoje", file=sys.stderr)
            else:
                print(f"[verificar] Canal '{canal['nome']}' ainda não postou hoje", file=sys.stderr)

            return ja_postou

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print(f"[verificar] Erro HTTP {e.code}: {body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[verificar] Erro ao verificar postagem: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: verificar_postagem_canal.py <canal>", file=sys.stderr)
        print("  canal: nome ou ID do canal", file=sys.stderr)
        print("\nRetorna exit code 0 se já postou hoje, 1 se não postou ou erro", file=sys.stderr)
        sys.exit(2)

    canal = sys.argv[1]
    ja_postou = verificar_postagem_hoje(canal)

    # Exit code: 0 = já postou, 1 = não postou
    sys.exit(0 if ja_postou else 1)
