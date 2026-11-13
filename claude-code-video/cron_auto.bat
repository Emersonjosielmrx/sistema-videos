@echo off
rem Tarefa ClaudeCodeVideo (a cada 20 min): retoma vídeo pausado por cota ou começa um novo se houver cota DE CERTEZA
cd /d D:\claude-code-video
rem 28/10: referencia nova (busca + analise) em paralelo, 1 por vez (trava propria), no maximo 1 a cada 3 h
start "" /b "D:\veo\venv\Scripts\python.exe" referencia.py rodada >> estado\referencia.log 2>&1
"D:\veo\venv\Scripts\python.exe" gerar.py --auto >> estado\cron.log 2>&1
rem melhorador (27/10): so age se ligado (LIGAR_MELHORADOR.bat); desligado sai na hora
"D:\veo\venv\Scripts\python.exe" melhorador.py >> estado\melhorador_cron.log 2>&1
