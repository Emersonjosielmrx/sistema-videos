#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def main():
    url = "https://hiper.cool/"
    print(f"Acessando {url} em modo HEADED...")
    with sync_playwright() as pw:
        # Launch headed so user can see it and solve Cloudflare if needed
        browser = pw.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent=UA,
            locale="pt-BR",
        )
        
        # Load state if exists
        state_path = Path(__file__).resolve().parent.parent / "secrets" / "playwright_state.json"
        if state_path.exists():
            ctx.storage_state(path=str(state_path))
            print("[OK] Sessão anterior carregada.")
            
        page = ctx.new_page()
        try:
            # Set a long timeout (90s)
            page.goto(url, wait_until="networkidle", timeout=90000)
            print("[OK] Página carregada! Título:", page.title())
            
            # Save state
            ctx.storage_state(path=str(state_path))
            print("[OK] Estado de sessão atualizado.")
            
            # Extract links
            links = page.query_selector_all("a")
            manga_links = set()
            for link in links:
                href = link.get_attribute("href") or ""
                text = (link.inner_text() or "").strip()
                if "/manga/" in href:
                    manga_links.add((href, text))
                    
            print(f"\nEncontrados {len(manga_links)} links de manga:")
            for href, text in sorted(manga_links):
                print(f"  - {text}: {href}")
                
            # Keep browser open for 15s to let the user inspect or solve anything
            print("Mantendo o browser aberto por 15s...")
            time.sleep(15)
            
        except Exception as e:
            print("Erro durante navegação:", e)
            print("Mantendo o browser aberto por 30s para depuração...")
            time.sleep(30)
        finally:
            browser.close()

if __name__ == "__main__":
    main()
