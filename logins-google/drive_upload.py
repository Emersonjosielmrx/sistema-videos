"""drive_upload.py — Upload de vídeos pro Google Drive via Chrome CDP + perfis.

Usa os Chrome profiles de D:/logins-google/chrome-profiles/ (mesmos do engajamento).

Uso:
    python drive_upload.py <arquivo_ou_pasta> [--conta <nome>] [--pasta-drive <caminho>]

Exemplos:
    python drive_upload.py "D:/hipercool-materiais/videos/the-meek-cat/cap05/normal/v1.mp4"
    python drive_upload.py "D:/hipercool-materiais/videos/the-meek-cat/cap05" --pasta-drive "hipercool/the-meek-cat/cap05"

Organização no Drive:
    hipercool/
      <obra>/
        <capXX>/
          normal/  hyperframes/  censored/  shorts/
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "D:/projetos-navegador/shared")
from google_session import ACCOUNTS, PORT_MAP, get_profile_dir, CHROME_PATH

PROFILES_DIR = Path("D:/logins-google/chrome-profiles")
UPLOAD_LOG = Path("D:/logins-google/drive_uploads.json")
INDEX_FILE = Path("D:/logins-google/drive_index.md")
DEFAULT_DRIVE_ROOT = "hipercool"


def load_upload_log():
    if UPLOAD_LOG.exists():
        return json.loads(UPLOAD_LOG.read_text(encoding="utf-8"))
    return {}


def save_upload_log(log):
    UPLOAD_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")


def get_available_accounts():
    return sorted([d.name for d in PROFILES_DIR.iterdir() if d.is_dir()])


def _append_index(filename, drive_folder, account, link=None):
    """Adiciona entrada no índice legível (markdown)."""
    if not INDEX_FILE.exists():
        INDEX_FILE.write_text("# Drive Backup — Índice de Vídeos\n\n| Arquivo | Pasta Drive | Conta | Link | Data |\n|---|---|---|---|---|\n", encoding="utf-8")
    link_col = f"[download]({link})" if link else "—"
    line = f"| {filename} | {drive_folder} | {account} | {link_col} | {time.strftime('%Y-%m-%d %H:%M')} |\n"
    with open(INDEX_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def infer_drive_path(file_path):
    """Infere o caminho no Drive a partir do path local do vídeo."""
    fp = Path(file_path).resolve()
    parts = fp.parts
    for i, part in enumerate(parts):
        if part == "videos" and i + 2 < len(parts):
            obra = parts[i + 1]
            rest = "/".join(parts[i + 2: -1])
            return f"{DEFAULT_DRIVE_ROOT}/{obra}/{rest}"
    return f"{DEFAULT_DRIVE_ROOT}/{fp.parent.name}"


def launch_chrome(account):
    """Lança Chrome com perfil e retorna (process, port). Não mata Chrome existente."""
    profile = str(get_profile_dir(account))
    port = 9900  # porta fixa pra upload, não conflita com engagement (9301-9347)

    import urllib.request
    # Verifica se a porta já está em uso
    for try_port in (9900, 9901, 9902):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{try_port}/json/version", timeout=2)
            continue  # porta em uso
        except Exception:
            port = try_port
            break

    proc = subprocess.Popen([
        CHROME_PATH, f"--user-data-dir={profile}", f"--remote-debugging-port={port}",
        "--no-first-run", "--no-default-browser-check", "--new-window",
        "--js-flags=--max-old-space-size=256",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Espera o CDP ficar pronto
    for attempt in range(20):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2)
            print(f"  Chrome CDP pronto na porta {port} (tentativa {attempt+1})")
            return proc, port
        except Exception:
            # Verifica se o processo morreu (perfil com lock)
            if proc.poll() is not None:
                raise RuntimeError(
                    f"Chrome não iniciou — perfil '{account}' provavelmente está com lock "
                    f"(em uso por outra instância). Tente outra conta."
                )

    proc.kill()
    raise RuntimeError(f"Chrome não respondeu na porta {port} após 20s")


def ensure_drive_folder(page, folder_path):
    """Navega/cria pastas no Drive. Retorna quando está na pasta final."""
    parts = [p for p in folder_path.split("/") if p]

    page.goto("https://drive.google.com/drive/my-drive", timeout=30000, wait_until="domcontentloaded")
    time.sleep(4)

    for folder_name in parts:
        found = False
        # Busca a pasta na listagem
        rows = page.query_selector_all(f'div[data-tooltip="{folder_name}"]')
        if not rows:
            # Tenta por texto exato em spans
            try:
                loc = page.locator(f'div[role="gridcell"] span:text-is("{folder_name}")')
                if loc.count() > 0:
                    rows = [loc.first]
            except Exception:
                pass

        if rows:
            el = rows[0]
            el.dblclick()
            time.sleep(3)
            found = True

        if not found:
            print(f"  Criando pasta: {folder_name}")
            _create_folder_drive(page, folder_name)
            time.sleep(2)
            # Entrar na pasta criada
            rows = page.query_selector_all(f'div[data-tooltip="{folder_name}"]')
            if rows:
                rows[0].dblclick()
                time.sleep(3)
            else:
                # Tenta refresh e buscar
                page.reload(wait_until="domcontentloaded")
                time.sleep(3)
                rows = page.query_selector_all(f'div[data-tooltip="{folder_name}"]')
                if rows:
                    rows[0].dblclick()
                    time.sleep(3)


def _create_folder_drive(page, name):
    """Cria pasta no Drive via menu Novo."""
    # Tenta via menu
    try:
        page.locator('button[aria-label="Novo"], button[aria-label="New"]').first.click()
        time.sleep(1.5)
        # O menu item contém "Nova pasta" ou "New folder" como substring
        menu = page.locator('div[role="menuitem"]')
        for i in range(menu.count()):
            text = menu.nth(i).inner_text(timeout=2000).lower()
            if "nova pasta" in text or "new folder" in text:
                menu.nth(i).click()
                break
        else:
            # Fecha menu e tenta atalho
            page.keyboard.press("Escape")
            time.sleep(0.5)
            page.keyboard.press("Alt+c")
            time.sleep(0.5)
            page.keyboard.press("f")
    except Exception:
        # Fallback: atalho direto
        page.keyboard.press("Escape")
        time.sleep(0.5)
        page.keyboard.press("Alt+c")
        time.sleep(0.5)
        page.keyboard.press("f")

    time.sleep(2)
    # Preencher nome no dialog
    try:
        dialog_input = page.locator('input[type="text"]').first
        if dialog_input.is_visible(timeout=3000):
            dialog_input.fill(name)
            time.sleep(0.5)
            page.keyboard.press("Enter")
            time.sleep(3)
    except Exception:
        pass


def upload_file(page, file_path):
    """Faz upload via file chooser do Drive. Retorna link compartilhável ou True."""
    abs_path = str(Path(file_path).resolve())
    size_mb = os.path.getsize(abs_path) / (1024 * 1024)

    try:
        with page.expect_file_chooser(timeout=10000) as fc_info:
            # Clicar em Novo → Carregar ficheiro/Upload file
            page.locator('button[aria-label="Novo"], button[aria-label="New"]').first.click()
            time.sleep(1.5)
            # Busca o item iterando (mais robusto que seletor fixo)
            menu = page.locator('div[role="menuitem"]')
            clicked = False
            for idx in range(menu.count()):
                try:
                    txt = menu.nth(idx).inner_text(timeout=1000).lower()
                    if "carregar ficheiro" in txt or "file upload" in txt or "upload de arquivo" in txt:
                        menu.nth(idx).click()
                        clicked = True
                        break
                except:
                    pass
            if not clicked:
                # Fecha e tenta atalho
                page.keyboard.press("Escape")
                time.sleep(0.5)
                page.keyboard.press("Alt+c")
                time.sleep(0.5)
                page.keyboard.press("u")
        file_chooser = fc_info.value
        file_chooser.set_files(abs_path)
    except Exception as e:
        # Fallback: tenta atalho Alt+C, U
        try:
            with page.expect_file_chooser(timeout=10000) as fc_info:
                page.keyboard.press("Escape")
                time.sleep(0.5)
                page.keyboard.press("Alt+c")
                time.sleep(0.5)
                page.keyboard.press("u")
            file_chooser = fc_info.value
            file_chooser.set_files(abs_path)
        except Exception as e2:
            raise RuntimeError(f"Não conseguiu abrir file chooser: {e2}")

    wait_time = max(60, int(size_mb * 3))
    print(f"  Uploading {Path(abs_path).name} ({size_mb:.1f} MB, timeout {wait_time}s)...")

    start = time.time()
    while (time.time() - start) < wait_time:
        try:
            text = page.locator("body").inner_text()
            low = text.lower()
            if any(x in low for x in ["upload concluído", "upload complete", "1 upload concluído",
                                       "carregamento concluído", "1 carregamento concluído"]):
                print("  Upload concluído!")
                time.sleep(2)
                # Tenta pegar link compartilhável
                link = _get_share_link(page, Path(abs_path).name)
                return link or True
        except Exception:
            pass
        time.sleep(5)

    print("  [WARN] Timeout — verificando se aparece na lista...")
    time.sleep(3)
    fname = Path(abs_path).stem
    if page.query_selector(f'div[data-tooltip*="{fname}"]'):
        print("  Arquivo visível na lista — provável sucesso")
        link = _get_share_link(page, Path(abs_path).name)
        return link or True
    return False


def _get_share_link(page, filename):
    """Tenta compartilhar o arquivo e pegar o link (qualquer pessoa com link)."""
    try:
        fname_stem = Path(filename).stem
        # Clica no arquivo
        file_el = page.query_selector(f'div[data-tooltip*="{fname_stem}"]')
        if not file_el:
            return None

        file_el.click()
        time.sleep(1)

        # Compartilhar: Ctrl+Shift+S ou via menu
        file_el.click(button="right")
        time.sleep(1.5)

        # Procura "Partilhar" ou "Compartilhar" ou "Share" no menu
        menu = page.locator('div[role="menuitem"]')
        share_clicked = False
        for i in range(menu.count()):
            try:
                txt = menu.nth(i).inner_text(timeout=1000).lower()
                if "partilh" in txt or "compartilh" in txt or "share" in txt:
                    if "link" not in txt:  # evita "copiar link" genérico
                        menu.nth(i).click()
                        share_clicked = True
                        break
            except:
                pass

        if not share_clicked:
            page.keyboard.press("Escape")
            return None

        time.sleep(3)

        # No dialog de compartilhamento, mudar pra "Qualquer pessoa com o link"
        # e copiar o link
        try:
            # Procura botão "Copiar link" / "Copy link" / "Obter link"
            link_btn = page.locator('button:has-text("Copiar ligação"), button:has-text("Copiar link"), button:has-text("Copy link"), button:has-text("Obter")')
            if link_btn.count() > 0:
                # Primeiro tenta mudar acesso pra "Qualquer pessoa com o link"
                restrict = page.locator('div:has-text("Restritos"), div:has-text("Restricted")')
                if restrict.count() > 0:
                    restrict.first.click()
                    time.sleep(1)
                    anyone = page.locator('li:has-text("Qualquer pessoa"), li:has-text("Anyone")')
                    if anyone.count() > 0:
                        anyone.first.click()
                        time.sleep(1)

                link_btn.first.click()
                time.sleep(1)

            # Extrair link da URL da página ou do clipboard
            # O Drive geralmente mostra o link no dialog
            link_input = page.locator('input[value*="drive.google.com"]')
            if link_input.count() > 0:
                link = link_input.first.get_attribute("value")
                print(f"  Link: {link}")
                page.keyboard.press("Escape")
                return link
        except Exception:
            pass

        # Fecha dialog
        page.keyboard.press("Escape")
        time.sleep(1)
        page.keyboard.press("Escape")

        # Fallback: monta link manualmente a partir do file ID na URL
        current_url = page.url
        if "/folders/" in current_url:
            # Não conseguiu o link individual, mas temos a pasta
            return None

    except Exception as e:
        print(f"  [WARN] Não conseguiu gerar link: {e}")
        try:
            page.keyboard.press("Escape")
        except:
            pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Upload de vídeos pro Google Drive")
    parser.add_argument("path", nargs="?", help="Arquivo ou pasta para upload")
    parser.add_argument("--conta", default="canalalucinaai", help="Nome da conta Google")
    parser.add_argument("--pasta-drive", default="", help="Caminho da pasta no Drive (auto-detecta se vazio)")
    parser.add_argument("--listar-contas", action="store_true", help="Lista contas disponíveis")
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que seria feito sem executar")
    args = parser.parse_args()

    if args.listar_contas or not args.path:
        print("Contas disponíveis (com chrome profile):")
        for acc in get_available_accounts():
            print(f"  {acc}")
        return

    if args.conta not in PORT_MAP:
        print(f"[ERRO] Conta '{args.conta}' não tem porta CDP configurada.")
        print(f"Contas válidas: {', '.join(sorted(PORT_MAP.keys())[:10])}...")
        sys.exit(1)

    target = Path(args.path)
    if not target.exists():
        print(f"[ERRO] Caminho não existe: {target}")
        sys.exit(1)

    if target.is_file():
        files = [target]
    else:
        files = sorted(target.rglob("*.mp4"))

    if not files:
        print("[ERRO] Nenhum vídeo encontrado")
        sys.exit(1)

    drive_path = args.pasta_drive or infer_drive_path(str(files[0]))

    print(f"Conta: {args.conta}")
    print(f"Arquivos: {len(files)}")
    print(f"Pasta Drive: {drive_path}")

    upload_log = load_upload_log()
    account_key = args.conta
    existing_files = upload_log.get(account_key, {}).get("files", [])
    # Suporta formato antigo (lista de strings) e novo (lista de dicts)
    uploaded_set = set()
    for entry in existing_files:
        if isinstance(entry, str):
            uploaded_set.add(entry)
        elif isinstance(entry, dict):
            uploaded_set.add(entry.get("path", ""))
    pending = [f for f in files if str(f.resolve()) not in uploaded_set]

    if not pending:
        print("Todos os arquivos já foram uploadados!")
        return

    print(f"Pendentes: {len(pending)}")
    total_mb = sum(f.stat().st_size for f in pending) / (1024**2)
    print(f"Total: {total_mb:.1f} MB")

    if args.dry_run:
        print("\n[DRY RUN] Arquivos que seriam uploadados:")
        for f in pending:
            print(f"  {f.name} ({f.stat().st_size / 1024**2:.1f} MB)")
        return

    from playwright.sync_api import sync_playwright

    print(f"\nLançando Chrome com perfil '{args.conta}'...")
    chrome_proc, port = launch_chrome(args.conta)

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            ctx = browser.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            print(f"Navegando pro Drive e criando pasta: {drive_path}")
            ensure_drive_folder(page, drive_path)

            # Refresh pra garantir que a listagem está limpa antes de uploads
            page.reload(wait_until="domcontentloaded")
            time.sleep(4)

            success = 0
            for i, f in enumerate(pending):
                print(f"\n[{i+1}/{len(pending)}] {f.name}")
                try:
                    result = upload_file(page, str(f))
                    if result:
                        success += 1
                        if account_key not in upload_log:
                            upload_log[account_key] = {"files": []}
                        entry = {
                            "path": str(f.resolve()),
                            "drive_folder": drive_path,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
                        }
                        if isinstance(result, str):
                            entry["link"] = result
                        upload_log[account_key]["files"].append(entry)
                        save_upload_log(upload_log)
                        _append_index(f.name, drive_path, account_key, result if isinstance(result, str) else None)
                    time.sleep(3)
                except Exception as e:
                    print(f"  [ERRO] {f.name}: {e}")

            print(f"\n{'='*50}")
            print(f"Resultado: {success}/{len(pending)} uploads OK")
            print(f"Índice: {INDEX_FILE}")
            browser.close()
    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            chrome_proc.kill()


if __name__ == "__main__":
    main()
