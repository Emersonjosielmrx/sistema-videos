"""
Criador de Canais YouTube — cria canais YouTube via RPA em contas Google que ainda não têm canal.

Usa o cofre.py de D:/logins-google para abrir Chrome com sessão Google já logada,
depois navega até o YouTube Studio e cria o canal com nome/descrição.

CLI:
  python youtube_channel.py listar                       → lista contas sem canal
  python youtube_channel.py criar <conta> --nome "Meu Canal" --desc "Sobre..."
  python youtube_channel.py criar_massa --arquivo contas.json
  python youtube_channel.py verificar [conta]             → testa quais têm/não têm canal
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, r"D:\logins-google")
import cofre

FACTORY_DIR = Path(__file__).resolve().parent
STATUS_FILE = FACTORY_DIR / "youtube_channels_status.json"
HISTORICO_FILE = FACTORY_DIR / "youtube_channels_historico.jsonl"
STUDIO_URL = "https://studio.youtube.com"


def _registrar(acao, conta, detalhes):
    entrada = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "acao": acao, "conta": conta, "detalhes": detalhes,
    }
    with open(HISTORICO_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    return entrada


def _conectar(conta, visivel=False):
    """Abre Chrome via cofre e conecta pelo Playwright CDP. Retorna (page, browser, porta, proc)."""
    from playwright.sync_api import sync_playwright

    porta, proc = cofre.abrir(conta, url="about:blank", visivel=visivel)
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    context = browser.contexts[0]
    page = context.pages[0] if context.pages else context.new_page()
    return page, browser, porta, proc, pw


def _desconectar(browser, proc, pw, conta=None):
    """Fecha browser e Chrome."""
    try:
        browser.close()
    except Exception:
        pass
    cofre.fechar(proc, nome=conta)
    try:
        pw.stop()
    except Exception:
        pass


def verificar_canal(conta):
    """Verifica se a conta Google tem canal YouTube. Retorna dict com status."""
    page, browser, porta, proc, pw = _conectar(conta)
    try:
        page.goto(STUDIO_URL, timeout=45000, wait_until="domcontentloaded")
        time.sleep(5)

        url = page.url

        if "accounts.google.com" in url:
            return {"conta": conta, "status": "sessao_expirada"}

        if "create_channel" in url or "channel_creation" in url:
            return {"conta": conta, "status": "sem_canal"}

        if "studio.youtube.com" in url:
            nome_canal = ""
            for sel in ['[class*="channel-name"]', '#channel-title',
                        '[class*="studio-header"] span', 'ytcp-channel-name']:
                el = page.query_selector(sel)
                if el:
                    nome_canal = el.inner_text().strip()
                    if nome_canal:
                        break
            return {"conta": conta, "status": "canal_ativo", "nome_canal": nome_canal}

        return {"conta": conta, "status": "desconhecido", "url": url[:200]}
    except Exception as e:
        return {"conta": conta, "status": "erro", "erro": str(e)}
    finally:
        _desconectar(browser, proc, pw, conta)


def criar_canal(conta, nome_canal, descricao="", foto_perfil=None, visivel=False):
    """Cria canal YouTube numa conta que ainda não tem. Navega pelo YouTube Studio."""
    page, browser, porta, proc, pw = _conectar(conta, visivel=visivel)
    try:
        page.goto(STUDIO_URL, timeout=45000, wait_until="domcontentloaded")
        time.sleep(5)

        url = page.url
        if "accounts.google.com" in url:
            return {"sucesso": False, "erro": "sessao_expirada"}

        if "studio.youtube.com" in url and "create_channel" not in url and "channel_creation" not in url:
            return {"sucesso": False, "erro": "canal_ja_existe", "url": url}

        # --- Fluxo de criação ---
        # Pode ser redirecionado para youtube.com/channel_creation ou studio.youtube.com/channel/create_channel
        if "youtube.com" not in url:
            page.goto("https://www.youtube.com/channel_creation", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

        # Preencher nome do canal
        nome_input = page.query_selector(
            'input[aria-label*="name" i], input[aria-label*="nome" i], '
            'input[placeholder*="name" i], input[placeholder*="nome" i], '
            '#channel-name-input input, input[name="channel-name"], '
            '#name-input input, div[id*="name"] input'
        )
        if nome_input:
            nome_input.click()
            time.sleep(0.3)
            nome_input.fill("")
            nome_input.type(nome_canal, delay=20)
            time.sleep(1)
        else:
            # Tentar via textbox (YouTube Studio usa divs editáveis às vezes)
            textbox = page.query_selector('[contenteditable="true"]')
            if textbox:
                textbox.click()
                textbox.type(nome_canal, delay=20)
                time.sleep(1)
            else:
                return {"sucesso": False, "erro": "campo_nome_nao_encontrado", "url": page.url}

        # Handle/identificador — YouTube pode exigir definir um handle
        handle_input = page.query_selector(
            'input[aria-label*="handle" i], input[placeholder*="@"], '
            '#handle-input input'
        )
        if handle_input:
            handle_sugerido = nome_canal.lower().replace(" ", "").replace("_", "")
            handle_input.click()
            handle_input.fill("")
            handle_input.type(handle_sugerido, delay=15)
            time.sleep(2)

        # Upload da foto de perfil se fornecida
        if foto_perfil and Path(foto_perfil).exists():
            foto_input = page.query_selector('input[type="file"][accept*="image"]')
            if foto_input:
                foto_input.set_input_files(str(Path(foto_perfil).resolve()))
                time.sleep(3)

        # Botão de criar (tentar vários textos possíveis)
        criar_btn = None
        for seletor in [
            'button:has-text("Create channel")', 'button:has-text("Criar canal")',
            'button:has-text("Create")', 'button:has-text("Criar")',
            '#create-channel-button', 'button[aria-label*="Create" i]',
            'button[aria-label*="Criar" i]',
        ]:
            criar_btn = page.query_selector(seletor)
            if criar_btn and criar_btn.is_visible():
                break
            criar_btn = None

        if not criar_btn:
            return {"sucesso": False, "erro": "botao_criar_nao_encontrado", "url": page.url}

        criar_btn.click()
        time.sleep(8)

        # Verificar se criou com sucesso
        url_final = page.url
        if "studio.youtube.com" in url_final and "create_channel" not in url_final:
            resultado = {
                "sucesso": True, "conta": conta,
                "nome_canal": nome_canal, "url_final": url_final,
            }
            _registrar("criar_canal", conta, resultado)

            # Adicionar descrição se tiver
            if descricao:
                _adicionar_descricao(page, descricao)

            return resultado

        # Pode ter ido pro YouTube normal (canal criado mas sem Studio ainda)
        if "youtube.com" in url_final and "create_channel" not in url_final:
            resultado = {
                "sucesso": True, "conta": conta,
                "nome_canal": nome_canal, "url_final": url_final,
                "nota": "canal criado, YouTube normal",
            }
            _registrar("criar_canal", conta, resultado)
            return resultado

        return {"sucesso": False, "erro": "criacao_nao_confirmada", "url": url_final}

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}
    finally:
        _desconectar(browser, proc, pw, conta)


def _adicionar_descricao(page, descricao):
    """Tenta adicionar descrição ao canal recém-criado via Studio -> Customization."""
    try:
        page.goto(f"{STUDIO_URL}/channel/editing/basic", timeout=30000, wait_until="domcontentloaded")
        time.sleep(5)
        desc_input = page.query_selector(
            '#description-container textarea, #description-textarea #textbox, '
            'div[aria-label*="description" i], textarea[aria-label*="description" i]'
        )
        if desc_input:
            desc_input.click()
            desc_input.type(descricao, delay=15)
            time.sleep(1)
            publish_btn = page.query_selector(
                'button:has-text("Publish"), button:has-text("Publicar"), #publish-button'
            )
            if publish_btn and publish_btn.is_visible():
                publish_btn.click()
                time.sleep(3)
    except Exception:
        pass


def criar_massa(arquivo_contas, visivel=False):
    """Cria canais em massa a partir de um JSON: [{"conta": "xxx", "nome": "Yyy", "desc": "..."}]"""
    dados = json.loads(Path(arquivo_contas).read_text(encoding="utf-8"))
    resultados = []
    for item in dados:
        conta_nome = item["conta"]
        nome = item.get("nome", conta_nome)
        desc = item.get("desc", "")
        foto = item.get("foto")

        print(f"  {conta_nome} -> {nome}...", end=" ", flush=True)
        r = criar_canal(conta_nome, nome, descricao=desc, foto_perfil=foto, visivel=visivel)
        print(r.get("sucesso", False) and "OK" or r.get("erro", "?"))
        resultados.append(r)
        time.sleep(3)

    return resultados


def verificar_todas():
    """Verifica todas as contas do cofre para saber quais têm/não têm canal."""
    reg = cofre._ler()
    resultados = []
    for email, entry in reg["contas"].items():
        apelido = entry.get("apelido", email.split("@")[0])
        print(f"  {apelido}...", end=" ", flush=True)
        r = verificar_canal(apelido)
        print(r["status"])
        resultados.append(r)
        time.sleep(2)

    saida = {
        "verificado_em": datetime.now(timezone.utc).isoformat(),
        "total": len(resultados),
        "com_canal": sum(1 for r in resultados if r["status"] == "canal_ativo"),
        "sem_canal": sum(1 for r in resultados if r["status"] == "sem_canal"),
        "sessao_morta": sum(1 for r in resultados if r["status"] == "sessao_expirada"),
        "resultados": resultados,
    }
    STATUS_FILE.write_text(json.dumps(saida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSalvo em {STATUS_FILE}")
    return saida


def listar_sem_canal():
    """Lista contas que não têm canal YouTube (precisa verificar_todas primeiro)."""
    if not STATUS_FILE.exists():
        print("Rode 'verificar' antes para mapear as contas.")
        return []
    dados = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    sem = [r for r in dados["resultados"] if r["status"] == "sem_canal"]
    for r in sem:
        print(f"  {r['conta']}")
    return sem


FUNCIONALIDADES = {
    "listar":     {"func": listar_sem_canal,  "desc": "Lista contas sem canal (precisa verificar antes)"},
    "verificar":  {"func": verificar_todas,   "desc": "Verifica todas as contas do cofre"},
    "criar":      {"func": criar_canal,       "desc": "Cria canal YouTube numa conta"},
    "criar_massa":{"func": criar_massa,       "desc": "Cria canais em lote (JSON)"},
}


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Uso:")
        for nome, info in FUNCIONALIDADES.items():
            print(f"  python youtube_channel.py {nome:15s} — {info['desc']}")
        sys.exit(0)

    cmd = args[0]

    if cmd == "listar":
        listar_sem_canal()

    elif cmd == "verificar":
        conta_arg = args[1] if len(args) > 1 else None
        if conta_arg:
            r = verificar_canal(conta_arg)
            print(json.dumps(r, indent=2, ensure_ascii=False))
        else:
            verificar_todas()

    elif cmd == "criar":
        if len(args) < 2:
            print("Uso: python youtube_channel.py criar <conta> --nome 'Nome do Canal' [--desc '...'] [--foto path]")
            sys.exit(1)
        conta_arg = args[1]
        nome = args[args.index("--nome") + 1] if "--nome" in args else conta_arg
        desc = args[args.index("--desc") + 1] if "--desc" in args else ""
        foto = args[args.index("--foto") + 1] if "--foto" in args else None
        visivel = "--visivel" in args
        r = criar_canal(conta_arg, nome, descricao=desc, foto_perfil=foto, visivel=visivel)
        print(json.dumps(r, indent=2, ensure_ascii=False))

    elif cmd == "criar_massa":
        arquivo = args[args.index("--arquivo") + 1] if "--arquivo" in args else (args[1] if len(args) > 1 else None)
        if not arquivo:
            print("Uso: python youtube_channel.py criar_massa --arquivo contas.json")
            sys.exit(1)
        visivel = "--visivel" in args
        resultados = criar_massa(arquivo, visivel=visivel)
        print(json.dumps(resultados, indent=2, ensure_ascii=False))

    else:
        print(f"Comando desconhecido: {cmd}")
        print(f"Disponíveis: {', '.join(FUNCIONALIDADES.keys())}")
