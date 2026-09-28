@echo off
setlocal
title Responda ou Estuda - Diagnostico
cd /d "%~dp0"

echo Iniciando o aplicativo com registros visiveis...
echo Feche a janela do jogo para encerrar este diagnostico.
echo.
py -3.14 "%~dp0iniciar_janela_app.py" --diagnostico
set "CODIGO_SAIDA=%errorlevel%"

if not "%CODIGO_SAIDA%"=="0" (
    echo.
    echo O aplicativo terminou com o codigo %CODIGO_SAIDA%.
    echo Consulte dados\iniciador_janela_app.log.
    pause
)
exit /b %CODIGO_SAIDA%
