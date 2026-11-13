# Inicia o Servidor do Painel Hermes Call (Vite)
Write-Host "Iniciando o Painel Hermes Call na porta 5173..." -ForegroundColor Green
Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory "d:\hipercool-refactor\client"

# Inicia o Backend (Go) se necessário
Write-Host "Iniciando o Backend (Go)..." -ForegroundColor Green
Start-Process -NoNewWindow -FilePath "go" -ArgumentList "run", "." -WorkingDirectory "d:\hipercool-refactor\cmd\server"

# Inicia o Servidor da Landing Page na porta 8000
Write-Host "Iniciando a Landing Page do Hermes Call na porta 8000..." -ForegroundColor Cyan
Start-Process -NoNewWindow -FilePath "npx" -ArgumentList "serve", "-p", "8000" -WorkingDirectory "d:\hipercool-refactor\landing"

Write-Host "=============================================" -ForegroundColor Yellow
Write-Host "Tudo online!" -ForegroundColor Yellow
Write-Host "1. Painel Administrativo: http://localhost:5173" -ForegroundColor Yellow
Write-Host "2. Landing Page: http://localhost:8000" -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Yellow
