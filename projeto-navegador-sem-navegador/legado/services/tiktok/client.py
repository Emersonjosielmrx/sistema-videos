# -*- coding: utf-8 -*-
"""
services/tiktok/client.py — Cliente HTTP puro do TikTok.
Consulta dados de perfil, validação de contas, embeds e vídeos sem abrir o navegador.
Utiliza a API oficial oEmbed para consultas imediatas sem risco de WAF,
com fallback para SSR quando cookies de sessão estiverem presentes.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional
import urllib.parse

from config import UA_DESKTOP, URLS
from core.auth import headers_tiktok
from core.session import PersistentSession

log = logging.getLogger("tiktok_http")

ORIGIN_TIKTOK = URLS["tiktok"]
OEMBED_TIKTOK = "https://www.tiktok.com/oembed"


class TikTokWebClient:
    """
    Cliente para automação e leitura de métricas do TikTok via HTTP puro.
    Elimina o consumo de 600+ MB de RAM e tempo de abertura do Chrome.
    """

    def __init__(self, conta: str = "padrao"):
        self.conta = conta
        self.session = PersistentSession("tiktok", self.conta)
        self.session.session.headers.update({
            "User-Agent": UA_DESKTOP,
            "Origin": ORIGIN_TIKTOK,
            "Referer": f"{ORIGIN_TIKTOK}/",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        })

    def _headers(self) -> Dict[str, str]:
        cookies = self.session.session.cookies.get_dict()
        return headers_tiktok(cookies)

    def obter_perfil_oembed(self, username: str) -> Dict[str, Any]:
        """
        Consulta metadados de perfil via API oficial oEmbed do TikTok.
        Retorno garantido em ~0.3s sem bloqueio por SlardarWAF / captcha.
        """
        handle = username.lstrip("@").strip()
        url_perfil = f"{ORIGIN_TIKTOK}/@{handle}"
        params = {"url": url_perfil}

        try:
            r = self.session.get(OEMBED_TIKTOK, params=params, headers={"User-Agent": UA_DESKTOP})
            if r.status_code == 200:
                dados = r.json()
                return {
                    "sucesso": True,
                    "username": handle,
                    "author_name": dados.get("author_name"),
                    "title": dados.get("title"),
                    "author_url": dados.get("author_url"),
                    "embed_type": dados.get("embed_type", "profile"),
                    "html": dados.get("html"),
                    "status_http": 200,
                }
            else:
                log.warning(f"oEmbed TikTok @{handle} retornou status {r.status_code}")
                return {
                    "sucesso": False,
                    "username": handle,
                    "status_http": r.status_code,
                    "erro": f"HTTP {r.status_code}"
                }
        except Exception as e:
            log.error(f"Exceção ao chamar oEmbed TikTok para @{handle}: {e}")
            return {"sucesso": False, "username": handle, "erro": str(e)}

    def obter_video_oembed(self, video_url: str) -> Dict[str, Any]:
        """
        Consulta metadados de um vídeo específico no TikTok via oEmbed.
        """
        params = {"url": video_url}
        try:
            r = self.session.get(OEMBED_TIKTOK, params=params, headers={"User-Agent": UA_DESKTOP})
            if r.status_code == 200:
                dados = r.json()
                return {
                    "sucesso": True,
                    "titulo": dados.get("title"),
                    "autor": dados.get("author_name"),
                    "autor_url": dados.get("author_url"),
                    "thumbnail_url": dados.get("thumbnail_url"),
                    "largura": dados.get("width"),
                    "altura": dados.get("height"),
                    "status_http": 200,
                }
            return {"sucesso": False, "status_http": r.status_code}
        except Exception as e:
            log.error(f"Erro ao consultar vídeo TikTok {video_url}: {e}")
            return {"sucesso": False, "erro": str(e)}

    def obter_perfil(self, username: str) -> Dict[str, Any]:
        """
        Lê dados do perfil do TikTok (@username).
        1. Consulta o oEmbed oficial para validar existência e metadados de autoria.
        2. Tenta coletar contadores detalhados via SSR caso o WAF não bloqueie.
        """
        handle = username.lstrip("@").strip()
        res_oembed = self.obter_perfil_oembed(handle)

        perfil = {
            "sucesso": res_oembed.get("sucesso", False),
            "username": handle,
            "author_name": res_oembed.get("author_name"),
            "titulo": res_oembed.get("title"),
            "url": res_oembed.get("author_url"),
            "seguidores": None,
            "curtidas_totais": None,
            "total_videos": None,
            "status_http": res_oembed.get("status_http", 0),
        }

        # Tentar enriquecer com contadores se SSR estiver disponível
        url = f"{ORIGIN_TIKTOK}/@{handle}"
        try:
            r = self.session.get(url, headers=self._headers(), timeout=10)
            if r.status_code == 200:
                html = r.text
                m = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>([^<]+)</script>', html)
                if m:
                    dados_json = json.loads(m.group(1))
                    user_detail = dados_json.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {})
                    stats = user_detail.get("userInfo", {}).get("stats", {})
                    perfil["seguidores"] = stats.get("followerCount")
                    perfil["curtidas_totais"] = stats.get("heartCount")
                    perfil["total_videos"] = stats.get("videoCount")
                else:
                    s_seg = re.search(r'"followerCount":(\d+)', html)
                    s_cur = re.search(r'"heartCount":(\d+)', html)
                    s_vid = re.search(r'"videoCount":(\d+)', html)
                    if s_seg:
                        perfil["seguidores"] = int(s_seg.group(1))
                    if s_cur:
                        perfil["curtidas_totais"] = int(s_cur.group(1))
                    if s_vid:
                        perfil["total_videos"] = int(s_vid.group(1))
        except Exception as e:
            log.debug(f"SSR TikTok não disponível (normal se WAF ativo): {e}")

        return perfil
