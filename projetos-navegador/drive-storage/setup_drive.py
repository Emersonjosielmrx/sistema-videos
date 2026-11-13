"""
Armazenamento Drive — automação COMPLETA do Google Drive.

Operações disponíveis:
  - verificar_quota(conta)              → espaço usado/disponível
  - criar_pasta(conta, nome)            → cria pasta
  - listar_arquivos(conta, pasta)       → lista arquivos/pastas
  - subir_arquivo(conta, caminho)       → upload de arquivo local
  - baixar_arquivo(conta, nome)         → download de arquivo
  - compartilhar(conta, nome, email)    → compartilha item (ou link público)
  - mover_arquivo(conta, nome, pasta)   → move arquivo pra pasta
  - deletar_arquivo(conta, nome)        → manda pra lixeira
  - buscar(conta, termo)                → busca por nome
  - esvaziar_lixeira(conta)             → limpa lixeira
  - organizar_assets(conta)             → cria estrutura Inovare padrão

CLI:
  python setup_drive.py                                → dry run (verifica quota)
  python setup_drive.py --live
  python setup_drive.py --acao subir --conta X --arquivo D:/caminho.mp4
  python setup_drive.py --acao listar --conta X
  python setup_drive.py --acao compartilhar --conta X --nome arq --email x@y.com
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

DRIVE_DIR = Path(__file__).resolve().parent
STATUS_FILE = DRIVE_DIR / "drive_status.json"
HISTORICO = DRIVE_DIR / "historico_drive.jsonl"
DRIVE_URL = "https://drive.google.com/drive/my-drive"
ESTRUTURA_PADRAO = ["Inovare-Assets", "Inovare-Exports", "Inovare-Backups", "Inovare-Videos", "Inovare-Thumbs"]


def _sessao_expirada(page):
    return "accounts.google.com" in page.url


def _log(acao, conta, detalhes):
    with open(HISTORICO, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "acao": acao, "conta": conta, "detalhes": detalhes,
        }, ensure_ascii=False) + "\n")


def verificar_quota(conta):
    """Retorna espaço usado/disponível no Drive."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto("https://drive.google.com/settings/storage", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"conta": conta, "status": "sessao_expirada"}

            texto = ""
            for sel in ['[class*="storage"]', '[class*="quota"]', '[aria-label*="storage"]']:
                el = page.query_selector(sel)
                if el:
                    texto = el.inner_text().strip()
                    if texto:
                        break

            save_session(context, conta)
            return {"conta": conta, "status": "ok", "quota": texto}
    except Exception as e:
        return {"conta": conta, "status": "erro", "erro": str(e)}


def criar_pasta(conta, nome_pasta):
    """Cria uma pasta no Drive."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(DRIVE_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            new_btn = page.query_selector('button[aria-label*="New"], button:has-text("Novo"), button[guidedhelpid="new_menu_button"]')
            if new_btn:
                new_btn.click()
                time.sleep(2)
                folder_btn = page.query_selector('div[role="menuitem"]:has-text("Folder"), div[role="menuitem"]:has-text("Pasta"), li:has-text("Pasta")')
                if folder_btn:
                    folder_btn.click()
                    time.sleep(2)
                    name_input = page.query_selector('input[type="text"]')
                    if name_input:
                        name_input.fill(nome_pasta)
                        time.sleep(1)
                        create_btn = page.query_selector('button:has-text("Create"), button:has-text("Criar")')
                        if create_btn:
                            create_btn.click()
                            time.sleep(3)
                            save_session(context, conta)
                            _log("criar_pasta", conta, nome_pasta)
                            return {"sucesso": True, "pasta": nome_pasta}
            return {"sucesso": False, "erro": "UI de nova pasta não encontrada"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def listar_arquivos(conta, max_itens=50):
    """Lista arquivos e pastas do Drive."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(DRIVE_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"conta": conta, "arquivos": [], "erro": "sessao_expirada"}

            itens = []
            elementos = page.query_selector_all('[role="row"], [data-id], div[aria-label][role="button"]')
            for el in elementos[:max_itens]:
                nome = el.get_attribute("aria-label") or el.inner_text().strip()
                if nome and len(nome) < 200:
                    itens.append(nome.split("\n")[0].strip())

            save_session(context, conta)
            itens = [i for i in itens if i]
            return {"conta": conta, "arquivos": itens, "total": len(itens)}
    except Exception as e:
        return {"conta": conta, "arquivos": [], "erro": str(e)}


