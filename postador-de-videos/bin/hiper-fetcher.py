#!/usr/bin/env python3
"""hiper-fetcher.py — Scraper Playwright pra hiper.cool

Baixa strips/painéis de capítulos do hiper.cool com stealth browser.
Lida com age-gate, lazy-loading, e proteção Cloudflare.

Uso:
    python bin/hiper-fetcher.py --url <chapter_url> --slug nome
    python bin/hiper-fetcher.py --url <url> --headed     # debug (browser visível)
    python bin/hiper-fetcher.py --discover <manga_url>   # lista capítulos
    python bin/hiper-fetcher.py --list-cache             # mostra cache local
"""
import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERRO: Playwright não instalado. Rode:\n"
          "  pip3 install playwright && python3 -m playwright install chromium",
          file=sys.stderr)
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("ERRO: Pillow não instalado. Rode: pip3 install Pillow", file=sys.stderr)
    sys.exit(1)

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "workspace" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Config
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
MIN_IMG_SIZE = 500  # pixels (width ou height mínimo pra considerar um painel real)
MAX_PANELS = 50     # limite de imagens por capítulo
SCROLL_STEPS = 80
SCROLL_PX = 2000
SCROLL_DELAY = 0.4

# Padrões de ad/logo pra filtrar
AD_PATTERNS = re.compile(
    r"logo|banner|advert|doubleclick|google-analytics|/ads/|pixel\.|"
    r"adsense|popup|modal-bg|watermark|marca-dagua", re.IGNORECASE
)

# Seletores do reader (tentativa em ordem — hiper.cool pode usar vários)
READER_SELECTORS = [
    ".chapter-images img",
    ".reading-content img",
    ".chapter-content img",
    "#chapter-container img",
    ".manga-reader img",
    ".reader-area img",
    # lerhentais.com (SPA React)
    ".reader img",
    ".comic-page img",
    "[class*='reader'] img",
    "[class*='chapter'] img",
    "article img",
    ".entry-content img",
    "img",
]

# Botões de age-gate comuns
AGE_GATE_SELECTORS = [
    "button:has-text('Entrar')",
    "button:has-text('Sou maior')",
    "button:has-text('18')",
    "button:has-text('Enter')",
    "button:has-text('Continuar')",
    "button:has-text('Aceitar')",
    "button:has-text('Concordo')",
    "button:has-text('Sim')",
    "button:has-text('Yes')",
    "button:has-text('Confirmar')",
    "a:has-text('Entrar')",
    "a:has-text('Sou maior')",
    "a:has-text('Sim, tenho')",
    "a:has-text('Continuar')",
    "[data-age-confirm]",
    ".age-gate button",
    ".nsfw-confirm button",
    "#age-verify button",
    ".modal button",
    "dialog button",
]


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


def slugify(text):
    """Converte texto pra slug seguro pra nome de pasta."""
    text = text.lower().strip()
    text = re.sub(r"[àáâãä]", "a", text)
    text = re.sub(r"[èéêë]", "e", text)
    text = re.sub(r"[ìíîï]", "i", text)
    text = re.sub(r"[òóôõö]", "o", text)
    text = re.sub(r"[ùúûü]", "u", text)
    text = re.sub(r"[ç]", "c", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:80]


def handle_age_gate(page):
    """Tenta clicar em botões/checkboxes de confirmação de idade.
    Faz múltiplas tentativas pra pegar modais que aparecem com delay."""
    found = False
    for attempt in range(3):
        # Tiamanhwa.com: div #tia-age-gate com botão dentro
        gate = page.query_selector("#tia-age-gate")
        if gate:
            btn = gate.query_selector("button") or gate.query_selector("a")
            if btn:
                try:
                    btn.click()
                    time.sleep(3)
                    return True
                except Exception:
                    page.evaluate('document.getElementById("tia-age-gate")?.remove()')
                    time.sleep(1)
                    return True

        # Checkboxes de confirmação
        for cb_sel in ["input[type='checkbox']", "[name*='age']", "[id*='age']", "[name*='nsfw']"]:
            try:
                cb = page.query_selector(cb_sel)
                if cb and cb.is_visible() and not cb.is_checked():
                    cb.click()
                    time.sleep(0.5)
                    found = True
            except Exception:
                continue

        # Botões
        for selector in AGE_GATE_SELECTORS:
            try:
                el = page.query_selector(selector)
                if el and el.is_visible():
                    log(f"  Age-gate detectado: {selector}")
                    el.click()
                    time.sleep(2)
                    return True
            except Exception:
                continue

        if found:
            return True
        time.sleep(1)
    return False


