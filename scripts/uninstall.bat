@echo off
setlocal
schtasks.exe /Delete /TN AutoShutdownScheduler /F >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=[Environment]::GetFolderPath('Desktop') + '\自動シャットダウン.lnk'; if(Test-Path $p){Remove-Item $p -Force}"
rd /S /Q "%LOCALAPPDATA%\AutoShutdown" >nul 2>&1
echo アンインストールしました。
pause
endlocal
