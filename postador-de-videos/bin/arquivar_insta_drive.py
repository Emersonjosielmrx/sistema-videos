# -*- coding: utf-8 -*-
"""Instagram de TODAS as empresas/produtos: no PC só o que ainda vai ser postado (25/10, dono: "deve ficar só os pra
postar no dia ... isso tem que valer não só pro MS Energy, mas pra todos os produtos que fazemos no Instagram").

  carrosséis postados (D:\\video-fila\\carrosseis_marcas\\<conta>\\<pasta> com meta.postado) -> Drive
      manhwa-drive:empresas/<conta>/postados/<pasta>  (rclone move: só apaga daqui depois de subir inteiro)
  cache das pastas das empresas (D:\\video-fila\\empresas_cache) com mais de 2 dias -> apagado (o original está no
      Drive em empresas/<conta>/usados)
  MS Energy -> D:\\ms-energy\\bin\\arquivar_drive_ms.py (vídeos postados/antigos/crus, trechos)

Roda 1x/dia no fim do carrossel_marca --todas (tarefa Marcas_Carrossel). Manual: python arquivar_insta_drive.py [--ver]
"""
import json
import subprocess
import sys
import time
from pathlib import Path

RCLONE = r"D:\tools\rclone.exe"
CARR = Path(r"D:\video-fila\carrosseis_marcas")
CACHE = Path(r"D:\video-fila\empresas_cache")
REMOTO = "manhwa-drive:empresas"


def carrosseis(ver=False, log=print):
    n = mb = 0
    for meta in CARR.glob("*/*/meta.json"):
        try:
            m = json.loads(meta.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        if not m.get("postado"):
            continue  # ainda vai sair: fica
        pasta = meta.parent
        tam = sum(f.stat().st_size for f in pasta.rglob("*") if f.is_file())
        n, mb = n + 1, mb + tam / 2**20
        if ver:
            continue
        r = subprocess.run([RCLONE, "move", str(pasta), f"{REMOTO}/{m['conta']}/postados/{pasta.name}",
                            "--delete-empty-src-dirs"], capture_output=True, text=True, timeout=1800)
        if r.returncode:
            log(f"  [carrossel] {pasta}: falhou ({(r.stderr or '')[-150:]}) - fica no PC")
        else:
            try:
                pasta.rmdir()
            except OSError:
                pass
    log(f"[carrosséis postados] {n} pasta(s), {mb:.0f} MB -> {REMOTO}/<conta>/postados{' (só mostrando)' if ver else ''}")


def cache_empresas(ver=False, log=print):
    limite = time.time() - 2 * 86400
    velhos = [f for f in CACHE.rglob("*") if f.is_file() and f.stat().st_mtime < limite] if CACHE.exists() else []
    mb = sum(f.stat().st_size for f in velhos) / 2**20
    if not ver:
        for f in velhos:
            f.unlink()
    log(f"[cache das empresas] {len(velhos)} arquivo(s) com mais de 2 dias, {mb:.0f} MB "
        f"{'(só mostrando)' if ver else 'apagados (originais no Drive em usados/)'}")


def fotos_na_hora(ver=False, log=print):
    """Fotos que o Veo/clone criam na hora (D:\\veo\\fotos_na_hora) com mais de 2 dias -> Drive (dono 25/10: "as fotos
    feitas do Veo pros projetos devem estar só no Drive"). As recentes ficam: o prompt que voltou pra fila e o estoque
    do mesmo tema ainda podem usar."""
    src = r"D:\veo\fotos_na_hora"
    if ver:
        limite = time.time() - 2 * 86400
        velhos = [f for f in Path(src).rglob("*") if f.is_file() and f.stat().st_mtime < limite]
        log(f"[fotos na hora] {len(velhos)} com mais de 2 dias, {sum(f.stat().st_size for f in velhos) / 2**20:.0f} MB "
            "-> manhwa-drive:veo/fotos_na_hora (só mostrando)")
        return
    r = subprocess.run([RCLONE, "move", src, "manhwa-drive:veo/fotos_na_hora", "--min-age", "2d"],
                       capture_output=True, text=True, timeout=1800)
    log(f"[fotos na hora] com mais de 2 dias -> manhwa-drive:veo/fotos_na_hora: "
        f"{'ok' if r.returncode == 0 else 'FALHOU ' + (r.stderr or '')[-150:]}")


def tudo(ver=False, log=print):
    carrosseis(ver, log)
    cache_empresas(ver, log)
    fotos_na_hora(ver, log)
    try:
        sys.path.append(r"D:\ms-energy\bin")
        import arquivar_drive_ms
        if ver:
            arquivar_drive_ms.recortar_trechos(True, log)
            arquivar_drive_ms.arquivar(True, log)
        else:
            arquivar_drive_ms.arquivar_dia(log)
    except Exception as e:  # noqa: BLE001
        log(f"[ms-energy] falhou: {type(e).__name__}: {e}")


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tudo("--ver" in sys.argv)
