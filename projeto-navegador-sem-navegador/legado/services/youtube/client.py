# -*- coding: utf-8 -*-
"""
services/youtube/client.py — Cliente HTTP puro do YouTube (Público + Studio).
Substitui a necessidade de abrir navegador para consultar canais, gerenciar vídeos e ler métricas.
"""
import hashlib
import json
import logging
import re
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from config import UA_DESKTOP, URLS
from core.auth import calcular_sapisidhash, headers_google
from core.session import PersistentSession

log = logging.getLogger("youtube_http")

API_BROWSE = "https://www.youtube.com/youtubei/v1/browse?prettyPrint=false"
CONTEXTO_BROWSE = {
    "client": {
        "clientName": "WEB",
        "clientVersion": "2.20251020.01.00",
        "hl": "pt",
        "gl": "BR"
    }
}


def _converter_numero(txt: Optional[str]) -> Optional[int]:
    """Converte '1,2 mil visualizações' / '3,4 mi de inscritos' -> int."""
    if not txt:
        return None
    t = txt.lower().replace("\xa0", " ")
    m = re.search(r"(\d[\d.,]*)\s*(mil|mi|bi|k|m|b)?(?![a-zà-ú])", t)
    if not m:
        return 0 if re.search(r"\b(nenhum|sem)", t) else None
    num, mult = m.group(1), m.group(2)
    if mult:
        multiplicadores = {"mil": 1000, "k": 1000, "mi": 10**6, "m": 10**6, "bi": 10**9, "b": 10**9}
        return int(Decimal(num.replace(",", ".")) * multiplicadores[mult])
    return int(re.sub(r"[.,]", "", num))


