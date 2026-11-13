r"""
Cloud APIs: liga APIs grátis do Google Cloud em cada conta Google do cofre (sem canal YouTube).

Ativa todas as APIs que têm cota grátis útil para os projetos:
- Cloud Text-to-Speech (4 milhões chars/mês)
- Cloud Translation (500k chars/mês)
- Cloud Vision (1k requests/mês)
- Cloud Natural Language (5k unidades/mês)
- YouTube Data API v3 (10k unidades/dia)
- Google Drive API
- Gmail API
- Google Sheets API
- Google Chat API

Cada API é ativada navegando até a biblioteca e clicando Enable.
O módulo SÓ roda em contas SEM canal YouTube.

CLI:
  python cloud_apis.py criar <conta>
  python cloud_apis.py criar_massa --sem-canal
  python cloud_apis.py criar_massa <conta1> <conta2> ...
  python cloud_apis.py listar
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre

DIR = Path(__file__).resolve().parent
REGISTRO = DIR / "cloud_apis_contas.json"

APIS_GRATIS = [
    ("Cloud Text-to-Speech", "https://console.cloud.google.com/apis/library/texttospeech.googleapis.com"),
    ("Cloud Translation", "https://console.cloud.google.com/apis/library/translate.googleapis.com"),
    ("Cloud Vision", "https://console.cloud.google.com/apis/library/vision.googleapis.com"),
    ("Cloud Natural Language", "https://console.cloud.google.com/apis/library/language.googleapis.com"),
    ("YouTube Data API v3", "https://console.cloud.google.com/apis/library/youtube.googleapis.com"),
    ("Google Drive API", "https://console.cloud.google.com/apis/library/drive.googleapis.com"),
    ("Gmail API", "https://console.cloud.google.com/apis/library/gmail.googleapis.com"),
    ("Google Sheets API", "https://console.cloud.google.com/apis/library/sheets.googleapis.com"),
    ("Google Chat API", "https://console.cloud.google.com/apis/library/chat.googleapis.com"),
]


def _ler(arq, padrao):
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else padrao


def _gravar(arq, dados, indent=2):
    tmp = arq.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(arq)


def _print(page, motivo):
    p = DIR / f"_debug_cloudapis_{datetime.now():%H%M%S}_{motivo}.png"
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
    for txt in ("Agree", "Aceitar", "Accept", "I agree", "Concordo", "Got it", "Entendi"):
        btn = page.get_by_role("button", name=txt)
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.click(timeout=5000)
                page.wait_for_timeout(2000)
                return True
        except Exception:
            pass
    return False


def _criar_projeto_se_necessario(page):
    corpo = page.inner_text("body")
    if "select a project" in corpo.lower() or "selecione um projeto" in corpo.lower():
        for txt in ("Create project", "Criar projeto", "New Project", "Novo projeto"):
            btn = page.get_by_role("button", name=txt)
            try:
                if btn.count() and btn.first.is_visible():
                    btn.first.click(timeout=10000)
                    page.wait_for_timeout(5000)
                    for txt2 in ("Create", "Criar"):
                        b2 = page.get_by_role("button", name=txt2, exact=True)
                        try:
                            if b2.count() and b2.first.is_visible():
                                b2.first.click(timeout=10000)
                                page.wait_for_timeout(8000)
                                return True
                        except Exception:
                            pass
            except Exception:
                pass
    return False


def _ativar_api(page, nome, url):
    page.goto(url, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)

    _aceitar_termos(page)

    corpo = page.inner_text("body")

    if "enable-mfa" in page.url or "Acesso ao Google Cloud bloqueado" in corpo:
        return {"api": nome, "status": "exige_2fa"}

    if "API enabled" in corpo or "API ativada" in corpo:
        return {"api": nome, "status": "ja_ativa"}

    _criar_projeto_se_necessario(page)

    # a página tem 2 botões "Ativar": o primeiro fica escondido (cfc-hidden)
    for txt in ("Ativar", "Enable"):
        btn = page.locator("mp-product-details-cta-button:not(.cfc-hidden) .mdc-button__label").filter(
            has_text=txt)
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.click(timeout=15000)
                page.wait_for_timeout(15000)
                if "/apis/api/" in page.url:
                    return {"api": nome, "status": "ativada"}
                corpo2 = page.inner_text("body")
                if any(s in corpo2 for s in ("API enabled", "API ativada", "Manage", "Gerenciar", "Disable", "Desativar")):
                    return {"api": nome, "status": "ativada"}
                return {"api": nome, "status": "nao_ativou (provável faturamento)", "url_final": page.url}
        except Exception as e:
            return {"api": nome, "status": "erro", "detalhe": str(e)[:200]}

    return {"api": nome, "status": "botao_nao_encontrado"}


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
            page.goto("https://console.cloud.google.com/", timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(8000)

            if "accounts.google.com" in page.url:
                _selecionar_conta(page, email)
                page.wait_for_timeout(5000)

            _aceitar_termos(page)

            # Google Cloud exige verificação em 2 etapas na conta (24/10); sem ela o console fica bloqueado
            if "enable-mfa" in page.url or "Acesso ao Google Cloud bloqueado" in page.inner_text("body"):
                reg[conta] = {"email": email, "completo": False, "erro": "exige_2fa",
                              "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
                _gravar(REGISTRO, reg)
                return {"sucesso": False, "conta": conta, "erro": "exige_2fa (ativar verificação em 2 etapas)"}

            apis_resultado = []
            for nome_api, url_api in APIS_GRATIS:
                r = _ativar_api(page, nome_api, url_api)
                apis_resultado.append(r)
                print(f"  {nome_api}: {r['status']}", flush=True)
                page.wait_for_timeout(3000)

            # TTS e Natural Language pedem faturamento: não seguram a conta como incompleta
            todas_ok = all(r["status"] in ("ativada", "ja_ativa") or r["status"].startswith("nao_ativou")
                           for r in apis_resultado)
            if r["status"] == "exige_2fa":
                print("  (bloqueio de 2 etapas apareceu depois de abrir)", flush=True)

            reg[conta] = {
                "email": email,
                "apis": apis_resultado,
                "completo": todas_ok,
                "erro": "exige_2fa" if any(a["status"] == "exige_2fa" for a in apis_resultado) else None,
                "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            _gravar(REGISTRO, reg)

            _print(page, f"{conta}_final")
            return {"sucesso": todas_ok, "conta": conta, "apis": apis_resultado}

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
        if i < len(contas) and not r.get("nota"):
            time.sleep(20)
    ok = sum(1 for r in resultados if r.get("sucesso"))
    print(f"\n{ok}/{len(resultados)} contas com APIs ativadas")
    return resultados


def listar():
    reg = _ler(REGISTRO, {})
    if not reg:
        print("Nenhuma conta Cloud APIs no registro local")
        return
    print(f"{'Conta':<35} {'Completo':<10} {'APIs ativadas'}")
    print("-" * 90)
    for conta, info in sorted(reg.items()):
        completo = "OK" if info.get("completo") else "X"
        ativas = sum(1 for a in info.get("apis", []) if a["status"] in ("ativada", "ja_ativa"))
        total = len(info.get("apis", []))
        print(f"{conta:<35} {completo:<10} {ativas}/{total}")
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