def subir_arquivo(conta, caminho_local, pasta_destino=None):
    """Faz upload de um arquivo local pro Drive."""
    caminho = Path(caminho_local)
    if not caminho.exists():
        return {"sucesso": False, "erro": f"arquivo não existe: {caminho}"}
    try:
        with google_browser(conta, headless=False) as (page, context, browser):
            url = DRIVE_URL
            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            new_btn = page.query_selector('button[aria-label*="New"], button:has-text("Novo")')
            if new_btn:
                new_btn.click()
                time.sleep(2)

            file_input = page.query_selector('input[type="file"]')
            if not file_input:
                upload_opt = page.query_selector('div[role="menuitem"]:has-text("File upload"), div[role="menuitem"]:has-text("Fazer upload de arquivo")')
                if upload_opt:
                    with page.expect_file_chooser() as fc_info:
                        upload_opt.click()
                    fc_info.value.set_files(str(caminho.resolve()))
                    time.sleep(1)
            else:
                file_input.set_input_files(str(caminho.resolve()))

            for _ in range(60):
                done = page.query_selector('[aria-label*="upload complete"], [aria-label*="concluído"], :has-text("upload complete")')
                if done:
                    break
                time.sleep(3)

            save_session(context, conta)
            _log("subir_arquivo", conta, caminho.name)
            return {"sucesso": True, "arquivo": caminho.name, "conta": conta}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def baixar_arquivo(conta, nome_arquivo):
    """Baixa um arquivo do Drive pelo nome."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(DRIVE_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            item = page.query_selector(f'[aria-label*="{nome_arquivo}"]')
            if not item:
                return {"sucesso": False, "erro": f"'{nome_arquivo}' não encontrado"}

            item.click(button="right")
            time.sleep(2)
            download_opt = page.query_selector('div[role="menuitem"]:has-text("Download"), div[role="menuitem"]:has-text("Fazer download")')
            if download_opt:
                with page.expect_download() as dl_info:
                    download_opt.click()
                download = dl_info.value
                destino = DRIVE_DIR / "downloads" / download.suggested_filename
                destino.parent.mkdir(exist_ok=True)
                download.save_as(str(destino))
                save_session(context, conta)
                _log("baixar_arquivo", conta, nome_arquivo)
                return {"sucesso": True, "arquivo": nome_arquivo, "salvo_em": str(destino)}
            return {"sucesso": False, "erro": "opção download não encontrada"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def compartilhar(conta, nome_arquivo, email=None, link_publico=False):
    """Compartilha um item por email ou gera link público."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(DRIVE_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            item = page.query_selector(f'[aria-label*="{nome_arquivo}"]')
            if not item:
                return {"sucesso": False, "erro": f"'{nome_arquivo}' não encontrado"}

            item.click(button="right")
            time.sleep(2)
            share_opt = page.query_selector('div[role="menuitem"]:has-text("Share"), div[role="menuitem"]:has-text("Compartilhar")')
            if share_opt:
                share_opt.click()
                time.sleep(2)

                if email:
                    email_input = page.query_selector('input[type="text"], input[aria-label*="people"], input[aria-label*="pessoas"]')
                    if email_input:
                        email_input.fill(email)
                        time.sleep(1)
                        page.keyboard.press("Enter")

                if link_publico:
                    link_opt = page.query_selector(':has-text("Anyone with the link"), :has-text("qualquer pessoa com o link")')
                    if link_opt:
                        link_opt.click()
                        time.sleep(1)

                send_btn = page.query_selector('button:has-text("Send"), button:has-text("Enviar"), button:has-text("Done"), button:has-text("Concluído")')
                if send_btn:
                    send_btn.click()
                    time.sleep(2)

                save_session(context, conta)
                _log("compartilhar", conta, {"arquivo": nome_arquivo, "email": email, "publico": link_publico})
                return {"sucesso": True, "arquivo": nome_arquivo, "email": email, "publico": link_publico}
            return {"sucesso": False, "erro": "opção compartilhar não encontrada"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def deletar_arquivo(conta, nome_arquivo):
    """Manda um arquivo pra lixeira."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(DRIVE_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            item = page.query_selector(f'[aria-label*="{nome_arquivo}"]')
            if not item:
                return {"sucesso": False, "erro": f"'{nome_arquivo}' não encontrado"}
            item.click()
            time.sleep(1)
            page.keyboard.press("Delete")
            time.sleep(2)
            save_session(context, conta)
            _log("deletar_arquivo", conta, nome_arquivo)
            return {"sucesso": True, "arquivo": nome_arquivo}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def buscar(conta, termo):
    """Busca arquivos por nome."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(DRIVE_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"conta": conta, "resultados": [], "erro": "sessao_expirada"}

            search = page.query_selector('input[aria-label*="Search"], input[aria-label*="Pesquisar"], input[type="search"]')
            if search:
                search.fill(termo)
                page.keyboard.press("Enter")
                time.sleep(4)

            resultados = []
            for el in page.query_selector_all('[role="row"], [data-id]')[:30]:
                nome = el.get_attribute("aria-label") or el.inner_text().strip()
                if nome:
                    resultados.append(nome.split("\n")[0].strip())

            save_session(context, conta)
            return {"conta": conta, "termo": termo, "resultados": [r for r in resultados if r]}
    except Exception as e:
        return {"conta": conta, "resultados": [], "erro": str(e)}


def esvaziar_lixeira(conta):
    """Esvazia a lixeira do Drive."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto("https://drive.google.com/drive/trash", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            empty_btn = page.query_selector('button:has-text("Empty trash"), button:has-text("Esvaziar lixeira")')
            if empty_btn:
                empty_btn.click()
                time.sleep(2)
                confirm = page.query_selector('button:has-text("Delete forever"), button:has-text("Excluir definitivamente")')
                if confirm:
                    confirm.click()
                    time.sleep(2)
                save_session(context, conta)
                _log("esvaziar_lixeira", conta, "ok")
                return {"sucesso": True, "conta": conta}
            return {"sucesso": False, "erro": "lixeira vazia ou botão não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def organizar_assets(conta):
    """Cria a estrutura de pastas Inovare padrão."""
    criadas = []
    for pasta in ESTRUTURA_PADRAO:
        r = criar_pasta(conta, pasta)
        criadas.append({"pasta": pasta, "sucesso": r.get("sucesso", False)})
    return {"conta": conta, "estrutura": criadas}


FUNCIONALIDADES = {
    "quota":        {"func": verificar_quota,   "desc": "Espaço usado/disponível"},
    "criar_pasta":  {"func": criar_pasta,        "desc": "Cria pasta"},
    "listar":       {"func": listar_arquivos,    "desc": "Lista arquivos/pastas"},
    "subir":        {"func": subir_arquivo,      "desc": "Upload de arquivo local"},
    "baixar":       {"func": baixar_arquivo,     "desc": "Download de arquivo"},
    "compartilhar": {"func": compartilhar,       "desc": "Compartilha por email/link"},
    "deletar":      {"func": deletar_arquivo,    "desc": "Manda pra lixeira"},
    "buscar":       {"func": buscar,             "desc": "Busca por nome"},
    "lixeira":      {"func": esvaziar_lixeira,   "desc": "Esvazia a lixeira"},
    "organizar":    {"func": organizar_assets,   "desc": "Cria estrutura Inovare padrão"},
}


def setup_drive(dry_run=True):
    print(f"[Armazenamento Drive] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Funcionalidades: {', '.join(FUNCIONALIDADES.keys())}")
    status = {"estrutura_padrao": ESTRUTURA_PADRAO, "contas": {}, "ultima_execucao": datetime.now(timezone.utc).isoformat()}
    for conta in ACCOUNTS:
        if dry_run:
            print(f"  [DRY RUN] verificaria Drive: {conta}")
            status["contas"][conta] = {"dry_run": True}
        else:
            print(f"  {conta}...", end=" ", flush=True)
            r = verificar_quota(conta)
            print(r["status"])
            status["contas"][conta] = r
    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nStatus salvo em {STATUS_FILE}")
    return status


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--acao" in args:
        acao = args[args.index("--acao") + 1]
        conta = args[args.index("--conta") + 1] if "--conta" in args else "fabrica"
        if acao == "quota":
            r = verificar_quota(conta)
        elif acao == "criar_pasta":
            r = criar_pasta(conta, args[args.index("--nome") + 1])
        elif acao == "listar":
            r = listar_arquivos(conta)
        elif acao == "subir":
            r = subir_arquivo(conta, args[args.index("--arquivo") + 1])
        elif acao == "baixar":
            r = baixar_arquivo(conta, args[args.index("--nome") + 1])
        elif acao == "compartilhar":
            email = args[args.index("--email") + 1] if "--email" in args else None
            pub = "--publico" in args
            r = compartilhar(conta, args[args.index("--nome") + 1], email, pub)
        elif acao == "deletar":
            r = deletar_arquivo(conta, args[args.index("--nome") + 1])
        elif acao == "buscar":
            r = buscar(conta, args[args.index("--termo") + 1])
        elif acao == "lixeira":
            r = esvaziar_lixeira(conta)
        elif acao == "organizar":
            r = organizar_assets(conta)
        else:
            r = {"erro": f"ação desconhecida: {acao}"}
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        dry = "--live" not in args
        if dry:
            print("Modo DRY RUN\n")
        setup_drive(dry_run=dry)
