import os
import sys
import shutil
import logging

logger = logging.getLogger(__name__)


def _extra_binary_path() -> str | None:
    if sys.platform == 'win32':
        return 'ffmpeg.exe'
    return None


def _find_binary(name: str) -> str | None:
    exe_name = f'{name}.exe' if sys.platform == 'win32' else name

    exe_dir = os.path.dirname(sys.executable)
    candidate = os.path.join(exe_dir, exe_name)
    if os.path.exists(candidate):
        logger.debug(f'{name} encontrado junto al ejecutable: {candidate}')
        return candidate

    parent = os.environ.get('NUITKA_ONEFILE_PARENT')
    if parent:
        candidate = os.path.join(parent, exe_name)
        if os.path.exists(candidate):
            logger.debug(f'{name} encontrado en NUITKA_ONEFILE_PARENT: {candidate}')
            return candidate

    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        candidate = os.path.join(meipass, exe_name)
        if os.path.exists(candidate):
            logger.debug(f'{name} encontrado en _MEIPASS: {candidate}')
            return candidate

    found = shutil.which(exe_name)
    if found:
        return found

    if sys.platform != 'win32':
        found = shutil.which(name)
        if found:
            return found

    return None


def find_ffmpeg() -> str | None:
    return _find_binary('ffmpeg')


def find_ffprobe() -> str | None:
    return _find_binary('ffprobe')


def find_deno() -> str | None:
    return _find_binary('deno')


def get_binaries_dir() -> str | None:
    for name in ('ffmpeg', 'ffprobe'):
        path = _find_binary(name)
        if path:
            return os.path.dirname(path)
    return None
