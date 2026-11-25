# prioridade_vscode.ps1 — 15/11 dona: "deixar o PC1 o máximo livre para o VS Code, com prioridade máxima".
# A cada 2 min (tarefa PrioridadeVSCode, oculta): VS Code + Claude Code em ALTA; TODA a produção em ABAIXO DO NORMAL
# (continua rodando, mas cede CPU quando o VS Code/chat precisa). Desligar: apagar a tarefa ou criar o arquivo
# D:\video-fila\PRIORIDADE_VSCODE_OFF.
# 24/11 (dona: "tá lento de novo ... faça os scripts para não acontecer de novo"): antes só alguns python de render
# cediam; os ~70 Chrome de automação, os ~150 python/pythonw e o rclone ficavam em Normal e disputavam a CPU com o VS
# Code. Agora cede tudo que não é do VS Code/Claude, e o WMI tem prazo (sem prazo a rodada ficava presa).
if (Test-Path 'D:\video-fila\PRIORIDADE_VSCODE_OFF') { exit }
$log = 'D:\video-fila\logs\prioridade_vscode.log'

# rodada anterior presa (> 3 min) = fecha
Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $PID -and $_.StartTime -and ((Get-Date) - $_.StartTime).TotalMinutes -gt 3 } | ForEach-Object {
    $cl = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -OperationTimeoutSec 10 -ErrorAction SilentlyContinue).CommandLine
    if ($cl -match 'prioridade_vscode\.ps1') { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }
}

function Por($p, $classe) { try { if ($p.PriorityClass -ne $classe) { $p.PriorityClass = $classe; return 1 } } catch {} ; 0 }
$n = 0

# 1. ALTA: VS Code e Claude Code
foreach ($p in Get-Process -Name 'Code', 'claude' -ErrorAction SilentlyContinue) { $n += Por $p 'High' }
# 25/11 (dona: "prioridade máxima na digitação e no mouse, mesmo lento não demorar digitar ou levar o mouse"):
# o caminho do teclado/mouse até a tela — desenho da tela (dwm), barra/janelas (explorer), teclado/IME (ctfmon,
# TextInputHost), touchpad Elan e o gancho do ditado (vibe-hotkey: gancho lento = cada tecla espera).
foreach ($p in Get-Process -Name 'dwm', 'explorer', 'ctfmon', 'TextInputHost', 'ElanTouchXiSvc', 'ETDCtrl', 'ETDTouch', 'SynTPEnh' -ErrorAction SilentlyContinue) { $n += Por $p 'High' }
try { $hk = [int](Get-Content 'C:\Users\Haylla\.claude\.vibe-hotkey-pid' -Raw).Trim(); $p = Get-Process -Id $hk -ErrorAction Stop; $n += Por $p 'High' } catch {}

# 2. BAIXA pelo nome (sem WMI): render e Drive
foreach ($p in Get-Process -Name 'ffmpeg', 'ffprobe', 'gera_imagem', 'rclone', 'yt-dlp' -ErrorAction SilentlyContinue) { $n += Por $p 'BelowNormal' }

# 3. BAIXA pela linha de comando (WMI com prazo)
try {
    $procs = Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='pythonw.exe' or Name='chrome.exe' or Name='node.exe'" -OperationTimeoutSec 45 -ErrorAction Stop
} catch { Add-Content $log ("{0:yyyy-MM-dd HH:mm} WMI nao respondeu em 45 s - so nomes aplicados" -f (Get-Date)); exit }
# do VS Code/Claude (extensões, MCP, pylance, depurador) — esses ficam como estão
$doEditor = '\\\.vscode|\\\.claude|claude-vscode|pylance|debugpy|\\mcp|mcp[-_]|language[-_]?server|jedi|ms-python|\\Microsoft VS Code\\'
foreach ($c in $procs) {
    $cl = "$($c.CommandLine)"
    if (-not $cl -or $cl -match $doEditor) { continue }
    if ($c.Name -eq 'chrome.exe' -and $cl -notmatch '--user-data-dir=') { continue }   # Chrome pessoal da dona
    if ($c.Name -eq 'node.exe' -and $cl -notmatch 'remotion|postador|tiktok|instagram|manhwa|hipercool|video') { continue }
    $p = Get-Process -Id $c.ProcessId -ErrorAction SilentlyContinue
    if ($p) { $n += Por $p 'BelowNormal' }
}
if ($n -gt 20) { Add-Content $log ("{0:yyyy-MM-dd HH:mm} {1} processos ajustados" -f (Get-Date), $n) }
