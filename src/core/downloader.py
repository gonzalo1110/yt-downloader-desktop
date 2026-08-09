import os
import sys
import time
import uuid
import logging
from dataclasses import dataclass, field
from typing import Optional, Callable

import yt_dlp
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool

from .format_detector import QUALITY_MAP, AUDIO_FORMATS
from .converter import convert_to_mp3, convert_to_flac
from .metadata import get_video_metadata, tag_audio_file, sanitize_filename
from .error_handler import (
    ErrorCategory,
    classify_error,
    user_message_for_category,
    actions_for_category,
)
from .binaries import find_deno, get_binaries_dir

logger = logging.getLogger(__name__)

_REMOTE_OPTS = {'remote_components': ['ejs:github']}

_deno_path = find_deno()
_deno_available = _deno_path is not None
if _deno_available:
    logger.info(f"Deno runtime detected at {_deno_path}")
else:
    logger.warning(
        "Deno runtime NOT detected. yt-dlp may fall back to other JS engines. "
        "Install deno for better YouTube anti-bot compatibility."
    )

_FFFMPEG_DIR = get_binaries_dir()


@dataclass
class DownloadTask:
    url: str
    output_format: str
    quality: str
    output_dir: str
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    noplaylist: bool = False
    title: str = ''
    cookies_from_browser: Optional[str] = None
    progress_callback: Optional[Callable] = None
    complete_callback: Optional[Callable] = None
    error_callback: Optional[Callable] = None


class DownloadSignals(QObject):
    progress = Signal(str, float, float, str)
    completed = Signal(str, str)
    error = Signal(str, str, str)  # task_id, user_msg, category
    status_message = Signal(str, str)


class DownloadRunnable(QRunnable):
    def __init__(self, task: DownloadTask, signals: DownloadSignals):
        super().__init__()
        self.task = task
        self.signals = signals
        self._cancelled = False
        self._retry_count = 0

    def cancel(self):
        self._cancelled = True

    # ── Top-level runner with silent auto-retry ─────────────────

    def run(self):
        tid = self.task.task_id
        try:
            self._do_download()
        except yt_dlp.utils.DownloadError as e:
            if self._cancelled:
                self._emit_error(tid, "Descarga cancelada", ErrorCategory.CANCELLED)
                return

            err_text = str(e)
            category = classify_error(err_text)

            if category == ErrorCategory.BOT_CHECK and self._retry_count == 0:
                self._retry_count += 1
                self.signals.status_message.emit(tid, "Reintentando...")
                time.sleep(3)
                try:
                    self._do_download()
                    return
                except Exception as retry_e:
                    rmsg = str(retry_e)
                    rcat = classify_error(rmsg)
                    if rcat in (ErrorCategory.BOT_CHECK, ErrorCategory.UNKNOWN):
                        rcat = ErrorCategory.BOT_CHECK
                    self._emit_error(tid, rmsg, rcat)
                return

            self._emit_error(tid, err_text, category)

        except yt_dlp.utils.ExtractorError as e:
            self._emit_error(tid, str(e), classify_error(str(e)))
        except yt_dlp.utils.UnavailableVideoError:
            self._emit_error(tid, "Video no disponible", ErrorCategory.UNAVAILABLE)
        except FileNotFoundError as e:
            self._emit_error(tid, str(e), ErrorCategory.UNKNOWN)
        except Exception as e:
            logger.exception(f"Error inesperado en tarea {tid}")
            self._emit_error(
                tid, f"Error inesperado: {_short_msg(e)}", ErrorCategory.UNKNOWN
            )

    def _emit_error(self, tid: str, raw_msg: str, category: ErrorCategory):
        user_msg = user_message_for_category(category, raw_msg)
        self.signals.error.emit(tid, user_msg, category.value)

    # ── Actual download logic ──────────────────────────────────

    def _do_download(self):
        tid = self.task.task_id

        self.signals.status_message.emit(tid, "Obteniendo información...")
        self.signals.progress.emit(tid, 0, 0, "Iniciando...")

        self.task.title = ''

        def progress_hook(d):
            if self._cancelled:
                raise yt_dlp.utils.DownloadError("Descarga cancelada por el usuario")

            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
                downloaded = d.get('downloaded_bytes', 0)
                percent = min((downloaded / total) * 100, 99.9)
                speed_bps = d.get('speed') or 0
                speed_mbps = speed_bps / 1_048_576
                eta = d.get('eta', 0)
                status_text = f"{percent:.1f}%"
                if speed_mbps > 0:
                    status_text += f" — {speed_mbps:.1f} MB/s"
                if eta:
                    status_text += f" — {_format_eta(eta)} rest."
                self.signals.progress.emit(tid, percent, speed_mbps, status_text)

            elif d['status'] == 'finished':
                self.signals.progress.emit(tid, 100, 0, "Procesando...")

        is_audio = self.task.output_format in ('mp3', 'flac')
        if is_audio:
            fmt = 'bestaudio/best'
        else:
            fmt = QUALITY_MAP.get(self.task.quality, QUALITY_MAP['720p'])

        ydl_opts = {
            'progress_hooks': [progress_hook],
            'outtmpl': os.path.join(
                self.task.output_dir, '%(title)s.%(ext)s'
            ),
            'format': fmt,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'merge_output_format': 'mp4' if not is_audio else None,
            'noplaylist': self.task.noplaylist,
            **_REMOTE_OPTS,
        }

        if _FFFMPEG_DIR:
            ydl_opts['ffmpeg_location'] = _FFFMPEG_DIR

        if _deno_path:
            ydl_opts['js_runtimes'] = {'deno': {'path': _deno_path}}

        if self.task.cookies_from_browser:
            ydl_opts['cookiesfrombrowser'] = (self.task.cookies_from_browser,)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.task.url, download=True)
            self.task.title = info.get('title', 'Video')
            temp_path = ydl.prepare_filename(info)

        if not os.path.exists(temp_path):
            temp_path = _find_downloaded_file(
                self.task.output_dir, self.task.title
            )

        if self._cancelled:
            self._cleanup(temp_path)
            return

        if is_audio:
            self.signals.status_message.emit(tid, "Convirtiendo audio...")
            metadata = get_video_metadata(info)
            ext = 'mp3' if self.task.output_format == 'mp3' else 'flac'
            safe_title = sanitize_filename(metadata['title'])
            artist_slug = sanitize_filename(metadata.get('artist', ''))
            if artist_slug and artist_slug != 'Unknown_Artist':
                audio_filename = f"{artist_slug} - {safe_title}.{ext}"
            else:
                audio_filename = f"{safe_title}.{ext}"

            output_path = os.path.join(
                self.task.output_dir, audio_filename
            )
            output_path = _uniquify(output_path)

            if self.task.output_format == 'mp3':
                bitrate = '192'
                if self.task.quality == 'MP3 320kbps':
                    bitrate = '320'
                convert_to_mp3(temp_path, output_path, bitrate)
            else:
                convert_to_flac(temp_path, output_path)

            tag_audio_file(output_path, metadata)
            self._cleanup(temp_path)
            final_path = output_path
        else:
            final_path = temp_path

        self.signals.completed.emit(tid, final_path)

    def _cleanup(self, path: str):
        try:
            if path and os.path.exists(path):
                os.remove(path)
                logger.info(f"Archivo temporal eliminado: {path}")
        except Exception:
            pass


