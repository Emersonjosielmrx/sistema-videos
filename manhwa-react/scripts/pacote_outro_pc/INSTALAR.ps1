# Instala o manhwa-react neste PC a partir do pacote baixado do Google Drive. Rode na pasta onde baixou os .zip:
#   powershell -ExecutionPolicy Bypass -File INSTALAR.ps1
$ErrorActionPreference = "Stop"
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$zips = "manhwa-react", "hub-assets", "hub-overlays", "fotos", "postador", "segredos"

function Parar($msg) { Write-Host "`nPAROU: $msg" -ForegroundColor Red; exit 1 }

if (-not (Test-Path "D:\")) { Parar "este PC nao tem o disco D:. O pacote usa os mesmos caminhos do PC principal (D:\manhwa-react, D:\hipercool-materiais...). Crie uma particao D: ou peca ao Claude deste PC para adaptar o config.json." }
foreach ($z in $zips) { if (-not (Test-Path (Join-Path $aqui "$z.zip"))) { Parar "falta $z.zip nesta pasta (baixe todos os arquivos da pasta do Drive)." } }
$livre = (Get-PSDrive D).Free / 1GB
if ($livre -lt 30) { Parar ("so {0:N0} GB livres no D:; precisa de uns 30 GB (pacote + ambiente Python)." -f $livre) }
if (Test-Path "D:\manhwa-react\mr") {
    $r = Read-Host "Ja existe D:\manhwa-react neste PC. Sobrescrever com a versao do pacote? (s/n)"
    if ($r -ne "s") { Parar "cancelado, nada foi mudado." }
}
$py = $null
try { $py = (& py -3.13 -c "import sys; print(sys.executable)") } catch { }
if (-not $py) { Parar "falta o Python 3.13. Instale com:  winget install -e --id Python.Python.3.13   e rode de novo." }

Write-Host "== Extraindo os pacotes em D:\ (alguns minutos)"
foreach ($z in $zips) {
    Write-Host "   $z.zip"
    tar -xf (Join-Path $aqui "$z.zip") -C "D:\"
    if ($LASTEXITCODE) { Parar "nao consegui extrair $z.zip" }
}
New-Item -ItemType Directory -Force "D:\hipercool-materiais\manhwa-react\shorts", "D:\hipercool-materiais\manhwa-react\cortes",
    "D:\hipercool-materiais\manhwa-react\grandes", "D:\hipercool-materiais\_postados\react" | Out-Null

Write-Host "== Criando o ambiente Python (baixa uns 2 GB na primeira vez)"
& py -3.13 -m venv D:\manhwa-react\.venv
$vpy = "D:\manhwa-react\.venv\Scripts\python.exe"
& $vpy -m pip install --upgrade pip --quiet
& $vpy -m pip install -r D:\manhwa-react\requirements.txt
if ($LASTEXITCODE) { Parar "a instalacao dos pacotes Python falhou (veja a mensagem acima)." }
& $vpy -m playwright install chromium
if ($LASTEXITCODE) { Parar "nao consegui instalar o Chromium do Playwright (usado no HyperFrames)." }

Write-Host "== Conferindo"
& D:\hipercool-materiais\bin\ffmpeg.exe -hide_banner -version | Select-Object -First 1
$env:PYTHONUTF8 = "1"
& $vpy -c "import sys; sys.path.insert(0, r'D:\manhwa-react'); from mr.common import load_config; from mr import pipeline, grande, temas; c = load_config(); print('manhwa-react ok:', len(c.get('channels') or []), 'canais no config')"
if ($LASTEXITCODE) { Parar "o teste de importacao falhou (veja a mensagem acima)." }

Write-Host "`nPRONTO." -ForegroundColor Green
Write-Host "Grave no OBS com a saida em D:\manhwa-react\1-COLOQUE-AQUI e processe com:"
Write-Host "   D:\manhwa-react\.venv\Scripts\python.exe D:\manhwa-react\manhwareact.py batch"
Write-Host "A POSTAGEM esta DESLIGADA neste PC: leia o LEIA-ME-OUTRO-PC.txt antes de ligar."
