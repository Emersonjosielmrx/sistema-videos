#!/usr/bin/env python3
"""tia-fetcher.py — Scraper pra tiamanhwa.com (tema Madara / WordPress)

Diferente do hiper.cool, o tiamanhwa.com serve as páginas do capítulo como
imagens estáticas em /wp-content/uploads/WP-manga/data/<hash>/imagem_NNN.webp,
acessíveis via HTTP direto com User-Agent de navegador (HTTP 200, sem
challenge de Cloudflare). Por isso NÃO precisamos de Playwright — basta
baixar o HTML do capítulo, extrair os data-src do reader em ordem, e baixar
cada strip.

Salva no mesmo formato que o hiper-fetcher (panel_NNN.jpg + _meta.json),
pra ser consumido por panel-splitter.py / hiper-pipeline.py sem alteração.

Uso:
    python bin/tia-fetcher.py --url <chapter_url> --slug nome
    python bin/tia-fetcher.py --discover <manhwa_url>   # lista capítulos
    python bin/tia-fetcher.py --url <url> --slug nome --max-panels 40
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
    from PIL import Image
except ImportError:
    print("ERRO: Pillow não instalado. Rode: pip3 install Pillow", file=sys.stderr)
    sys.exit(1)

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "workspace" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE = "https://tiamanhwa.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
# Cookie pra passar o age-gate de conteúdo adulto do tiamanhwa.
ADULT_COOKIE = "wpmanga-adult=1"
MIN_BYTES = 8000  # strips reais têm centenas de KB; thumbs/ícones são menores

# Páginas do capítulo (strips verticais). O reader Madara do tiamanhwa usa
# data-src (lazy-load) apontando pra WP-manga/data/<hash>/imagem_NNN.ext
PAGE_IMG_RE = re.compile(
    r'(?:data-src|data-lazy-src|src)\s*=\s*["\']\s*'
    r'(https://tiamanhwa\.com/wp-content/uploads/WP-manga/data/[^"\']+?'
    r'\.(?:webp|jpe?g|png))\s*["\']',
    re.IGNORECASE,
)


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[àáâãä]", "a", text)
    text = re.sub(r"[èéêë]", "e", text)
    text = re.sub(r"[ìíîï]", "i", text)
    text = re.sub(r"[òóôõö]", "o", text)
    text = re.sub(r"[ùúûü]", "u", text)
    text = re.sub(r"[ç]", "c", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:80]


def http_get(url, referer=BASE, binary=False, timeout=60):
    headers = {
        "User-Agent": UA,
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Referer": referer,
        "Cookie": ADULT_COOKIE,
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    return data if binary else data.decode("utf-8", errors="replace")


def discover(manhwa_url):
    """Lista capítulos de uma página de série."""
    html = http_get(manhwa_url)
    slug = manhwa_url.rstrip("/").split("/")[-1]
    chap_re = re.compile(
        rf'https://tiamanhwa\.com/manhwa/{re.escape(slug)}/(capitulo-[0-9]+)/')
    caps = sorted(set(chap_re.findall(html)),
                  key=lambda c: int(c.split("-")[-1]))
    print(f"\nSérie: {slug} — {len(caps)} capítulos encontrados (no HTML estático):")
    for c in caps:
        print(f"  {BASE}/manhwa/{slug}/{c}/")
    return caps


def collect_page_urls(chapter_url):
    """Extrai as URLs das páginas (strips) do capítulo, em ordem."""
    html = http_get(chapter_url, referer=chapter_url)
    seen = []
    for m in PAGE_IMG_RE.finditer(html):
        u = m.group(1).strip()
        if u not in seen:
            seen.append(u)
    return seen


def download_strip(url, out_path, referer):
    try:
        data = http_get(url, referer=referer, binary=True)
    except Exception as e:
        log(f"  download falhou: {url[-50:]} — {e}")
        return False
    if len(data) < MIN_BYTES:
        log(f"  ignorado (muito pequeno, {len(data)}B): {url[-50:]}")
        return False
    tmp = out_path.with_suffix(".dl")
    tmp.write_bytes(data)
    # Converter pra jpg (panel-splitter espera jpg como no hiper-fetcher)
    try:
        img = Image.open(tmp).convert("RGB")
        img.save(out_path, "JPEG", quality=92)
        tmp.unlink()
        return True
    except Exception as e:
        log(f"  conversão falhou: {e}")
        tmp.unlink(missing_ok=True)
        return False


def fetch_chapter(chapter_url, slug, max_panels=50):
    out_dir = CACHE_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    log(f"Capítulo: {chapter_url}")
    log(f"Destino:  {out_dir}")

    urls = collect_page_urls(chapter_url)
    if not urls:
        log("ERRO: nenhuma página encontrada no HTML do capítulo.")
        log("      (o reader pode ter mudado de estrutura — checar PAGE_IMG_RE)")
        return False
    log(f"{len(urls)} páginas detectadas no reader.")
    urls = urls[:max_panels]

    ok = 0
    for i, u in enumerate(urls):
        out_path = out_dir / f"panel_{i:03d}.jpg"
        if download_strip(u, out_path, referer=chapter_url):
            ok += 1
            log(f"  ✓ panel_{i:03d}.jpg ({u.split('/')[-1]})")
        time.sleep(0.3)

    meta = {
        "url": chapter_url,
        "slug": slug,
        "source": "tiamanhwa.com",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "images_count": ok,
    }
    (out_dir / "_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    log(f"Concluído: {ok}/{len(urls)} páginas salvas em {out_dir}")
    return ok > 0


def main():
    ap = argparse.ArgumentParser(description="Scraper tiamanhwa.com")
    ap.add_argument("--url", help="URL do capítulo")
    ap.add_argument("--slug", help="Slug de pasta no cache")
    ap.add_argument("--discover", metavar="MANHWA_URL",
                    help="Lista capítulos de uma série")
    ap.add_argument("--max-panels", type=int, default=50)
    args = ap.parse_args()

    if args.discover:
        discover(args.discover)
        return
    if not args.url or not args.slug:
        ap.error("--url e --slug são obrigatórios (ou use --discover)")
    ok = fetch_chapter(args.url, args.slug, max_panels=args.max_panels)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
