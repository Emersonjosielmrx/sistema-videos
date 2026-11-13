r"""youtube_criar_canal.py — cria o canal do YouTube de UMA conta (dona 11/11: "crie os canais das 4 contas novas").

Abre o Chrome do cofre da conta pelo MESMO IP do Kaggle (youtube_web_poster._proxy_da_conta_kaggle — a conta só
existe num IP), vai em /create_channel, preenche nome e @ e clica em "Criar canal". Lê o channel_id (UC...) da página
do canal e grava em config\canais_novos_criados.json. Prints em logs\criar_canal\.

    python bin\youtube_criar_canal.py <email> "<Nome do canal>" <handle_sem_arroba> [--ver]
--ver = só abre e tira print (não cria).
"""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
import youtube_web_poster as y  # noqa: E402

PRINTS = BIN.parent / "logs" / "criar_canal"
REG = BIN.parent / "config" / "canais_novos_criados.json"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    email, nome, handle = sys.argv[1], sys.argv[2], sys.argv[3].lstrip("@")
    ver = "--ver" in sys.argv
    PRINTS.mkdir(parents=True, exist_ok=True)
    extra = y._proxy_da_conta_kaggle(email)
    porta, proc = cofre.abrir(email, "about:blank", False, extra=extra)
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            pg = br.contexts[0].new_page()
            if extra:
                pg.goto("https://api.ipify.org", timeout=60000)
                print(f"IP: {pg.inner_text('body').strip()}", flush=True)
            pg.goto("https://www.youtube.com/create_channel", timeout=120000, wait_until="domcontentloaded")
            # 13/11: 9 s fixos não bastavam pelo proxy (a 2035 abriu o diálogo no --ver e não na 2ª vez: print em branco)
            try:
                pg.locator("tp-yt-paper-dialog, ytd-channel-creation-dialog-renderer, [role=dialog]").filter(
                    has_text=re.compile(r"Identificador|Handle", re.I)).first.wait_for(state="visible", timeout=60000)
            except Exception:  # noqa: BLE001 — sem diálogo: o teste abaixo decide
                pass
            pg.wait_for_timeout(2000)
            pg.screenshot(path=str(PRINTS / f"{handle}_1_form.png"))
            # 12/11: o form é um DIÁLOGO por cima da página — "input:visible" pegava a caixa de pesquisa do YouTube
            # (atrás do diálogo) e o clique batia no backdrop. Só os campos de dentro do diálogo.
            dlg = pg.locator("tp-yt-paper-dialog, ytd-channel-creation-dialog-renderer, [role=dialog]").filter(
                has_text=re.compile(r"Identificador|Handle", re.I)).first
            caixas = dlg.locator("input:visible")
            print(f"campos no diálogo: {caixas.count()}", flush=True)
            if caixas.count() < 2:
                print("formulário de criar canal não apareceu (a conta já tem canal?) — veja o print", flush=True)
                return
            if ver:
                return
            nome_in, handle_in = caixas.nth(0), caixas.nth(1)
            nome_in.click()
            nome_in.fill(nome)
            pg.wait_for_timeout(1500)
            handle_in.click()
            handle_in.fill("")
            handle_in.type(handle, delay=60)
            pg.wait_for_timeout(5000)
            corpo = pg.inner_text("body")
            pg.screenshot(path=str(PRINTS / f"{handle}_2_preenchido.png"))
            if re.search(r"não está disponível|indisponível|not available|já está em uso", corpo, re.I):
                print(f"@{handle} indisponível — parei (não criei)", flush=True)
                return
            dlg.get_by_role("button", name=re.compile(r"^(Criar canal|Create channel)$", re.I)).click(timeout=20000)
            pg.wait_for_timeout(15000)
            pg.goto("https://www.youtube.com/account_advanced", timeout=120000, wait_until="domcontentloaded")
            pg.wait_for_timeout(6000)
            # 12/11: o regex solto no HTML pegou outro texto (UC0zQX... = base64) — lê o campo "ID do canal" da tela
            uc = None
            try:
                campo = pg.get_by_text(re.compile(r"^(ID do canal|Channel ID)$")).first.locator("xpath=following::*[1]")
                uc = re.search(r"(UC[\w-]{22})", campo.inner_text(timeout=8000))
            except Exception:  # noqa: BLE001
                pass
            if not uc:
                uc = re.search(r"(UC[\w-]{22})", pg.inner_text("body"))
            pg.screenshot(path=str(PRINTS / f"{handle}_3_criado.png"))
            cid = uc.group(1) if uc else None
            print(f"CRIADO: {nome} @{handle} channel_id={cid}", flush=True)
            reg = json.loads(REG.read_text("utf-8")) if REG.exists() else {}
            reg[email] = {"nome": nome, "handle": "@" + handle, "channel_id": cid,
                          "criado": datetime.now().isoformat(timespec="minutes"),
                          "ip": "mesmo do Kaggle" if extra else "casa"}
            REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    finally:
        cofre.fechar(proc, None, email)


if __name__ == "__main__":
    main()
