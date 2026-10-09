@echo off
title Frontline: Steel Vanguard RTS | Сталевий Рубіж
chcp 65001 > nul
cd /d "%~dp0"

if exist "FrontlineWarfare.exe" (
    start "" "FrontlineWarfare.exe"
) else (
    echo [INFO] Запуск через Python...
    python main.py
)
exit
