@echo off
rem D:\sistema\catalogo\diario.bat - OBRA sistema unico: manutencao AUTOMATICA diaria (tarefa SistemaUnificacao 06:30)
rem 1 analisa uso real  2 troca p/ Python unico as tarefas PRONTAS (max 15/dia, volta sozinha se piorar)
rem 3 atualiza D:\sistema\projetos  4 codigo comum (copias identicas -> 1 arquivo)  5 quarentena (pastas mortas + juncao)  6 aposentar venvs  7 scripts mortos -> D:\sistema2
set SISTEMA_USO=0
set PY=D:\veo\venv\Scripts\python.exe -X utf8
set L=D:\sistema\mapa\diario.log
echo ===== %date% %time% >> %L%
%PY% D:\sistema\catalogo\analisar_uso.py >> %L% 2>&1
%PY% D:\sistema\catalogo\trocar_python.py --aplicar --max 15 >> %L% 2>&1
%PY% D:\sistema\catalogo\montar_pasta_unica.py >> %L% 2>&1
%PY% D:\sistema\catalogo\comum.py --aplicar >> %L% 2>&1
%PY% D:\sistema\catalogo\quarentena.py --aplicar >> %L% 2>&1
%PY% D:\sistema\catalogo\aposentar.py --aplicar >> %L% 2>&1
%PY% D:\sistema\catalogo\limpar_scripts.py --aplicar >> %L% 2>&1
%PY% D:\sistema\catalogo\limpar_scripts.py --drive >> %L% 2>&1
%PY% D:\sistema\catalogo\juncoes.py --aplicar >> %L% 2>&1
%PY% D:\sistema\catalogo\levantar_nao_codigo.py >> %L% 2>&1
%PY% D:\sistema\catalogo\em_observacao.py >> %L% 2>&1
%PY% D:\sistema\catalogo\catalogo.py md > D:\sistema\catalogo\CATALOGO.md 2>&1
