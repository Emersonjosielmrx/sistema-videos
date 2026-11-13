#!/usr/bin/env python3
"""
add_openrouter_keys.py - Adiciona chaves OpenRouter e configura proxies no Hermes Call

Uso:
    python3 add_openrouter_keys.py --token SEU_JWT_TOKEN --url http://localhost:8080

Ou via variáveis de ambiente:
    export HERMES_TOKEN="<SEGREDO_REMOVIDO>"
    export HERMES_API_URL="http://localhost:8080"
    python3 add_openrouter_keys.py
"""

import argparse
import json
import os
import sys
import time
from typing import List, Tuple

try:
    import requests
except ImportError:
    print("❌ Erro: requests não instalado")
    print("Instale com: pip3 install requests")
    sys.exit(1)


# Chaves OpenRouter (api_key, nome)
OPENROUTER_KEYS: List[Tuple[str, str]] = [
    ("<SEGREDO_REMOVIDO>", "-1"),
    ("<SEGREDO_REMOVIDO>", "alicina ai"),
    ("<SEGREDO_REMOVIDO>", "andre"),
    ("<SEGREDO_REMOVIDO>", "emerson paga"),
]

# Chaves Groq (api_key, nome)
GROQ_KEYS: List[Tuple[str, str]] = [
    ("<SEGREDO_REMOVIDO>", "groq-1"),
    ("<SEGREDO_REMOVIDO>", "groq-2"),
    ("<SEGREDO_REMOVIDO>", "groq-3"),
    ("<SEGREDO_REMOVIDO>", "groq-4"),
    ("<SEGREDO_REMOVIDO>", "groq-5"),
    ("<SEGREDO_REMOVIDO>", "groq-6"),
    ("<SEGREDO_REMOVIDO>", "groq-7"),
    ("<SEGREDO_REMOVIDO>", "groq-8"),
    ("<SEGREDO_REMOVIDO>", "groq-9"),
]

# Proxies Webshare
PROXY_URLS: List[str] = [
    # Host: 45.39.15.202:6632
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@45.39.15.202:6632/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",  # Hhhbgf

    # Host: 31.59.20.176:6754
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@31.59.20.176:6754/",

    # Host: p.webshare.io:80
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
    "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80/",
]


def add_openrouter_keys(api_url: str, token: str) -> int:
    """Adiciona chaves OpenRouter via API. Retorna número de chaves adicionadas com sucesso."""
    print("=" * 50)
    print(f"🔑 Adicionando {len(OPENROUTER_KEYS)} chaves OpenRouter...")
    print("=" * 50)
    print()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    success_count = 0

    for api_key, name in OPENROUTER_KEYS:
        print(f"Adicionando: {name}")

        payload = {
            "name": f"OpenRouter - {name}",
            "type": "llm",
            "provider": "openrouter",
            "api_key": api_key,
            "base_url": "https://openrouter.ai/api",
        }

        try:
            response = requests.post(
                f"{api_url}/api/credentials",
                headers=headers,
                json=payload,
                timeout=10,
            )

            if response.status_code in (200, 201):
                print(f"  ✅ Adicionada com sucesso")
                success_count += 1
            else:
                print(f"  ❌ Erro: HTTP {response.status_code}")
                try:
                    print(f"  Resposta: {response.json()}")
                except:
                    print(f"  Resposta: {response.text[:200]}")

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Erro de conexão: {e}")

        time.sleep(0.5)

    print()
    return success_count


def add_groq_keys(api_url: str, token: str) -> int:
    """Adiciona chaves Groq via API. Retorna número de chaves adicionadas com sucesso."""
    print("=" * 50)
    print(f"🚀 Adicionando {len(GROQ_KEYS)} chaves Groq...")
    print("=" * 50)
    print()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    success_count = 0

    for api_key, name in GROQ_KEYS:
        print(f"Adicionando: {name}")

        payload = {
            "name": f"Groq - {name}",
            "type": "llm",
            "provider": "groq",
            "api_key": api_key,
            "base_url": "https://api.groq.com/openai",
        }

        try:
            response = requests.post(
                f"{api_url}/api/credentials",
                headers=headers,
                json=payload,
                timeout=10,
            )

            if response.status_code in (200, 201):
                print(f"  ✅ Adicionada com sucesso")
                success_count += 1
            else:
                print(f"  ❌ Erro: HTTP {response.status_code}")
                try:
                    print(f"  Resposta: {response.json()}")
                except:
                    print(f"  Resposta: {response.text[:200]}")

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Erro de conexão: {e}")

        time.sleep(0.5)

    print()
    return success_count


def configure_proxies(api_url: str, token: str) -> bool:
    """Configura proxies Webshare via API. Retorna True se sucesso."""
    print("=" * 50)
    print(f"🌐 Configurando {len(PROXY_URLS)} proxies Webshare...")
    print("=" * 50)
    print()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    payload = {
        "proxy": {
            "enabled": True,
            "proxy_urls": PROXY_URLS,
        }
    }

    try:
        response = requests.post(
            f"{api_url}/api/settings",
            headers=headers,
            json=payload,
            timeout=10,
        )

        if response.status_code in (200, 201):
            print("✅ Proxies configurados com sucesso")
            return True
        else:
            print(f"❌ Erro ao configurar proxies: HTTP {response.status_code}")
            try:
                print(f"Resposta: {response.json()}")
            except:
                print(f"Resposta: {response.text[:200]}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Adiciona chaves OpenRouter e configura proxies no Hermes Call"
    )
    parser.add_argument(
        "--token",
        default=os.getenv("HERMES_TOKEN"),
        help="JWT token de autenticação (ou defina HERMES_TOKEN)",
    )
    parser.add_argument(
        "--url",
        default=os.getenv("HERMES_API_URL", "http://localhost:8080"),
        help="URL da API do Hermes Call (padrão: http://localhost:8080)",
    )
    parser.add_argument(
        "--skip-keys",
        action="store_true",
        help="Pular adição de chaves OpenRouter",
    )
    parser.add_argument(
        "--skip-groq",
        action="store_true",
        help="Pular adição de chaves Groq",
    )
    parser.add_argument(
        "--skip-proxies",
        action="store_true",
        help="Pular configuração de proxies",
    )

    args = parser.parse_args()

    if not args.token:
        print("❌ Erro: Token não fornecido")
        print("Use: --token SEU_TOKEN ou defina HERMES_TOKEN")
        sys.exit(1)

    print()
    print("🚀 Iniciando configuração do Hermes Call")
    print(f"📍 API URL: {args.url}")
    print()

    openrouter_added = 0
    groq_added = 0
    proxies_ok = False

    if not args.skip_keys:
        openrouter_added = add_openrouter_keys(args.url, args.token)

    if not args.skip_groq:
        groq_added = add_groq_keys(args.url, args.token)

    if not args.skip_proxies:
        proxies_ok = configure_proxies(args.url, args.token)

    print()
    print("=" * 50)
    print("✅ Concluído!")
    print("=" * 50)
    print()
    print(f"📊 Resumo:")
    print(f"  - Chaves OpenRouter adicionadas: {openrouter_added}/{len(OPENROUTER_KEYS)}")
    print(f"  - Chaves Groq adicionadas: {groq_added}/{len(GROQ_KEYS)}")
    print(f"  - Proxies configurados: {'✅' if proxies_ok else '❌'}")
    print()
    print("📝 Próximos passos:")
    print("  1. Reinicie o serviço Hermes Call")
    print("  2. Verifique os logs: journalctl -u hermes-call -f")
    print("  3. Confirme que vê: 'proxy pool initialized'")
    print()


if __name__ == "__main__":
    main()
