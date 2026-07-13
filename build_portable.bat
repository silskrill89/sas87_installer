@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================
echo  GTA SAS 1987 Installer - One-Click Builder
echo ============================================
echo  This script will:
echo    1. Find or download Python 3.10+
echo    2. Install all required libraries
echo    3. Build a standalone .exe
echo ============================================
echo.

REM =====================================================================
REM  STEP 1: Find Python
REM =====================================================================
echo [1/6] Looking for Python...
echo.

set "PY_EXE="

REM Try PATH first (skip Windows Store stub)
for /f "delims=" %%i in ('where python 2^>nul') do (
    echo %%i | findstr /i /c:"WindowsApps" >nul || (
        set "PY_EXE=%%i"
        goto :found_py
    )
)

REM Try py launcher
where py >nul 2>&1
if %errorlevel%==0 (
    set "PY_EXE=py"
    goto :found_py
)

REM Scan common locations
for %%P in (
    "C:\Python3*"
    "C:\Program Files\Python3*"
    "C:\Program Files (x86)\Python3*"
) do (
    for %%F in (%%P) do (
        if exist "%%F\python.exe" (
            set "PY_EXE=%%F\python.exe"
            goto :found_py
        )
    )
)
if exist "%LOCALAPPDATA%\Programs\Python" (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        if exist "%%D\python.exe" (
            set "PY_EXE=%%D\python.exe"
            goto :found_py
        )
    )
)

REM Check registry
for %%K in (HKCU HKLM) do (
    for %%R in ("Software\Python\PythonCore" "Software\WOW6432Node\Python\PythonCore") do (
        for /f "tokens=*" %%V in ('reg query "%%K\%%R" 2^>nul') do (
            for /f "tokens=2,*" %%A in ('reg query "%%K\%%R\%%V\InstallPath" /ve 2^>nul') do (
                if exist "%%Bpython.exe" (
                    set "PY_EXE=%%Bpython.exe"
                    goto :found_py
                )
            )
        )
    )
)

goto :no_python

:found_py
echo   Found Python: %PY_EXE%
%PY_EXE% -c "import sys; print(f'  Version: {sys.version}')" 2>nul
if errorlevel 1 (
    echo   [WARN] Python found but not responding. Trying anyway...
)
echo.
goto :step2

:no_python
echo.
echo ============================================
echo  Python not found on this PC.
echo.
echo  Downloading Python 3.12 automatically...
echo ============================================
echo.

REM Download Python installer
set "PYINSTALLER=%TEMP%\python-3.12.7-amd64.exe"
echo Downloading Python 3.12.7...
powershell -NoProfile -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile '%PYINSTALLER%' }"
if errorlevel 1 (
    echo.
    echo [ERROR] Download failed. Please install Python manually:
    echo   https://www.python.org/downloads/
    echo   (tick "Add Python to PATH" during install)
    pause
    exit /b 1
)

echo Installing Python 3.12.7 (user install, no admin needed)...
%PYINSTALLER% /passive InstallAllUsers=0 PrependPath=1 Include_pip=1
if errorlevel 1 (
    echo.
    echo [ERROR] Python install failed. Try running the installer manually:
    echo   %PYINSTALLER%
    pause
    exit /b 1
)

REM Refresh PATH
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=py"

echo.
echo Python installed. Verifying...
%PY_EXE% -c "import sys; print(f'  Python {sys.version}')" 2>nul
if errorlevel 1 (
    echo [ERROR] Python installed but not responding.
    pause
    exit /b 1
)
echo.

:step2
REM =====================================================================
REM  STEP 2: Ensure pip
REM =====================================================================
echo [2/6] Checking pip...
%PY_EXE% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo   Bootstrapping pip via ensurepip...
    %PY_EXE% -m ensurepip --upgrade
    if errorlevel 1 (
        echo [ERROR] Could not install pip.
        pause
        exit /b 1
    )
)
echo   pip OK
echo.

REM =====================================================================
REM  STEP 3: Install all dependencies
REM =====================================================================
echo [3/6] Installing required libraries...
echo.
echo   This may take a few minutes on first run.
echo.

echo   --- Upgrading pip ---
%PY_EXE% -m pip install --upgrade pip >nul 2>&1

