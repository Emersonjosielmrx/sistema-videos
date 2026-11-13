@echo off
REM R5 (22/10): colheita de reações reais dos narradores parceiros, de madrugada, só pelo proxy (tarefa ReacoesColheita 01:30)
set PYTHONUTF8=1
D:\veo\venv\Scripts\python.exe D:\hipercool-materiais\bin\reacoes_colheita.py --max-pedidos 40 >> D:\hipercool-materiais\amostras_voz\reacoes_colheita.log 2>&1
