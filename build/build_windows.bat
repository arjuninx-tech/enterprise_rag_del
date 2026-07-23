@echo off
setlocal EnableDelayedExpansion
cls

echo ============================================================
echo  ISO Manual Assistant -- Windows Build
echo  (No Inno Setup or external tools required)
echo ============================================================
echo.

:: ── Change to project root ───────────────────────────────────────────────────
cd /d "%~dp0.."
set "ROOT=%CD%"
echo [INFO] Project root: %ROOT%
echo.

:: ── Prerequisite checks ───────────────────────────────────────────────────────
echo [1/7] Checking prerequisites...

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ and add it to PATH.
    goto :fail
)
for /f "tokens=*" %%v in ('python --version') do echo        %%v

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [..] Installing PyInstaller...
    pip install pyinstaller --quiet
    if errorlevel 1 ( echo [ERROR] Could not install PyInstaller. & goto :fail )
)
echo        PyInstaller ready.
echo.

:: ── Step 1b: Build knowledge base if needed ──────────────────────────────────
if not exist "%ROOT%\data\vector_db" (
    echo [..] data\vector_db\ not found -- checking for source documents...
    if exist "%ROOT%\data\approved_documents\" (
        :: Count files in approved_documents (any file)
        set "DOC_COUNT=0"
        for /f %%f in ('dir /b /a-d "%ROOT%\data\approved_documents\" 2^>nul ^| find /c /v ""') do set "DOC_COUNT=%%f"
        if !DOC_COUNT! GTR 0 (
            echo [..] Found !DOC_COUNT! document(s). Building knowledge base now...
            echo       ^(Requires Ollama + nomic-embed-text to be running^)
            echo.
            python build\build_kb.py
            if errorlevel 1 (
                echo.
                echo [WARN] Knowledge base build failed. Users will need to rebuild after install.
                echo        Make sure Ollama is running: ollama serve
                echo        And nomic-embed-text is pulled: ollama pull nomic-embed-text
                echo.
            )
        ) else (
            echo [WARN] data\approved_documents\ is empty.
            echo        Add ISO documents there and re-run, OR users can add docs after install.
            echo.
        )
    ) else (
        echo [WARN] data\approved_documents\ not found. No KB will be bundled.
        echo        Users will add documents and rebuild the knowledge base after installing.
        echo.
    )
) else (
    echo [OK]  Pre-built knowledge base found -- will be bundled.
    echo.
)

:: ── Step 2: Clean ─────────────────────────────────────────────────────────────
echo [3/7] Cleaning previous output...
if exist "%ROOT%\dist\ISO_Manual_Assistant"           rmdir /s /q "%ROOT%\dist\ISO_Manual_Assistant"
if exist "%ROOT%\dist\ISO_Manual_Assistant_Setup.exe" del /q "%ROOT%\dist\ISO_Manual_Assistant_Setup.exe"
if exist "%ROOT%\dist\ISO_Manual_Assistant_Package"   rmdir /s /q "%ROOT%\dist\ISO_Manual_Assistant_Package"
for /d /r "%ROOT%\app" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /d /r "%ROOT%\setup_wizard" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo        Done.
echo.

:: ── Step 2: Build main app ────────────────────────────────────────────────────
echo [4/7] Building main app with PyInstaller...
echo       (bundles Python + chromadb + pywebview -- takes 3-6 minutes)
echo.

python -m PyInstaller build\iso_assist.spec --noconfirm --clean

if errorlevel 1 ( echo. & echo [ERROR] Main app build failed. & goto :fail )

if not exist "%ROOT%\dist\ISO_Manual_Assistant\ISO_Manual_Assistant.exe" (
    echo [ERROR] ISO_Manual_Assistant.exe not found in dist\.
    goto :fail
)
echo.
echo [OK]  Main app built: dist\ISO_Manual_Assistant\
echo.

:: ── Step 3: Build setup wizard ────────────────────────────────────────────────
echo [5/7] Building setup wizard...

python -m PyInstaller build\setup_wizard.spec --noconfirm --clean

if errorlevel 1 ( echo. & echo [ERROR] Setup wizard build failed. & goto :fail )

if not exist "%ROOT%\dist\ISO_Manual_Assistant_Setup.exe" (
    echo [ERROR] ISO_Manual_Assistant_Setup.exe not found.
    goto :fail
)
echo [OK]  Setup wizard built: dist\ISO_Manual_Assistant_Setup.exe
echo.

