@echo off
rem 29/10 (dona: "faça com cada vídeo do drive, deixe em ponto de não parar"): tarefa EngenhariaReversaMedir, de hora
rem em hora, escondida. Mede os nossos Shorts (traz 1 do Drive por vez e apaga), continua de onde parou (medidas_nossos.jsonl),
rem 1 cópia por vez (trava), para sozinha com D: < 1 GB. Sem IA. Resultado: comparacao_nossos.md
set PYTHONUTF8=1
cd /d D:\video-fila\engenharia_reversa
D:\veo\venv\Scripts\python.exe -u medir_nossos.py >> medir_nossos.log 2>&1
