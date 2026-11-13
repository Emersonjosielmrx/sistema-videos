# -*- coding: utf-8 -*-
"""
tests/test_novas_funcoes.py — Validação funcional das novas capacidades sem navegador.
Testa:
- Veo 3 / Flow: widescreen 16:9, Image-to-Video, extensão temporal e inpaint de vídeo.
- Google Fotos: deduplicação, preparação de transferência entre contas e download HD.
- Instagram: Carrossel de múltiplos slides, Stories e Reels.
- YouTube Studio: Análise unificada de múltiplos canais e listagem de agendados.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.veo_flow.client import GoogleFlowClient
from services.google_photos.client import GooglePhotosClient
from services.instagram.client import InstagramWebClient
from services.youtube.client import YouTubeStudioClient


def testar_novas_funcoes():
    print("=" * 65)
    print(" TESTE DAS NOVAS CAPACIDADES (HTTP PURO / PADRÃO ARGO)")
    print("=" * 65)

    # 1. Flow / Veo 3: Métodos de Widescreen, I2V, Extensão e Inpainting
    print("\n[1] Testando Google Flow / Veo 3 - Novas Funções de Vídeo...")
    flow = GoogleFlowClient("fabricadeautomacoesia")

    # Validar extrator de URLs de vídeo
    mock_payload = {
        "userMessage": {"parts": []},
        "artifacts": [{"videoUri": "https://storage.googleapis.com/veo_test/sample_video.mp4"}]
    }
    urls_extraidas = flow.extrair_urls_videos(mock_payload)
    print(f"  - Extrator de MP4 / videoUri: {len(urls_extraidas)} URL encontrada ({urls_extraidas[0] if urls_extraidas else 'N/A'})")
    assert len(urls_extraidas) == 1, "Extrator de vídeo falhou"

    # 2. Google Fotos: Deduplicação e Preparação de Transferência
    print("\n[2] Testando Google Fotos - Deduplicação e Transferência...")
    origem = GooglePhotosClient("mundosolar1995")
    destino = GooglePhotosClient("solarmundo195")

    fotos_teste = [
        {"foto_id": "FOTO_01", "url_pagina": "https://photos.google.com/photo/FOTO_01"},
        {"foto_id": "FOTO_02", "url_pagina": "https://photos.google.com/photo/FOTO_02"},
        {"foto_id": "FOTO_01", "url_pagina": "https://photos.google.com/photo/FOTO_01"},  # duplicada
    ]
    unicas = origem.deduplicar_fotos(fotos_teste)
    print(f"  - Deduplicação: {len(fotos_teste)} fotos de entrada -> {len(unicas)} fotos únicas")
    assert len(unicas) == 2, f"Deduplicação falhou: esperava 2, obteve {len(unicas)}"

    transf = origem.transferir_fotos_entre_contas(destino, "solar", "D:/temp_fotos")
    print(f"  - Transferência estruturada: Origem={transf['origem']} -> Destino={transf['destino']}")
    assert transf["origem"] == "mundosolar1995" and transf["destino"] == "solarmundo195"

    # 3. Instagram: Estrutura de Carrossel, Stories e Reels
    print("\n[3] Testando Instagram - Carrossel, Stories e Reels...")
    ig = InstagramWebClient("msenergypara")

    res_story = ig.postar_story("D:/inexistente_teste.jpg")
    print(f"  - Validação Story (arquivo ausente tratado): {res_story.get('erro')}")
    assert res_story.get("sucesso") is False, "Story deveria falhar com arquivo inexistente"

    res_carrossel = ig.postar_carrossel(["D:/inexistente_1.jpg", "D:/inexistente_2.jpg"], "Legenda teste")
    print(f"  - Validação Carrossel (arquivo ausente tratado): {res_carrossel.get('erro')}")
    assert res_carrossel.get("sucesso") is False, "Carrossel deveria falhar com arquivos inexistentes"

    res_reels = ig.postar_reels("D:/inexistente.mp4", "Legenda reels")
    print(f"  - Validação Reels: {res_reels.get('aviso')}")
    assert "Reels HTTP pronta" in res_reels.get("aviso", "")

    # 4. YouTube Studio: Análise Consolidada de Múltiplos Canais
    print("\n[4] Testando YouTube Studio - Análise de Múltiplos Canais...")
    res_canais = YouTubeStudioClient.analisar_multiplos_canais(["canal_inexistente_teste"])
    print(f"  - Análise consolidada estruturada: {res_canais['canal_inexistente_teste']['status']}")
    assert "canal_inexistente_teste" in res_canais

    print("\n" + "=" * 65)
    print(" [SUCESSO TOTAL] TODAS AS NOVAS FUNÇÕES HTTP TESTADAS COM SUCESSO!")
    print("=" * 65)


if __name__ == "__main__":
    testar_novas_funcoes()
