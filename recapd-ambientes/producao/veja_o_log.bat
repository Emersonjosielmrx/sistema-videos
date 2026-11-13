@echo off
title Log do Hipercool - Render em tempo Real
chcp 65001 >nul
cd /d D:\hipercool-inferior-fix
echo Olhando o que ta acontecendo agora:
powershell -Command "Get-Content cap06_run_censurado_v6_3.log -Tail 15 -Wait"
pause
