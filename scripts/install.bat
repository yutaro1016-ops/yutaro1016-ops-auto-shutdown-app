@echo off
setlocal
set "SRC=%~dp0\..\dist\AutoShutdown.exe"
set "DEST=%LOCALAPPDATA%\AutoShutdown"

if not exist "%SRC%" (
  echo AutoShutdown.exe が見つかりません。先に scripts\build.bat を実行してください。
  pause
  exit /b 1
)

if not exist "%DEST%" mkdir "%DEST%"
copy /Y "%SRC%" "%DEST%\AutoShutdown.exe" >nul
if errorlevel 1 exit /b 1

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\自動シャットダウン.lnk'); $s.TargetPath='%DEST%\AutoShutdown.exe'; $s.WorkingDirectory='%DEST%'; $s.Description='指定時刻シャットダウン'; $s.Save()"
if errorlevel 1 exit /b 1

echo インストールしました。デスクトップの「自動シャットダウン」から起動できます。
pause
endlocal
