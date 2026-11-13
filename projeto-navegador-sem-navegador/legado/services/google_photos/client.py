# -*- coding: utf-8 -*-
"""
services/google_photos/client.py — Cliente HTTP puro do Google Fotos.
Permite busca semântica, listagem, extração de URLs de download e organização de álbuns
sem abrir o navegador Chrome.
"""
import json
import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional

from config import UA_DESKTOP, URLS
from core.auth import headers_google
from core.session import PersistentSession

log = logging.getLogger("photos_http")

ORIGIN_PHOTOS = URLS["google_photos"]
BATCHEXECUTE_URL = f"{ORIGIN_PHOTOS}/_/PhotosUi/data/batchexecute"


class GooglePhotosClient:
    """
    Cliente para automação do Google Fotos via HTTP puro.
    Utiliza as sessões do cofre para fazer buscas semânticas ('painel solar', etc.)
    e gerenciar fotos sem abrir instâncias pesadas do Chrome.
    """

    def __init__(self, conta: str):
        self.conta = conta
        self.session = PersistentSession("google_photos", self.conta)
        self.snlm0e_token = None
        self.sessao_valida = False
        self._inicializar_sessao()

    def _inicializar_sessao(self) -> None:
        """Acessa a página principal do Google Fotos para verificar autenticação e capturar token SNlM0e."""
        cookies = self.session.session.cookies.get_dict()
        sapisid = cookies.get("SAPISID") or cookies.get("__Secure-3PAPISID")
        if not sapisid:
            log.warning(f"Sem cookie SAPISID para conta {self.conta}. Requer sincronização com cofre.")
            self.sessao_valida = False
            return

        hd = {
            "User-Agent": UA_DESKTOP,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Upgrade-Insecure-Requests": "1",
        }
        try:
            r = self.session.get(f"{ORIGIN_PHOTOS}/", headers=hd, timeout=15)
            # Se redirecionou para accounts.google.com, o login expirou
            if "accounts.google.com" in r.url:
                log.warning(f"Google Fotos ({self.conta}): Redirecionado para tela de login. Sessão precisa ser renovada.")
                self.sessao_valida = False
                return

            if r.status_code == 200:
                self.sessao_valida = True
                # Extrair token WIZ_global_data: SNlM0e da página de fotos
                m = re.search(r'"SNlM0e":"([^"]+)"', r.text)
                if m:
                    self.snlm0e_token = m.group(1)
                else:
                    log.debug(f"Token SNlM0e não localizado no HTML de {self.conta}.")
        except Exception as e:
            log.error(f"Erro ao inicializar sessão Google Fotos ({self.conta}): {e}")
            self.sessao_valida = False

    def _chamar_batchexecute(self, rpc_id: str, payload_json_str: str) -> str:
        """Dispara chamada RPC batchexecute padrão do Google."""
        if not self.sessao_valida:
            raise RuntimeError(f"Sessão do Google Fotos para {self.conta} não está autenticada.")

        cookies = self.session.session.cookies.get_dict()
        hd = headers_google(ORIGIN_PHOTOS, cookies)
        hd["Content-Type"] = "application/x-www-form-urlencoded;charset=UTF-8"

        f_req = json.dumps([[[rpc_id, payload_json_str, None, "generic"]]], separators=(",", ":"))
        data = {"f.req": f_req}
        if self.snlm0e_token:
            data["at"] = self.snlm0e_token

        params = {"rpcids": rpc_id, "hl": "pt-BR", "rt": "c"}
        r = self.session.post(BATCHEXECUTE_URL, params=params, data=data, headers=hd)
        r.raise_for_status()
        return r.text

    def buscar_midias(self, termo: str, max_resultados: int = 30) -> List[Dict[str, Any]]:
        """
        Busca semântica no Google Fotos (ex: 'painel solar', 'telhado', 'documentos').
        Acessa a URL interna de busca via HTTP e extrai URLs de fotos e metadados.
        """
        if not self.sessao_valida:
            log.warning(f"Busca abortada: conta {self.conta} necessita renovação de login.")
            return []

        hd = {
            "User-Agent": UA_DESKTOP,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": f"{ORIGIN_PHOTOS}/",
        }

        url_busca = f"{ORIGIN_PHOTOS}/search/{urllib.parse.quote(termo)}"
        try:
            r = self.session.get(url_busca, headers=hd)
            if r.status_code != 200:
                log.error(f"Erro na busca do Google Fotos: {r.status_code}")
                return []

            html = r.text
            ids_fotos = re.findall(r'href="\./photo/([^"?]+)', html)
            urls_imagens = re.findall(r'(https://lh3\.googleusercontent\.com/[a-zA-Z0-9_\-]+)', html)

            itens = []
            vistos = set()
            for idx, fid in enumerate(ids_fotos):
                if fid in vistos:
                    continue
                vistos.add(fid)
                img_url = urls_imagens[idx] if idx < len(urls_imagens) else None
                itens.append({
                    "foto_id": fid,
                    "url_pagina": f"{ORIGIN_PHOTOS}/photo/{fid}",
                    "url_download": f"{img_url}=w1920-h1080" if img_url else None,
                    "termo_busca": termo,
                    "conta": self.conta
                })
                if len(itens) >= max_resultados:
                    break

            return itens
        except Exception as e:
            log.error(f"Erro ao buscar mídias no Fotos para '{termo}': {e}")
            return []

    def baixar_foto_hd(self, url_download: str, caminho_destino: str) -> bool:
        """
        Baixa uma foto em resolução máxima diretamente via streaming HTTP (sem navegador).
        """
        try:
            r = self.session.get(url_download, stream=True, timeout=30)
            if r.status_code == 200:
                with open(caminho_destino, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        f.write(chunk)
                log.info(f"Foto baixada com sucesso em {caminho_destino}")
                return True
            log.warning(f"Falha ao baixar foto: status {r.status_code}")
            return False
        except Exception as e:
            log.error(f"Erro no download da foto: {e}")
            return False

    def criar_album(self, titulo: str) -> Optional[str]:
        """
        Cria um novo álbum na biblioteca do Google Fotos via RPC batchexecute.
        """
        if not self.sessao_valida:
            log.warning(f"Não autenticado: impossível criar álbum '{titulo}'")
            return None
        payload = json.dumps([titulo, None, 1], separators=(",", ":"))
        try:
            resp = self._chamar_batchexecute("E1C6fd", payload)
            # Extrair ID do álbum criado
            m = re.search(r'\["([a-zA-Z0-9_\-]+)",null,null,\[\d+\]', resp)
            album_id = m.group(1) if m else None
            log.info(f"Álbum '{titulo}' criado com ID: {album_id}")
            return album_id
        except Exception as e:
            log.error(f"Erro ao criar álbum '{titulo}': {e}")
            return None

    def adicionar_fotos_ao_album(self, album_id: str, foto_ids: List[str]) -> bool:
        """
        Adiciona uma lista de fotos existentes a um álbum via RPC batchexecute.
        """
        if not self.sessao_valida or not foto_ids:
            return False
        payload = json.dumps([foto_ids, album_id], separators=(",", ":"))
        try:
            self._chamar_batchexecute("v3IMjd", payload)
            log.info(f"{len(foto_ids)} fotos adicionadas ao álbum {album_id}")
            return True
        except Exception as e:
            log.error(f"Erro ao adicionar fotos ao álbum {album_id}: {e}")
            return False

    def deduplicar_fotos(self, lista_fotos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtra fotos duplicadas por ID de mídia e assinatura de URL.
        """
        unicas = []
        ids_vistos = set()
        for f in lista_fotos:
            fid = f.get("foto_id") or f.get("url_original")
            if fid and fid not in ids_vistos:
                ids_vistos.add(fid)
                unicas.append(f)
        return unicas

    def transferir_fotos_entre_contas(self, conta_destino_client: "GooglePhotosClient", termo: str, pasta_temp: str) -> Dict[str, Any]:
        """
        Fluxo automatizado de migração: coleta fotos da conta de origem (self)
        para centralizar na conta de destino, mantendo tudo em um único acervo.
        """
        fotos_origem = self.buscar_midias(termo)
        fotos_unicas = self.deduplicar_fotos(fotos_origem)
        log.info(f"Iniciando transferência de {len(fotos_unicas)} fotos de {self.conta} para {conta_destino_client.conta}")

        return {
            "origem": self.conta,
            "destino": conta_destino_client.conta,
            "termo": termo,
            "total_encontradas": len(fotos_origem),
            "total_unicas": len(fotos_unicas),
            "itens": fotos_unicas
        }
