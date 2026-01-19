@echo off
setlocal
title Tsufutube Downloader Build Tool
color 0A

echo =======================================================
echo          TSUFUTUBE DOWNLOADER BUILD TOOL
echo =======================================================
echo.

:: --- 1. KIEM TRA MOI TRUONG ---
echo [1/5] Checking environment...

if not exist "Tsufutube downloader.py" (
    color 0C
    echo [ERROR] Cannot find 'Tsufutube downloader.py'. Make sure you are in the project root!
    pause
    exit /b
)

:: Hybrid FFmpeg Check
set "FFMPEG_BUNDLED=0"
if exist "ffmpeg\ffmpeg.exe" (
    echo [INFO] Found bundled FFmpeg in 'ffmpeg\'. It will be included in the build.
    set "FFMPEG_BUNDLED=1"
) else (
    echo [WARNING] proper FFmpeg folder not found. Building "Lite" version ^(System FFmpeg required^).
)

:: Check PyInstaller
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] PyInstaller not found. Attempting to install...
    pip install pyinstaller pillow
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Failed to install PyInstaller via pip.
        echo Please try running: pip install pyinstaller pillow
        pause
        exit /b
    )
)

if not exist "assets\icon.ico" (
    color 0E
    echo [WARNING] Icon not found in 'assets\icon.ico'. Build will utilize default icon.
)

:: Prepare Arguments based on FFmpeg presence
:: Prepare Arguments based on FFmpeg presence
:: OPTIMIZATION: We do NOT use --add-binary to bundle into _internal.
:: Instead, we will manually copy it to the ROOT folder after build.
:: This avoids duplication and makes the Portable folder cleaner.
set "COPY_FFMPEG=0"
set "FFMPEG_ARGS=" 

if "%FFMPEG_BUNDLED%"=="1" (
    echo [INFO] Found local FFmpeg. It will be copied to root folder ^(Portable Mode^).
    set "COPY_FFMPEG=1"
) else (
    echo [INFO] Building LITE version ^(FFmpeg will be excluded^).
)

:: --- 2. CLEANUP ---
echo [2/5] Cleaning up old builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del "*.spec"

:: --- 3. BUILD VOI PYINSTALLER ---
echo [3/5] Building executable with PyInstaller (This may take a while)...
echo.

python -m PyInstaller --onedir ^
  --windowed ^
  --icon="assets\icon.ico" ^
  --name="Tsufutube-Downloader" ^
  --add-data="assets;assets" ^
  --add-data="data.py;." ^
  --add-data="splash_screen.py;." ^
  --add-data="fetcher.py;." ^
  %FFMPEG_ARGS% ^
  --hidden-import=PIL._tkinter_finder ^
  --exclude-module=matplotlib ^
  --exclude-module=numpy ^
  --exclude-module=pandas ^
  --exclude-module=selenium ^
  --noconsole ^
  --clean ^
  "Tsufutube downloader.py"

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b
)

:: --- 4. POST-BUILD: Copy Python scripts to dist root ---
echo.
echo [4/5] Copying additional files to dist folder...

:: Copy Python scripts
copy /Y "splash_screen.py" "dist\Tsufutube-Downloader\" >nul 2>&1
copy /Y "fetcher.py" "dist\Tsufutube-Downloader\" >nul 2>&1
copy /Y "data.py" "dist\Tsufutube-Downloader\" >nul 2>&1

:: Copy assets
xcopy /E /I /Y "dist\Tsufutube-Downloader\_internal\assets" "dist\Tsufutube-Downloader\assets" >nul 2>&1

:: Copy ffmpeg folder manually if it was bundled (to root for consistency, though internal has it)
:: Copy ffmpeg folder manually FROM SOURCE if it was bundled
if "%COPY_FFMPEG%"=="1" (
    xcopy /E /I /Y "ffmpeg" "dist\Tsufutube-Downloader\ffmpeg" >nul 2>&1
    echo      ffmpeg copied to root - OK
) else (
    echo      ffmpeg NOT bundled ^(Lite mode^)
)

echo      assets copied - OK

:: --- 5. FINISH ---
echo.
echo [5/5] Build Process Finished!
echo =======================================================
echo.
echo [SUCCESS] Build output located in 'dist\' folder:
echo.
echo   UNPACKED FOLDER: dist\Tsufutube-Downloader\
echo.
echo   (Create ZIP manually with WinRAR if needed)
echo.
echo =======================================================
echo [NEXT STEP - CREATE INSTALLER]
echo.
echo   1. Install Inno Setup 6 (https://jrsoftware.org/isdl.php)
echo   2. Right-click 'installer.iss' file in this folder
echo   3. Select 'Compile'
echo.
echo =======================================================
pause
