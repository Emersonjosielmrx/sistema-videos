"""Abre a pergunta 'Can I top up by credit card?' do FAQ do AccsMarket e lê a resposta.
Uso: python accs_cartao.py"""
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=False, args=["--window-position=-2000,0", "--disable-blink-features=AutomationControlled"])
    pg = br.new_context(locale="en-US", viewport={"width": 1280, "height": 1800}).new_page()
    pg.goto("https://www.accsmarket.com/en/faq", wait_until="domcontentloaded", timeout=45000); time.sleep(6)
    for q in ("Can I top up by credit card?", "I paid for an order but the balance was not updated"):
        try:
            pg.get_by_text(q).first.click(); time.sleep(3)
        except Exception as e:
            print("ERRO clique", q, str(e)[:100])
    tx = pg.inner_text("body")
    for q in ("Can I top up by credit card?", "I paid for an order"):
        i = tx.find(q)
        print("=====", q); print(tx[i:i+1500] if i >= 0 else "não achei")
    br.close()
