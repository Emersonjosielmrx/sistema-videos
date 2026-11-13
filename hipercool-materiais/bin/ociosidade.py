"""Quais dos 3 PCs estao livres para pegar trabalho pesado (render, Whisper local, troca de venv...).

- este PC e o pc2 (ssh pc2): livre = CPU media baixa e nenhum render (ffmpeg) rodando
- desktop (ssh desktop, i5 2 nucleos, onde o dono GRAVA): so ajuda se NAO tiver OBS nem editor/vibe code aberto
  (VS Code, Cursor, Antigravity, Windsurf, Claude) e ninguem mexendo no teclado/mouse ha IDLE_MIN; e so tarefa leve.

Uso: python ociosidade.py            -> tabela dos 3 PCs
     from ociosidade import livres   -> ["este", "pc2", ...] na ordem de preferencia
"""
import base64
import json
import subprocess
import sys

CPU_MAX = 35          # % media de CPU acima disso = ocupado
IDLE_MIN = 20         # desktop: minutos sem teclado/mouse
RENDER = {"ffmpeg"}
USO_HUMANO = {"obs64", "obs32", "obs", "code", "cursor", "antigravity", "windsurf", "claude"}
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"  # o ssh do Windows trava apos autenticar (17/10); o do Git nao
PCS = {"este": None, "pc2": "pc2", "desktop": "desktop"}

# roda no PC alvo; devolve JSON. Tempo sem input via GetLastInputInfo (so vale na sessao do usuario: via ssh
# pode vir vazio, entao no desktop o criterio forte e OBS/editor aberto)
_PS = r"""
$cpu = (Get-CimInstance Win32_Processor | Measure-Object LoadPercentage -Average).Average
$procs = @(Get-Process | ForEach-Object { $_.ProcessName.ToLower() } | Sort-Object -Unique)
$idle = $null
try {
Add-Type @'
using System; using System.Runtime.InteropServices;
public class LI { [StructLayout(LayoutKind.Sequential)] struct L { public uint s; public uint t; }
[DllImport("user32.dll")] static extern bool GetLastInputInfo(ref L l);
public static double Min() { L l = new L(); l.s = 8; if (!GetLastInputInfo(ref l)) return -1;
return (Environment.TickCount - (int)l.t) / 60000.0; } }
'@
$m = [LI]::Min(); if ($m -ge 0) { $idle = $m }
} catch {}
@{ cpu = $cpu; procs = $procs; idle_min = $idle } | ConvertTo-Json -Compress
"""


def _medir(host):
    enc = base64.b64encode(_PS.encode("utf-16-le")).decode()
    cmd = ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", enc]
    if host:
        cmd = [SSH, "-n", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", host] + cmd
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:  # noqa: BLE001  fora do ar / sem ssh = nao conta como livre
        return {"erro": str(e)[:120]}


def status(nome):
    """18/10 (unificação): a medida vem do medidor ÚNICO D:\\video-fila\\maquinas.py (mesmas regras pros 3 PCs: render
    rodando, CPU/RAM/disco, desktop com OBS/editor aberto ou teclado/mouse há menos de 20 min, vez reservada)."""
    if r"D:\video-fila" not in sys.path:
        sys.path.insert(0, r"D:\video-fila")
    import maquinas
    m = maquinas.medir({"este": "pc1"}.get(nome, nome))
    return {"pc": nome, "livre": bool(m.get("ocioso")), "motivo": m.get("motivo", ""), "cpu": m.get("cpu"),
            "leve": nome == "desktop"}


def livres():
    return [s["pc"] for s in map(status, PCS) if s["livre"]]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for s in map(status, PCS):
        print(f"{s['pc']:8} {'LIVRE' if s['livre'] else 'ocupado':8} {s['motivo']}" + (" (so tarefa leve)" if s.get("leve") else ""))
