# -*- coding: utf-8 -*-
"""instalar_pc2_cortes.py — Cortes (Shorts de parceiro COM voz clonada) no PC2 (dono 26/10/2026: "deixe o outro PC
apto a rodar os cortes..."). Reusa os passos do instalar_pc3.py; muda só o que o PC2 tem diferente: o "subst D: C:\\"
(o .pth do venv do recap faz) em vez de junções no D:, e o venv já existe (C:\\Python313).

    python instalar_pc2_cortes.py            # tudo
    python instalar_pc2_cortes.py <passo>    # pastas, codigo, segredos, voz, vozes, modelos, assets, venv, testar
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import instalar_pc3 as ip  # noqa: E402

ip.HOST = "pc2"
ip.LOG = Path(__file__).resolve().parent / "logs" / "instalar_pc2_cortes.log"
FEITOS = Path(__file__).resolve().parent / "estado" / "instalar_pc2_cortes.json"


def passo_pastas():
    ip.log("pastas no PC2 (D: = subst de C:, o código acha D:\\recapd-ambientes\\producao pela junção)")
    print(ip.ps(r"""
New-Item -ItemType Directory -Force C:\recapd-e-animes\logs, C:\recapd-e-animes\workspace\anime, 'C:\hipercool-materiais\animes recap\shorts', C:\hipercool-materiais\videos_voz_clonada, C:\hipercool-materiais\anime, C:\recapd-ambientes | Out-Null
if (-not (Test-Path C:\recapd-ambientes\producao)) { cmd /c mklink /J C:\recapd-ambientes\producao C:\recapd-e-animes | Out-Null }
"C:\recapd-ambientes\producao -> " + (Get-Item C:\recapd-ambientes\producao).Target
"""))


def passo_venv():
    ip.log("venv do Cortes no PC2 (já existe: C:\\Python313) — só os pacotes")
    print(ip.ps(rf"""
& C:\recapd-e-animes\venv\Scripts\python.exe -m pip install --disable-pip-version-check -q {' '.join(ip.PACOTES)} 2>&1 | Select-Object -Last 5
& C:\recapd-e-animes\venv\Scripts\python.exe -c "import edge_tts, cv2, numpy, PIL; print('venv ok')"
& C:\hipercool-materiais\python\venv_vozes\Scripts\python.exe -c "import torch; print('venv_vozes ok, torch', torch.__version__)"
""", timeout=3600))


def passo_testar():
    ip.log("teste: imports do pipeline no PC2")
    print(ip.ps(r"""
cd C:\recapd-e-animes\bin
& C:\recapd-e-animes\venv\Scripts\python.exe -X utf8 -c "import os, shutil, anime_auto, anime_tts, anime_voz_clonada as v; print('pipeline importa ok | D:', os.path.exists('D:/hipercool-materiais/python/venv_vozes/Scripts/python.exe'), '| ffmpeg', shutil.which('ffmpeg')); print('vozes no PC2:', len(v._ordem()))"
"livre C: {0:N1} GB" -f ((Get-PSDrive C).Free/1GB)
""", timeout=600))


def mandar(origem, itens, destino, excluir=()):
    """Igual ao do PC3, mas o ssh do PC2 já cai no cmd: sem o "cmd /c" embrulhando (as aspas aninhadas quebravam)."""
    import subprocess
    import time
    ini = time.time()
    exc = [f"--exclude={e}" for e in excluir]
    t = subprocess.Popen([ip.TAR, "-cf", "-", *exc, "-C", str(origem), *itens], stdout=subprocess.PIPE,
                         creationflags=ip._SEM_JANELA)
    win = destino.replace("/", "\\")
    r = subprocess.run([ip.SSH, "-o", "BatchMode=yes", ip.HOST, f'(if not exist "{win}" mkdir "{win}") & tar -xf - -C "{destino}"'],
                       stdin=t.stdout, capture_output=True, timeout=6 * 3600, creationflags=ip._SEM_JANELA)
    t.stdout.close()
    ok = t.wait() == 0 and r.returncode == 0
    ip.log(f"  {'ok' if ok else 'FALHOU'} {origem} [{', '.join(itens)[:120]}] -> {destino} ({time.time() - ini:.0f} s)"
           + ("" if ok else f" {(r.stderr or b'').decode('utf-8', 'replace')[-300:]}"))
    if not ok:
        raise RuntimeError(f"cópia falhou: {origem} -> {destino}")


ip.mandar = mandar
PASSOS = dict(ip.PASSOS, pastas=passo_pastas, venv=passo_venv, testar=passo_testar)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        feitos = json.loads(FEITOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        feitos = {}
    pedidos = sys.argv[1:] or [p for p in PASSOS if p not in feitos]
    for p in pedidos:
        PASSOS[p]()
        feitos[p] = datetime.now().isoformat(timespec="seconds")
        FEITOS.parent.mkdir(exist_ok=True)
        FEITOS.write_text(json.dumps(feitos, ensure_ascii=False, indent=1), encoding="utf-8")
    ip.log("fim: " + ", ".join(pedidos))


if __name__ == "__main__":
    main()
