@echo off
chcp 65001 >nul
title Khoi dong MARGA AI OS
cd /d "%~dp0"

echo Bat MARGA AI OS chay NEN - state co dinh trong .marga\state...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-marga.ps1" -Open

echo.
echo Da bat tai http://127.0.0.1:28779.
echo (State plugin: mo .marga\state. Xem loi: mo .marga\state\marga.stderr.log)
timeout /t 4 >nul
