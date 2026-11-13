# -*- coding: utf-8 -*-
"""
services/instagram/client.py — Cliente HTTP puro da Web API privada do Instagram.
Permite consultar perfis, extrair mídias, contadores e preparar postagens sem abrir navegador.
Requer cookies de sessão (sessionid) para operações autenticadas.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional

from config import UA_DESKTOP, URLS
from core.auth import headers_instagram
from core.session import PersistentSession

log = logging.getLogger("instagram_http")

ORIGIN_INSTA = URLS["instagram"]
API_V1 = f"{ORIGIN_INSTA}/api/v1"


class InstagramWebClient:
    """
    Cliente para automação do Instagram via Web API privada.
    Funciona 100% por requisições HTTP usando cookies persistentes de sessão (sessionid).
    """

    def __init__(self, conta: str):
        self.conta = conta
        self.session = PersistentSession("instagram", self.conta)
        self.session.session.headers.update({
            "User-Agent": UA_DESKTOP,
            "Origin": ORIGIN_INSTA,
            "Referer": f"{ORIGIN_INSTA}/",
            "X-IG-App-ID": "936619743392459",
            "X-Requested-With": "XMLHttpRequest",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        })

    def _headers(self) -> Dict[str, str]:
        cookies = self.session.session.cookies.get_dict()
        return headers_instagram(cookies)

    def obter_perfil(self, username: str) -> Dict[str, Any]:
        """
        Consulta informações completas do perfil via Web Profile Info API.
        Retorna seguidores, seguindo, biografia, link externo e status da conta.
        """
        clean_user = username.lstrip("@").strip()
        url = f"{API_V1}/users/web_profile_info/?username={clean_user}"

        try:
            r = self.session.get(url, headers=self._headers(), timeout=12)
            if r.status_code == 200:
                dados = r.json().get("data", {}).get("user", {})
                if not dados:
                    return {
                        "sucesso": False,
                        "status_http": 200,
                        "erro": "Usuário não encontrado na resposta",
                        "username": clean_user
                    }

                return {
                    "sucesso": True,
                    "status_http": 200,
                    "id": dados.get("id"),
                    "username": dados.get("username"),
                    "nome_completo": dados.get("full_name"),
                    "biografia": dados.get("biography"),
                    "link_bio": dados.get("external_url"),
                    "seguidores": dados.get("edge_followed_by", {}).get("count", 0),
                    "seguindo": dados.get("edge_follow", {}).get("count", 0),
                    "total_midias": dados.get("edge_owner_to_timeline_media", {}).get("count", 0),
                    "e_comercial": dados.get("is_business_account", False),
                    "categoria": dados.get("category_name"),
                }
            elif r.status_code == 401:
                log.warning(f"Instagram @{clean_user}: status 401 - Requer cookie sessionid ativo.")
                return {
                    "sucesso": False,
                    "status_http": 401,
                    "erro": "Autenticação requerida (cookie sessionid ausente ou expirado)",
                    "username": clean_user
                }
            else:
                log.warning(f"Erro ao obter perfil @{clean_user}: status {r.status_code}")
                return {
                    "sucesso": False,
                    "status_http": r.status_code,
                    "erro": f"Status HTTP {r.status_code}",
                    "username": clean_user
                }
        except Exception as e:
            log.error(f"Exceção ao obter perfil Instagram @{clean_user}: {e}")
            return {"sucesso": False, "status_http": 0, "erro": str(e), "username": clean_user}

    def obter_midias_recentes(self, username: str, max_itens: int = 12) -> List[Dict[str, Any]]:
        """
        Obtém as postagens recentes do perfil com contagem de likes, comentários e views (se vídeo).
        """
        clean_user = username.lstrip("@").strip()
        url = f"{API_V1}/users/web_profile_info/?username={clean_user}"
        try:
            r = self.session.get(url, headers=self._headers(), timeout=12)
            if r.status_code != 200:
                return []

            user_data = r.json().get("data", {}).get("user", {})
            edges = user_data.get("edge_owner_to_timeline_media", {}).get("edges", [])

            itens = []
            for edge in edges[:max_itens]:
                node = edge.get("node", {})
                shortcode = node.get("shortcode")
                itens.append({
                    "id": node.get("id"),
                    "shortcode": shortcode,
                    "url": f"{ORIGIN_INSTA}/p/{shortcode}/" if shortcode else None,
                    "tipo": node.get("__typename"),
                    "e_video": node.get("is_video", False),
                    "views_video": node.get("video_view_count"),
                    "curtidas": node.get("edge_liked_by", {}).get("count", 0),
                    "comentarios": node.get("edge_media_to_comment", {}).get("count", 0),
                    "timestamp": node.get("taken_at_timestamp"),
                    "legenda": (
                        node.get("edge_media_to_caption", {})
                        .get("edges", [{}])[0]
                        .get("node", {})
                        .get("text", "")
                    ) if node.get("edge_media_to_caption", {}).get("edges") else "",
                })
            return itens
        except Exception as e:
            log.error(f"Erro ao extrair mídias de @{clean_user}: {e}")
            return []

    def obter_stories_ativos(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Consulta os Stories ativos de um perfil via Web API privada.
        """
        url = f"{API_V1}/feed/user/{user_id}/reel_media/"
        try:
            r = self.session.get(url, headers=self._headers(), timeout=12)
            if r.status_code == 200:
                itens = r.json().get("items", [])
                stories = []
                for it in itens:
                    stories.append({
                        "id": it.get("id"),
                        "tipo": it.get("media_type"),
                        "timestamp": it.get("taken_at"),
                        "expira_em": it.get("expiring_at"),
                        "imagem_url": it.get("image_versions2", {}).get("candidates", [{}])[0].get("url"),
                    })
                return stories
            return []
        except Exception as e:
            log.error(f"Erro ao consultar stories de {user_id}: {e}")
            return []

    def _upload_imagem_raw(self, caminho_imagem: str) -> Optional[str]:
        """
        Faz upload binário de uma imagem para os servidores do Instagram via rupload.
        Retorna o upload_id gerado.
        """
        import time, os
        upload_id = str(int(time.time() * 1000))
        if not os.path.exists(caminho_imagem):
            log.error(f"Arquivo não existe: {caminho_imagem}")
            return None

        tamanho = os.path.getsize(caminho_imagem)
        rupload_url = f"{ORIGIN_INSTA}/rupload_igphoto/{upload_id}"
        hd = self._headers()
        hd.update({
            "X-Entity-Name": upload_id,
            "X-Entity-Length": str(tamanho),
            "Offset": "0",
            "Content-Type": "image/jpeg",
        })

        try:
            with open(caminho_imagem, "rb") as f:
                r = self.session.post(rupload_url, data=f, headers=hd, timeout=45)
            if r.status_code in (200, 201):
                return upload_id
            log.warning(f"Falha no rupload: {r.status_code} - {r.text[:150]}")
            return None
        except Exception as e:
            log.error(f"Erro no upload de imagem Instagram: {e}")
            return None

    def postar_story(self, caminho_imagem: str) -> Dict[str, Any]:
        """
        Publica uma imagem diretamente nos Stories via HTTP puro sem abrir navegador.
        """
        upload_id = self._upload_imagem_raw(caminho_imagem)
        if not upload_id:
            return {"sucesso": False, "erro": "Falha no upload da imagem"}

        url_config = f"{API_V1}/media/configure_to_story/"
        payload = {
            "upload_id": upload_id,
            "story_media_creation_date": str(int(time.time()) - 3),
            "client_shared_at": str(int(time.time())),
            "configure_mode": "1",
        }
        hd = self._headers()
        hd["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

        try:
            r = self.session.post(url_config, data=payload, headers=hd, timeout=30)
            if r.status_code == 200:
                dados = r.json()
                return {"sucesso": True, "media_id": dados.get("media", {}).get("id"), "tipo": "story"}
            return {"sucesso": False, "status_http": r.status_code, "erro": r.text[:200]}
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}

    def postar_carrossel(self, lista_imagens: List[str], legenda: str = "") -> Dict[str, Any]:
        """
        Publica um Carrossel (Sidecar) com múltiplos slides via HTTP puro.
        """
        upload_ids = []
        for img in lista_imagens:
            uid = self._upload_imagem_raw(img)
            if uid:
                upload_ids.append(uid)

        if not upload_ids:
            return {"sucesso": False, "erro": "Nenhuma imagem foi carregada com sucesso"}

        url_config = f"{API_V1}/media/configure_sidecar/"
        children = [{"upload_id": uid} for uid in upload_ids]
        payload = {
            "client_sidecar_id": str(int(time.time() * 1000)),
            "caption": legenda,
            "children_metadata": json.dumps(children),
        }
        hd = self._headers()
        hd["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

        try:
            r = self.session.post(url_config, data=payload, headers=hd, timeout=30)
            if r.status_code == 200:
                dados = r.json()
                return {
                    "sucesso": True,
                    "media_id": dados.get("media", {}).get("id"),
                    "total_slides": len(upload_ids),
                    "tipo": "carrossel"
                }
            return {"sucesso": False, "status_http": r.status_code, "erro": r.text[:200]}
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}

    def postar_reels(self, caminho_video: str, legenda: str = "", preview_feed: bool = True) -> Dict[str, Any]:
        """
        Prepara a publicação de Reels / Vídeo Vertical via endpoint de clips do Instagram.
        """
        return {
            "sucesso": False,
            "aviso": "Estrutura de Reels HTTP pronta (requer upload prévio do stream de vídeo e capa)",
            "preview_feed": preview_feed,
            "legenda": legenda
        }
