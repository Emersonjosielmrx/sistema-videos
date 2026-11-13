#!/usr/bin/env python3
"""stats_views_navegador.py — Estatisticas via navegador (sem token OAuth)."""
import argparse
import json
import sys
import time
import re
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BIN = Path(__file__).resolve().parent
RAIZ = BIN.parent

def extrair_numero_views(texto):
    """Extrai número de views do texto (ex: '1,2 mil visualizações' -> 1200)."""
    if not texto:
        return 0
    
    texto = texto.lower()
    
    # Remove "visualizações" e similares
    texto = texto.replace("visualizações", "").replace("visualizacao", "").replace("views", "").strip()
    
    # Procura padrões tipo "1,2 mil" ou "1.234"
    if "mil" in texto:
        nums = re.findall(r'(\d+[,.]?\d*)', texto)
        if nums:
            num = nums[0].replace(",", ".")
            return int(float(num) * 1000)
    elif "mi" in texto:  # milhões
        nums = re.findall(r'(\d+[,.]?\d*)', texto)
        if nums:
            num = nums[0].replace(",", ".")
            return int(float(num) * 1000000)
    else:
        # Número direto (ex: "1.234")
        nums = re.findall(r'\d+', texto.replace(".", "").replace(",", ""))
        if nums:
            return int(nums[0])
    
    return 0

def coletar_views_navegador(handle, max_videos=50):
    """Coleta views via Playwright."""
    from playwright.sync_api import sync_playwright
    
    resultados = []
    url = f"https://www.youtube.com/{handle}/videos"
    
    print(f"  Acessando {url}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(4)
            
            # Rola para carregar mais vídeos
            for _ in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            
            # Tenta diferentes seletores
            videos = page.query_selector_all("ytd-rich-item-renderer")
            if not videos:
                videos = page.query_selector_all("ytd-grid-video-renderer")
            
            print(f"  Encontrados {len(videos)} vídeos")
            
            for idx, video in enumerate(videos[:max_videos]):
                try:
                    # Título
                    titulo_el = video.query_selector("#video-title")
                    if not titulo_el:
                        titulo_el = video.query_selector("a#video-title-link")
                    titulo = titulo_el.get_attribute("title") if titulo_el else ""
                    
                    # Link
                    link = titulo_el.get_attribute("href") if titulo_el else ""
                    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else ""
                    
                    # Views - tenta vários seletores
                    views_text = ""
                    
                    # Tenta metadata-line
                    metadata = video.query_selector("#metadata-line")
                    if metadata:
                        spans = metadata.query_selector_all("span")
                        for span in spans:
                            text = span.inner_text().strip()
                            if "visualiza" in text or "view" in text:
                                views_text = text
                                break
                    
                    # Se não achou, tenta aria-label do título
                    if not views_text and titulo_el:
                        aria = titulo_el.get_attribute("aria-label")
                        if aria and ("visualiza" in aria or "view" in aria):
                            views_text = aria
                    
                    # Se ainda não achou, pega todo o texto do video
                    if not views_text:
                        texto_completo = video.inner_text()
                        for linha in texto_completo.split("\n"):
                            if "visualiza" in linha.lower() or "view" in linha.lower():
                                views_text = linha
                                break
                    
                    views = extrair_numero_views(views_text)
                    
                    if titulo:  # só adiciona se tem título
                        resultados.append({
                            "id": video_id,
                            "titulo": titulo[:80],
                            "views": views,
                            "views_text": views_text[:50]
                        })
                        
                        if idx < 3:  # debug dos 3 primeiros
                            print(f"    [{idx+1}] {views:>6} views | {titulo[:40]}")
                
                except Exception as e:
                    print(f"    Erro vídeo {idx}: {e}")
                    continue
                    
        except Exception as e:
            print(f"  ERRO: {e}")
        finally:
            browser.close()
    
    return resultados

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", help="canal específico")
    ap.add_argument("--max-videos", type=int, default=50)
    args = ap.parse_args()
    
    with open(RAIZ / "config" / "canais.json", encoding="utf-8") as f:
        dados = json.load(f)
    
    canais = []
    for info in dados["canais"].values():
        if args.canal:
            if args.canal.lower() not in info["nome"].lower():
                continue
        if info.get("handle"):
            canais.append(info)
    
    if not canais:
        print("Nenhum canal encontrado")
        return
    
    print(f"\nColetando {len(canais)} canal(is) via navegador...\n")
    
    resumo = []
    for canal in canais:
        print(f"\n── {canal['nome']} ({canal['handle']}) ──")
        try:
            videos = coletar_views_navegador(canal["handle"], args.max_videos)
            if videos:
                videos.sort(key=lambda v: v["views"], reverse=True)
                total = sum(v["views"] for v in videos)
                print(f"  Total: {total:,} views em {len(videos)} vídeos")
                for v in videos:
                    resumo.append((v["views"], canal["nome"], v["titulo"]))
        except Exception as e:
            print(f"  ERRO: {e}")
        time.sleep(5)
    
    if resumo:
        resumo.sort(reverse=True)
        print(f"\n{'='*72}\nTOP 10:\n{'='*72}")
        for views, nome, tit in resumo[:10]:
            print(f"   {views:>6} | {nome[:24]:<25} | {tit[:36]}")
        print(f"\nTotal: {sum(r[0] for r in resumo):,} views em {len(resumo)} vídeos")

if __name__ == "__main__":
    main()
