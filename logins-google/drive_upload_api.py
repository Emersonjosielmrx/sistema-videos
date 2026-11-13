"""drive_upload_api.py — Upload pro Google Drive via API (sem browser).

Requer token gerado por drive_auth.py.

Uso:
    python drive_upload_api.py <arquivo_ou_pasta> [--conta <nome>] [--pasta-drive <caminho>]

Exemplos:
    python drive_upload_api.py "D:/hipercool-materiais/videos/the-meek-cat/cap05" --conta solarmundo195
    python drive_upload_api.py video.mp4 --conta solarmundo195 --pasta-drive "hipercool/meek-cat/cap05/normal"
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKENS_DIR = Path("D:/logins-google/drive_tokens")
UPLOAD_LOG = Path("D:/logins-google/drive_uploads.json")
INDEX_FILE = Path("D:/logins-google/drive_index.md")
DEFAULT_DRIVE_ROOT = "hipercool"


def load_credentials(account):
    token_path = TOKENS_DIR / f"{account}.json"
    if not token_path.exists():
        print(f"[ERRO] Token não encontrado: {token_path}")
        print(f"Rode primeiro: python drive_auth.py {account}@gmail.com")
        sys.exit(1)

    data = json.loads(token_path.read_text(encoding="utf-8"))
    creds = Credentials(
        token=data.get("token"),
        refresh_token=data["refresh_token"],
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data.get("scopes"),
    )

    if creds.expired or not creds.valid:
        creds.refresh(Request())
        data["token"] = creds.token
        token_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return creds


def get_or_create_folder(service, name, parent_id=None):
    """Busca ou cria pasta no Drive. Retorna folder ID."""
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, fields="files(id, name)", spaces="drive").execute()
    files = results.get("files", [])

    if files:
        return files[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(body=metadata, fields="id").execute()
    print(f"  Pasta criada: {name}")
    return folder["id"]


def ensure_folder_path(service, folder_path):
    """Cria hierarquia de pastas e retorna o ID da última."""
    parts = [p for p in folder_path.split("/") if p]
    parent_id = None
    for part in parts:
        parent_id = get_or_create_folder(service, part, parent_id)
    return parent_id


def upload_file(service, file_path, folder_id):
    """Upload de arquivo pro Drive. Retorna file ID."""
    fname = Path(file_path).name
    size_mb = os.path.getsize(file_path) / (1024 * 1024)

    metadata = {"name": fname}
    if folder_id:
        metadata["parents"] = [folder_id]

    media = MediaFileUpload(
        file_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024,  # 10MB chunks
    )

    print(f"  Uploading {fname} ({size_mb:.1f} MB)...")
    request = service.files().create(body=metadata, media_body=media, fields="id,webViewLink")

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"    {pct}%", end="\r")

    file_id = response["id"]
    link = response.get("webViewLink", "")
    print(f"  Concluído! ID: {file_id}")
    return file_id, link


def make_shareable(service, file_id):
    """Torna o arquivo acessível por qualquer pessoa com o link."""
    permission = {"type": "anyone", "role": "reader"}
    service.permissions().create(fileId=file_id, body=permission).execute()
    file_info = service.files().get(fileId=file_id, fields="webViewLink").execute()
    link = file_info.get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view")
    return link


def infer_drive_path(file_path):
    fp = Path(file_path).resolve()
    parts = fp.parts
    for i, part in enumerate(parts):
        if part == "videos" and i + 2 < len(parts):
            obra = parts[i + 1]
            rest = "/".join(parts[i + 2: -1])
            return f"{DEFAULT_DRIVE_ROOT}/{obra}/{rest}"
    return f"{DEFAULT_DRIVE_ROOT}/{fp.parent.name}"


def load_upload_log():
    if UPLOAD_LOG.exists():
        return json.loads(UPLOAD_LOG.read_text(encoding="utf-8"))
    return {}


def save_upload_log(log):
    UPLOAD_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")


def append_index(filename, drive_folder, account, link=None):
    if not INDEX_FILE.exists():
        INDEX_FILE.write_text(
            "# Drive Backup — Índice de Vídeos\n\n"
            "| Arquivo | Pasta Drive | Conta | Link | Data |\n"
            "|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    link_col = f"[download]({link})" if link else "—"
    line = f"| {filename} | {drive_folder} | {account} | {link_col} | {time.strftime('%Y-%m-%d %H:%M')} |\n"
    with open(INDEX_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def main():
    parser = argparse.ArgumentParser(description="Upload pro Google Drive via API")
    parser.add_argument("path", nargs="?", help="Arquivo ou pasta para upload")
    parser.add_argument("--conta", default="solarmundo195", help="Nome da conta")
    parser.add_argument("--pasta-drive", default="", help="Caminho no Drive (auto-detecta)")
    parser.add_argument("--share", action="store_true", default=True, help="Gerar link compartilhável")
    parser.add_argument("--dry-run", action="store_true", help="Mostra sem executar")
    parser.add_argument("--listar-contas", action="store_true", help="Lista tokens disponíveis")
    args = parser.parse_args()

    if args.listar_contas or not args.path:
        print("Tokens disponíveis:")
        for f in sorted(TOKENS_DIR.glob("*.json")):
            print(f"  {f.stem}")
        if not list(TOKENS_DIR.glob("*.json")):
            print("  (nenhum — rode drive_auth.py primeiro)")
        return

    target = Path(args.path)
    if not target.exists():
        print(f"[ERRO] Caminho não existe: {target}")
        sys.exit(1)

    if target.is_file():
        files = [target]
    else:
        files = sorted(target.rglob("*.mp4"))

    if not files:
        print("[ERRO] Nenhum vídeo .mp4 encontrado")
        sys.exit(1)

    drive_path = args.pasta_drive or infer_drive_path(str(files[0]))

    print(f"Conta: {args.conta}")
    print(f"Arquivos: {len(files)}")
    print(f"Pasta Drive: {drive_path}")

    upload_log = load_upload_log()
    account_key = args.conta
    existing = upload_log.get(account_key, {}).get("files", [])
    uploaded_set = set()
    for entry in existing:
        if isinstance(entry, str):
            uploaded_set.add(entry)
        elif isinstance(entry, dict):
            uploaded_set.add(entry.get("path", ""))
    pending = [f for f in files if str(f.resolve()) not in uploaded_set]

    if not pending:
        print("Todos já foram uploadados!")
        return

    total_mb = sum(f.stat().st_size for f in pending) / (1024**2)
    print(f"Pendentes: {len(pending)} ({total_mb:.1f} MB)")

    if args.dry_run:
        for f in pending:
            print(f"  {f.name} ({f.stat().st_size / 1024**2:.1f} MB)")
        return

    print(f"\nAutenticando...")
    creds = load_credentials(args.conta)
    service = build("drive", "v3", credentials=creds)

    print(f"Criando pastas: {drive_path}")
    folder_id = ensure_folder_path(service, drive_path)

    success = 0
    for i, f in enumerate(pending):
        print(f"\n[{i+1}/{len(pending)}] {f.name}")
        try:
            file_id, link = upload_file(service, str(f), folder_id)

            if args.share:
                link = make_shareable(service, file_id)
                print(f"  Link: {link}")

            success += 1
            if account_key not in upload_log:
                upload_log[account_key] = {"files": []}
            upload_log[account_key]["files"].append({
                "path": str(f.resolve()),
                "drive_folder": drive_path,
                "file_id": file_id,
                "link": link,
                "timestamp": time.strftime("%Y-%m-%d %H:%M"),
            })
            save_upload_log(upload_log)
            append_index(f.name, drive_path, account_key, link)

        except Exception as e:
            print(f"  [ERRO] {e}")

    print(f"\n{'='*50}")
    print(f"Resultado: {success}/{len(pending)} uploads OK")
    print(f"Índice: {INDEX_FILE}")


if __name__ == "__main__":
    main()
