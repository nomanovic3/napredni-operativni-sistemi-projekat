@echo off
cd /d "%~dp0"
if not exist sveu16.exe (
  echo Nedostaje sveu16.exe. Prvo pokrenite build.ps1 uz GCC ili Clang.
  pause
  exit /b 1
)
start "" sveu16.exe
