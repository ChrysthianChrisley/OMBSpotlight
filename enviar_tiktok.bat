@echo off
chcp 65001 > nul
title Enviar Videos para o TikTok - @onemanbands
echo =======================================================
echo     ENVIAR VIDEOS PARA O TIKTOK: @onemanbands
echo        (Protecao Anti-Shadowban: Max 2 por dia)
echo =======================================================
echo.
python tiktok_uploader.py --upload
echo.
pause
