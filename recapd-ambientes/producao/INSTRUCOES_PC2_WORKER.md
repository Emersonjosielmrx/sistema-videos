# Instruções para o PC2 (192.168.18.7) — Worker de Render

## Passo 1: Habilitar acesso guest (RODAR COMO ADMINISTRADOR)

Abra PowerShell como Admin e cole TUDO de uma vez:

```powershell
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters' -Name 'AllowInsecureGuestAuth' -Value 1 -Type DWord
Restart-Service LanmanWorkstation -Force
net use Z: \192.168.18.36\workspace /persistent:yes
dir Z:\panels\regressed-warriors-cap33\
```

Se o último comando mostrar arquivos .jpg, FUNCIONOU.

## Passo 2: Testar o daemon

O worker_daemon.py em C:\hipercool-videos\bin\ já foi editado pra usar Z:\ como fonte de panels.
Reiniciar o daemon:

```powershell
taskkill /F /IM python.exe
cd C:\hipercool-videos
.\venv\Scripts\python.exe bin\worker_daemon.py
```

## Passo 3: Confirmar

Depois de iniciar o daemon, ele deve responder na porta 8771.
O PC principal (192.168.18.36) vai enviar caps automaticamente via HTTP.
