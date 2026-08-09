import subprocess
import os
import sys
import shutil
import logging

from .binaries import find_ffmpeg

logger = logging.getLogger(__name__)


def _get_ffmpeg_path() -> str:
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        return ffmpeg
    raise FileNotFoundError(
        "FFmpeg no encontrado. Aseg\u00fbrate de que ffmpeg est\u00e9 instalado o "
        "incluido en el paquete."
    )


def convert_to_mp3(
    input_file: str, output_file: str, bitrate: str = '192'
) -> str:
    ffmpeg = _get_ffmpeg_path()
    cmd = [
        ffmpeg, '-i', input_file,
        '-vn',
        '-acodec', 'libmp3lame',
        '-ab', f'{bitrate}k',
        '-y',
        output_file,
    ]
    logger.info(f"Convirtiendo a MP3 {bitrate}kbps: {input_file}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Error al convertir a MP3: {result.stderr[:500]}"
        )
    return output_file


def convert_to_flac(input_file: str, output_file: str) -> str:
    ffmpeg = _get_ffmpeg_path()
    cmd = [
        ffmpeg, '-i', input_file,
        '-vn',
        '-acodec', 'flac',
        '-y',
        output_file,
    ]
    logger.info(f"Convirtiendo a FLAC: {input_file}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Error al convertir a FLAC: {result.stderr[:500]}"
        )
    return output_file
