#!/usr/bin/env python3
"""Diagnostico rapido: conecta no Chrome e tira screenshot do estado atual."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright

port = int(sys.argv[1]) if len(sys.argv) > 1 else 9250

with sync_playwright() as pw:
    browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
    ctx = browser.contexts[0] if browser.contexts else None
    if not ctx:
        print(f"Nenhum contexto no Chrome porta {port}")
        sys.exit(1)
    pages = ctx.pages
    print(f"Chrome porta {port}: {len(pages)} abas")
    for i, p in enumerate(pages):
        url = p.url
        title = p.title()
        print(f"  Aba {i}: {url[:120]} | titulo: {title[:60]}")
        if "flow" in url.lower() or "labs.google" in url.lower():
            # Tirar screenshot
            out = f"logs/diag_flow_{port}_{i}.png"
            p.screenshot(path=out)
            print(f"  Screenshot: {out}")
            # Listar elementos interativos
            elems = p.evaluate("""() => {
                const results = [];
                for (const el of document.querySelectorAll('button, [role=button], a, textarea, input, [contenteditable]')) {
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden') continue;
                    const txt = (el.innerText || '').trim().substring(0, 80);
                    const tag = el.tagName;
                    const href = (el.getAttribute('href') || '').substring(0, 80);
                    const ph = (el.getAttribute('placeholder') || '').substring(0, 60);
                    const ce = el.getAttribute('contenteditable') || '';
                    results.push(`${tag}|${txt}|href=${href}|ph=${ph}|ce=${ce}`);
                }
                return results;
            }""")
            print(f"  {len(elems)} elementos interativos:")
            for e in elems[:30]:
                print(f"    {e}")
            # Body text excerpt
            body = (p.evaluate("() => document.body.innerText") or "")[:500]
            print(f"  Body text:\n{body}")
    browser.close()
