@echo off
REM ============================================================
REM  Descarga los binarios necesarios para el build de Windows.
REM  Ejecuta esto en la maquina Windows ANTES de build_windows.bat
REM ============================================================
setlocal enabledelayedexpansion

echo =============================================
echo  Descarga de binarios para YT Downloader
echo =============================================
echo.

if not exist resources mkdir resources

REM --- FFmpeg (LGPL build) ---
REM IMPORTANTE: Usamos el build LGPL de BtbN (NO gyan.dev) porque
REM los builds de gyan.dev incluyen libx264/libx265, lo que fuerza
REM licencia GPL sobre el binario completo. La app solo necesita
REM codificadores libres (libmp3lame, flac), ambos compatibles con LGPL.
REM El build LGPL trae ffmpeg.exe + ffprobe.exe sin componentes GPL.

if not exist resources\ffmpeg.exe (
    echo [1/3] FFmpeg no encontrado.
    echo.
    echo Descarga el build LGPL para Windows x64 desde:
    echo   https://github.com/BtbN/FFmpeg-Builds/releases/latest
    echo.
    echo Archivo: ffmpeg-master-latest-win64-lgpl.zip
    echo (el que dice "lgpl", NO "gpl")
    echo.
    echo Extrae ffmpeg.exe y ffprobe.exe de la carpeta bin\ del .zip
    echo y colocalos en resources\
    echo.
    echo Usa 7-Zip (https://7-zip.org) para extraer el .zip
    pause
) else (
    echo [1/3] ffmpeg.exe encontrado.
)
if not exist resources\ffprobe.exe (
    echo [1/3] ffprobe.exe no encontrado. Debe estar junto a ffmpeg.exe en resources\
    pause
)

REM Verificacion rapida: ffmpeg -version debe decir --enable-lgpl
if exist resources\ffmpeg.exe (
    echo.
    echo Verificando build de FFmpeg...
    resources\ffmpeg.exe -version 2>&1 | findstr /i "enable-lgpl" >nul
    if !ERRORLEVEL! equ 0 (
        echo OK: FFmpeg confirma ser build LGPL (--enable-lgpl presente)
    ) else (
        echo WARNING: No se encontro --enable-lgpl en la salida de ffmpeg -version.
        echo Asegurate de haber descargado la variante lgpl, no gpl.
        echo Puedes ignorar si solo aparece --enable-gpl (algunos builds reportan ambos).
    )
)

REM --- Deno ---
if not exist resources\deno.exe (
    echo.
    echo [2/3] Deno no encontrado.
    echo.
    echo Descarga el .zip de Deno para Windows x64 desde:
    echo   https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip
    echo.
    echo Extrae deno.exe del .zip y colocalo en resources\
    pause
) else (
    echo [2/3] deno.exe encontrado.
)

REM --- Icono ---
if not exist resources\icon.ico (
    echo.
    echo [3/3] icon.ico no encontrado (opcional).
    echo.
    echo Puedes usar https://icoconverter.com para crear un .ico desde una imagen PNG.
    echo Mientras tanto Nuitka usara el icono por defecto de Windows.
    echo.
    timeout /t 3 >nul
) else (
    echo [3/3] icon.ico encontrado.
)

echo.
echo =============================================
echo  Resumen de resources\:
echo =============================================
dir resources\ /b 2>nul
echo.
echo Una vez que tengas ffmpeg.exe, ffprobe.exe y deno.exe
echo en resources\, ejecuta build_windows.bat
echo =============================================
pause
