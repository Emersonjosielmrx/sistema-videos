"""limpar_workspace_maquinas.py — 23/11 dona: "por que postador-worker e recap de animes têm 12 e 23 GB no disco do
desktop? Não está sendo feita limpeza, só acumulando."

Causa: o desktop (e o PC2) renderizam Shorts em C:\\recapd-e-animes\\workspace\\anime\\<id>_<título>; o PC1 traz o
vídeo pronto e a pasta de lá NUNCA era apagada (só havia limpeza no PC2 e só com disco já baixo). O desktop chegou a
900 pastas / 23 GB e o C ficou com 1 GB (Chrome do TikTok não abria: "WinError 112 espaço insuficiente").

Regra (segura): pasta com mais de 24 h cujo id de 11 letras JÁ está num postar.json do PC1 (o Short chegou aqui) =
apaga. A que não chegou fica (o vigia/humano decide). Também apaga o CACHE do Chrome dos perfis
C:\\postador-worker\\perfis (Cache, Code Cache, GPUCache, GrShaderCache) — login/cookies ficam intactos.

    python limpar_workspace_maquinas.py            # desktop e pc2
    python limpar_workspace_maquinas.py --ensaio   # só conta
Tarefa do Windows LimparWorkspaceMaquinas (1x por dia, 05:30).
"""
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SHORTS = Path(r"D:\hipercool-materiais\animes recap\shorts")
LOG = Path(r"D:\video-fila\logs\limpar_workspace_maquinas.log")
MAQUINAS = ["desktop", "pc2"]
SSH, SCP = "ssh", "scp"
SEM_JANELA = 0x08000000

PS = r"""
$ensaio = '__ENSAIO__' -eq '1'
$ids = Get-Content C:\Users\Public\ids_no_pc1.txt | Where-Object { $_ }
$set = New-Object 'System.Collections.Generic.HashSet[string]'; foreach ($i in $ids) { [void]$set.Add($i) }
$lim=(Get-Date).AddHours(-24); $n=0; $b=0; $fica=0
$base='C:\recapd-e-animes\workspace\anime'
if (Test-Path $base) {
 Get-ChildItem $base -Directory | Where-Object { $_.LastWriteTime -lt $lim } | ForEach-Object {
  if ($set.Contains($_.Name.Substring(0,[Math]::Min(11,$_.Name.Length)))) {
    $b += (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    if (-not $ensaio) { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }; $n++ } else { $fica++ } } }
$c=0
if (Test-Path C:\postador-worker\perfis) {
 foreach ($nome in 'Cache','Code Cache','GPUCache','GrShaderCache') {
  Get-ChildItem C:\postador-worker\perfis -Recurse -Directory -Filter $nome -ErrorAction SilentlyContinue | ForEach-Object {
   $c += (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
   if (-not $ensaio) { Get-ChildItem $_.FullName -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue } } } }
"RESULT pastas=$n gb={0:N2} ficaram=$fica cache_gb={1:N2} c_livre={2:N1}" -f ($b/1GB), ($c/1GB), ((Get-PSDrive C).Free/1GB)
"""


def log(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    linha = f"[{datetime.now():%d/%m %H:%M}] {m}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def ids_no_pc1():
    ids = set()
    for pj in SHORTS.glob("*/postar.json"):
        try:
            ids.update(re.findall(r"[A-Za-z0-9_-]{11}", pj.read_text("utf-8", "ignore")))
        except OSError:
            pass
    return ids


def limpar(maq, ids, ensaio):
    with tempfile.TemporaryDirectory() as t:
        lista, ps = Path(t) / "ids_no_pc1.txt", Path(t) / "limpar_ws.ps1"
        lista.write_text("\n".join(sorted(ids)), "utf-8")
        ps.write_text(PS.replace("__ENSAIO__", "1" if ensaio else "0"), "utf-8")
        for arq in (lista, ps):
            r = subprocess.run([SCP, "-q", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", str(arq),
                                f"{maq}:C:/Users/Public/{arq.name}"], capture_output=True, timeout=120,
                               creationflags=SEM_JANELA)
            if r.returncode:
                log(f"{maq}: não copiei {arq.name} ({r.stderr.decode(errors='replace').strip()[-120:]})")
                return
    r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", maq,
                        "powershell -NoProfile -ExecutionPolicy Bypass -File C:\\Users\\Public\\limpar_ws.ps1"],
                       capture_output=True, timeout=1800, creationflags=SEM_JANELA)
    out = r.stdout.decode(errors="replace")
    m = re.search(r"RESULT .*", out)
    log(f"{maq}{' [ensaio]' if ensaio else ''}: {m.group(0) if m else 'sem resposta: ' + out.strip()[-150:]}")


if __name__ == "__main__":
    ensaio = "--ensaio" in sys.argv
    ids = ids_no_pc1()
    log(f"{len(ids)} ids de Shorts já no PC1")
    for maq in [a for a in sys.argv[1:] if not a.startswith("--")] or MAQUINAS:
        try:
            limpar(maq, ids, ensaio)
        except Exception as e:  # noqa: BLE001
            log(f"{maq}: {type(e).__name__}: {str(e)[:150]}")
