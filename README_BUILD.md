# Build de YT Downloader para Windows

## Requisitos previos (en la maquina Windows)

| Componente | Donde obtenerlo |
|---|---|
| **Python 3.11 o superior** | https://python.org (marca "Add Python to PATH" durante la instalacion) |
| **7-Zip** (para extraer .7z) | https://7-zip.org |
| **Inno Setup 6** (solo para crear instalador) | https://jrsoftware.org/isdl.php |

## Paso 1: Descargar binarios

Ejecuta `download_binaries.bat` o descarga manualmente:

1. **FFmpeg (LGPL)** — `ffmpeg.exe` y `ffprobe.exe`
   - URL: https://github.com/BtbN/FFmpeg-Builds/releases/latest
   - Archivo: **`ffmpeg-master-latest-win64-lgpl.zip`** (el que dice **lgpl**, NO `gpl`)
   - Extraer los archivos `bin/ffmpeg.exe` y `bin/ffprobe.exe` a `resources/`
   - **Razon:** usamos el build LGPL porque la app no necesita codificadores GPL
     (libx264/libx265). Los builds de gyan.dev incluyen esos codificadores
     forzando licencia GPL. Con BtbN/LGPL nos aseguramos de distribuir solo
     codificadores libres (libmp3lame, flac).

2. **Deno** — `deno.exe`
   - URL: https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip
   - Extraer `deno.exe` a `resources/`

3. **Icono** (opcional) — `icon.ico`
   - Crea un .ico desde un PNG de 256x256 con https://icoconverter.com
   - Si no hay icono, Nuitka usa el icono por defecto de Windows

### Verificacion del build LGPL

Abre una terminal en `resources/` y ejecuta:

```cmd
ffmpeg.exe -version | findstr enable-lgpl
```

Debe mostrar `--enable-lgpl` (o al menos no debe mostrar `libx264` ni `libx265`
entre los componentes habilitados). Si ves `libx264` o `libx265` en la salida,
significa que descargaste el build GPL por error — descarga la variante `lgpl`.

**Estructura esperada de `resources/`:**
```
resources/
  ffmpeg.exe
  ffprobe.exe
  deno.exe
  icon.ico         (opcional)
```

## Paso 2: Build del .exe con Nuitka

Abre una terminal (cmd.exe) en la raiz del proyecto y ejecuta:

```cmd
build_windows.bat
```

Esto hara automaticamente:
1. Crear/activar un virtualenv
2. `pip install -r requirements.txt` (incluye PySide6, yt-dlp, mutagen, pycryptodomex)
3. `pip install nuitka`
4. Ejecutar Nuitka con todas las opciones necesarias

**Tiempo estimado:** 3-10 minutos (depende de la maquina).
**Resultado:** `dist/main.exe` (~50-80 MB, onefile, portable)

### Notas sobre el build

- `--onefile` genera un solo .exe que se extrae a `%TEMP%` al ejecutarse. La primera ejecucion puede tardar unos segundos en iniciar por la extraccion.
- Los binarios (ffmpeg, ffprobe, deno) estan embebidos dentro del .exe.
- `--windows-console-mode=disable` oculta la consola; si hay errores, se muestran como ventanas de dialogo.
- `--standalone` + `--onefile` asegura que no se necesitan DLLs externas.

## Paso 3: Probar el .exe

Antes de crear el instalador, verifica que el .exe funcione correctamente:

1. Navega a `dist/` y haz doble clic en `main.exe`
2. Prueba descargar un video publico (ej. https://www.youtube.com/watch?v=dQw4w9WgXcQ)
3. Prueba que el boton "Usar sesion" funcione con tu navegador
4. Cierra la app

Si todo funciona, continua con el instalador.

## Paso 4: Crear el instalador con Inno Setup

1. Abre Inno Setup (Inicio > Inno Setup 6)
2. Menu: File > Open... > `installer/setup.iss`
3. Build > Compile (Ctrl+F9)
4. El instalador se genera en `dist/YTDownloader_Setup_v1.0.0.exe`

## Paso 5: Probar el instalador en una PC limpia

1. Copia el instalador a una PC Windows **sin Python instalado**
2. Ejecuta el instalador (puede mostrar advertencia de SmartScreen, ver abajo)
3. Verifica que la app se abre desde el acceso directo del escritorio
4. Prueba descargar un video

## SmartScreen / Antivirus

Al no estar firmado digitalmente, Windows SmartScreen mostrara un aviso la primera vez:

> "Windows protegio su PC" / "Windows protected your PC"

Para continuar:
1. Haz clic en **"Mas informacion"** / **"More info"**
2. Luego en **"Ejecutar de todas formas"** / **"Run anyway"**

Esto es normal para software sin firma digital. No indica un problema de seguridad.
Para eliminar este aviso en el futuro, se necesitaria un certificado de firma de codigo
(servicio de pago, no incluido en este proyecto).

## Solucion de problemas

| Problema | Causa probable | Solucion |
|---|---|---|
| Nuitka falla con "Module not found" | Falta `--include-package=src` | Verifica que build_windows.bat incluya ese flag |
| El .exe abre pero no descarga | FFmpeg o Deno no estan embebidos | Revisa que resources/ tenga los binarios antes de compilar |
| "No se pudo descargar" con bot-check | Faltan cookies de navegador | Usa el boton "Usar sesion" en la app |
| El .exe no se abre o crashea al inicio | Antivirus bloqueando la extraccion | Agrega el .exe a las exclusiones del antivirus |
| pycryptodomex falla al instalarse | Sin compilador C en Windows | Usa `pip install pycryptodomex` desde https://pycryptodomex.org (ruedas precompiladas disponibles para Windows) |