def handle_cloudflare(page):
    """Detecta e espera challenge Cloudflare."""
    try:
        content = page.content()[:5000].lower()
        if "challenge" in page.url.lower() or "cf-chl" in content or "cloudflare" in content:
            log("  Cloudflare challenge detectado — esperando 15s...")
            time.sleep(15)
            return True
    except Exception:
        pass
    return False


def scroll_page(page):
    """Scroll agressivo pra triggar lazy-loading."""
    last_height = 0
    for step in range(SCROLL_STEPS):
        page.evaluate("window.scrollBy(0, 2000)")
        time.sleep(SCROLL_DELAY)
        cur = page.evaluate("document.body.scrollHeight")
        if cur == last_height:
            break
        last_height = cur
    # Voltar pro topo
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.5)


def collect_images(page, reader_selector=None):
    """Coleta URLs de imagens do reader. Filtra ads e imagens pequenas."""
    # Tentar seletor específico primeiro
    selectors = [reader_selector] if reader_selector else READER_SELECTORS

    images = []
    for sel in selectors:
        try:
            elements = page.query_selector_all(sel)
            if elements and len(elements) >= 3:
                # Filtrar por tamanho e padrão de ad
                for el in elements:
                    try:
                        nat_w = el.evaluate("e => e.naturalWidth")
                        nat_h = el.evaluate("e => e.naturalHeight")
                        src = el.evaluate("e => e.src || e.dataset.src || e.dataset.lazySrc || ''")

                        if nat_w < MIN_IMG_SIZE and nat_h < MIN_IMG_SIZE:
                            continue
                        if not src or AD_PATTERNS.search(src):
                            continue

                        images.append({"src": src, "width": nat_w, "height": nat_h, "el": el})
                    except Exception:
                        continue

                if images:
                    log(f"  Seletor '{sel}': {len(images)} imagens encontradas")
                    break
        except Exception:
            continue

    # Limitar
    return images[:MAX_PANELS]


