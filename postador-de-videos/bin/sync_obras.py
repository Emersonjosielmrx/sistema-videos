#!/usr/bin/env python3
"""sync_obras.py — Sincroniza painéis de TODAS as obras. KEYLESS (scrape+split, ZERO IA).

O que faz, sozinho e idempotente:
  1. Le workspace/obras.json (registro de obras).
  2. Pra cada obra habilitada, descobre quais caps EXISTEM de verdade (conta
     .reading-content img na pagina ANTES de baixar — placeholder/buraco = 0 imgs).
  3. Baixa + corta so o que falta (pula cap ja cortado).
  4. Roda QC em cada cap cortado: pinta de vermelho contagens suspeitas, paineis
     em branco, paineis gigantes (corte que nao pegou o gap).
  5. Escreve relatorio em logs/sync_obras_report.json + log legivel.

Uso:
  python bin/sync_obras.py                 # todas as obras habilitadas
  python bin/sync_obras.py perverts-daily-life   # so uma
  python bin/sync_obras.py --qc-only       # so revalida cortes existentes, sem baixar
  python bin/sync_obras.py --probe-only     # so descobre o que existe, sem baixar

NAO toca Gemini. Seguro rodar em paralelo a render (pula o que ja existe).
"""
import argparse
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "bin")

PROJECT = Path(__file__).resolve().parent.parent
PYEXE = r"D:\hipercool-videos\venv\Scripts\python.exe"
PANELS = PROJECT / "workspace" / "panels"
CACHE = PROJECT / "workspace" / "cache"
OBRAS_JSON = PROJECT / "workspace" / "obras.json"
LOG = PROJECT / "logs" / "sync_obras.log"
REPORT = PROJECT / "logs" / "sync_obras_report.json"
MIN_REAL_IMGS = 6          # menos que isso na pagina = placeholder/buraco
MIN_STRIP_HEIGHT = 1000    # strip de manhwa de verdade e alto
LOG.parent.mkdir(exist_ok=True)

# fetcher (hifen no nome -> importlib)
_spec = importlib.util.spec_from_file_location("hf", str(PROJECT / "bin" / "hiper-fetcher.py"))
hf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hf)