def _achar_chave(obj: Any, chave: str):
    """Varre um dicionário ou lista recursivamente em busca de todas as ocorrências de uma chave."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == chave:
                yield v
            yield from _achar_chave(v, chave)
    elif isinstance(obj, list):
        for item in obj:
            yield from _achar_chave(item, chave)


def _extrair_texto(v: Any) -> str:
    """Extrai texto de estruturas complexas do YouTube (runs, simpleText, content)."""
    if isinstance(v, dict):
        if "simpleText" in v:
            return v["simpleText"]
        if "runs" in v:
            return "".join(r.get("text", "") for r in v["runs"])
        if "content" in v:
            return v["content"]
    return v if isinstance(v, str) else ""


class YouTubePublico:
    """Consulta dados públicos de qualquer canal/vídeo do YouTube sem login."""

    def __init__(self):
        self.session = PersistentSession("youtube", "_publico")
        self.session.session.headers.update({
            "User-Agent": UA_DESKTOP,
            "Accept-Language": "pt-BR,pt;q=0.9",
            "Origin": URLS["youtube"]
        })

    def browse(self, channel_id: str, params: Optional[str] = None) -> Dict[str, Any]:
        corpo = {"context": CONTEXTO_BROWSE, "browseId": channel_id}
        if params:
            corpo["params"] = params.replace("%3D", "=")
        r = self.session.post(API_BROWSE, json=corpo)
        r.raise_for_status()
        return r.json()

    def obter_resumo_canal(self, channel_id: str) -> Dict[str, Any]:
        d = self.browse(channel_id)
        meta = next(_achar_chave(d, "channelMetadataRenderer"), {})
        cab = json.dumps(next(_achar_chave(d, "pageHeaderViewModel"), {}), ensure_ascii=False)
        insc = re.search(r'"content":\s*"([^"]*inscrit[^"]*)"', cab)
        nvid = re.search(r'"content":\s*"([^"]*v[íi]deos?)"', cab)

        # Últimos vídeos
        videos = []
        for v in _achar_chave(d, "videoRenderer"):
            videos.append({
                "id": v.get("videoId"),
                "titulo": _extrair_texto(v.get("title")),
                "views": _converter_numero(_extrair_texto(v.get("viewCountText"))),
                "quando": _extrair_texto(v.get("publishedTimeText"))
            })

        # Últimos shorts
        shorts = []
        for v in _achar_chave(d, "shortsLockupViewModel"):
            vid = v.get("onTap", {}).get("innertubeCommand", {}).get("reelWatchEndpoint", {}).get("videoId")
            ov = v.get("overlayMetadata", {})
            shorts.append({
                "id": vid,
                "titulo": ov.get("primaryText", {}).get("content", ""),
                "views": _converter_numero(ov.get("secondaryText", {}).get("content", ""))
            })

        return {
            "channel_id": channel_id,
            "nome": meta.get("title"),
            "inscritos": _converter_numero(insc.group(1)) if insc else None,
            "videos_no_canal": _converter_numero(nvid.group(1)) if nvid else None,
            "ultimos_videos": videos[:10],
            "ultimos_shorts": shorts[:10]
        }


class YouTubeStudioClient:
    """
    Cliente HTTP do YouTube Studio.
    Usa SAPISIDHASH + cookies do canal para operar no Studio diretamente,
    sem abrir navegador e sem consumir cotas da Data API v3.
    """

    def __init__(self, slug_ou_conta: str):
        self.conta = slug_ou_conta
        self.session = PersistentSession("youtube_studio", self.conta)
        self.origin = URLS["youtube_studio"]

        # Carregar parâmetros essenciais da página Studio
        self.channel_id = None
        self.innertube_key = None
        self.innertube_version = None
        self._inicializar_studio()

    def _inicializar_studio(self) -> None:
        """Acessa a home do Studio via HTTP para extrair tokens dinâmicos da sessão."""
        cookies = self.session.session.cookies.get_dict()
        sapisid = cookies.get("SAPISID") or cookies.get("__Secure-3PAPISID")
        if not sapisid:
            raise RuntimeError(f"Sem cookie SAPISID para conta {self.conta}. Sincronize os cookies primeiro.")

        hd = {
            "User-Agent": UA_DESKTOP,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Upgrade-Insecure-Requests": "1",
        }
        r = self.session.get(f"{self.origin}/", headers=hd)
        if r.status_code != 200:
            raise RuntimeError(f"Falha ao abrir Studio para {self.conta}: status {r.status_code}")

        html = r.text
        cid = re.search(r'"CHANNEL_ID":"([^"]+)"', html)
        key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
        ver = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html)

        if not cid or not key:
            raise RuntimeError(f"Studio não reconheceu o login de {self.conta}. Verifique os cookies.")

        self.channel_id = cid.group(1)
        self.innertube_key = key.group(1)
        self.innertube_version = ver.group(1) if ver else "2.20251020.01.00"

    def _post_studio(self, rota: str, corpo: Dict[str, Any]) -> Dict[str, Any]:
        """Envia requisição autenticada para o backend do Studio."""
        cookies = self.session.session.cookies.get_dict()
        hd = headers_google(self.origin, cookies)
        corpo["context"] = {
            "client": {
                "clientName": 62,  # 62 = YouTube Studio Web
                "clientVersion": self.innertube_version,
                "hl": "pt",
                "gl": "BR"
            }
        }
        url = f"{self.origin}/youtubei/v1/{rota}?alt=json&key={self.innertube_key}"
        r = self.session.post(url, json=corpo, headers=hd)
        r.raise_for_status()
        return r.json()

    def listar_videos(self, quantos: int = 30) -> List[Dict[str, Any]]:
        """
        Lista os últimos uploads do canal com status completos:
        views, curtidas, comentários, monetização, direitos autorais e agendamento.
        """
        mask = {
            "videoId": True,
            "title": True,
            "privacy": True,
            "timePublishedSeconds": True,
            "lengthSeconds": True,
            "scheduledPublishingDetails": {"all": True},
            "publicMetrics": {"all": True},
            "privateMetrics": {"all": True},
            "claimDetails": {"all": True},
            "monetization": {"all": True},
            "allRestrictions": {"all": True}
        }
        corpo = {
            "filter": {
                "and": {
                    "operands": [
                        {"channelIdIs": {"value": self.channel_id}},
                        {"videoOriginIs": {"value": "VIDEO_ORIGIN_UPLOAD"}}
                    ]
                }
            },
            "order": "VIDEO_ORDER_DISPLAY_TIME_DESC",
            "pageSize": quantos,
            "mask": mask
        }
        dados = self._post_studio("creator/list_creator_videos", corpo)
        saida = []
        for v in dados.get("videos", []):
            pub = v.get("publicMetrics", {})
            priv = v.get("privateMetrics", {})
            agendado = v.get("scheduledPublishingDetails", {})
            saida.append({
                "id": v.get("videoId"),
                "titulo": v.get("title", {}).get("runs", [{}])[0].get("text", ""),
                "privacidade": v.get("privacy"),
                "duracao_segundos": int(v.get("lengthSeconds", 0)),
                "views": int(pub.get("viewCount", 0)),
                "curtidas": int(pub.get("likeCount", 0)),
                "comentarios": int(pub.get("commentCount", 0)),
                "agendado_para": agendado.get("scheduledPublishTimeSeconds"),
                "monetizacao": v.get("monetization", {}).get("status"),
                "tem_reivindicacao": bool(v.get("claimDetails", {}).get("hasClaims")),
            })
        return saida

    def listar_videos_agendados(self, quantos: int = 50) -> List[Dict[str, Any]]:
        """
        Retorna especificamente os vídeos que estão na fila de agendamento do canal.
        """
        todos = self.listar_videos(quantos=quantos)
        agendados = [v for v in todos if v.get("privacidade") == "SCHEDULED" or v.get("agendado_para")]
        return agendados

    @classmethod
    def analisar_multiplos_canais(cls, slugs: List[str], quantos_videos: int = 10) -> Dict[str, Any]:
        """
        Coleta métricas analíticas e status de múltiplos canais sem abrir navegador,
        consolidando uma visão panorâmica de todo o ecossistema.
        """
        resultado = {}
        for s in slugs:
            try:
                cli = cls(s)
                vids = cli.listar_videos(quantos=quantos_videos)
                agendados = [v for v in vids if v.get("privacidade") == "SCHEDULED" or v.get("agendado_para")]
                total_views = sum(v.get("views", 0) for v in vids)
                reivindicados = sum(1 for v in vids if v.get("tem_reivindicacao"))

                resultado[s] = {
                    "status": "OK",
                    "channel_id": cli.channel_id,
                    "videos_analisados": len(vids),
                    "total_views_recentes": total_views,
                    "videos_agendados": len(agendados),
                    "videos_com_claims": reivindicados,
                }
            except Exception as e:
                resultado[s] = {"status": "ERRO", "erro": str(e)}
        return resultado
