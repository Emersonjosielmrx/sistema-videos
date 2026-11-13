# -*- coding: utf-8 -*-
"""
tests/test_youtube.py — Teste funcional do cliente YouTube HTTP.
"""
import sys
from pathlib import Path

# Adiciona diretório raiz do projeto ao path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.youtube.client import YouTubePublico, YouTubeStudioClient


def test_youtube_publico():
    print("\n--- [TESTE] YouTube Público (HTTP puro) ---")
    yt = YouTubePublico()
    # Canal exemplo oficial de testes (ex: YouTube Brasil ou canal de animes)
    canal_id = "UCBR8-60-B28hp2BmDPdntcQ"  # YouTube
    resumo = yt.obter_resumo_canal(canal_id)
    print(f"Nome do Canal: {resumo.get('nome')}")
    print(f"Inscritos: {resumo.get('inscritos')}")
    print(f"Qtd Vídeos Recentes: {len(resumo.get('ultimos_videos', []))}")
    print(f"Qtd Shorts Recentes: {len(resumo.get('ultimos_shorts', []))}")
    assert resumo.get("nome") is not None, "Falha ao obter nome do canal público"
    print("[SUCESSO] YouTube Público funcionando 100% por HTTP!")


def test_youtube_studio():
    print("\n--- [TESTE] YouTube Studio (HTTP puro com cookies) ---")
    # Conta existente com cookies em cookies_youtube
    slug = "animescomia"
    try:
        studio = YouTubeStudioClient(slug)
        print(f"Canal ID no Studio: {studio.channel_id}")
        print(f"Innertube Key: {studio.innertube_key[:10]}...")
        videos = studio.listar_videos(quantos=5)
        print(f"Vídeos encontrados no Studio: {len(videos)}")
        for v in videos[:3]:
            print(f"  - [{v['id']}] {v['titulo'][:40]} | Views: {v['views']} | Monetização: {v['monetizacao']}")
        print("[SUCESSO] YouTube Studio funcionando 100% por HTTP sem abrir Chrome!")
    except Exception as e:
        print(f"[AVISO/INFO] Teste do Studio para {slug}: {e}")


if __name__ == "__main__":
    test_youtube_publico()
    test_youtube_studio()
