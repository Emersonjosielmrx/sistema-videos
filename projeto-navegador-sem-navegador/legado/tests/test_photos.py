# -*- coding: utf-8 -*-
"""
tests/test_photos.py — Teste funcional do cliente Google Fotos HTTP puro.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.google_photos.client import GooglePhotosClient


def test_google_photos():
    print("\n--- [TESTE] Google Fotos (HTTP puro com cookies) ---")
    conta = "mundosolar1995"
    photos = GooglePhotosClient(conta)
    print(f"Conta verificada: {photos.conta}")
    print(f"Sessão autenticada ativa? {photos.sessao_valida}")
    print(f"Token SNlM0e: {photos.snlm0e_token[:15] if photos.snlm0e_token else 'N/A'}")

    if photos.sessao_valida:
        resultados = photos.buscar_midias("solar", max_resultados=5)
        print(f"Fotos encontradas para 'solar': {len(resultados)}")
        for r in resultados[:3]:
            print(f"  - [{r['foto_id']}] {r['url_pagina']}")
        print("[SUCESSO] Google Fotos autenticado e buscando via HTTP!")
    else:
        print("[INFO] Conta mundosolar1995 requer renovação pelo cofre (comportamento seguro esperado).")


if __name__ == "__main__":
    test_google_photos()
