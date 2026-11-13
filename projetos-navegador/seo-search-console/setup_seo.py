"""
SEO Search Console — automação COMPLETA do Google Search Console.

Operações disponíveis:
  - verificar_acesso(conta)             → lista propriedades cadastradas
  - adicionar_propriedade(conta, url)   → adiciona site/domínio
  - relatorio_performance(conta, url)   → cliques/impressões/CTR/posição
  - inspecionar_url(conta, url_pagina)  → status de indexação de uma URL
  - enviar_sitemap(conta, url, sitemap) → submete sitemap
  - gerar_sitemap(urls, saida)          → gera sitemap.xml local (offline)
  - top_keywords(conta, url)            → consultas que mais trazem tráfego
  - cobertura_indice(conta, url)        → páginas indexadas vs erros

CLI:
  python setup_seo.py                                   → dry run
  python setup_seo.py --live
  python setup_seo.py --acao adicionar --conta X --url https://site.com
  python setup_seo.py --acao performance --conta X --url https://site.com
  python setup_seo.py --acao sitemap_local --urls url1,url2 --saida sitemap.xml
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

SEO_DIR = Path(__file__).resolve().parent
STATUS_FILE = SEO_DIR / "seo_status.json"
GSC_URL = "https://search.google.com/search-console"


def _sessao_expirada(page):
    return "accounts.google.com" in page.url


def verificar_acesso(conta):
    """Lista propriedades cadastradas no Search Console."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(GSC_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"conta": conta, "status": "sessao_expirada"}

            propriedades = []
            for el in page.query_selector_all('[class*="property"], a[href*="resource_id"], [role="option"]')[:15]:
                t = el.inner_text().strip()
                if t and len(t) < 120:
                    propriedades.append(t)
            save_session(context, conta)
            return {"conta": conta, "status": "ok", "propriedades": list(dict.fromkeys(propriedades))}
    except Exception as e:
        return {"conta": conta, "status": "erro", "erro": str(e)}


def adicionar_propriedade(conta, url):
    """Adiciona um site/domínio ao Search Console."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{GSC_URL}/welcome", timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            url_input = page.query_selector('input[type="url"], input[type="text"]')
            if url_input:
                url_input.fill(url)
                time.sleep(1)
                cont = page.query_selector('button:has-text("Continue"), button:has-text("Continuar")')
                if cont:
                    cont.click()
                    time.sleep(6)
                    save_session(context, conta)
                    return {"sucesso": True, "url": url, "nota": "pode exigir verificação DNS/HTML"}
            return {"sucesso": False, "erro": "input não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def relatorio_performance(conta, url_propriedade):
    """Pega cliques/impressões/CTR/posição da propriedade."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{GSC_URL}/performance/search-analytics?resource_id={url_propriedade}",
                      timeout=45000, wait_until="domcontentloaded")
            time.sleep(8)
            if _sessao_expirada(page):
                return {"conta": conta, "erro": "sessao_expirada"}

            metricas = {}
            for card in page.query_selector_all('[class*="metric"], [role="tab"]'):
                t = card.inner_text().strip()
                if t and any(k in t.lower() for k in ["click", "clique", "impress", "ctr", "position", "posição"]):
                    metricas[t.split("\n")[0]] = "\n".join(t.split("\n")[1:])[:60]
            save_session(context, conta)
            return {"conta": conta, "propriedade": url_propriedade, "metricas": metricas}
    except Exception as e:
        return {"conta": conta, "erro": str(e)}


