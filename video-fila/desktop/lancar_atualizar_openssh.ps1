# Manda atualizar_openssh.ps1 pro desktop e solta ele pelo WMI (sobrevive quando o sshd cai). O sshd 7.7 de la
# derruba o login de vez em quando: tenta ate entrar.
param([int]$Tentativas = 40)
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $aqui 'atualizar_openssh.ps1')))
$remoto = "`$d='C:\ProgramData\ssh\atualizar_openssh.ps1'; [IO.File]::WriteAllBytes(`$d,[Convert]::FromBase64String('$b64')); " +
          "`$r=Invoke-CimMethod Win32_Process -MethodName Create -Arguments @{CommandLine='powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\ProgramData\ssh\atualizar_openssh.ps1'}; " +
          "'LANCADO pid=' + `$r.ProcessId + ' rv=' + `$r.ReturnValue"
$enc = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($remoto))
for ($i = 1; $i -le $Tentativas; $i++) {
    $saida = (ssh -o ConnectTimeout=15 -o BatchMode=yes desktop "powershell -NoProfile -EncodedCommand $enc" 2>&1) -join ' '
    "$(Get-Date -Format HH:mm:ss) tentativa $i : $saida"
    if ($saida -match 'LANCADO pid=\d+ rv=0') { exit 0 }
    Start-Sleep 10
}
exit 1