class DownloadManager(QObject):
    def __init__(self, max_concurrent: int = 2):
        super().__init__()
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(max_concurrent)
        self.signals = DownloadSignals()
        self._pending_queue: list[DownloadRunnable] = []
        self._active_runnables: dict[str, DownloadRunnable] = {}

        self.signals.completed.connect(self._on_task_done)
        self.signals.error.connect(self._on_task_done)

    @property
    def max_concurrent(self) -> int:
        return self.pool.maxThreadCount()

    @property
    def pending_count(self) -> int:
        return len(self._pending_queue)

    @property
    def active_count(self) -> int:
        return len(self._active_runnables)

    def enqueue(
        self,
        url: str,
        output_format: str,
        quality: str,
        output_dir: str,
        noplaylist: bool = False,
        cookies_from_browser: Optional[str] = None,
    ) -> str:
        task = DownloadTask(
            url=url,
            output_format=output_format,
            quality=quality,
            output_dir=output_dir,
            noplaylist=noplaylist,
            cookies_from_browser=cookies_from_browser,
        )
        runnable = DownloadRunnable(task, self.signals)
        logger.info(
            f"Encolada tarea {task.task_id}: {url} "
            f"({output_format}, {quality})"
        )

        if self.pool.activeThreadCount() < self.pool.maxThreadCount():
            self._start_runnable(runnable)
        else:
            self._pending_queue.append(runnable)

        return task.task_id

    def _start_runnable(self, runnable: DownloadRunnable):
        self._active_runnables[runnable.task.task_id] = runnable
        self.pool.start(runnable)

    def _process_queue(self):
        while (
            self._pending_queue
            and self.pool.activeThreadCount() < self.pool.maxThreadCount()
        ):
            runnable = self._pending_queue.pop(0)
            self._start_runnable(runnable)

    def _on_task_done(self, task_id: str, *args):
        self._active_runnables.pop(task_id, None)
        self._process_queue()

    def cancel(self, task_id: str) -> bool:
        canceled = ErrorCategory.CANCELLED.value
        for i, r in enumerate(self._pending_queue):
            if r.task.task_id == task_id:
                self._pending_queue.pop(i)
                self.signals.error.emit(task_id, "Descarga cancelada", canceled)
                logger.info(f"Tarea cancelada (en cola): {task_id}")
                return True

        runnable = self._active_runnables.pop(task_id, None)
        if runnable:
            runnable.cancel()
            self.signals.error.emit(task_id, "Descarga cancelada", canceled)
            self._process_queue()
            logger.info(f"Tarea cancelada (activa): {task_id}")
            return True

        return False

    def cancel_all(self):
        canceled = ErrorCategory.CANCELLED.value
        pend_count = len(self._pending_queue)
        for r in self._pending_queue:
            self.signals.error.emit(r.task.task_id, "Descarga cancelada", canceled)
        self._pending_queue.clear()

        act_count = len(self._active_runnables)
        for tid, runnable in list(self._active_runnables.items()):
            runnable.cancel()
        self._active_runnables.clear()

        logger.info(
            f"Canceladas todas: {pend_count} pendientes, "
            f"{act_count} activas"
        )


def _format_eta(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}h {minutes}m"


def _short_msg(e: Exception) -> str:
    msg = str(e)
    return msg[:200] + '...' if len(msg) > 200 else msg


def _find_downloaded_file(directory: str, title: str) -> str:
    for fname in os.listdir(directory):
        if title.lower() in fname.lower():
            return os.path.join(directory, fname)
    safe = sanitize_filename(title)
    for fname in os.listdir(directory):
        if safe.lower() in fname.lower():
            return os.path.join(directory, fname)
    raise FileNotFoundError(
        f"No se encontró el archivo descargado para: {title}"
    )


def _uniquify(path: str) -> str:
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    counter = 1
    while True:
        new_path = f"{base}_{counter}{ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1
