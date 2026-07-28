@echo off
setlocal
cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python 3 was not found. Please install Python 3.11 or later.
    exit /b 1
  )
  python -m venv .venv
  if errorlevel 1 exit /b 1
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1

pip install -r requirements.txt
if errorlevel 1 exit /b 1

if not exist "build" mkdir "build"
python -c "from PIL import Image; img=Image.open(r'source\icons\Godius_104.png').convert('RGBA'); img.save(r'build\GodiusCrystalBuffTimer.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
if errorlevel 1 exit /b 1

pyinstaller --clean GodiusCrystalBuffTimer.spec
if errorlevel 1 exit /b 1

echo.
echo Build complete: dist\GodiusCrystalBuffTimer.exe
