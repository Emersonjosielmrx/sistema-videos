r"""
Chat Hub Agentes: configura o Google Chat API em cada conta do cofre (sem canal YouTube)
para servir de canal de comunicação entre agentes.

Ativa a Google Chat API e cria um webhook em cada Space, permitindo que agentes conversem
entre si via Google Chat (cada conta = 1 espaço = 1 agente).

Passos:
  1. Ativar Chat API (console.cloud.google.com/apis/library/chat.googleapis.com)
  2. Abrir Google Chat (chat.google.com)
  3. Criar um Space (ou usar existente)
  4. Configurar webhook no Space -> Manage webhooks -> Add webhook

O módulo SÓ roda em contas SEM canal YouTube.

CLI:
  python chat_hub_agentes.py criar <conta>
  python chat_hub_agentes.py criar_massa --sem-canal
  python chat_hub_agentes.py criar_massa <conta1> <conta2> ...
  python chat_hub_agentes.py listar
"""
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre

DIR = Path(__file__).resolve().parent
REGISTRO = DIR / "chat_hub_contas.json"
CHAT_URL = "https://chat.google.com/"
CHAT_API_URL = "https://console.cloud.google.com/apis/library/chat.googleapis.com"
SPACE_NAME = "agentes-hub"


def _ler(arq, padrao):
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else padrao


def _gravar(arq, dados, indent=2):
    tmp = arq.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(arq)


def _print(page, motivo):
    p = DIR / f"_debug_chathub_{datetime.now():%H%M%S}_{motivo}.png"
    try:
        page.screenshot(path=str(p))
    except Exception:
        pass
    return str(p)


def contas_sem_canal():
    # msenergypara é de cliente (MS Energy): fora sem o dono decidir
    return [info.get("apelido") or email.split("@")[0]
            for email, info in cofre._ler()["contas"].items()
            if info.get("google") == "vivo" and not info.get("usos", {}).get("youtube")
            and email != "msenergypara@gmail.com"]


def _selecionar_conta(page, email):
    if "accounts.google.com" not in page.url:
        return
    if "accountchooser" in page.url or "selectaccount" in page.url.lower():
        esc = page.get_by_text(email, exact=True)
        try:
            if esc.count() and esc.first.is_visible():
                esc.first.click()
                page.wait_for_timeout(3000)
        except Exception:
            pass
    for txt in ("Continuar", "Continue", "Permitir", "Allow"):
        b = page.get_by_role("button", name=txt, exact=True)
        try:
            if b.count() and b.first.is_visible():
                b.first.click()
                page.wait_for_timeout(3000)
                break
        except Exception:
            pass


def _aceitar_termos(page):
    for txt in ("Agree", "Aceitar", "Accept", "I agree", "Concordo", "Got it", "Entendi",
                "Continue", "Continuar"):
        btn = page.get_by_role("button", name=txt)
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.click(timeout=5000)
                page.wait_for_timeout(2000)
        except Exception:
            pass


def _ativar_chat_api(page, email):
    page.goto(CHAT_API_URL, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)

    if "accounts.google.com" in page.url:
        _selecionar_conta(page, email)
        page.wait_for_timeout(5000)

    _aceitar_termos(page)

    corpo = page.inner_text("body")
    if "API enabled" in corpo or "API ativada" in corpo:
        return {"status": "ja_ativa"}

    for txt in ("Enable", "Ativar", "Enable API", "Ativar API"):
        btn = page.get_by_role("button", name=txt)
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.click(timeout=15000)
                page.wait_for_timeout(10000)
                return {"status": "ativada"}
        except Exception:
            pass

    return {"status": "nao_conseguiu_ativar"}


def _abrir_chat(page, email):
    page.goto(CHAT_URL, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)

    if "accounts.google.com" in page.url:
        _selecionar_conta(page, email)
        page.wait_for_timeout(5000)

    _aceitar_termos(page)

    if "chat.google.com" not in page.url and "mail.google.com" not in page.url:
        return {"status": "nao_abriu_chat", "url": page.url}

    return {"status": "chat_aberto"}


def _criar_space(page):
    for txt in ("Create or find a space", "Criar ou encontrar um espaço", "New space", "Novo espaço",
                "Create space", "Criar espaço"):
        btn = page.locator(f'button:has-text("{txt}"), [aria-label*="{txt}"]').first
        try:
            if btn.count() and btn.is_visible():
                btn.click(timeout=10000)
                page.wait_for_timeout(3000)
                break
        except Exception:
            pass

    for txt in ("Create a space", "Criar um espaço", "Create space", "Criar espaço"):
        btn = page.locator(f'button:has-text("{txt}"), [role="menuitem"]:has-text("{txt}")').first
        try:
            if btn.count() and btn.is_visible():
                btn.click(timeout=10000)
                page.wait_for_timeout(3000)
                break
        except Exception:
            pass

    nome_input = page.locator('input[aria-label*="Space name"], input[aria-label*="Nome do espaço"], '
                              'input[placeholder*="name"], input[placeholder*="nome"]').first
    try:
        if nome_input.count() and nome_input.is_visible():
            nome_input.fill(SPACE_NAME)
            page.wait_for_timeout(1000)
    except Exception:
        pass

    for txt in ("Create", "Criar"):
        btn = page.get_by_role("button", name=txt, exact=True)
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.click(timeout=10000)
                page.wait_for_timeout(5000)
                return {"status": "space_criado", "nome": SPACE_NAME}
        except Exception:
            pass

    return {"status": "space_nao_criado"}


