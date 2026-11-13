# Script para rodar NO PC3
# Abre Chrome para fazer login com emersonjosiel2026@gmail.com

$profileDir = "D:\logins-google\chrome-profiles\emersonjosiel2026"
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"

Write-Host "Criando diretorio de perfil..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $profileDir -Force | Out-Null

Write-Host "Abrindo Chrome para login..." -ForegroundColor Yellow
Write-Host ""
Write-Host "INSTRUCOES:" -ForegroundColor Green
Write-Host "1. Faca login com: emersonjosiel2026@gmail.com" -ForegroundColor Green
Write-Host "2. Apos logar, FECHE o Chrome" -ForegroundColor Green
Write-Host "3. O perfil sera salvo automaticamente" -ForegroundColor Green
Write-Host ""

& $chromePath --user-data-dir=$profileDir --no-first-run "https://accounts.google.com/signin"

Write-Host ""
Write-Host "Perfil salvo em: $profileDir" -ForegroundColor Cyan
Write-Host "Conta pronta para usar no bot!" -ForegroundColor Cyan
