# Roda no PC2 (via ssh, disparado pelo fila.py do PC1) o render de UMA língua de um capítulo, desacoplado.
# Criado por WMI (Win32_Process.Create): processo filho do ssh morre quando a conexão fecha.
# "subst D: C:\" dentro do cmd do render: os caminhos fixos D:\... do código caem em C:\... do PC2.
param([string]$Chave, [string]$Lang, [string]$TituloB64, [string]$Pasta, [int]$Fim = 0, [int]$Inicio = 0)
$titulo = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($TituloB64))
New-Item -ItemType Directory -Force C:\hipercool-videos\logs | Out-Null
$log = "C:\hipercool-videos\logs\pc2_${Chave}_${Lang}.log"
$args_ = "--panels-dir `"$Pasta`" --titulo `"$titulo`" --max-panels 120 --subtitles --karaoke --censura " +
         "--skip-notify --output-suffix _$($Lang.ToUpper()) --idioma $Lang"
if ($Fim) { $args_ += " --skip-final $Fim" }
if ($Inicio) { $args_ += " --start-panel $Inicio" }
$linha = "cmd /c `"subst D: C:\ >nul 2>&1 & set PYTHONUTF8=1& set GEMINI_TTS_PROXY_ENABLED=1& set HIPER_CACHE_2P5D=1& " +
         "C:\hipercool-videos\venv\Scripts\python.exe -u bin\hiper-pipeline.py $args_ > `"$log`" 2>&1`""
# dona 26/10: sem janela no PC2 — ShowWindow 0 (SW_HIDE); python/ffmpeg filhos herdam o console escondido
$si = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow = [uint16]0 }
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create `
     -Arguments @{ CommandLine = $linha; CurrentDirectory = "C:\hipercool-videos"; ProcessStartupInformation = $si }
"PID $($r.ProcessId) rc $($r.ReturnValue)"
