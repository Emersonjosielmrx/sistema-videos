r"""
Cloud Run: ativa o serviço Cloud Run e Container Registry em cada conta Google do cofre
(Google Cloud Console, tier grátis).

Passos: console.cloud.google.com -> ativar faturamento (free trial) -> ativar API Cloud Run,
        Container Registry, Cloud Build.
A cota grátis do Cloud Run: 2 milhões de requests/mês, 360.000 GB-s de memória, 180.000 vCPU-s.
Container Registry: 0,5 GB de armazenamento grátis.

O módulo SÓ roda em contas SEM canal YouTube (contas suspensas ou sem canal).

CLI:
  python cloud_run.py criar <conta>
  python cloud_run.py criar_massa --sem-canal           # todas sem canal com Google vivo
  python cloud_run.py criar_massa <conta1> <conta2> ...
  python cloud_run.py listar
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
REGISTRO = DIR / "cloud_run_contas.json"
CONSOLE_URL = "https://console.cloud.google.com/"
CLOUD_RUN_API = "https://console.cloud.google.com/apis/library/run.googleapis.com"
CONTAINER_REG_API = "https://console.cloud.google.com/apis/library/containerregistry.googleapis.com"
CLOUD_BUILD_API = "https://console.cloud.google.com/apis/library/cloudbuild.googleapis.com"
CLOUD_FUNCTIONS_API = "https://console.cloud.google.com/apis/library/cloudfunctions.googleapis.com"

APIS_PARA_ATIVAR = [
    ("Cloud Run", CLOUD_RUN_API),
    ("Container Registry", CONTAINER_REG_API),
    ("Cloud Build", CLOUD_BUILD_API),
    ("Cloud Functions", CLOUD_FUNCTIONS_API),
]


def _ler(arq, padrao):
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else padrao


def _gravar(arq, dados, indent=2):
    tmp = arq.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(arq)


def _print(page, motivo):
    p = DIR / f"_debug_cloudrun_{datetime.now():%H%M%S}_{motivo}.png"
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


def _aceitar_termos(page):
    for txt in ("Agree", "Aceitar", "Accept", "I agree", "Concordo", "Concordar", "Got it", "Entendi"):
        btn = page.get_by_role("button", name=txt)
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.click(timeout=5000)
                page.wait_for_timeout(2000)
                return True
        except Exception:
            pass
    return False


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


def _ativar_free_trial(page, email):
    page.goto(CONSOLE_URL, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)

    if "accounts.google.com" in page.url:
        _selecionar_conta(page, email)
        page.wait_for_timeout(5000)

    _aceitar_termos(page)

    for txt in ("Try for free", "Start free", "Ativar", "Activate", "Comece gratuitamente",
                "Teste grátis", "Start Free Trial", "Try Google Cloud for free"):
        btn = page.get_by_role("button", name=txt)
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.click(timeout=10000)
                page.wait_for_timeout(5000)
                _aceitar_termos(page)
                return True
        except Exception:
            pass
    link = page.locator('a:has-text("Try for free"), a:has-text("Start free"), a:has-text("Ativar")')
    try:
        if link.count() and link.first.is_visible():
            link.first.click(timeout=10000)
            page.wait_for_timeout(5000)
            _aceitar_termos(page)
            return True
    except Exception:
        pass
    return False


def _ativar_api(page, nome, url):
    page.goto(url, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)

    _aceitar_termos(page)

    corpo = page.inner_text("body")

    if "API enabled" in corpo or "API ativada" in corpo:
        return {"api": nome, "status": "ja_ativa"}

    for txt in ("Enable", "Ativar", "Enable API", "Ativar API"):
        btn = page.get_by_role("button", name=txt, exact=True)
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.click(timeout=15000)
                page.wait_for_timeout(10000)
                corpo2 = page.inner_text("body")
                if "API enabled" in corpo2 or "API ativada" in corpo2 or "Manage" in corpo2 or "Gerenciar" in corpo2:
                    return {"api": nome, "status": "ativada"}
                return {"api": nome, "status": "clicou_enable", "url_final": page.url}
        except Exception as e:
            return {"api": nome, "status": "erro", "detalhe": str(e)[:200]}

    if "billing" in corpo.lower() or "faturamento" in corpo.lower():
        return {"api": nome, "status": "precisa_faturamento"}

    if "project" in corpo.lower() and ("select" in corpo.lower() or "create" in corpo.lower()):
        for txt2 in ("Create project", "Criar projeto", "Create", "Criar",
                      "Select project", "Selecionar projeto"):
            b = page.get_by_role("button", name=txt2)
            try:
                if b.count() and b.first.is_visible():
                    b.first.click(timeout=10000)
                    page.wait_for_timeout(5000)
                    return _ativar_api(page, nome, url)
            except Exception:
                pass

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
            _ativar_free_trial(page, email)
            page.wait_for_timeout(3000)

            # Google Cloud exige verificação em 2 etapas na conta (24/10); sem ela o console fica bloqueado
            if "enable-mfa" in page.url or "Acesso ao Google Cloud bloqueado" in page.inner_text("body"):
                reg[conta] = {"email": email, "completo": False, "erro": "exige_2fa",
                              "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
                _gravar(REGISTRO, reg)
                return {"sucesso": False, "conta": conta, "erro": "exige_2fa (ativar verificação em 2 etapas)"}

            apis_resultado = []
            for nome_api, url_api in APIS_PARA_ATIVAR:
                r = _ativar_api(page, nome_api, url_api)
                apis_resultado.append(r)
                print(f"  {nome_api}: {r['status']}", flush=True)
                page.wait_for_timeout(3000)

            todas_ok = all(r["status"] in ("ativada", "ja_ativa") for r in apis_resultado)

            reg[conta] = {
                "email": email,
                "apis": apis_resultado,
                "completo": todas_ok,
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
        if i < len(contas):
            time.sleep(20)
    ok = sum(1 for r in resultados if r.get("sucesso"))
    print(f"\n{ok}/{len(resultados)} contas com Cloud Run ativado")
    return resultados


def listar():
    reg = _ler(REGISTRO, {})
    if not reg:
        print("Nenhuma conta Cloud Run no registro local")
        return
    print(f"{'Conta':<35} {'Completo':<10} {'APIs'}")
    print("-" * 90)
    for conta, info in sorted(reg.items()):
        completo = "OK" if info.get("completo") else "X"
        apis = ", ".join(f"{a['api']}={a['status']}" for a in info.get("apis", []))
        print(f"{conta:<35} {completo:<10} {apis}")
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
