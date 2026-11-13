# Roda no PC2 (disparado pelo D:\video-fila\ocioso.py do PC1) UM Short de parceiro, desacoplado (dono 17/10/2026:
# 12/11 dona: "o Short não pode parar; pode fazer os internacionais, que é mais render" — -Idiomas hi,vi... (padrão nenhum)
# "se o hipercool estiver usando um PC, a fila tem que entender de usar o outro"). Cópia do pc2_rodar.ps1 do hipercool:
# processo criado por WMI (filho do ssh morre quando a conexão fecha) e "subst D: C:\" (os caminhos D:\hipercool-materiais
# do código caem em C:\hipercool-materiais do PC2). Sem línguas aqui; o vídeo pronto fica em
# C:\hipercool-materiais\animes recap\shorts\<pasta> e o PC1 busca. Ao terminar grava logs\pc2_parceiro_<Id>.fim
param([string]$Id, [string]$Fonte, [string]$Handle, [string]$Canal, [string]$Tipo = "manhwa", [string]$Idiomas = "nenhum")
New-Item -ItemType Directory -Force C:\recapd-e-animes\logs | Out-Null
$log = "C:\recapd-e-animes\logs\pc2_parceiro_$Id.log"
$fim = "C:\recapd-e-animes\logs\pc2_parceiro_$Id.fim"
Remove-Item $fim -ErrorAction SilentlyContinue
$linha = "cmd /c `"subst D: C:\ >nul 2>&1 & set PYTHONUTF8=1& set PYTHONIOENCODING=utf-8& set ANIME_IDIOMAS=$Idiomas& " +
         "set PARCEIRO_HANDLE=$Handle& set PARCEIRO_CANAL=$Canal& set PARCEIRO_TIPO=$Tipo& set SEM_YTDLP=1& " +
         "C:\recapd-e-animes\venv\Scripts\python.exe -u C:\recapd-e-animes\bin\anime_auto.py --modo short --fonte $Fonte --engine local " +
         "--limit 1 --top 1 --id=$Id >`"$log`" 2>&1 & echo fim > `"$fim`"`""
# dona 26/10: sem janela no PC2 — ShowWindow 0 (SW_HIDE) esconde o cmd; o python/ffmpeg/rclone filhos herdam o console
# escondido (antes cada Short abria janelas de cmd/python na tela de lá)
$si = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow = [uint16]0 }
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create `
     -Arguments @{ CommandLine = $linha; CurrentDirectory = "C:\recapd-e-animes\bin"; ProcessStartupInformation = $si }
"PID $($r.ProcessId) rc $($r.ReturnValue)"
