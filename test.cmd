@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run setup.cmd first.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pytest
set "test_exit=%ERRORLEVEL%"
pause
exit /b %test_exit%
