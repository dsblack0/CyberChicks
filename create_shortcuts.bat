@echo off
echo 🔺 SnapAlert Shortcut Generator
echo.
echo This will create Windows shortcuts for your custom alerts...
echo.
pause

powershell -ExecutionPolicy Bypass -File register.ps1

echo.
echo Press any key to exit...
pause > nul 