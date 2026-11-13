r"""matar_travados.py — mata render TRAVADO sozinho (12/11, dona: "sempre pode matar só render travado; tem que ter um
sistema pra isso, pra não depender da IA"). Antes o maquinas.py só MARCAVA "render travado há mais de 6 h (não conta)".

Travado = processo RAIZ de render (hiper-pipeline / hiper-longo / anime-pipeline / anime_auto, o mesmo critério do
maquinas.py) vivo há mais de TRAVADO_H (6 h) E com CPU praticamente parada: a árvore dele (raiz + filhos: ffmpeg,
python) gastou menos de CPU_MIN_S (5 s) de CPU em 2 min de observação. Render longo que ainda trabalha gasta muito mais
que isso, então NUNCA é morto. Mata a árvore inteira (taskkill /T) e registra.

Máquinas: PC1 e PC2 e desktop (Windows). Não mexe em pythonw nem no que não for render; 1 ssh por máquina (sem rajada).
Tarefa MatarTravados de hora em hora. MATAR_TRAVADOS=0 desliga.

    python matar_travados.py            # mata o que estiver travado
    python matar_travados.py --ver      # só mostra
"""
import base64
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOG = BASE / "estado" / "matar_travados.log"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe" if Path(r"C:\Program Files\Git\usr\bin\ssh.exe").exists() else "ssh"
TRAVADO_H = 6
CPU_MIN_S = 5
MAQS = ("pc1", "pc2", "desktop")

PS = r"""
$rp = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'hiper-pipeline|hiper-longo|anime-pipeline|anime_auto' -and $_.CommandLine -notmatch 'abastecedor_kaggle' })
$ids = @($rp | ForEach-Object { $_.ProcessId })
$raiz = @($rp | Where-Object { $ids -notcontains $_.ParentProcessId -and ((Get-Date) - $_.CreationDate).TotalHours -ge __H__ })
function Arvore($p) { $f = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$p" | ForEach-Object { $_.ProcessId }); @($p) + @($f | ForEach-Object { Arvore $_ }) }
function CpuS($lista) { ($lista | ForEach-Object { (Get-Process -Id $_ -ErrorAction SilentlyContinue).CPU } | Measure-Object -Sum).Sum }
$cand = @()
foreach ($r in $raiz) { $a = Arvore $r.ProcessId; $cand += ,@($r, $a, (CpuS $a)) }
if ($cand.Count) { Start-Sleep 120 }
foreach ($c in $cand) {
  $r = $c[0]; $a = $c[1]; $gasto = (CpuS $a) - $c[2]
  $h = [math]::Round(((Get-Date) - $r.CreationDate).TotalHours, 1)
  $cmd = $r.CommandLine.Substring(0, [Math]::Min(140, $r.CommandLine.Length))
  if ($gasto -lt __CPU__) {
    if ('__MATAR__' -eq '1') { taskkill /PID $r.ProcessId /T /F | Out-Null; $acao = 'MATOU' } else { $acao = 'MATARIA' }
  } else { $acao = 'trabalhando' }
  Write-Output ("$acao|$($r.ProcessId)|$h|$([math]::Round($gasto,1))|$cmd")
}
Write-Output "FIM"
"""


def rodar(host, matar):
    s = PS.replace("__H__", str(TRAVADO_H)).replace("__CPU__", str(CPU_MIN_S)).replace("__MATAR__", "1" if matar else "0")
    enc = base64.b64encode(s.encode("utf-16-le")).decode()
    cmd = ["powershell", "-NoProfile", "-EncodedCommand", enc]
    if host != "pc1":
        cmd = [SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", host, " ".join(cmd)]
    r = subprocess.run(cmd, capture_output=True, timeout=400, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return [l for l in (r.stdout or b"").decode("utf-8", "replace").splitlines() if "|" in l]


def main(matar):
    if os.environ.get("MATAR_TRAVADOS", "1") == "0":
        return
    for h in MAQS:
        try:
            linhas = rodar(h, matar)
        except Exception as e:  # noqa: BLE001
            linhas = [f"erro|{type(e).__name__}"]
        for l in linhas:
            msg = f"[{datetime.now():%d/%m %H:%M}] {h}: {l}"
            print(msg, flush=True)
            if l.startswith("MATOU"):
                with LOG.open("a", encoding="utf-8") as f:
                    f.write(msg + "\n")


if __name__ == "__main__":
    main("--ver" not in sys.argv)
