# Roda no PC3 (desktop) UM Short de parceiro COM voz clonada, disparado pelo D:\video-fila\ocioso.py do PC1 (dono
# 12/11 dona: "o Short não pode parar; pode fazer os internacionais, que é mais render" — -Idiomas hi,vi... (padrão nenhum)
# 24/10/2026: kanban das Máquinas, "colocar no PC3"). Cópia do pc2_parceiro.ps1 SEM o "subst D: C:\" — o PC3 tem um D:
# de verdade; as junções D:\hipercool-materiais e D:\recapd-ambientes\producao (instalar_pc3.py) fazem o mesmo papel.
# O PC1 já mandou a fonte baixada (o PC3 nunca usa yt-dlp: mesmo IP da casa). Pronto em
# C:\hipercool-materiais\animes recap\shorts\<pasta>; o PC1 busca. Ao terminar grava logs\pc3_parceiro_<Id>.fim
param([string]$Id, [string]$Fonte, [string]$Handle, [string]$Canal, [string]$Tipo = "manhwa", [string]$Idiomas = "nenhum")
New-Item -ItemType Directory -Force C:\recapd-e-animes\logs | Out-Null
$log = "C:\recapd-e-animes\logs\pc3_parceiro_$Id.log"
$fim = "C:\recapd-e-animes\logs\pc3_parceiro_$Id.fim"
Remove-Item $fim -ErrorAction SilentlyContinue
$linha = "cmd /c `"set PATH=C:\hipercool-materiais\bin;%PATH%& set PYTHONUTF8=1& set PYTHONIOENCODING=utf-8& set ANIME_IDIOMAS=$Idiomas& " +
         "set PARCEIRO_HANDLE=$Handle& set PARCEIRO_CANAL=$Canal& set PARCEIRO_TIPO=$Tipo& set SEM_YTDLP=1& " +
         "C:\recapd-e-animes\venv\Scripts\python.exe -u C:\recapd-e-animes\bin\anime_auto.py --modo short --fonte $Fonte --engine local " +
         "--limit 1 --top 1 --id=$Id >`"$log`" 2>&1 & echo fim > `"$fim`"`""
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create `
     -Arguments @{ CommandLine = $linha; CurrentDirectory = "C:\recapd-e-animes\bin" }
"PID $($r.ProcessId) rc $($r.ReturnValue)"
