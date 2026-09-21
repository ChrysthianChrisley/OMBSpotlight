@echo off
title One-Man Bands - Upload de Pendencias YouTube
cd /d "%~dp0"

echo ======================================================================
echo    ONE-MAN BAND SPOTLIGHT - ENVIAR VIDEOS PENDENTES PARA O YOUTUBE
echo ======================================================================
echo.
echo Processando lista de pendencias...
echo.

python uploader.py --upload-pending

echo.
echo ======================================================================
echo  Processamento finalizado. Pressione qualquer tecla para fechar...
echo ======================================================================
pause > nul