def w(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_obras():
    data = json.loads(OBRAS_JSON.read_text(encoding="utf-8"))
    return data["site_base"], [o for o in data["obras"] if o.get("enabled", True)]


def probe_chapter_imgs(page, url):
    """Quantas imagens de CONTEUDO a pagina tem (sem baixar). 0 = placeholder/buraco."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2500)
        for sel in (".reading-content img", ".chapter-images img", ".reader-area img"):
            n = page.eval_on_selector_all(sel, "els=>els.length")
            if n:
                return n
        return 0
    except Exception:
        return -1  # erro de rede


def cut_count(slug):
    d = PANELS / slug
    return len(list(d.glob("*.jpg"))) if d.exists() else 0


def has_narration(slug):
    """True se ja existe narration_cache pra esse cap (qualquer variante de N painéis).
    Se tem narração, NAO se pode apagar/renumerar painel (desalinha fala×painel)."""
    ndir = PROJECT / "workspace" / "narration_cache"
    return any(ndir.glob(f"{slug}_*panels.json")) or any(ndir.glob(f"{slug}_sk*panels.json"))


def is_pure_blank(path):
    """Painel-lixo: cor quase uniforme (branco ou preto puro). Painel real, mesmo
    de cena escura/fundo branco, tem traço/balão → stddev mais alto."""
    from PIL import Image, ImageStat
    try:
        im = Image.open(path).convert("L")
        st = ImageStat.Stat(im)
        return st.stddev[0] < 3.0 and (st.mean[0] > 250 or st.mean[0] < 5)
    except Exception:
        return False


def clean_blanks(slug):
    """Remove painéis-lixo e RENUMERA sequencial. SO chamar em cap SEM narração."""
    if has_narration(slug):
        return 0  # trava: nunca renumera cap com narração já gerada
    d = PANELS / slug
    files = sorted(d.glob("*.jpg"))
    junk = [f for f in files if is_pure_blank(f)]
    if not junk:
        return 0
    for f in junk:
        f.unlink()
    # renumera o que sobrou pra panel_000.. contiguo
    keep = sorted(d.glob("*.jpg"))
    for i, f in enumerate(keep):
        target = d / f"panel_{i:03d}.jpg"
        if f != target:
            f.rename(target)
    return len(junk)


def qc_chapter(slug):
    """Valida os cortes de UM cap. Retorna dict com problemas encontrados."""
    from PIL import Image, ImageStat
    d = PANELS / slug
    files = sorted(d.glob("*.jpg"))
    issues = {"slug": slug, "n_panels": len(files), "blank": [], "giant": [],
              "tiny": [], "ok": True}
    if not files:
        issues["ok"] = False
        issues["error"] = "sem painéis"
        return issues
    for f in files:
        try:
            im = Image.open(f)
            wd, ht = im.size
            g = im.convert("L")
            stat = ImageStat.Stat(g)
            mean, std = stat.mean[0], stat.stddev[0]
            # Branco/preto de VERDADE = cor uniforme (stddev baixo). Painel real com
            # fundo branco tem mean alto MAS stddev>15 (balões/traço). So flagueia
            # quando e quase uniforme: sem conteúdo.
            if (mean > 248 or mean < 6) and std < 12:
                issues["blank"].append(f.name)
            if ht > 4500:                        # corte nao pegou o gap (painel gigante)
                issues["giant"].append(f"{f.name}({ht}px)")
            if ht < 200:                         # sobra/lixo
                issues["tiny"].append(f"{f.name}({ht}px)")
        except Exception as e:
            issues["blank"].append(f"{f.name}(ERR)")
    issues["ok"] = not (issues["blank"] or issues["giant"])
    return issues


def sync_obra(obra, site_base, probe_only=False, qc_only=False):
    sl, ss = obra["slug_local"], obra["slug_site"]
    max_cap = obra.get("max_cap", 50)
    w(f"--- obra {sl} (site={ss}, max={max_cap}) ---")
    result = {"slug": sl, "baixados": [], "ja_tinha": [], "vazios": [],
              "erros": [], "qc": []}

    # QC-only: nao abre browser nem baixa.
    if qc_only:
        for c in range(1, max_cap + 1):
            slug = f"{sl}-cap{c:02d}"
            if cut_count(slug) > MIN_REAL_IMGS:
                result["ja_tinha"].append(c)
                result["qc"].append(qc_chapter(slug))
        return result

    # FASE 1: probe (meu browser). Coleta quais caps faltam baixar e existem no site.
    # Importante: fecho ESTE browser antes da fase 2, porque fetch_chapter abre o
    # proprio sync_playwright e nao se pode aninhar duas instancias sync.
    to_download = []  # (cap, n_imgs)
    from playwright.sync_api import sync_playwright
    st = PROJECT / "secrets" / "playwright_state.json"
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(storage_state=str(st)) if st.exists() else b.new_context()
        page = ctx.new_page()
        for c in range(1, max_cap + 1):
            slug = f"{sl}-cap{c:02d}"
            if cut_count(slug) > MIN_REAL_IMGS:
                result["ja_tinha"].append(c)
                continue
            url = f"{site_base}/{ss}/capitulo-{c}/"
            n_imgs = probe_chapter_imgs(page, url)
            if n_imgs == -1:
                w(f"  cap{c:02d}: ERRO de rede no probe")
                result["erros"].append(c)
                continue
            if n_imgs < MIN_REAL_IMGS:
                result["vazios"].append(c)
                continue
            if probe_only:
                w(f"  cap{c:02d}: {n_imgs} imgs de conteúdo (existe, não baixado)")
                continue
            to_download.append((c, n_imgs))
        page.close()
        b.close()

    if probe_only:
        return result

    # FASE 2: baixa + corta (fetch_chapter abre seu proprio Playwright — browser da fase 1 ja fechado).
    for c, n_imgs in to_download:
        slug = f"{sl}-cap{c:02d}"
        url = f"{site_base}/{ss}/capitulo-{c}/"
        # retry com backoff: erro transiente de rede ("Connection closed") nao pode
        # derrubar a fila inteira. fetch_chapter tem cache, entao re-tentar e barato.
        out = None
        for attempt in range(3):
            try:
                out = hf.fetch_chapter(url, slug, headed=False)
                break
            except Exception as e:
                if attempt < 2:
                    w(f"  cap{c:02d}: falha scrape (tent {attempt+1}/3: {str(e)[:40]}) — retry em {(attempt+1)*10}s")
                    time.sleep((attempt + 1) * 10)
                else:
                    w(f"  cap{c:02d}: ERRO scrape após 3 tentativas ({str(e)[:50]})")
                    result["erros"].append(c)
        if out is None:
            continue
        pout = PANELS / slug
        subprocess.run([PYEXE, "bin/panel-splitter.py", "--split",
                        "--input", str(out) + "/", "--out", str(pout) + "/"],
                       capture_output=True, text=True)
        # limpa painéis-lixo (branco/preto puro) e renumera — seguro só aqui,
        # pois o cap acabou de ser cortado e ainda nao tem narração.
        removed = clean_blanks(slug)
        qc = qc_chapter(slug)
        result["qc"].append(qc)
        extra = f"  (−{removed} lixo)" if removed else ""
        flag = "" if qc["ok"] else f"  ⚠ QC: blank={len(qc['blank'])} giant={len(qc['giant'])}"
        w(f"  cap{c:02d}: {n_imgs} strips → {qc['n_panels']} painéis{extra}{flag}")
        result["baixados"].append(c)

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("obra", nargs="?", default=None, help="slug_local de uma obra (default: todas)")
    ap.add_argument("--probe-only", action="store_true", help="só descobre o que existe")
    ap.add_argument("--qc-only", action="store_true", help="só revalida cortes existentes")
    args = ap.parse_args()

    site_base, obras = load_obras()
    if args.obra:
        obras = [o for o in obras if o["slug_local"] == args.obra]
        if not obras:
            print(f"obra '{args.obra}' não está em obras.json (ou desabilitada)")
            sys.exit(1)

    w(f"=== SYNC início — {len(obras)} obra(s) "
      f"{'[PROBE]' if args.probe_only else '[QC]' if args.qc_only else '[FULL]'} ===")
    all_results = []
    for o in obras:
        all_results.append(sync_obra(o, site_base, args.probe_only, args.qc_only))

    REPORT.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")

    # resumo
    w("=== RESUMO ===")
    for r in all_results:
        bad = [q["slug"] for q in r["qc"] if not q.get("ok", True)]
        w(f"{r['slug']}: +{len(r['baixados'])} novos, {len(r['ja_tinha'])} já tinha, "
          f"{len(r['vazios'])} vazios, {len(r['erros'])} erros"
          + (f" | ⚠ REVISAR: {bad}" if bad else " | QC ok"))
    w(f"Relatório: {REPORT}")


if __name__ == "__main__":
    main()
