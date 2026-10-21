@echo off
setlocal
title Responde ou Estuda - Modo Administrador
cd /d "%~dp0"

rem MODO ADMINISTRADOR: navegacao livre entre as questoes, gabarito visivel,
rem cronometro desligado e saldos gravados em dados\estado_admin.json.
set "RESPONDA_ADMIN=1"

where pyw >nul 2>&1
if not errorlevel 1 (
    start "" pyw -3.14 "%~dp0iniciar_janela_app.py"
    exit /b 0
)

where py >nul 2>&1
if not errorlevel 1 (
    py -3.14 "%~dp0iniciar_janela_app.py"
    if errorlevel 1 exit /b 1
    exit /b 0
)

echo Python 3.14 nao foi localizado.
echo Execute primeiro o arquivo INSTALAR.bat.
pause
exit /b 1