def download_image(url, out_path, referer="https://hiper.cool/"):
    """Download direto via HTTP GET com headers."""
    headers = {"User-Agent": UA, "Referer": referer}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        if len(data) < 5000:
            return False
        with open(out_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        log(f"  download falhou: {url[:80]} — {e}")
        return False


def screenshot_element(el, out_path):
    """Fallback: screenshot do elemento (pra blob: URLs)."""
    try:
        el.scroll_into_view_if_needed()
        time.sleep(0.3)
        el.screenshot(path=str(out_path), type="jpeg", quality=90)
        return out_path.exists() and out_path.stat().st_size > 5000
    except Exception as e:
        log(f"  screenshot falhou: {e}")
        return False


def convert_webp_to_jpg(img_path):
    """Converte webp pra jpg se necessário."""
    if img_path.suffix.lower() == ".webp":
        jpg_path = img_path.with_suffix(".jpg")
        try:
            img = Image.open(img_path).convert("RGB")
            img.save(jpg_path, "JPEG", quality=90)
            img_path.unlink()
            return jpg_path
        except Exception as e:
            log(f"  conversão webp→jpg falhou: {e}")
    return img_path


def fetch_chapter(url, slug, headed=False, reader_selector=None):
    """Baixa todas as imagens de um capítulo.

    Retorna path do diretório de cache ou None em erro.
    """
    out_dir = CACHE_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # Checar se já existe no cache
    existing = list(out_dir.glob("panel_*.jpg")) + list(out_dir.glob("panel_*.png"))
    if existing:
        log(f"  Cache hit: {len(existing)} imagens em {out_dir}")
        return out_dir

    log(f"Fetching: {url}")
    log(f"  Slug: {slug}")
    log(f"  Output: {out_dir}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=not headed,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        playwright_state_path = PROJECT_DIR / "secrets" / "playwright_state.json"
        playwright_state_path.parent.mkdir(parents=True, exist_ok=True)

        context_kwargs = {
            "viewport": {"width": 1366, "height": 900},
            "user_agent": UA,
            "locale": "pt-BR",
            "timezone_id": "America/Sao_Paulo",
        }
        if playwright_state_path.exists():
            context_kwargs["storage_state"] = str(playwright_state_path)
            log("  ✓ Carregando sessão anterior de secrets/playwright_state.json")

        ctx = browser.new_context(**context_kwargs)

        # Stealth básico
        ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            window.chrome = {runtime: {}};
        """)

        page = ctx.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

            # Handle Cloudflare
            handle_cloudflare(page)

            # Handle age-gate
            handle_age_gate(page)
            time.sleep(1)

            # Scroll pra lazy-loading
            log("  Scrolling pra lazy-loading...")
            scroll_page(page)

            # Salvar estado atual de sessão
            try:
                ctx.storage_state(path=str(playwright_state_path))
                log("  ✓ Estado de sessão salvo/atualizado")
            except Exception as e_state:
                log(f"  ⚠ Não foi possível salvar o estado de sessão: {e_state}")

            # Coletar imagens
            images = collect_images(page, reader_selector)
            if not images:
                log("  ✗ Nenhuma imagem encontrada!")
                if headed:
                    log("  Browser aberto — inspecione o DOM manualmente.")
                    try:
                        input("  Pressione ENTER pra fechar...")
                    except EOFError:
                        pass
                browser.close()
                return None

            log(f"  Baixando {len(images)} imagens (paralelo)...")
            from concurrent.futures import ThreadPoolExecutor

            # Separar HTTP (paralelizável) de blob (precisa screenshot na página)
            http_tasks = []
            for i, img_info in enumerate(images):
                src = img_info["src"]
                ext = ".png" if ".png" in src.lower() else (".webp" if ".webp" in src.lower() else ".jpg")
                out_path = out_dir / f"panel_{i:03d}{ext}"
                if src.startswith("http"):
                    http_tasks.append((i, src, out_path))

            results = {}

            def _dl(task):
                i, src, op = task
                return i, download_image(src, op, referer=url), op

            # Pool conservador (5 workers) pra não estressar o servidor
            with ThreadPoolExecutor(max_workers=5) as ex:
                for i, ok, op in ex.map(_dl, http_tasks):
                    results[i] = (ok, op)

            downloaded = 0
            for i, img_info in enumerate(images):
                ok, op = results.get(i, (False, None))
                if ok and op:
                    convert_webp_to_jpg(op)
                    downloaded += 1
                else:
                    # Fallback screenshot (sequencial — precisa do elemento na página)
                    sp = out_dir / f"panel_{i:03d}.jpg"
                    if screenshot_element(img_info["el"], sp):
                        downloaded += 1

            log(f"  ✓ {downloaded}/{len(images)} imagens baixadas")

        except Exception as e:
            log(f"  ✗ Erro: {e}")
            if headed:
                try:
                    input("  Pressione ENTER pra fechar...")
                except EOFError:
                    pass
            browser.close()
            return None

        browser.close()

    # Salvar meta
    meta = {
        "url": url,
        "slug": slug,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "images_count": downloaded,
    }
    (out_dir / "_meta.json").write_text(json.dumps(meta, indent=2))

    return out_dir


def discover_chapters(manga_url, headed=False):
    """Lista capítulos disponíveis de uma página de mangá."""
    log(f"Discovering chapters: {manga_url}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=not headed,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent=UA, locale="pt-BR",
        )
        page = ctx.new_page()

        try:
            page.goto(manga_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            handle_age_gate(page)
            time.sleep(1)

            # Buscar links de capítulos (patterns comuns)
            chapter_selectors = [
                "a[href*='capitulo']",
                "a[href*='chapter']",
                "a[href*='cap-']",
                "a[href*='/read/']",
                ".chapter-list a",
                ".chapters a",
                ".listing-chapters a",
                "ul.chapters li a",
            ]

            chapters = []
            for sel in chapter_selectors:
                try:
                    links = page.query_selector_all(sel)
                    for link in links:
                        href = link.get_attribute("href") or ""
                        text = (link.inner_text() or "").strip()
                        if href and text:
                            if not href.startswith("http"):
                                href = page.evaluate(f"new URL('{href}', window.location.href).href")
                            chapters.append({"url": href, "title": text})
                except Exception:
                    continue
                if chapters:
                    break

            # Deduplicar por URL
            seen = set()
            unique = []
            for ch in chapters:
                if ch["url"] not in seen:
                    seen.add(ch["url"])
                    unique.append(ch)
            chapters = unique

        except Exception as e:
            log(f"  ✗ Erro: {e}")
            chapters = []

        browser.close()

    return chapters


def list_cache():
    """Lista capítulos no cache local."""
    if not CACHE_DIR.exists():
        print("Cache vazio.")
        return
    for d in sorted(CACHE_DIR.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            imgs = list(d.glob("panel_*"))
            meta_path = d / "_meta.json"
            meta = ""
            if meta_path.exists():
                m = json.loads(meta_path.read_text())
                meta = f" — {m.get('fetched_at', '?')}"
            print(f"  {d.name}: {len(imgs)} imagens{meta}")


def main():
    parser = argparse.ArgumentParser(description="Scraper Playwright pra hiper.cool")
    parser.add_argument("--url", help="URL do capítulo pra baixar")
    parser.add_argument("--slug", help="Nome/slug pro diretório de cache")
    parser.add_argument("--headed", action="store_true",
                        help="Browser visível (pra debug)")
    parser.add_argument("--reader-selector",
                        help="CSS selector customizado pro container de imagens")
    parser.add_argument("--discover", metavar="MANGA_URL",
                        help="Lista capítulos de uma página de mangá")
    parser.add_argument("--list-cache", action="store_true",
                        help="Mostra capítulos no cache local")
    parser.add_argument("--force", action="store_true",
                        help="Ignora cache e baixa de novo")

    args = parser.parse_args()

    if args.list_cache:
        list_cache()
        return

    if args.discover:
        chapters = discover_chapters(args.discover, headed=args.headed)
        if chapters:
            print(f"\n{len(chapters)} capítulos encontrados:\n")
            for i, ch in enumerate(chapters):
                print(f"  [{i+1:3d}] {ch['title']}")
                print(f"        {ch['url']}")
        else:
            print("Nenhum capítulo encontrado.")
        return

    if args.url:
        if not args.slug:
            # Auto-gerar slug da URL
            args.slug = slugify(args.url.split("/")[-1] or args.url.split("/")[-2] or "chapter")

        if args.force:
            # Limpar cache
            out_dir = CACHE_DIR / args.slug
            if out_dir.exists():
                import shutil
                shutil.rmtree(out_dir)

        result = fetch_chapter(args.url, args.slug,
                               headed=args.headed,
                               reader_selector=args.reader_selector)
        if result:
            print(f"\n✓ Capítulo salvo em: {result}/")
            imgs = list(result.glob("panel_*"))
            print(f"  {len(imgs)} imagens")
            print(f"\nPróximo passo — testar corte de painéis:")
            print(f"  python bin/panel-splitter.py --test --input {result}")
        else:
            print("\n✗ Falha ao baixar capítulo.", file=sys.stderr)
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()

