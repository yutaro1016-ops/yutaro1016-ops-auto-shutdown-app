@echo off
setlocal
cd /d "%~dp0\.."

where py >nul 2>&1
if %errorlevel%==0 (
  set PY=py
) else (
  set PY=python
)

%PY% -m pip install --upgrade pip
if errorlevel 1 exit /b 1
%PY% -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
%PY% -m pytest -q
if errorlevel 1 exit /b 1

%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name AutoShutdown --icon assets\app.ico src\main.py
if errorlevel 1 exit /b 1

echo.
echo Build complete: dist\AutoShutdown.exe
endlocal
