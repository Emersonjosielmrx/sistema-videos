@echo off
rem 29/10 engenharia reversa: toda segunda, escondido (tarefa EngenhariaReversaSemanal). Sem IA.
rem amostra nova dos parceiros (devagar, para no bloqueio) -> mede -> mede os nossos -> relatório + resumo Telegram
set PYTHONUTF8=1
cd /d D:\video-fila\engenharia_reversa
set PY=D:\veo\venv\Scripts\python.exe
%PY% -u amostra.py --n 5 --max 30 --pausa 120 >> semanal.log 2>&1
%PY% -u medir.py >> semanal.log 2>&1
%PY% -u medir_nossos.py >> semanal.log 2>&1
%PY% -u relatorio_semanal.py >> semanal.log 2>&1
rem 29/10 Fable: cruzamentos só-arquivo (elegibilidade, júri x views) junto do relatório
%PY% -u continuaram_x_views.py --csv >> semanal.log 2>&1
%PY% -u juri_x_views.py >> semanal.log 2>&1
