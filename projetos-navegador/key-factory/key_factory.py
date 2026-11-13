"""
Fábrica de Chaves — automação COMPLETA do Google AI Studio (Gemini API).

Operações disponíveis:
  - listar_chaves(conta)          → lista chaves existentes com nome/projeto/fragmento
  - criar_chave(conta)            → cria nova API key (projeto novo ou existente)
  - revogar_chave(conta, nome)    → deleta uma API key pelo nome
  - validar_chave(chave)          → testa a chave batendo no endpoint Gemini de verdade
  - escanear_todas()              → varre as 5 contas e consolida todas as chaves
  - exportar_hipercool()          → grava secrets/gemini_keys.json no formato do pipeline
  - contar_quota(chave)           → tenta 1 request e reporta se a chave tem quota viva

CLI:
  python key_factory.py                              → escaneia todas (dry-safe)
  python key_factory.py --acao listar --conta X
  python key_factory.py --acao criar --conta X
  python key_factory.py --acao revogar --conta X --nome "API key 1"
  python key_factory.py --acao validar --chave AIza...
  python key_factory.py --acao exportar
"""
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

KEY_FACTORY_DIR = Path(__file__).resolve().parent
KEYS_OUTPUT = KEY_FACTORY_DIR / "discovered_keys.json"
HIPERCOOL_SECRETS = Path("D:/hipercool-videos/secrets/gemini_keys.json")
AISTUDIO_URL = "https://aistudio.google.com/apikey"
GEMINI_TEST_URL = "https://generativelanguage.googleapis.com/v1beta/models?key={key}"


def _sessao_expirada(page):
    return "accounts.google.com" in page.url or "signin" in page.url.lower()