def inspecionar_url(conta, url_pagina):
    """Status de indexação de uma URL específica."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(GSC_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"erro": "sessao_expirada"}

            inspect = page.query_selector('input[aria-label*="Inspect"], input[placeholder*="Inspecionar"], input[type="search"]')
            if inspect:
                inspect.fill(url_pagina)
                page.keyboard.press("Enter")
                time.sleep(8)
                resultado = ""
                res_el = page.query_selector('[class*="inspection-result"], [class*="coverage"], [role="status"]')
                if res_el:
                    resultado = res_el.inner_text().strip()[:300]
                save_session(context, conta)
                return {"conta": conta, "url": url_pagina, "resultado": resultado or "sem status legível"}
            return {"erro": "campo de inspeção não encontrado"}
    except Exception as e:
        return {"erro": str(e)}


def enviar_sitemap(conta, url_propriedade, url_sitemap):
    """Submete um sitemap ao Search Console."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{GSC_URL}/sitemaps?resource_id={url_propriedade}",
                      timeout=45000, wait_until="domcontentloaded")
            time.sleep(7)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            sm_input = page.query_selector('input[aria-label*="sitemap"], input[type="text"]')
            if sm_input:
                sm_input.fill(url_sitemap)
                time.sleep(1)
                submit = page.query_selector('button:has-text("Submit"), button:has-text("Enviar")')
                if submit:
                    submit.click()
                    time.sleep(4)
                    save_session(context, conta)
                    return {"sucesso": True, "sitemap": url_sitemap}
            return {"sucesso": False, "erro": "campo de sitemap não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def gerar_sitemap(urls, saida="sitemap.xml"):
    """Gera um sitemap.xml local (offline, não precisa de sessão)."""
    if isinstance(urls, str):
        urls = [u.strip() for u in urls.split(",") if u.strip()]
    agora = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        linhas.append(f"  <url><loc>{u}</loc><lastmod>{agora}</lastmod><changefreq>daily</changefreq></url>")
    linhas.append("</urlset>")
    caminho = SEO_DIR / saida
    caminho.write_text("\n".join(linhas), encoding="utf-8")
    return {"sucesso": True, "arquivo": str(caminho), "urls": len(urls)}


def top_keywords(conta, url_propriedade, max_kw=20):
    """Consultas que mais trazem tráfego."""
    r = relatorio_performance(conta, url_propriedade)
    if "erro" in r:
        return r
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{GSC_URL}/performance/search-analytics?resource_id={url_propriedade}",
                      timeout=45000, wait_until="domcontentloaded")
            time.sleep(8)
            if _sessao_expirada(page):
                return {"erro": "sessao_expirada"}
            keywords = []
            for row in page.query_selector_all('[role="row"], tr')[:max_kw + 5]:
                t = row.inner_text().strip().split("\n")[0]
                if t and len(t) < 100 and t.lower() not in ("query", "consulta"):
                    keywords.append(t)
            save_session(context, conta)
            return {"conta": conta, "keywords": keywords[:max_kw]}
    except Exception as e:
        return {"erro": str(e)}


def cobertura_indice(conta, url_propriedade):
    """Páginas indexadas vs com erro."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{GSC_URL}/index/coverage?resource_id={url_propriedade}",
                      timeout=45000, wait_until="domcontentloaded")
            time.sleep(8)
            if _sessao_expirada(page):
                return {"erro": "sessao_expirada"}
            dados = {}
            for card in page.query_selector_all('[class*="coverage"], [class*="status-card"]'):
                t = card.inner_text().strip()
                if t:
                    partes = t.split("\n")
                    if len(partes) >= 2:
                        dados[partes[0]] = partes[1]
            save_session(context, conta)
            return {"conta": conta, "cobertura": dados}
    except Exception as e:
        return {"erro": str(e)}


FUNCIONALIDADES = {
    "verificar":    {"func": verificar_acesso,      "desc": "Lista propriedades cadastradas"},
    "adicionar":    {"func": adicionar_propriedade, "desc": "Adiciona site/domínio"},
    "performance":  {"func": relatorio_performance, "desc": "Cliques/impressões/CTR/posição"},
    "inspecionar":  {"func": inspecionar_url,       "desc": "Status de indexação de URL"},
    "sitemap":      {"func": enviar_sitemap,        "desc": "Submete sitemap"},
    "sitemap_local":{"func": gerar_sitemap,         "desc": "Gera sitemap.xml local (offline)"},
    "keywords":     {"func": top_keywords,          "desc": "Top consultas de busca"},
    "cobertura":    {"func": cobertura_indice,      "desc": "Páginas indexadas vs erros"},
}


def setup_seo(dry_run=True):
    print(f"[SEO Search Console] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Funcionalidades: {', '.join(FUNCIONALIDADES.keys())}")
    status = {"contas": {}, "ultima_execucao": datetime.now(timezone.utc).isoformat()}
    for conta in ACCOUNTS:
        if dry_run:
            print(f"  [DRY RUN] verificaria Search Console: {conta}")
            status["contas"][conta] = {"dry_run": True}
        else:
            print(f"  {conta}...", end=" ", flush=True)
            r = verificar_acesso(conta)
            print(r["status"])
            status["contas"][conta] = r
    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nStatus salvo em {STATUS_FILE}")
    return status


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--acao" in args:
        acao = args[args.index("--acao") + 1]
        conta = args[args.index("--conta") + 1] if "--conta" in args else "fabrica"
        url = args[args.index("--url") + 1] if "--url" in args else None
        if acao == "verificar":
            r = verificar_acesso(conta)
        elif acao == "adicionar":
            r = adicionar_propriedade(conta, url)
        elif acao == "performance":
            r = relatorio_performance(conta, url)
        elif acao == "inspecionar":
            r = inspecionar_url(conta, url)
        elif acao == "sitemap":
            r = enviar_sitemap(conta, url, args[args.index("--sitemap") + 1])
        elif acao == "sitemap_local":
            urls = args[args.index("--urls") + 1] if "--urls" in args else ""
            saida = args[args.index("--saida") + 1] if "--saida" in args else "sitemap.xml"
            r = gerar_sitemap(urls, saida)
        elif acao == "keywords":
            r = top_keywords(conta, url)
        elif acao == "cobertura":
            r = cobertura_indice(conta, url)
        else:
            r = {"erro": f"ação desconhecida: {acao}"}
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        dry = "--live" not in args
        if dry:
            print("Modo DRY RUN\n")
        setup_seo(dry_run=dry)
