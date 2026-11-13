@echo off
echo Iniciando o Painel Administrativo (Vite) na porta 5173...
start cmd /k "cd client && npm run dev"

echo Iniciando o Backend (Go)...
start cmd /k "cd cmd\server && go run ."

echo Iniciando a Landing Page na porta 8000...
start cmd /k "cd landing && npx serve -p 8000"

echo Tudo inicializado! Verifique as janelas que abriram.
