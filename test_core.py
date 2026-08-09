#!/usr/bin/env python3
"""
Test del núcleo de descarga — prueba 2–3 descargas simultáneas
desde consola SIN necesidad de la UI.

Uso:
    python test_core.py [URL1] [URL2] [URL3]

Si no se pasan URLs, usa unos defaults públicos de prueba.
"""

import sys
import os
import tempfile
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from PySide6.QtCore import QCoreApplication, QTimer

# ── Silenciar logs de yt-dlp y los nuestros ──────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s %(message)s'
)

from core.downloader import DownloadManager
from core.format_detector import detect_available_qualities, validate_url


# ── URLs de prueba públicas (cortesía de Blender Foundation) ──────────
DEFAULT_URLS = [
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ',   # Rick Astley
    'https://www.youtube.com/watch?v=LXb3EKWsInQ',   # Blender — Big Buck Bunny
    'https://www.youtube.com/watch?v=YE7VzlLtp-4',   # Blender — Sintel
]

TEST_FORMAT = 'mp3'       # mp4 / mp3 / flac
TEST_QUALITY = '720p'     # 1080p / 720p / 480p / 360p
TEST_AUDIO_QUALITY = 'MP3 192kbps'


def main():
    urls = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_URLS

    for url in urls:
        if not validate_url(url):
            print(f"⚠️  URL inválida o no soportada: {url}")
            return 1

    app = QCoreApplication(sys.argv)

    out_dir = tempfile.mkdtemp(prefix='yt_test_')
    print(f"📁 Carpeta de salida: {out_dir}\n")

    manager = DownloadManager(max_concurrent=2)
    results = {}
    remaining = len(urls)

    # ── Conectar señales ─────────────────────────────────────────────
    manager.signals.progress.connect(
        lambda tid, pct, speed, txt: print(
            f"  [{tid[:6]}][{pct:5.1f}%] {txt}"
        )
    )
    manager.signals.status_message.connect(
        lambda tid, msg: print(f"  [{tid[:6]}] {msg}")
    )
    manager.signals.completed.connect(
        lambda tid, path: (
            print(f"  ✅ [{tid[:6]}] Completado → {path}"),
            handle_done(tid)
        )
    )
    manager.signals.error.connect(
        lambda tid, err: (
            print(f"  ❌ [{tid[:6]}] ERROR: {err}"),
            handle_done(tid)
        )
    )

    def handle_done(tid):
        nonlocal remaining
        remaining -= 1
        if remaining <= 0:
            print(f"\n📁 Todos los archivos en: {out_dir}")
            QCoreApplication.quit()

    # ── Encolar descargas ────────────────────────────────────────────
    for i, url in enumerate(urls, 1):
        print(f"\n🎬 [{i}/{len(urls)}] Analizando: {url}")

        try:
            qualities = detect_available_qualities(url)
            print(f"   Calidades detectadas: {', '.join(qualities)}")
        except Exception as e:
            print(f"   ⚠️  No se pudieron detectar calidades: {e}")

        if TEST_FORMAT == 'mp4':
            q = TEST_QUALITY
            if qualities and TEST_QUALITY not in qualities:
                q = qualities[0]
            fmt_name = 'mp4'
            q_label = q
        else:
            q_label = TEST_AUDIO_QUALITY
            fmt_name = TEST_FORMAT

        task_id = manager.enqueue(url, fmt_name, q_label, out_dir)
        print(f"   🆔 Tarea: {task_id[:12]}")

    # ── Timer de seguridad por si algo cuelga (5 min) ────────────────
    def force_quit():
        print("\n⏰ Timeout: forzando salida.")
        QCoreApplication.quit()

    QTimer.singleShot(300_000, force_quit)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
