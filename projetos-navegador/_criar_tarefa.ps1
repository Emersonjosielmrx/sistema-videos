# ============================================================
# _criar_tarefa.ps1 — Cria a ÚNICA tarefa agendada do MegaEngage
# ============================================================
# Tarefa "MegaEngageMonitor": roda _monitor_agent.ps1 que mantém o bot vivo.
# Gatilhos:
#   - Ao fazer logon (PC ligou / usuária entrou) -> garante bot no ar.
#   - A cada 12 min por 7 dias -> relança se cair, deduplica, limpa dead_accounts.
# Expira em 7 dias (depois disso para de monitorar sozinha).
#
# IMPORTANTE: deve existir SÓ ESTA tarefa cuidando do bot. Se criar outra
# (ex: MegaEngageBot) elas competem e sobem instâncias duplicadas.
# ============================================================
$ErrorActionPreference = "Stop"

$taskName = "MegaEngageMonitor"
$ps1 = "D:\projetos-navegador\_monitor_agent.ps1"

# Remove qualquer tarefa antiga concorrente
Unregister-ScheduledTask -TaskName "MegaEngageMonitor" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "MegaEngageBot"     -Confirm:$false -ErrorAction SilentlyContinue

# Ação: rodar o monitor via powershell (janela oculta)
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ps1`""

$now = Get-Date

# Gatilho 1: ao logon
$trigLogon = New-ScheduledTaskTrigger -AtLogOn

# Gatilho 2: a cada 12 min por 7 dias
$trigRepeat = New-ScheduledTaskTrigger -Once -At $now `
    -RepetitionInterval (New-TimeSpan -Minutes 12) `
    -RepetitionDuration (New-TimeSpan -Days 7)

# Expira em 7 dias
$trigLogon.EndBoundary  = $now.AddDays(7).ToString("s")
$trigRepeat.EndBoundary = $now.AddDays(7).ToString("s")

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigLogon, $trigRepeat `
    -Settings $settings `
    -Principal $principal `
    -Description "Monitor unico do MegaEngage: relanca/deduplica/limpa. Expira em $($now.AddDays(7).ToString('dd/MM/yyyy'))." | Out-Null

Write-Host "OK: tarefa '$taskName' criada. Expira em $($now.AddDays(7).ToString('dd/MM/yyyy HH:mm'))."
