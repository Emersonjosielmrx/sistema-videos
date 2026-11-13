"""limpar_espaco.py — Limpa cache regenerável e move backups pro Drive.

Roda periodicamente para manter D:/logins-google enxuto.

Uso:
    python limpar_espaco.py                  # Só limpa cache (seguro, sem perder nada)
    python limpar_espaco.py --drive          # Limpa cache + envia backups pro Drive
    python limpar_espaco.py --dry-run        # Mostra o que faria sem fazer
    python limpar_espaco.py --drive --conta X # Usa conta X pro Drive (padrão: mundosolar1995)
"""
import argparse
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path

BASE = Path("D:/logins-google")

CACHE_DIRS = [
    "Cache",
    "Code Cache",
    "GPUCache",
    "Service Worker/ScriptCache",
    "Service Worker/CacheStorage",
]

BULK_REGEN_DIRS = [
    "BrowserMetrics",
    "optimization_guide_model_store",
    "WasmTtsEngine",
    "Safe Browsing",
    "OnDeviceHeadSuggestModel",
    "GrShaderCache",
    "ActorSafetyLists",
    "hyphen-data",
    "ZxcvbnData",
    "Download Service",
]

PROFILE_LOCATIONS = [
    BASE / "chrome-profiles",
    BASE / "cofre" / "perfis",
]

CHROME_SYSTEM = Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data"

PARA_DRIVE = {
    "prints": [
        BASE / "colab_prints",
        BASE / "kiro_prints",
        BASE / "yt_prints",
    ],
    "imagens": [
        "logs_aistudio_fabrica.png",
        "_diag_2031.png",
        "_diag_e4487017.png",
    ],
    "logs": [
        "kiro_creditos_rodada.log",
        "kiro_fila.log",
        "kiro_reconferir.log",
        "kiro_reconferir2.log",
        "yt_canais_rodada.log",
        "logar_fila_erros.txt",
        "logar_fila_saida.txt",
    ],
}


def fmt(size_bytes):
    if size_bytes >= 1 << 30:
        return f"{size_bytes / (1 << 30):.2f} GB"
    return f"{size_bytes / (1 << 20):.1f} MB"


def dir_size(path):
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total


def rm(path, dry_run=False):
    """Remove arquivo ou pasta, retorna bytes liberados."""
    if not path.exists():
        return 0
    size = path.stat().st_size if path.is_file() else dir_size(path)
    if dry_run:
        return size
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink()
    except OSError as e:
        print(f"  [ERRO] {path}: {e}")
        return 0
    return size


def em_uso(user_data_dir):
    """Chrome mantém o 'lockfile' aberto com bloqueio exclusivo enquanto roda."""
    lf = user_data_dir / "lockfile"
    if not lf.exists():
        return False
    try:
        with open(lf, "a"):
            return False
    except OSError:
        return True


PULADOS = []


def limpar_cache_perfis(location, dry_run=False):
    """Limpa cache e pastas regeneráveis de todos os perfis em um diretório."""
    if not location.exists():
        return 0
    total = 0
    for perfil in sorted(location.iterdir()):
        if not perfil.is_dir():
            continue
        if em_uso(perfil):
            PULADOS.append(perfil.name)
            continue
        profile_dirs = [perfil]
        for sub in ("Default", "Profile 1"):
            p = perfil / sub
            if p.exists():
                profile_dirs.append(p)

        for pdir in profile_dirs:
            for cache_name in CACHE_DIRS:
                cache_path = pdir / cache_name
                s = rm(cache_path, dry_run)
                if s > 0:
                    total += s

        for bulk_name in BULK_REGEN_DIRS:
            bulk_path = perfil / bulk_name
            s = rm(bulk_path, dry_run)
            if s > 0:
                total += s
    return total


