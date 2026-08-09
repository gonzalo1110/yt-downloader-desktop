@echo off
REM ============================================================
REM  YT Downloader - Build con Nuitka (Windows)
REM  Ejecutar en la maquina Windows con Python 3.11+ instalado.
REM  Antes de ejecutar, asegurate de tener todos los binarios
REM  en resources\ (ver download_binaries.bat).
REM ============================================================
setlocal enabledelayedexpansion

echo =============================================
echo  YT Downloader — Build con Nuitka
echo =============================================

REM --- Verificar Python ---
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python no encontrado. Instala Python 3.11+ desde https://python.org
    pause
    exit /b 1
)

REM --- Verificar binarios requeridos ---
set MISSING=0
if not exist resources\ffmpeg.exe (
    echo ERROR: Falta resources\ffmpeg.exe
    set MISSING=1
)
if not exist resources\ffprobe.exe (
    echo ERROR: Falta resources\ffprobe.exe
    set MISSING=1
)
if not exist resources\deno.exe (
    echo ERROR: Falta resources\deno.exe
    set MISSING=1
)
if not exist resources\icon.ico (
    echo WARNING: Falta resources\icon.ico (se usara icono por defecto)
)
if %MISSING% equ 1 (
    echo.
    echo Ejecuta download_binaries.bat para descargar los archivos faltantes.
    pause
    exit /b 1
)

REM --- Crear/activar virtualenv ---
if not exist venv (
    echo Creando virtualenv...
    python -m venv venv
)
call venv\Scripts\activate.bat

REM --- Instalar dependencias ---
echo Instalando dependencias...
pip install -r requirements.txt
pip install nuitka

REM --- Build con Nuitka ---
echo.
echo Ejecutando Nuitka (esto puede tomar varios minutos)...

set ICON_FLAG=
if exist resources\icon.ico (
    set ICON_FLAG=--windows-icon-from-ico=resources\icon.ico
)

python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-console-mode=disable ^
    --enable-plugin=pyside6 ^
    --include-package=src ^
    --include-data-file=resources\ffmpeg.exe=ffmpeg.exe ^
    --include-data-file=resources\ffprobe.exe=ffprobe.exe ^
    --include-data-file=resources\deno.exe=deno.exe ^
    %ICON_FLAG% ^
    --company-name="YTDownloader" ^
    --product-name="YT Downloader" ^
    --file-version=1.0.0.0 ^
    --product-version=1.0.0.0 ^
    --output-dir=dist ^
    src\main.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo =============================================
    echo  Build completado: dist\main.exe
    echo =============================================
    echo.
    echo Pasos siguientes:
    echo   1. Abre Inno Setup (https://jrsoftware.org/isdl.php)
    echo   2. Abre installer\setup.iss y compila (Ctrl+F9)
    echo   3. El instalador se generara en dist\YTDownloader_Setup_v1.0.0.exe
) else (
    echo.
    echo ERROR: El build de Nuitka fallo. Revisa los mensajes arriba.
    pause
    exit /b 1
)

endlocal
pause
