# YT Downloader Desktop

Descarga videos y audio de YouTube con cola de descargas concurrentes y conversión a MP3/FLAC.

## Requisitos

- **Python 3.11+**
- **FFmpeg** (en Linux viene con el sistema; en Windows se embeberá en el .exe)

## Desarrollo en Linux

```bash
# 1. Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar en modo desarrollo
chmod +x run_dev.sh
./run_dev.sh

# 4. Probar el núcleo de descarga (sin UI)
python test_core.py
```

## Build para Windows (en máquina Windows)

1. Instalar **Python 3.11+** desde python.org (marcar "Add to PATH").
2. Clonar / copiar el proyecto en la máquina.
3. Abrir una terminal en la raíz del proyecto y ejecutar:

```cmd
build_windows.bat
```

4. El script creará un virtualenv, instalará dependencias, descargará
   ffmpeg (si no existe en `resources\`), y generará el .exe con Nuitka
   en `build\main.exe`.

5. **Opcional — Instalador:** abre `installer\setup.iss` con Inno Setup 6
   y compila. El instalador aparecerá en `dist\`.

## Estructura del proyecto

```
src/
├── main.py                 # Punto de entrada de la app
├── core/
│   ├── format_detector.py  # Detección de calidades disponibles
│   ├── downloader.py       # Gestor de descargas (cola, concurrencia)
│   ├── converter.py        # Conversión MP3/FLAC vía FFmpeg
│   └── metadata.py         # Metadatos ID3 y renombrado
└── ui/
    └── __init__.py         # Interfaz gráfica (próximamente)
test_core.py                # Prueba del núcleo sin UI
requirements.txt            # Dependencias fijadas
run_dev.sh                  # Script de desarrollo Linux
build_windows.bat           # Script de build Windows
```

## Nota legal

Esta herramienta descarga contenido de YouTube para uso personal.
Revisa los Términos de Servicio de YouTube antes de usarla.