def limpar_cache_sistema(dry_run=False):
    """Limpa cache dos perfis do Chrome do sistema."""
    if not CHROME_SYSTEM.exists():
        return 0
    if em_uso(CHROME_SYSTEM):
        PULADOS.append("Chrome do sistema (aberto)")
        return 0
    total = 0
    for item in sorted(CHROME_SYSTEM.iterdir()):
        if not item.is_dir():
            continue
        if not (item.name == "Default" or item.name.startswith("Profile ")):
            continue
        for cache_name in CACHE_DIRS:
            cache_path = item / cache_name
            s = rm(cache_path, dry_run)
            if s > 0:
                total += s
    for bulk_name in BULK_REGEN_DIRS:
        bulk_path = CHROME_SYSTEM / bulk_name
        s = rm(bulk_path, dry_run)
        if s > 0:
            total += s
    return total


def limpar_temporarios(dry_run=False):
    """Só o que é 100% descartável; o resto vai pro Drive."""
    total = 0
    for p in [BASE / "__pycache__"]:
        total += rm(p, dry_run)
    vazia = BASE / "chrome-profiles-new"
    if vazia.exists() and not any(vazia.iterdir()) and not dry_run:
        vazia.rmdir()
    return total


def pastas_duvidosas():
    """Pastas que podem ter valor: vão zipadas pro Drive antes de sair do disco."""
    itens = []
    rem = BASE / "cofre" / "_removidos"
    if rem.exists() and any(rem.iterdir()):
        itens.append(rem)
    itens += sorted(p for p in (BASE / "cofre" / "perfis").glob("*.bkp_*") if p.is_dir())
    return itens


def upload_para_drive(conta, dry_run=False):
    """Envia prints/imagens/docs pro Drive usando drive_upload_api.py."""
    try:
        from google.oauth2.credentials import Credentials  # noqa: F811
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        print("  [ERRO] google-api-python-client não instalado. Rode: pip install google-api-python-client google-auth-oauthlib")
        return 0

    tokens_dir = BASE / "drive_tokens"
    token_path = tokens_dir / f"{conta}.json"
    if not token_path.exists():
        print(f"  [ERRO] Token não encontrado: {token_path}")
        print(f"  Rode: python drive_auth.py {conta}@gmail.com")
        return 0

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

    service = build("drive", "v3", credentials=creds)

    dia = time.strftime("%Y-%m-%d")
    raiz = f"logins-google-backup/{dia}"
    folder_id = _get_or_create_folder(service, "logins-google-backup")
    folder_id = _get_or_create_folder(service, dia, parent_id=folder_id)

    # (arquivo local, subpasta no Drive, o que apagar depois do upload)
    fila = []
    for prints_dir in PARA_DRIVE["prints"]:
        if prints_dir.exists():
            fila += [(f, prints_dir.name, f) for f in sorted(prints_dir.iterdir()) if f.is_file()]
    for nome in PARA_DRIVE["imagens"] + PARA_DRIVE["logs"]:
        f = BASE / nome
        if f.exists():
            fila.append((f, "", f))
    tmp = BASE / "_zip_tmp"
    for pasta in pastas_duvidosas():
        if dry_run:
            fila.append((pasta, "pastas", pasta))
            continue
        tmp.mkdir(exist_ok=True)
        z = tmp / f"{pasta.name}.zip"
        # strict_timestamps=False: perfis do Chrome têm arquivos com data < 1980
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED, strict_timestamps=False) as zf:
            for f in pasta.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(pasta))
        fila.append((z, "pastas", pasta))

    total = 0
    subpastas = {"": folder_id}
    for local, sub, apagar in fila:
        tam = dir_size(local) if local.is_dir() else local.stat().st_size
        destino = f"{raiz}/{sub + '/' if sub else ''}{local.name}"
        if dry_run:
            print(f"  [DRY-RUN] {apagar} -> {destino}")
            total += tam
            continue
        if sub not in subpastas:
            subpastas[sub] = _get_or_create_folder(service, sub, parent_id=folder_id)
        try:
            fid = _upload_file(service, local, subpastas[sub])
        except Exception as e:
            print(f"  [ERRO] {local.name}: {e} (mantido no disco)")
            continue
        registrar(dia, apagar, destino, tam, conta, fid)
        rm(apagar)
        if local != apagar:
            local.unlink()
        total += tam
        print(f"  ✓ {apagar.relative_to(BASE)} -> {destino}")

    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    return total


REGISTRO = BASE / "DRIVE_MOVIDOS.md"


