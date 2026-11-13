@echo off
cd /d "%~dp0"
sveu16.exe --batch tests\smoke.fth > tests\last-run.txt
if errorlevel 1 goto fail
findstr /L /C:"?(-" tests\last-run.txt >nul
if not errorlevel 1 goto fail
findstr /L /C:"2 3 + . 5 " tests\last-run.txt >nul
if errorlevel 1 goto fail
findstr /L /C:"9 KVADRAT . 81 " tests\last-run.txt >nul
if errorlevel 1 goto fail
findstr /L /C:"1 8 LSHIFT . 256 " tests\last-run.txt >nul
if errorlevel 1 goto fail
findstr /L /C:"256 4 RSHIFT . 16 " tests\last-run.txt >nul
if errorlevel 1 goto fail
findstr /L /C:"SUMA . 45 " tests\last-run.txt >nul
if errorlevel 1 goto fail
type tests\last-run.txt
echo PASS: boot, Forth, nove rijeci, varijable, petlja i video.
if /I not "%~1"=="--no-pause" pause
exit /b 0
:fail
type tests\last-run.txt
echo FAIL: Provjerite poruku iznad. Zatvorite drugi prozor emulatora prije testiranja.
if /I not "%~1"=="--no-pause" pause
exit /b 1
