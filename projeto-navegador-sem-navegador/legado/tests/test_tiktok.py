# -*- coding: utf-8 -*-
"""
tests/test_tiktok.py — Teste funcional do cliente TikTok HTTP puro.
Valida consulta sem navegador usando a API oficial oEmbed e SSR.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.tiktok.client import TikTokWebClient


def test_tiktok_perfil():
    print("\n--- [TESTE] TikTok Web (HTTP puro) ---")
    tk = TikTokWebClient("padrao")
    alvo = "tiktok"  # perfil oficial do TikTok
    res = tk.obter_perfil(alvo)

    print(f"Username: @{res.get('username')}")
    print(f"Sucesso: {res.get('sucesso')}")
    print(f"Nome do Autor: {res.get('author_name')}")
    print(f"Título Retornado: {res.get('titulo')}")
    print(f"Status HTTP: {res.get('status_http')}")
    print(f"Seguidores (se SSR liberado): {res.get('seguidores')}")

    # Asserções estritas - nada de falsos positivos
    assert res.get("sucesso") is True, "Falha: oEmbed TikTok não retornou sucesso"
    assert res.get("status_http") == 200, f"Falha: status HTTP foi {res.get('status_http')}"
    assert res.get("author_name") is not None, "Falha: author_name veio nulo"
    assert res.get("username") == alvo, f"Username incorreto: {res.get('username')}"

    print("[SUCESSO] TikTok Web respondeu com sucesso por HTTP!")


if __name__ == "__main__":
    test_tiktok_perfil()
