@echo off
setlocal
cd /d "%~dp0"

set PY=

if exist "..\.venv\Scripts\python.exe" (
  set "PY=..\.venv\Scripts\python.exe"
  goto run
)

where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py -3"
  goto run
)

where python >nul 2>nul
if %errorlevel%==0 (
  set "PY=python"
  goto run
)

echo Python 3 was not found. Please install Python 3.11 or later.
pause
exit /b 1

:run
%PY% -c "import numpy; import PIL" >nul 2>nul
if errorlevel 1 (
  echo Required Python packages are missing.
  echo.
  echo Run these commands from the repository root:
  echo   python -m venv .venv
  echo   .venv\Scripts\activate
  echo   pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)

%PY% "%~dp0godius_buff_timer.py"
if errorlevel 1 pause
