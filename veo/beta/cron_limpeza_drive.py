# -*- coding: utf-8 -*-
"""cron_limpeza_drive.py — libera disco MOVENDO para o Drive (nada e apagado sem copia).

1. Move a tmp do render (pos_producao/tmp/_montar_final, arquivos com mais de 2h) para o Drive.
2. Move os git bundles de D:\\veo para o Drive.
3. Move os perfis Chrome orfaos/duplicados para o Drive.

O rclone move so remove o arquivo local depois de confirmar a copia no Drive.

Uso:
    python cron_limpeza_drive.py              # roda tudo
    python cron_limpeza_drive.py --dry-run    # so mostra o que faria
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

BASE = Path(os.path.dirname(os.path.abspath(__file__)))
VEO_ROOT = BASE.parent
RCLONE = Path(r"D:\tools\rclone.exe")
DRIVE_ROOT = "manhwa-drive:veo_backups"  # nunca usar colab649 (dono, 26/10: Drive cheio e desativado)

TMP_RENDER = BASE / "pos_producao" / "tmp" / "_montar_final"
IDADE_MIN_S = 2 * 3600  # nao toca em arquivo de render em andamento
REGISTRO = VEO_ROOT / "MOVIDOS_PARA_DRIVE.md"
ZIP_TMP = VEO_ROOT / "_zip_para_drive"
_movidos = []  # (origem, destino no Drive, MB, detalhe)

PERFIS_ORFAOS = [
    BASE / "chrome_gen_nova_225153",
    BASE / "chrome_gen_nova_224751",
    BASE / "chrome_gen_conta7",
    BASE / "chrome_gen_conta8",
    VEO_ROOT / "beta$NEWPROF",
    BASE / "profiles" / "chrome_gen_nova_1786128712",
    BASE / "profiles" / "chrome_gen_nova_1786128902",
]

sys.path.insert(0, str(BASE))
try:
    import sem_janela  # noqa: F401
except ImportError:
    pass


def _log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [limpeza] {msg}", flush=True)


def _mb(paths):
    return sum(f.stat().st_size for f in paths) / (1024 * 1024)


def _rclone(*args, dry_run=False):
    if dry_run:
        _log(f"  [DRY] rclone {' '.join(args)}")
        return True
    try:
        r = subprocess.run([str(RCLONE), *args, "--stats-log-level", "NOTICE"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=3600)
    except subprocess.TimeoutExpired:
        _log("  ERRO rclone: timeout 1h")
        return False
    if r.returncode != 0:
        _log(f"  ERRO rclone (codigo {r.returncode}): {(r.stderr + r.stdout).strip()[-800:]}")
        return False
    return True


def mover_tmp_render(dry_run=False):
    limite = time.time() - IDADE_MIN_S
    arquivos = [f for f in TMP_RENDER.glob("*") if f.is_file() and f.stat().st_mtime < limite]
    if not arquivos:
        _log("tmp do render: nada para mover")
        return
    tamanhos = {f: f.stat().st_size for f in arquivos}
    _mb_total = sum(tamanhos.values()) / (1024 * 1024)
    _log(f"tmp do render: movendo {len(arquivos)} arquivo(s) ({_mb_total:.0f} MB)")
    lista = BASE / "logs" / "_lista_tmp_render.txt"
    lista.write_text("\n".join(f.name for f in arquivos), encoding="utf-8")
    try:
        ok = _rclone("move", str(TMP_RENDER), f"{DRIVE_ROOT}/render_tmp",
                     "--files-from", str(lista), dry_run=dry_run)
    finally:
        lista.unlink(missing_ok=True)
    # rclone move apaga cada arquivo assim que ele chega no Drive, mesmo se outros falharem
    movidos = arquivos if dry_run else [f for f in arquivos if not f.exists()]
    _log("  OK" if ok else f"  FALHA PARCIAL: {len(movidos)} de {len(arquivos)} movidos, o resto ficou no disco")
    if movidos:
        mb = _mb_total if dry_run else sum(tamanhos[f] for f in movidos) / (1024 * 1024)
        nomes = sorted(f.name for f in movidos)
        _movidos.append((str(TMP_RENDER), f"{DRIVE_ROOT}/render_tmp", mb,
                         f"{len(nomes)} arquivos:\n" + "\n".join(f"  - {n}" for n in nomes)))


def mover_backups(dry_run=False):
    bundles = sorted(VEO_ROOT.glob("*.bundle"))
    if not bundles:
        _log("backups: nada para mover")
        return
    for b in bundles:
        mb = _mb([b])
        _log(f"backup: movendo {b.name} ({mb:.0f} MB)")
        ok = _rclone("moveto", str(b), f"{DRIVE_ROOT}/git_bundles/{b.name}", dry_run=dry_run)
        _log("  OK" if ok else "  FALHA: arquivo ficou no disco")
        if ok:
            _movidos.append((str(b), f"{DRIVE_ROOT}/git_bundles/{b.name}", mb, "backup git"))


def mover_perfis(dry_run=False):
    for p in PERFIS_ORFAOS:
        if not p.exists():
            continue
        if p.is_symlink() or os.path.isjunction(p):
            _log(f"perfil: {p.name} e atalho para {os.readlink(p)} (perfil em uso), pulado")
            continue
        # perfil tem milhares de arquivos pequenos: o Drive sobe 1 zip muito mais rapido
        mb = _mb([f for f in p.rglob("*") if f.is_file()])
        destino = f"{DRIVE_ROOT}/perfis_chrome/{p.name}.zip"
        _log(f"perfil: compactando e movendo {p.name} ({mb:.0f} MB)")
        if dry_run:
            _rclone("moveto", f"{p.name}.zip", destino, dry_run=True)
            _movidos.append((str(p), destino, mb, "perfil Chrome compactado"))
            continue
        ZIP_TMP.mkdir(exist_ok=True)
        zip_path = ZIP_TMP / f"{p.name}.zip"
        try:
            # strict_timestamps=False: o Chrome tem arquivos com data anterior a 1980
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, strict_timestamps=False) as z:
                for f in p.rglob("*"):
                    if f.is_file():
                        z.write(f, f.relative_to(p))
        except (OSError, ValueError) as e:
            zip_path.unlink(missing_ok=True)
            _log(f"  FALHA ao compactar: {e}")
            continue
        ok = _rclone("moveto", str(zip_path), destino)
        if ok:
            shutil.rmtree(p)
            _log("  OK")
            _movidos.append((str(p), destino, mb,
                             f"perfil Chrome duplicado/sem uso, compactado. Restaurar: rclone copyto {destino} . e descompactar em {p}"))
        else:
            zip_path.unlink(missing_ok=True)
            _log("  FALHA: perfil continua no disco")


def registrar(dry_run=False):
    if not _movidos:
        _log("registro: nada foi movido, nada a anotar")
        return
    total = sum(m[2] for m in _movidos)
    linhas = [f"\n## {time.strftime('%Y-%m-%d %H:%M')}{' (SIMULACAO)' if dry_run else ''} — {total:.0f} MB movidos\n"]
    for origem, destino, mb, detalhe in _movidos:
        linhas.append(f"- **{origem}** -> `{destino}` ({mb:.0f} MB) — {detalhe}")
    if not REGISTRO.exists():
        linhas.insert(0, "# Movidos para o Drive\n\nGerado por beta/cron_limpeza_drive.py. "
                         "Para trazer algo de volta: D:\\tools\\rclone.exe move <destino> <origem>\n")
    if dry_run:
        _log("registro (simulacao, nao gravado):\n" + "\n".join(l.split("\n  - ")[0] for l in linhas))
        return
    with REGISTRO.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(linhas) + "\n")
    _log(f"registro: anotado em {REGISTRO}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="so mostra o que faria")
    dry = p.parse_args().dry_run

    if dry:
        _log("=== MODO DRY-RUN (nada sera alterado) ===")
    if not RCLONE.exists():
        _log(f"ERRO: rclone nao encontrado em {RCLONE}")
        return 1

    try:
        mover_tmp_render(dry_run=dry)
        mover_backups(dry_run=dry)
        mover_perfis(dry_run=dry)
    finally:
        registrar(dry_run=dry)
    _log("=== Concluido ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