def registrar(dia, local, destino, tam, conta, fid):
    if not REGISTRO.exists():
        REGISTRO.write_text(
            "# Arquivos movidos para o Google Drive\n\n"
            "Gerado por limpar_espaco.py. Cada linha é algo que SAIU do disco e está no Drive.\n"
            "Pastas foram enviadas como .zip.\n\n"
            "| Data | Caminho original | No Drive | Tamanho | Conta | Link |\n|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    link = f"https://drive.google.com/file/d/{fid}/view"
    with open(REGISTRO, "a", encoding="utf-8") as f:
        f.write(f"| {dia} | {local} | {destino} | {fmt(tam)} | {conta} | [abrir]({link}) |\n")


def _exec(req, tentativas=8):
    """O client ID público do rclone é compartilhado e estoura cota por minuto: espera e tenta de novo."""
    from googleapiclient.errors import HttpError
    for i in range(tentativas):
        try:
            return req.execute()
        except HttpError as e:
            if e.resp.status not in (403, 429, 500, 503) or i == tentativas - 1:
                raise
            espera = min(60, 5 * 2 ** i)
            print(f"  [cota do Google] aguardando {espera}s...")
            time.sleep(espera)


def _get_or_create_folder(service, name, parent_id=None):
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    results = _exec(service.files().list(q=q, spaces="drive", fields="files(id)"))
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        body["parents"] = [parent_id]
    folder = _exec(service.files().create(body=body, fields="id"))
    return folder["id"]


def _upload_file(service, local_path, parent_id):
    from googleapiclient.http import MediaFileUpload
    media = MediaFileUpload(str(local_path), resumable=True)
    body = {"name": local_path.name, "parents": [parent_id]}
    return _exec(service.files().create(body=body, media_body=media, fields="id"))["id"]


def main():
    parser = argparse.ArgumentParser(description="Limpa cache e move backups pro Drive")
    parser.add_argument("--drive", action="store_true", help="Também envia backups pro Drive")
    parser.add_argument("--conta", default="mundosolar1995", help="Conta do Drive (padrão: mundosolar1995)")
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que faria sem executar")
    args = parser.parse_args()

    if args.dry_run:
        print("=== MODO DRY-RUN (nada será alterado) ===\n")

    print("=== 1. CACHE DO CHROME (SISTEMA) ===")
    s1 = limpar_cache_sistema(args.dry_run)
    print(f"  {'Liberaria' if args.dry_run else 'Liberado'}: {fmt(s1)}")

    print("\n=== 2. CACHE EM chrome-profiles ===")
    s2 = limpar_cache_perfis(PROFILE_LOCATIONS[0], args.dry_run)
    print(f"  {'Liberaria' if args.dry_run else 'Liberado'}: {fmt(s2)}")

    print("\n=== 3. CACHE NO COFRE ===")
    s3 = limpar_cache_perfis(PROFILE_LOCATIONS[1], args.dry_run)
    print(f"  {'Liberaria' if args.dry_run else 'Liberado'}: {fmt(s3)}")

    print("\n=== 4. TEMPORÁRIOS (__pycache__) ===")
    s4 = limpar_temporarios(args.dry_run)
    print(f"  {'Liberaria' if args.dry_run else 'Liberado'}: {fmt(s4)}")

    total_cache = s1 + s2 + s3 + s4

    total_drive = 0
    if args.drive:
        print(f"\n=== 5. UPLOAD PRO DRIVE (conta: {args.conta}) ===")
        total_drive = upload_para_drive(args.conta, args.dry_run)
        if total_drive > 0:
            print(f"  {'Enviaria' if args.dry_run else 'Enviado'}: {fmt(total_drive)}")
        else:
            print("  Nada para enviar.")

    if PULADOS:
        print(f"\nPulados por estarem abertos ({len(PULADOS)}): {', '.join(PULADOS)}")
    print(f"\n{'=' * 40}")
    verb = "Liberaria" if args.dry_run else "Liberado"
    print(f"TOTAL {verb}: {fmt(total_cache + total_drive)}")
    print(f"  Cache/temporários: {fmt(total_cache)}")
    if args.drive:
        print(f"  Movido pro Drive:  {fmt(total_drive)}")


if __name__ == "__main__":
    main()
