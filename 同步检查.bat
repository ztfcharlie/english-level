@echo off
chcp 65001 >nul
cd /d "%~dp0tools"
echo.
echo   RAZ 播放器 - 同步检查
echo   --------------------------------------------------
echo   重新核对 27 个级别的分P，看有没有被人改动过。
echo   约需 1 分钟。
echo.
python check_sync.py
if errorlevel 1 goto :end
echo.
set /p ans=  要自动修正位置变动并重建播放器吗？(y/N)
if /i not "%ans%"=="y" goto :end
echo.
python check_sync.py --fix
python make_app.py
echo.
echo   完成。刷新浏览器即可。
:end
echo.
pause
