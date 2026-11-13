# -*- coding: utf-8 -*-
"""
tests/test_all.py — Suíte completa de validação sem navegador.
Executa os testes de todos os módulos HTTP e gera um relatório consolidado com dados reais.
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.youtube.client import YouTubePublico
from services.google_photos.client import GooglePhotosClient
from services.tiktok.client import TikTokWebClient
from services.instagram.client import InstagramWebClient


def run_all_tests():
    print("=" * 65)
    print(" SUÍTE DE TESTES: PROJETO NAVEGADOR SEM NAVEGADOR (HTTP PURO)")
    print("=" * 65)

    resultados = []

    # 1. YouTube Público (Browse API sem login)
    t0 = time.time()
    try:
        yt = YouTubePublico()
        res = yt.obter_resumo_canal("UCBR8-60-B28hp2BmDPdntcQ")
        dur = time.time() - t0
        nome = res.get("nome")
        inscritos = res.get("inscritos")
        if nome and inscritos:
            status = "OK"
            detalhe = f"Canal: {nome} ({inscritos} inscritos)"
        else:
            status = "FALHA"
            detalhe = f"Dados incompletos: {res}"
        resultados.append(("YouTube Público", status, f"{dur:.2f}s", detalhe))
    except Exception as e:
        resultados.append(("YouTube Público", "ERRO", f"{time.time()-t0:.2f}s", str(e)))

    # 2. TikTok Web (oEmbed oficial sem WAF)
    t0 = time.time()
    try:
        tk = TikTokWebClient("padrao")
        res_tk = tk.obter_perfil("tiktok")
        dur = time.time() - t0
        if res_tk.get("sucesso") and res_tk.get("author_name"):
            status = "OK"
            detalhe = f"@{res_tk.get('username')} -> '{res_tk.get('author_name')}' (HTTP {res_tk.get('status_http')})"
        else:
            status = "FALHA"
            detalhe = f"Falha na consulta: {res_tk.get('erro')}"
        resultados.append(("TikTok oEmbed API", status, f"{dur:.2f}s", detalhe))
    except Exception as e:
        resultados.append(("TikTok oEmbed API", "ERRO", f"{time.time()-t0:.2f}s", str(e)))

    # 3. Instagram Web API
    t0 = time.time()
    try:
        ig = InstagramWebClient("msenergypara")
        res_ig = ig.obter_perfil("instagram")
        dur = time.time() - t0
        if res_ig.get("sucesso"):
            status = "OK"
            detalhe = f"@{res_ig.get('username')} ({res_ig.get('seguidores')} seguidores)"
        else:
            # Reportar o status real da API sem falso positivo
            status = "INFO"
            detalhe = f"Status {res_ig.get('status_http')}: {res_ig.get('erro')}"
        resultados.append(("Instagram Web API", status, f"{dur:.2f}s", detalhe))
    except Exception as e:
        resultados.append(("Instagram Web API", "ERRO", f"{time.time()-t0:.2f}s", str(e)))

    # 4. Google Fotos (Detecção de Sessão e Auth)
    t0 = time.time()
    try:
        gf = GooglePhotosClient("mundosolar1995")
        dur = time.time() - t0
        if gf.sessao_valida:
            status = "OK"
            detalhe = f"Autenticado (SNlM0e: {gf.snlm0e_token[:12]}...)"
        else:
            status = "INFO"
            detalhe = f"Sessão expirada para {gf.conta} (requer renovação no cofre)"
        resultados.append(("Google Fotos Auth", status, f"{dur:.2f}s", detalhe))
    except Exception as e:
        resultados.append(("Google Fotos Auth", "ERRO", f"{time.time()-t0:.2f}s", str(e)))

    # Exibição do relatório consolidado
    print("\n" + "=" * 65)
    print(" RELATÓRIO DE EXECUÇÃO HTTP PURO (SEM NAVEGADOR)")
    print("=" * 65)
    for modulo, st, tempo, detalhe in resultados:
        print(f"[{st:5}] {modulo:22} | {tempo:6} | {detalhe}")
    print("=" * 65)


if __name__ == "__main__":
    run_all_tests()
