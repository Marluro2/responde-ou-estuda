@echo off
cd /d "%~dp0"
echo Instalando as dependencias do Responde ou Estuda...
py -3.14 -m pip install -r requirements.txt
echo.
echo Instalacao concluida.
pause