echo   --- Installing PySide6 (Qt6 GUI framework) ---
%PY_EXE% -m pip install --upgrade PySide6
if errorlevel 1 (
    echo   [WARN] PySide6 install had issues. Retrying with --user...
    %PY_EXE% -m pip install --upgrade --user PySide6
)

echo   --- Installing remaining dependencies ---
%PY_EXE% -m pip install -r requirements.txt
if errorlevel 1 (
    echo   [WARN] Some dependencies failed. Retrying with --user...
    %PY_EXE% -m pip install --user -r requirements.txt
)

echo   --- Installing PyInstaller (build tool) ---
%PY_EXE% -m pip install "pyinstaller>=6.0"
if errorlevel 1 (
    echo   [WARN] PyInstaller install had issues. Retrying with --user...
    %PY_EXE% -m pip install --user "pyinstaller>=6.0"
)

echo.
echo   Verifying all imports...
%PY_EXE% -c "import PySide6; import requests; import bs4; import py7zr; import rarfile; print('  All dependencies OK')"
if errorlevel 1 (
    echo.
    echo   [WARN] Some imports failed. The build may still work.
    echo   If it fails, try: %PY_EXE% -m pip install --force-reinstall -r requirements.txt PySide6
)
echo.

REM =====================================================================
REM  STEP 4: Clean previous builds
REM =====================================================================
echo [4/6] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo   Done.
echo.

REM =====================================================================
REM  STEP 5: Build the .exe (minimal — only Qt6Core/Gui/Widgets)
REM =====================================================================
echo [5/6] Building standalone .exe (this takes a few minutes)...
echo.
echo   Using minimal spec: only Qt6Core, Qt6Gui, Qt6Widgets bundled.
echo   Exe will be ~75-80MB (down from ~250MB with full PySide6).
echo.

%PY_EXE% -m PyInstaller installer.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check the output above for errors.
    echo.
    echo Common fixes:
    echo   1. Run: %PY_EXE% -m pip install --force-reinstall PySide6
    echo   2. Install Visual C++ Redistributable:
    echo      https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo   3. Try deleting the 'build' folder and running this script again
    pause
    exit /b 1
)

echo.
echo   Build complete!
echo.

REM =====================================================================
REM  STEP 6: Assemble portable folder
REM =====================================================================
echo [6/6] Assembling portable distribution folder...
echo.

set "OUT=dist\GTA_SAS_1987_Installer_Portable"
if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%"

copy "dist\GTA_SAS_1987_Installer.exe" "%OUT%\" >nul
copy "README.md" "%OUT%\" >nul
copy "CREDITS.md" "%OUT%\" >nul
copy "INSTALLER_GUIDE.pdf" "%OUT%\" >nul
copy "requirements.txt" "%OUT%\" >nul
copy "run.bat" "%OUT%\" >nul
copy "diagnose.bat" "%OUT%\" >nul
xcopy /E /I /Y "data" "%OUT%\data" >nul
xcopy /E /I /Y "fonts" "%OUT%\fonts" >nul

REM Create a simple "run me" batch file for the portable version
(
echo @echo off
echo echo.
echo echo ============================================
echo echo  GTA San Andreas Stories 1987 - Installer
echo echo ============================================
echo echo.
echo echo Double-click this file to start the installer.
echo echo.
echo echo If nothing happens, try right-clicking and selecting "Run as administrator".
echo echo.
echo pause
echo start "" "%~dp0GTA_SAS_1987_Installer.exe"
echo exit /b 0
) > "%OUT%\INSTALL.bat"

echo.
echo ============================================
echo  BUILD COMPLETE!
echo.
echo  Your installer is ready:
echo  %CD%\%OUT%
echo.
echo  Files included:
echo    GTA_SAS_1987_Installer.exe  (standalone, no Python needed)
echo    INSTALL.bat                 (double-click to launch)
echo    README.md                   (instructions)
echo    CREDITS.md                  (credits)
echo    INSTALLER_GUIDE.pdf         (full guide)
echo    data\                       (mod data)
echo    fonts\                      (fonts)
echo.
echo  To share: zip the entire "%OUT%" folder
echo  To test: double-click "%OUT%\INSTALL.bat"
echo ============================================
echo.

REM Open the output folder
explorer "%OUT%"

pause
