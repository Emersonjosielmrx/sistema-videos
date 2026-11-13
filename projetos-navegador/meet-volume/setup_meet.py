"""
Meet Volume — automação COMPLETA do Google Meet (coordenação multi-conta).

Operações disponíveis:
  - verificar_acesso(conta)             → confirma acesso ao Meet
  - criar_reuniao(conta)                → cria reunião instantânea, retorna URL
  - entrar_reuniao(conta, codigo)       → entra numa reunião (mic/cam off)
  - sair_reuniao(conta, codigo)         → entra e sai (útil pra testes)
  - lotar_reuniao(codigo, n)            → enche com N contas
  - agendar_reuniao(conta, titulo, dt)  → agenda via Google Calendar
  - ativar_legendas(conta, codigo)      → entra e liga legendas automáticas
  - listar_participantes(conta, codigo) → lista quem está na sala

CLI:
  python setup_meet.py                                 → dry run
  python setup_meet.py --create [conta]
  python setup_meet.py --fill CODIGO [n]
  python setup_meet.py --acao entrar --conta X --codigo abc-defg-hij
  python setup_meet.py --acao agendar --conta X --titulo "Reunião" --data "2026-07-05 15:00"
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

MEET_DIR = Path(__file__).resolve().parent
STATUS_FILE = MEET_DIR / "meet_status.json"
HISTORICO = MEET_DIR / "historico_meet.jsonl"
MEET_URL = "https://meet.google.com"
CALENDAR_URL = "https://calendar.google.com"


def _sessao_expirada(page):
    return "accounts.google.com" in page.url


def _log(acao, conta, detalhes):
    with open(HISTORICO, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "acao": acao, "conta": conta, "detalhes": detalhes}, ensure_ascii=False) + "\n")


def _mutar(page):
    for label in ["microphone", "microfone", "camera", "câmera"]:
        btn = page.query_selector(f'button[aria-label*="{label}"]')
        if btn:
            try:
                btn.click()
                time.sleep(0.3)
            except Exception:
                pass


def verificar_acesso(conta):
    """Confirma acesso ao Meet."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(MEET_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"conta": conta, "status": "sessao_expirada"}
            save_session(context, conta)
            return {"conta": conta, "status": "ok" if "meet.google.com" in page.url else "redirect"}
    except Exception as e:
        return {"conta": conta, "status": "erro", "erro": str(e)}


def criar_reuniao(conta):
    """Cria uma reunião instantânea e retorna a URL."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(MEET_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            new_btn = page.query_selector('button:has-text("New meeting"), button:has-text("Nova reunião"), button[data-action-type="new-meeting"]')
            if new_btn:
                new_btn.click()
                time.sleep(3)
                instant = page.query_selector('li:has-text("Start an instant meeting"), li:has-text("Iniciar reunião instantânea"), [role="menuitem"]:has-text("instant")')
                if instant:
                    instant.click()
                    time.sleep(6)
                    url = page.url
                    save_session(context, conta)
                    _log("criar_reuniao", conta, url)
                    return {"sucesso": True, "meet_url": url, "conta": conta}
            return {"sucesso": False, "erro": "botão nova reunião não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def entrar_reuniao(conta, codigo, permanecer_s=0):
    """Entra numa reunião com mic/cam desligados."""
    try:
        with google_browser(conta) as (page, context, browser):
            url = f"{MEET_URL}/{codigo}" if not codigo.startswith("http") else codigo
            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            _mutar(page)
            join = page.query_selector('button:has-text("Join now"), button:has-text("Participar agora"), button:has-text("Ask to join"), button:has-text("Pedir para participar")')
            if join:
                join.click()
                time.sleep(5)
                if permanecer_s > 0:
                    time.sleep(permanecer_s)
                save_session(context, conta)
                _log("entrar_reuniao", conta, codigo)
                return {"sucesso": True, "conta": conta, "reuniao": codigo}
            return {"sucesso": False, "erro": "botão participar não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def sair_reuniao(conta, codigo):
    """Entra e sai (útil pra teste de presença)."""
    try:
        with google_browser(conta) as (page, context, browser):
            url = f"{MEET_URL}/{codigo}" if not codigo.startswith("http") else codigo
            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}
            _mutar(page)
            join = page.query_selector('button:has-text("Join now"), button:has-text("Participar agora")')
            if join:
                join.click()
                time.sleep(4)
            leave = page.query_selector('button[aria-label*="Leave call"], button[aria-label*="Sair da chamada"]')
            if leave:
                leave.click()
                time.sleep(2)
            save_session(context, conta)
            return {"sucesso": True, "conta": conta}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def lotar_reuniao(codigo, num_participantes=5):
    """Enche uma reunião com múltiplas contas."""
    print(f"  Lotando reunião {codigo} com {num_participantes} participantes...")
    resultados = []
    contas = list(ACCOUNTS.keys())
    for i in range(min(num_participantes, len(contas))):
        conta = contas[i]
        print(f"    {conta} entrando...", end=" ", flush=True)
        r = entrar_reuniao(conta, codigo)
        print("OK" if r.get("sucesso") else f"FALHA: {r.get('erro')}")
        resultados.append(r)
        time.sleep(3)
    return {"codigo": codigo, "resultados": resultados}


def agendar_reuniao(conta, titulo, data_hora):
    """Agenda uma reunião via Google Calendar com link Meet."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{CALENDAR_URL}/calendar/u/0/r/eventedit", timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            titulo_input = page.query_selector('input[aria-label*="title"], input[aria-label*="título"], input[placeholder*="title"]')
            if titulo_input:
                titulo_input.fill(titulo)
                time.sleep(1)

            meet_btn = page.query_selector('button:has-text("Add Google Meet"), button:has-text("Adicionar videoconferência")')
            if meet_btn:
                meet_btn.click()
                time.sleep(2)

            save_btn = page.query_selector('button:has-text("Save"), button:has-text("Salvar")')
            if save_btn:
                save_btn.click()
                time.sleep(3)

            save_session(context, conta)
            _log("agendar_reuniao", conta, {"titulo": titulo, "data": data_hora})
            return {"sucesso": True, "titulo": titulo, "data": data_hora, "conta": conta}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def ativar_legendas(conta, codigo):
    """Entra na reunião e liga legendas automáticas."""
    try:
        with google_browser(conta) as (page, context, browser):
            url = f"{MEET_URL}/{codigo}" if not codigo.startswith("http") else codigo
            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}
            _mutar(page)
            join = page.query_selector('button:has-text("Join now"), button:has-text("Participar agora")')
            if join:
                join.click()
                time.sleep(5)
            cc = page.query_selector('button[aria-label*="captions"], button[aria-label*="legendas"]')
            if cc:
                cc.click()
                time.sleep(2)
                save_session(context, conta)
                return {"sucesso": True, "conta": conta, "legendas": "ativadas"}
            return {"sucesso": False, "erro": "botão de legendas não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def listar_participantes(conta, codigo):
    """Lista participantes de uma reunião ativa."""
    try:
        with google_browser(conta) as (page, context, browser):
            url = f"{MEET_URL}/{codigo}" if not codigo.startswith("http") else codigo
            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"conta": conta, "participantes": [], "erro": "sessao_expirada"}
            _mutar(page)
            join = page.query_selector('button:has-text("Join now"), button:has-text("Participar agora")')
            if join:
                join.click()
                time.sleep(5)
            people_btn = page.query_selector('button[aria-label*="people"], button[aria-label*="pessoas"], button[aria-label*="participants"]')
            if people_btn:
                people_btn.click()
                time.sleep(2)
            participantes = []
            for el in page.query_selector_all('[role="listitem"], [class*="participant"]'):
                t = el.inner_text().strip().split("\n")[0]
                if t and len(t) < 60:
                    participantes.append(t)
            save_session(context, conta)
            return {"conta": conta, "participantes": list(dict.fromkeys(participantes))}
    except Exception as e:
        return {"conta": conta, "participantes": [], "erro": str(e)}


