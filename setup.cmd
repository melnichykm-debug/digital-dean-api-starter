@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys; assert sys.version_info >= (3, 12), 'Python 3.12 or newer is required'"
if errorlevel 1 goto failed
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -e ".[dev]"
if errorlevel 1 goto failed
echo Setup complete. Run start.cmd to launch the API.
pause
exit /b 0
:failed
echo Setup failed. See the error above and the launch guide.
pause
exit /b 1
