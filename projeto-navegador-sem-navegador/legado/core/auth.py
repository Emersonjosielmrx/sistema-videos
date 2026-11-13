# -*- coding: utf-8 -*-
r"""
core/auth.py — Módulo de Autenticação e Gestão de Cookies sem navegador.

Funções:
  - Assinatura SAPISIDHASH dinâmica para qualquer serviço Google
  - Carregamento e salvamento atômico de cookies em JSON
  - Sincronização transparente com os cookies existentes em D:\gemini-argo e D:\logins-google\cofre
  - Geração de headers específicos para Instagram, TikTok e YouTube
"""
import hashlib
import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests

from config import COOKIES_DIR, GEMINI_ARGO_COOKIES, GEMINI_ARGO_YT_COOKIES, UA_DESKTOP

log = logging.getLogger("auth_http")

# Cookies críticos do ecossistema Google
GOOGLE_COOKIES_CRITICOS = {
    "SAPISID", "APISID", "SSID", "HSID", "SID", "SIDCC",
    "__Secure-1PSID", "__Secure-3PSID", "__Secure-1PAPISID", "__Secure-3PAPISID"
}


def calcular_sapisidhash(sapisid: str, origin: str) -> str:
    """
    Gera o cabeçalho Authorization: SAPISIDHASH {ts}_{hash} exigido pelo Google
    em requisições autenticadas internas (YouTube Studio, Photos, Flow, etc.).
    """
    ts = int(time.time())
    digest = hashlib.sha1(f"{ts} {sapisid} {origin}".encode("utf-8")).hexdigest()
    return f"SAPISIDHASH {ts}_{digest}"


def obter_caminho_cookie(servico: str, conta: str) -> Path:
    """Retorna o caminho do arquivo de cookies local."""
    return COOKIES_DIR / f"{servico}_{conta}.json"


def sincronizar_cookies_cdp(servico: str, conta: str, url_alvo: Optional[str] = None) -> Dict[str, str]:
    """
    Sincronização 1-click rápida com Chrome CDP invisível via cofre.
    Abre o perfil invisível por 5-8 segundos apenas para assentar a sessão
    e extrair os cookies atualizados via Network.getAllCookies, salvando em JSON.
    Depois fecha imediatamente o Chrome.
    """
    import sys
    sys.path.insert(0, r"D:\logins-google")
    import cofre
    from playwright.sync_api import sync_playwright

    urls_padrao = {
        "youtube": "https://www.youtube.com",
        "youtube_studio": "https://studio.youtube.com",
        "google_photos": "https://photos.google.com",
        "veo_flow": "https://labs.google/fx/pt/tools/flow",
        "google": "https://myaccount.google.com",
    }
    destino = url_alvo or urls_padrao.get(servico, "https://myaccount.google.com")

    log.info(f"Sincronizando cookies de {conta} para {servico} ({destino})...")
    porta, proc = cofre.abrir(conta, url="about:blank", visivel=False)
    br = None
    cookies_extraidos = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = br.contexts[0] if br.contexts else br.new_context()
            pg = ctx.new_page()
            pg.goto(destino, wait_until="domcontentloaded", timeout=45000)
            time.sleep(5)
            cdp = ctx.new_cdp_session(pg)
            todos = cdp.send("Network.getAllCookies")["cookies"]
            pg.close()

            # Filtrar cookies relevantes
            for c in todos:
                nome = c["name"]
                val = c["value"]
                dom = c.get("domain", "").lstrip(".")
                if servico in ("youtube", "youtube_studio") and ("youtube.com" in dom or "google.com" in dom):
                    cookies_extraidos[nome] = val
                elif "google.com" in dom or "labs.google" in dom:
                    cookies_extraidos[nome] = val
                elif servico in ("instagram", "tiktok"):
                    cookies_extraidos[nome] = val
    finally:
        cofre.fechar(proc, br, conta)

    if cookies_extraidos:
        salvar_cookies(servico, conta, cookies_extraidos)
        log.info(f"Sucesso: {len(cookies_extraidos)} cookies sincronizados para {conta} ({servico})")
    return cookies_extraidos