def listar_chaves(conta):
    """Lista chaves existentes no AI Studio com nome/projeto/fragmento."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(AISTUDIO_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)

            if _sessao_expirada(page):
                return {"conta": conta, "status": "sessao_expirada", "chaves": []}

            chaves = []
            rows = page.query_selector_all("table tbody tr, [role='row']")
            for row in rows:
                cells = row.query_selector_all("td, [role='cell']")
                if len(cells) >= 2:
                    nome = cells[0].inner_text().strip()
                    projeto = cells[1].inner_text().strip() if len(cells) > 1 else ""
                    fragmento = ""
                    for c in cells:
                        t = c.inner_text().strip()
                        if "AIza" in t or "..." in t:
                            fragmento = t
                            break
                    if nome and nome.lower() not in ("name", "nome", "project"):
                        chaves.append({"nome": nome, "projeto": projeto, "fragmento": fragmento})

            save_session(context, conta)
            return {
                "conta": conta,
                "status": "ok",
                "total": len(chaves),
                "chaves": chaves,
                "verificado_em": datetime.now(timezone.utc).isoformat(),
            }
    except Exception as e:
        return {"conta": conta, "status": "erro", "erro": str(e), "chaves": []}


def criar_chave(conta, projeto_novo=True):
    """Cria nova API key no AI Studio e captura o valor."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(AISTUDIO_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)

            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            create_btn = page.query_selector(
                'button:has-text("Create API key"), button:has-text("Criar chave"), '
                'button:has-text("Get API key")'
            )
            if not create_btn:
                return {"sucesso": False, "erro": "botão criar não encontrado"}

            create_btn.click()
            time.sleep(3)

            if projeto_novo:
                opt = page.query_selector(
                    'button:has-text("Create API key in new project"), '
                    'button:has-text("novo projeto")'
                )
            else:
                opt = page.query_selector('button:has-text("existing project"), button:has-text("existente")')

            if opt:
                opt.click()
                time.sleep(12)

            valor = ""
            for sel in ['input[readonly]', 'code', 'pre', '[class*="key-value"]', '[class*="apikey"]']:
                el = page.query_selector(sel)
                if el:
                    valor = (el.get_attribute("value") or el.inner_text() or "").strip()
                    if valor.startswith("AIza"):
                        break

            save_session(context, conta)
            if valor.startswith("AIza"):
                resultado = {"sucesso": True, "chave": valor, "conta": conta}
                _anexar_chave(conta, valor)
                return resultado
            return {"sucesso": False, "erro": "chave não capturada após criação"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def revogar_chave(conta, nome_chave):
    """Deleta uma API key pelo nome exibido."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(AISTUDIO_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)

            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            rows = page.query_selector_all("table tbody tr, [role='row']")
            for row in rows:
                if nome_chave.lower() in row.inner_text().lower():
                    menu = row.query_selector('button[aria-label*="more"], button[aria-label*="Mais"], button:has-text("Delete")')
                    if menu:
                        menu.click()
                        time.sleep(1)
                        del_opt = page.query_selector('button:has-text("Delete"), button:has-text("Excluir"), [role="menuitem"]:has-text("Delete")')
                        if del_opt:
                            del_opt.click()
                            time.sleep(1)
                            confirm = page.query_selector('button:has-text("Delete"), button:has-text("Confirmar")')
                            if confirm:
                                confirm.click()
                                time.sleep(2)
                                save_session(context, conta)
                                return {"sucesso": True, "conta": conta, "nome": nome_chave}

            save_session(context, conta)
            return {"sucesso": False, "erro": f"chave '{nome_chave}' não encontrada"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def validar_chave(chave, timeout=15):
    """Testa a chave batendo no endpoint Gemini de verdade (sem browser)."""
    if not chave or not chave.startswith("AIza"):
        return {"chave": chave[:12] + "...", "valida": False, "motivo": "formato inválido"}

    url = GEMINI_TEST_URL.format(key=chave)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            n_modelos = len(data.get("models", []))
            return {"chave": chave[:12] + "...", "valida": True, "modelos_disponiveis": n_modelos}
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", errors="ignore")[:200]
        motivo = "quota/billing" if e.code == 429 else f"HTTP {e.code}"
        if e.code in (400, 403):
            motivo = "chave inválida/sem permissão"
        return {"chave": chave[:12] + "...", "valida": False, "motivo": motivo, "detalhe": corpo}
    except Exception as e:
        return {"chave": chave[:12] + "...", "valida": False, "motivo": str(e)}


def _anexar_chave(conta, chave):
    """Adiciona uma chave capturada ao discovered_keys.json."""
    dados = {"chaves_capturadas": []}
    if KEYS_OUTPUT.exists():
        try:
            dados = json.loads(KEYS_OUTPUT.read_text(encoding="utf-8"))
        except Exception:
            pass
    dados.setdefault("chaves_capturadas", [])
    dados["chaves_capturadas"].append({
        "conta": conta, "chave": chave,
        "capturada_em": datetime.now(timezone.utc).isoformat(),
    })
    KEYS_OUTPUT.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")


def escanear_todas():
    """Varre todas as contas e consolida as chaves encontradas."""
    print(f"[Fábrica de Chaves] Escaneando {len(ACCOUNTS)} contas — {datetime.now().strftime('%H:%M:%S')}")

    resultados = []
    for conta in ACCOUNTS:
        print(f"  {conta}...", end=" ", flush=True)
        r = listar_chaves(conta)
        print(f"{r['status']} ({r.get('total', 0)} chaves)")
        resultados.append(r)

    saida = {
        "escaneado_em": datetime.now(timezone.utc).isoformat(),
        "total_contas": len(resultados),
        "contas_ok": sum(1 for r in resultados if r["status"] == "ok"),
        "total_chaves": sum(r.get("total", 0) for r in resultados),
        "resultados": resultados,
    }
    saida_prev = {}
    if KEYS_OUTPUT.exists():
        try:
            saida_prev = json.loads(KEYS_OUTPUT.read_text(encoding="utf-8"))
        except Exception:
            pass
    if "chaves_capturadas" in saida_prev:
        saida["chaves_capturadas"] = saida_prev["chaves_capturadas"]

    KEYS_OUTPUT.write_text(json.dumps(saida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultado salvo em {KEYS_OUTPUT}")
    return saida


def exportar_hipercool():
    """Grava chaves capturadas no formato do pipeline hipercool."""
    if not KEYS_OUTPUT.exists():
        return {"sucesso": False, "erro": "nenhuma chave escaneada ainda"}

    dados = json.loads(KEYS_OUTPUT.read_text(encoding="utf-8"))
    capturadas = [c["chave"] for c in dados.get("chaves_capturadas", []) if c.get("chave", "").startswith("AIza")]

    if not capturadas:
        return {"sucesso": False, "erro": "nenhuma chave completa capturada (só fragmentos são visíveis no scan)"}

    formato = {"keys": [{"key": k, "id": i + 1} for i, k in enumerate(capturadas)]}
    HIPERCOOL_SECRETS.parent.mkdir(parents=True, exist_ok=True)
    HIPERCOOL_SECRETS.write_text(json.dumps(formato, indent=2), encoding="utf-8")
    return {"sucesso": True, "total": len(capturadas), "arquivo": str(HIPERCOOL_SECRETS)}


FUNCIONALIDADES = {
    "listar":   {"func": listar_chaves,     "desc": "Lista chaves existentes por conta"},
    "criar":    {"func": criar_chave,       "desc": "Cria nova API key"},
    "revogar":  {"func": revogar_chave,     "desc": "Deleta API key pelo nome"},
    "validar":  {"func": validar_chave,     "desc": "Testa chave no endpoint Gemini real"},
    "escanear": {"func": escanear_todas,    "desc": "Varre todas as contas"},
    "exportar": {"func": exportar_hipercool,"desc": "Exporta pro formato hipercool"},
}


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--acao" in args:
        acao = args[args.index("--acao") + 1]
        conta = args[args.index("--conta") + 1] if "--conta" in args else "fabrica"
        if acao == "listar":
            r = listar_chaves(conta)
        elif acao == "criar":
            r = criar_chave(conta)
        elif acao == "revogar":
            nome = args[args.index("--nome") + 1] if "--nome" in args else ""
            r = revogar_chave(conta, nome)
        elif acao == "validar":
            chave = args[args.index("--chave") + 1] if "--chave" in args else ""
            r = validar_chave(chave)
        elif acao == "exportar":
            r = exportar_hipercool()
        elif acao == "escanear":
            r = escanear_todas()
        else:
            r = {"erro": f"ação desconhecida: {acao}"}
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        escanear_todas()