FUNCIONALIDADES = {
    "verificar":     {"func": verificar_acesso,     "desc": "Confirma acesso ao Meet"},
    "criar":         {"func": criar_reuniao,        "desc": "Cria reunião instantânea"},
    "entrar":        {"func": entrar_reuniao,       "desc": "Entra numa reunião"},
    "sair":          {"func": sair_reuniao,         "desc": "Entra e sai"},
    "lotar":         {"func": lotar_reuniao,        "desc": "Enche com N contas"},
    "agendar":       {"func": agendar_reuniao,      "desc": "Agenda via Calendar"},
    "legendas":      {"func": ativar_legendas,      "desc": "Liga legendas automáticas"},
    "participantes": {"func": listar_participantes, "desc": "Lista participantes"},
}


def setup_meet(dry_run=True):
    print(f"[Meet Volume] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Funcionalidades: {', '.join(FUNCIONALIDADES.keys())}")
    status = {"contas": {}, "ultima_execucao": datetime.now(timezone.utc).isoformat()}
    for conta in ACCOUNTS:
        if dry_run:
            print(f"  [DRY RUN] verificaria Meet: {conta}")
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
    if "--create" in args:
        i = args.index("--create")
        conta = args[i + 1] if i + 1 < len(args) and not args[i + 1].startswith("--") else "fabrica"
        print(json.dumps(criar_reuniao(conta), indent=2, ensure_ascii=False))
    elif "--fill" in args:
        i = args.index("--fill")
        code = args[i + 1]
        n = int(args[i + 2]) if i + 2 < len(args) and args[i + 2].isdigit() else 5
        print(json.dumps(lotar_reuniao(code, n), indent=2, ensure_ascii=False))
    elif "--acao" in args:
        acao = args[args.index("--acao") + 1]
        conta = args[args.index("--conta") + 1] if "--conta" in args else "fabrica"
        codigo = args[args.index("--codigo") + 1] if "--codigo" in args else None
        if acao == "verificar":
            r = verificar_acesso(conta)
        elif acao == "criar":
            r = criar_reuniao(conta)
        elif acao == "entrar":
            r = entrar_reuniao(conta, codigo)
        elif acao == "sair":
            r = sair_reuniao(conta, codigo)
        elif acao == "legendas":
            r = ativar_legendas(conta, codigo)
        elif acao == "participantes":
            r = listar_participantes(conta, codigo)
        elif acao == "agendar":
            r = agendar_reuniao(conta, args[args.index("--titulo") + 1], args[args.index("--data") + 1])
        else:
            r = {"erro": f"ação desconhecida: {acao}"}
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        setup_meet(dry_run="--live" not in args)