def carregar_cookies(servico: str, conta: str, auto_sync: bool = False) -> Dict[str, str]:
    r"""
    Carrega cookies salvos para um serviço e conta.
    Se não encontrar no cache local, tenta reaproveitar de D:\gemini-argo.
    Se auto_sync=True e estiver vazio, tenta sincronizar via CDP uma vez.
    """
    caminho = obter_caminho_cookie(servico, conta)
    if caminho.exists():
        try:
            return json.loads(caminho.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning(f"Erro ao ler {caminho}: {e}")

    # Fallback inteligente: buscar nos caches existentes do ecossistema
    candidatos = []
    if servico in ("youtube", "youtube_studio"):
        candidatos.append(GEMINI_ARGO_YT_COOKIES / f"{conta}.json")
        candidatos.append(GEMINI_ARGO_COOKIES / f"{conta}.json")
    elif servico in ("google", "google_photos", "veo_flow", "gemini"):
        candidatos.append(GEMINI_ARGO_COOKIES / f"{conta}.json")

    for cand in candidatos:
        if cand.exists():
            try:
                dados = json.loads(cand.read_text(encoding="utf-8"))
                # Salvar no nosso repositório local
                salvar_cookies(servico, conta, dados)
                log.info(f"Cookies de {conta} ({servico}) importados com sucesso de {cand}")
                return dados
            except Exception:
                pass

    if auto_sync:
        try:
            log.info(f"Iniciando sincronização silenciosa CDP para {conta} ({servico})...")
            return sincronizar_cookies_cdp(servico, conta)
        except Exception as e:
            log.warning(f"Auto-sync CDP falhou para {conta} ({servico}): {e}")

    return {}


def salvar_cookies(servico: str, conta: str, cookies: Dict[str, str]) -> None:
    """Salva os cookies atualizados no cache local em JSON."""
    caminho = obter_caminho_cookie(servico, conta)
    try:
        temp = caminho.with_suffix(".tmp")
        temp.write_text(json.dumps(cookies, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(caminho)
    except Exception as e:
        log.error(f"Erro ao salvar cookies em {caminho}: {e}")


def headers_google(origin: str, cookies: Dict[str, str], sapisid: Optional[str] = None) -> Dict[str, str]:
    """
    Monta cabeçalhos completos de requisição autenticada do Google.
    """
    sapisid_val = sapisid or cookies.get("SAPISID") or cookies.get("__Secure-3PAPISID") or cookies.get("__Secure-1PAPISID")
    if not sapisid_val:
        raise ValueError("Cookie SAPISID não encontrado para gerar assinatura Google.")

    auth_header = calcular_sapisidhash(sapisid_val, origin)
    return {
        "User-Agent": UA_DESKTOP,
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": origin,
        "X-Origin": origin,
        "Authorization": auth_header,
        "x-goog-authuser": "0",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }


def headers_instagram(cookies: Dict[str, str]) -> Dict[str, str]:
    """
    Monta cabeçalhos da Web API privada do Instagram.
    """
    csrf_token = cookies.get("csrftoken", "")
    return {
        "User-Agent": UA_DESKTOP,
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://www.instagram.com",
        "Referer": "https://www.instagram.com/",
        "X-IG-App-ID": "936619743392459",
        "X-CSRFToken": csrf_token,
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }


def headers_tiktok(cookies: Dict[str, str]) -> Dict[str, str]:
    """
    Monta cabeçalhos para endpoints web e creator do TikTok.
    """
    csrf_token = cookies.get("csrf_token") or cookies.get("tt_csrf_token", "")
    return {
        "User-Agent": UA_DESKTOP,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://www.tiktok.com",
        "Referer": "https://www.tiktok.com/",
        "x-secsdk-csrf-token": csrf_token,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
