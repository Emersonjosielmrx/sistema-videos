@echo off
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
d:\recapd-ambientes\producao\venv\Scripts\python.exe d:\recapd-ambientes\producao\bin\anime-pipeline.py --video-source "d:\recapd-ambientes\producao\workspace\anime\vDIFuEamH5c_The_ENTIRE_Story_of_Attack_on_Titan_in_2\source.mp4" --script "d:\recapd-ambientes\producao\workspace\anime\vDIFuEamH5c_The_ENTIRE_Story_of_Attack_on_Titan_in_2\roteiro.txt" --titulo "The ENTIRE Story of Attack on Titan in 23 Minutes" --formato deitado --skip-notify > "d:\recapd-ambientes\producao\logs\aot_render_20260805_v2.log" 2>&1