:: ── Step 3b: Build uninstaller ─────────────────────────────────────────────────
echo [6/7] Building uninstaller...

python -m PyInstaller build\uninstaller.spec --noconfirm --clean

if errorlevel 1 ( echo. & echo [ERROR] Uninstaller build failed. & goto :fail )

if not exist "%ROOT%\dist\ISO_Manual_Assistant_Uninstall.exe" (
    echo [ERROR] ISO_Manual_Assistant_Uninstall.exe not found.
    goto :fail
)
echo [OK]  Uninstaller built: dist\ISO_Manual_Assistant_Uninstall.exe
echo.

:: ── Step 4: Assemble distribution package ────────────────────────────────────
echo [7/7] Assembling distribution package...
set "PKG=%ROOT%\dist\ISO_Manual_Assistant_Package"
mkdir "%PKG%" 2>nul

:: Setup wizard (run this first)
copy /y "%ROOT%\dist\ISO_Manual_Assistant_Setup.exe" "%PKG%\" >nul

:: Uninstaller (setup wizard copies this into INSTALL_DIR during install)
copy /y "%ROOT%\dist\ISO_Manual_Assistant_Uninstall.exe" "%PKG%\" >nul

:: Main app folder
xcopy /s /e /q /i "%ROOT%\dist\ISO_Manual_Assistant" "%PKG%\ISO_Manual_Assistant\" >nul

:: Pre-built knowledge base (next to setup wizard so wizard can find it)
if exist "%ROOT%\data\vector_db" (
    xcopy /s /e /q /i "%ROOT%\data\vector_db" "%PKG%\vector_db\" >nul
    echo        Pre-built KB copied to package.
)

:: Simple README for end users
(
echo ISO Manual Assistant
echo ====================
echo.
echo INSTALLATION:
echo   1. Run ISO_Manual_Assistant_Setup.exe
echo   2. Select the AI models you want to download
echo   3. Click Install and wait ^(model downloads can take 10-30 min^)
echo   4. Launch from the Desktop shortcut or run:
echo      ISO_Manual_Assistant\ISO_Manual_Assistant.exe
echo.
echo REQUIREMENTS:
echo   - Windows 10 / 11 ^(64-bit^)
echo   - Internet connection during first setup ^(for model downloads^)
echo   - ~5-20 GB free disk space depending on models selected
echo.
echo SUPPORT: https://github.com/your-org/iso-manual-assistant
) > "%PKG%\README.txt"

echo [OK]  Package assembled: dist\ISO_Manual_Assistant_Package\
echo.

:: ── Bonus: Create zip ────────────────────────────────────────────────────────
echo [+]   Creating distribution zip...

set "ZIP=%ROOT%\dist\ISO_Manual_Assistant_v1.0.0_Windows.zip"
if exist "%ZIP%" del /q "%ZIP%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path '%PKG%\*' -DestinationPath '%ZIP%' -Force" >nul 2>&1

if exist "%ZIP%" (
    echo [OK]  Zip created: dist\ISO_Manual_Assistant_v1.0.0_Windows.zip
) else (
    echo [WARN] Zip creation failed ^(PowerShell Compress-Archive not available^).
    echo        Manually zip the folder: dist\ISO_Manual_Assistant_Package\
)
echo.

:: ── Done ─────────────────────────────────────────────────────────────────────
echo ============================================================
echo  BUILD COMPLETE
echo ============================================================
echo.
echo  Distribution folder: dist\ISO_Manual_Assistant_Package\
if exist "%ZIP%" echo  Distribution zip:    dist\ISO_Manual_Assistant_v1.0.0_Windows.zip
echo.
echo  Contents:
echo    ISO_Manual_Assistant_Setup.exe    ^<-- users run this first
echo    ISO_Manual_Assistant_Uninstall.exe^<-- uninstaller (auto-placed in install dir)
echo    ISO_Manual_Assistant\             ^<-- main application
echo    vector_db\                        ^<-- pre-built knowledge base
echo    README.txt
echo.
echo  Next steps:
echo    1. Test by running: dist\ISO_Manual_Assistant_Package\ISO_Manual_Assistant_Setup.exe
echo    2. Share the zip with end users
echo.
goto :end

:fail
echo.
echo ============================================================
echo  BUILD FAILED -- see errors above
echo ============================================================
echo.
exit /b 1

:end
endlocal
