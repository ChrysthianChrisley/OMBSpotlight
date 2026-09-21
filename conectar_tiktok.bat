@echo off
chcp 65001 > nul
title Conectar Conta TikTok - @onemanbands
echo =======================================================
echo          CONECTAR CONTA TIKTOK: @onemanbands
echo =======================================================
echo.
echo Abrindo o navegador para autenticar sua conta...
echo.
python tiktok_uploader.py --login
echo.
pause