def _configurar_webhook(page):
    for txt in ("Manage webhooks", "Gerenciar webhooks", "Apps & integrations",
                "Apps e integrações", "Manage apps", "Gerenciar apps"):
        btn = page.locator(f'button:has-text("{txt}"), [role="menuitem"]:has-text("{txt}"), '
                           f'a:has-text("{txt}")').first
        try:
            if btn.count() and btn.is_visible():
                btn.click(timeout=10000)
                page.wait_for_timeout(3000)
                break
        except Exception:
            pass

    for txt in ("Add webhooks", "Adicionar webhooks", "Incoming Webhooks", "Add webhook"):
        btn = page.locator(f'button:has-text("{txt}"), a:has-text("{txt}")').first
        try:
            if btn.count() and btn.is_visible():
                btn.click(timeout=10000)
                page.wait_for_timeout(3000)

                nome_input = page.locator('input[aria-label*="Name"], input[aria-label*="Nome"]').first
                if nome_input.count() and nome_input.is_visible():
                    nome_input.fill("agente-bot")
                    page.wait_for_timeout(1000)

                for txt2 in ("Save", "Salvar"):
                    save = page.get_by_role("button", name=txt2, exact=True)
                    if save.count() and save.first.is_visible():
                        save.first.click(timeout=10000)
                        page.wait_for_timeout(3000)
                        break

                webhook_url = None
                urls = re.findall(r"https://chat\.googleapis\.com/v1/spaces/[^\s\"']+", page.inner_text("body"))
                if urls:
                    webhook_url = urls[0]

                return {"status": "webhook_criado" if webhook_url else "webhook_sem_url",
                        "webhook_url": webhook_url}
        except Exception:
            pass

    return {"status": "webhook_nao_configurado"}


def criar(conta, visivel=True):
    from playwright.sync_api import sync_playwright

    email, info = cofre.conta(conta)
    if info.get("google") != "vivo":
        return {"sucesso": False, "conta": conta, "erro": "google_morto_no_cofre"}

    reg = _ler(REGISTRO, {})
    anterior = reg.get(conta)
    if anterior and anterior.get("completo"):
        return {"sucesso": True, "conta": conta, "nota": "já configurado"}

    porta, proc = cofre.abrir(conta, url="about:blank", visivel=visivel)

    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        page = br.contexts[0].new_page()
        try:
            print(f"  Ativando Chat API...", flush=True)
            api_r = _ativar_chat_api(page, email)
            print(f"  Chat API: {api_r['status']}", flush=True)

            print(f"  Abrindo Google Chat...", flush=True)
            chat_r = _abrir_chat(page, email)
            print(f"  Chat: {chat_r['status']}", flush=True)

            space_r = {"status": "nao_tentado"}
            webhook_r = {"status": "nao_tentado"}

            if chat_r["status"] == "chat_aberto":
                print(f"  Criando Space '{SPACE_NAME}'...", flush=True)
                space_r = _criar_space(page)
                print(f"  Space: {space_r['status']}", flush=True)

                if space_r["status"] == "space_criado":
                    print(f"  Configurando webhook...", flush=True)
                    webhook_r = _configurar_webhook(page)
                    print(f"  Webhook: {webhook_r['status']}", flush=True)

            completo = (api_r["status"] in ("ativada", "ja_ativa") and
                        chat_r["status"] == "chat_aberto")

            reg[conta] = {
                "email": email,
                "chat_api": api_r,
                "chat": chat_r,
                "space": space_r,
                "webhook": webhook_r,
                "webhook_url": webhook_r.get("webhook_url"),
                "completo": completo,
                "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            _gravar(REGISTRO, reg)

            _print(page, f"{conta}_final")
            return {"sucesso": completo, "conta": conta, "webhook_url": webhook_r.get("webhook_url")}

        except Exception as e:
            _print(page, f"{conta}_erro")
            return {"sucesso": False, "conta": conta, "erro": str(e)[:300]}
        finally:
            try:
                page.close()
            except Exception:
                pass
            cofre.fechar(proc, br, nome=conta)


def criar_massa(contas, visivel=True):
    resultados = []
    for i, c in enumerate(contas, 1):
        print(f"\n[{i}/{len(contas)}] {c}...", flush=True)
        r = criar(c, visivel=visivel)
        print(f"  -> {'OK' if r.get('sucesso') else r.get('erro') or r.get('nota', 'FALHA')}", flush=True)
        resultados.append(r)
        if i < len(contas):
            time.sleep(20)
    ok = sum(1 for r in resultados if r.get("sucesso"))
    print(f"\n{ok}/{len(resultados)} contas com Chat Hub configurado")
    return resultados


def listar():
    reg = _ler(REGISTRO, {})
    if not reg:
        print("Nenhuma conta Chat Hub no registro local")
        return
    print(f"{'Conta':<35} {'Completo':<10} {'Webhook'}")
    print("-" * 90)
    for conta, info in sorted(reg.items()):
        completo = "OK" if info.get("completo") else "X"
        webhook = info.get("webhook_url", "nenhum")
        if webhook and len(webhook) > 50:
            webhook = webhook[:50] + "..."
        print(f"{conta:<35} {completo:<10} {webhook}")
    total_ok = sum(1 for v in reg.values() if v.get("completo"))
    print(f"\nTotal: {len(reg)} | Completas: {total_ok}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
    elif a[0] == "criar" and len(a) >= 2:
        print(json.dumps(criar(a[1]), indent=2, ensure_ascii=False))
    elif a[0] == "criar_massa":
        lista = contas_sem_canal() if "--sem-canal" in a else [x for x in a[1:] if not x.startswith("--")]
        criar_massa(lista)
    elif a[0] == "listar":
        listar()
    else:
        print(__doc__)
