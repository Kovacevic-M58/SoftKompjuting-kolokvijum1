@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

call :find_python
if defined PY goto have_python

echo === Python nije pronadjen - instaliram Python 3.12 preko winget-a ===
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
call :find_python
if not defined PY (
  echo.
  echo Instalacija Pythona nije uspela. Instaliraj ga rucno sa python.org
  echo i stikliraj "Add python.exe to PATH", pa ponovo pokreni ovaj fajl.
  pause
  exit /b 1
)

:have_python
echo === Koristim: %PY% ===
"%PY%" --version

echo.
echo === Instaliram biblioteke (numpy, opencv-python, matplotlib) ===
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install numpy opencv-python matplotlib
if errorlevel 1 (
  echo Instalacija biblioteka nije uspela.
  pause
  exit /b 1
)

echo.
echo === Pokrecem banane.py (data1\count.csv, slike u data1\images) ===
cd /d "%~dp0data1"
"%PY%" "..\banane.py" images/
echo.
echo Gornji broj je prosecna greska (MAE) - sto blize 0, to bolje.
pause
exit /b 0

:find_python
set "PY="
for %%V in (313 312 311 310) do (
  if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
  if not defined PY if exist "%ProgramFiles%\Python%%V\python.exe" set "PY=%ProgramFiles%\Python%%V\python.exe"
)
if not defined PY (
  for /f "delims=" %%P in ('where python 2^>nul ^| findstr /v /i "WindowsApps"') do if not defined PY set "PY=%%P"
)
exit /b 0
