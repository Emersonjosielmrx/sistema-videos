# prioridade_vscode.ps1 — 15/11 dona: "deixar o PC1 o máximo livre para o VS Code, com prioridade máxima".
# A cada 2 min (tarefa PrioridadeVSCode, oculta): VS Code + Claude Code em ALTA; render/IA pesados do PC1 em
# ABAIXO DO NORMAL (continuam rodando, mas cedem CPU quando o VS Code precisa). Desligar: apagar a tarefa ou
# criar o arquivo D:\video-fila\PRIORIDADE_VSCODE_OFF.
if (Test-Path 'D:\video-fila\PRIORIDADE_VSCODE_OFF') { exit }
$alta = 'Code','claude'
$baixa = 'ffmpeg','ffprobe','gera_imagem'
foreach ($p in Get-Process -Name $alta -ErrorAction SilentlyContinue) {
    try { if ($p.PriorityClass -ne 'High') { $p.PriorityClass = 'High' } } catch {}
}
foreach ($p in Get-Process -Name $baixa -ErrorAction SilentlyContinue) {
    try { if ($p.PriorityClass -ne 'BelowNormal') { $p.PriorityClass = 'BelowNormal' } } catch {}
}
# python/pythonw de PRODUÇÃO (render, imagem, pilha) também cedem; os do Claude/VS Code (MCP, pylance) não
$pesados = 'anime_auto|anime-pipeline|encher_pilha|gera_imagem|parceiro_diario|capar_shorts|capa_ia_anime|cron_gerar_video|montar|vozes_isolar|separar_trilha|whisper|demucs|melhores_cortes|rodizio_longos'
Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='pythonw.exe'" | Where-Object { $_.CommandLine -match $pesados } | ForEach-Object {
    try { $p = Get-Process -Id $_.ProcessId -ErrorAction Stop; if ($p.PriorityClass -ne 'BelowNormal') { $p.PriorityClass = 'BelowNormal' } } catch {}
}
