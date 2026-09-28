@echo off
chcp 65001 >nul
title RAZ 磨耳朵
cd /d "%~dp0"

rem A tiny local server keeps the B站 embed player happy (a file:// page sends no
rem Referer, which some embeds dislike). Falls back to opening the file directly.

set PORT=8899
where python >nul 2>nul
if errorlevel 1 goto NOPYTHON

echo.
echo   RAZ 磨耳朵 已经启动
echo   浏览器会自动打开，这个黑窗口不要关，关掉就停了。
echo.
echo   地址: http://localhost:%PORT%/
echo.

start "" "http://localhost:%PORT%/index.html"
python -m http.server %PORT% --bind 127.0.0.1
goto :EOF

:NOPYTHON
echo.
echo   没找到 Python，直接用文件方式打开（也能用，只是偶尔播放器会挑剔）。
echo.
start "" "英语分级播放器.html"
timeout /t 3 >nul
