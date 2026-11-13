# opus55_assumir_botao.ps1 ON|OFF — botão "Opus 5.5 ASSUMIR" (24/10). Liga/desliga o modo em que o Opus 5.5 faz todos
# os papéis das melhorias enquanto houver cota Claude (fora a reserva da dona). Ver D:\video-fila\opus55.py.
param([Parameter(Mandatory = $true)][ValidateSet('ON', 'OFF')][string]$Modo)
$acao = if ($Modo -eq 'ON') { 'ligar' } else { 'desligar' }
$env:PYTHONUTF8 = '1'
$msg = (& 'D:\veo\venv\Scripts\python.exe' 'D:\video-fila\opus55.py' $acao 2>&1 | Out-String).Trim()
Add-Type -AssemblyName System.Windows.Forms
[void][System.Windows.Forms.MessageBox]::Show($msg, 'Opus 5.5 ASSUMIR')
