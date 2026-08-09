import json
import logging
import os
import platform
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

from PySide6.QtCore import QThread, Signal, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from src.core.downloader import DownloadManager
from src.core.format_detector import (
    detect_available_qualities, validate_url, detect_url_type,
)
from src.core.error_handler import (
    ErrorCategory, actions_for_category,
)
from src.ui.download_item import (
    DownloadItem,
    STATE_COMPLETED,
    STATE_DOWNLOADING,
    STATE_CONVERTING,
    STATE_ERROR,
)
from src.ui.styles import STYLESHEET
from src.ui.toast import Toast


def _get_config_dir() -> Path:
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
    else:
        base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    return base / 'YTDownloader'


def _default_download_dir() -> str:
    return str(Path.home() / 'Downloads')


class Config:
    def __init__(self):
        self.config_dir = _get_config_dir()
        self.config_file = self.config_dir / 'config.json'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self._save()

    def _load(self) -> dict:
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self):
        try:
            self.config_file.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False),
                encoding='utf-8',
            )
        except OSError:
            pass


class FormatDetector(QThread):
    detected = Signal(list)
    failed = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            quals = detect_available_qualities(self.url)
            self.detected.emit(quals)
        except Exception as e:
            self.failed.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT Downloader")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        self.download_manager = DownloadManager(max_concurrent=2)
        self.config = Config()
        self.active_items: dict[str, DownloadItem] = {}
        self.format_detector: FormatDetector | None = None
        self._pending_url_type: str = 'video'
        self._pending_playlist_count: int = 0
        self._installed_browsers: list[str] = []

        self._setup_ui()
        self._connect_signals()
        self._load_config()
        self._detect_installed_browsers()

    # ── UI Setup ─────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self.setStyleSheet(STYLESHEET)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self._build_input_card(layout)
        self._build_scroll_area(layout)

    def _build_input_card(self, parent_layout: QVBoxLayout):
        card = QFrame()
        card.setObjectName('inputCard')
        card.setStyleSheet("""
            QFrame#inputCard {
                background-color: #FFFFFF;
                border: 1px solid #E8E8ED;
                border-radius: 12px;
            }
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(12)

        url_row = QHBoxLayout()
        url_row.setSpacing(8)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "Pega aquí el enlace de YouTube (video, short o playlist)..."
        )
        self.url_input.setClearButtonEnabled(True)
        self.paste_btn = QPushButton("📋 Pegar")
        self.paste_btn.setObjectName('pasteBtn')
        self.paste_btn.setCursor(Qt.PointingHandCursor)
        url_row.addWidget(self.url_input, 1)
        url_row.addWidget(self.paste_btn)

        opts = QHBoxLayout()
        opts.setSpacing(8)
        self.format_combo = QComboBox()
        self.format_combo.addItems(['MP4', 'MP3', 'FLAC'])
        self.quality_combo = QComboBox()
        self.quality_combo.setMinimumWidth(140)
        self.quality_combo.addItems(['720p', '1080p', '480p', '360p'])
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Carpeta de destino...")
        self.folder_input.setReadOnly(True)
        self.browse_btn = QPushButton("📁 Explorar")
        self.browse_btn.setObjectName('browseBtn')
        self.browse_btn.setCursor(Qt.PointingHandCursor)

        opts.addWidget(QLabel("Formato:"))
        opts.addWidget(self.format_combo)
        opts.addSpacing(4)
        opts.addWidget(QLabel("Calidad:"))
        opts.addWidget(self.quality_combo)
        opts.addSpacing(12)
        opts.addWidget(self.folder_input, 1)
        opts.addWidget(self.browse_btn)

        self.detect_label = QLabel("")
        self.detect_label.setStyleSheet(
            "color: #8E8E93; font-size: 12px; font-style: italic; padding: 2px 0;"
        )
        self.detect_label.setVisible(False)

        self.playlist_notice = QLabel("")
        self.playlist_notice.setStyleSheet(
            "color: #E67E22; font-size: 12px; padding: 4px 0;"
        )
        self.playlist_notice.setWordWrap(True)
        self.playlist_notice.setVisible(False)

        self.download_btn = QPushButton("↓  DESCARGAR")
        self.download_btn.setObjectName('downloadBtn')
        self.download_btn.setEnabled(False)
        self.download_btn.setCursor(Qt.PointingHandCursor)

        cl.addLayout(url_row)
        cl.addLayout(opts)
        cl.addWidget(self.detect_label)
        cl.addWidget(self.playlist_notice)
        cl.addWidget(self.download_btn)

        parent_layout.addWidget(card)

    def _build_scroll_area(self, parent_layout: QVBoxLayout):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        self.scroll_layout = QVBoxLayout(content)
        self.scroll_layout.setContentsMargins(0, 4, 0, 4)
        self.scroll_layout.setSpacing(2)

        header_row = QHBoxLayout()
        self.active_header = QLabel("Descargas activas")
        self.active_header.setObjectName('sectionHeader')
        self.active_header.setVisible(False)

        self.cancel_all_btn = QPushButton("✕ Cancelar todas")
        self.cancel_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFE0E0; color: #C0392B;
                font-size: 12px; padding: 4px 12px;
                border-radius: 4px; border: none;
            }
            QPushButton:hover { background-color: #FFCACA; }
        """)
        self.cancel_all_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_all_btn.setVisible(False)

        header_row.addWidget(self.active_header, 1)
        header_row.addWidget(self.cancel_all_btn)

        self.active_section = QVBoxLayout()
        self.active_section.setSpacing(4)

        self.completed_header = QLabel("Completadas")
        self.completed_header.setObjectName('sectionHeader')
        self.completed_header.setVisible(False)

        self.completed_section = QVBoxLayout()
        self.completed_section.setSpacing(4)

        self.scroll_layout.addLayout(header_row)
        self.scroll_layout.addLayout(self.active_section)
        self.scroll_layout.addSpacing(8)
        self.scroll_layout.addWidget(self.completed_header)
        self.scroll_layout.addLayout(self.completed_section)
        self.scroll_layout.addStretch()

        scroll.setWidget(content)
        parent_layout.addWidget(scroll, 1)

    # ── Signal Connections ───────────────────────────────────────

    def _connect_signals(self):
        self.paste_btn.clicked.connect(self._on_paste)
        self.url_input.returnPressed.connect(self._on_url_submit)
        self.url_input.textChanged.connect(self._on_url_text_changed)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        self.browse_btn.clicked.connect(self._on_browse)
        self.download_btn.clicked.connect(self._on_download)
        self.cancel_all_btn.clicked.connect(self._on_cancel_all)

        self.download_manager.signals.progress.connect(self._on_progress)
        self.download_manager.signals.completed.connect(self._on_completed)
        self.download_manager.signals.error.connect(self._on_error)
        self.download_manager.signals.status_message.connect(
            self._on_status_message
        )

    # ── Config ────────────────────────────────────────────────────

    def _load_config(self):
        folder = self.config.get('download_dir', _default_download_dir())
        self.folder_input.setText(folder)
        self._update_download_btn()

    def _save_folder(self):
        folder = self.folder_input.text().strip()
        if folder:
            self.config.set('download_dir', folder)

    def _update_download_btn(self):
        url = self.url_input.text().strip()
        folder = self.folder_input.text().strip()
        self.download_btn.setEnabled(bool(url) and bool(folder))

    # ── URL / Format detection ────────────────────────────────────

    def _on_paste(self):
        url = QApplication.clipboard().text().strip()
        if url:
            self.url_input.setText(url)
            self._trigger_detection(url)
            self._check_url_type(url)

    def _on_url_submit(self):
        url = self.url_input.text().strip()
        if url:
            self._trigger_detection(url)
            self._check_url_type(url)

    def _check_url_type(self, url: str):
        self.playlist_notice.setVisible(False)
        self._pending_url_type = 'video'
        self._pending_playlist_count = 0

        if not validate_url(url):
            return

        url_type, count = detect_url_type(url)

        if url_type == 'video_in_playlist':
            self._pending_url_type = 'video_in_playlist'
            self.playlist_notice.setText(
                "ℹ️  Este enlace pertenece a una lista de reproducción. "
                "Se descargará solo este video. Si quieres toda la "
                "lista, pega el enlace de la playlist directamente."
            )
            self.playlist_notice.setVisible(True)

        elif url_type == 'playlist':
            self._pending_url_type = 'playlist'
            self._pending_playlist_count = count
            msg = (
                f"ℹ️  Lista de reproducción detectada: {count} videos. "
                "Presiona DESCARGAR para elegir qué hacer."
            )
            self.playlist_notice.setText(msg)
            self.playlist_notice.setVisible(True)

    def _on_cancel_all(self):
        reply = QMessageBox.question(
            self,
            "Cancelar todas las descargas",
            "¿Estás seguro de que quieres cancelar todas las "
            "descargas activas y pendientes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            for tid in list(self.active_items.keys()):
                item = self.active_items.pop(tid, None)
                if item:
                    self.active_section.removeWidget(item)
                    item.deleteLater()
            self.download_manager.cancel_all()
            self._update_section_visibility()

    def _on_url_text_changed(self, text: str):
        self._update_download_btn()

    def _trigger_detection(self, url: str):
        if self.format_detector and self.format_detector.isRunning():
            self.format_detector.quit()
            self.format_detector.wait()

        if not validate_url(url):
            self.detect_label.setText(
                "⚠️  URL no válida. Debe ser un enlace de YouTube."
            )
            self.detect_label.setVisible(True)
            self._update_download_btn()
            return

        self.detect_label.setText("⏳ Detectando calidades disponibles...")
        self.detect_label.setVisible(True)

        self.format_detector = FormatDetector(url)
        self.format_detector.detected.connect(self._on_formats_detected)
        self.format_detector.failed.connect(self._on_formats_failed)
        self.format_detector.start()

    def _on_formats_detected(self, qualities: list[str]):
        self._last_qualities = qualities
        self.detect_label.setVisible(False)
        self._populate_quality_combo()
        self._update_download_btn()

    def _on_formats_failed(self, error_msg: str):
        self._last_qualities = None
        self.detect_label.setText(
            f"⚠️  No se pudieron detectar calidades. Usando valores por defecto."
        )
        self._populate_quality_combo()

    def _populate_quality_combo(self):
        fmt = self.format_combo.currentText()
        self.quality_combo.blockSignals(True)
        self.quality_combo.clear()

        if fmt == 'MP4':
            quals = (
                getattr(self, '_last_qualities', None)
                or ['1080p', '720p', '480p', '360p']
            )
            for q in quals:
                self.quality_combo.addItem(q)
            self.quality_combo.setEnabled(True)
        elif fmt == 'MP3':
            self.quality_combo.addItems(['192kbps', '320kbps'])
            self.quality_combo.setEnabled(True)
        else:
            self.quality_combo.addItem('Calidad original (FLAC)')
            self.quality_combo.setEnabled(False)

        self.quality_combo.blockSignals(False)

    # ── UI Action handlers ────────────────────────────────────────

    def _on_format_changed(self, _index: int):
        self._populate_quality_combo()

    def _on_browse(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de destino",
            self.folder_input.text() or _default_download_dir(),
        )
        if folder:
            self.folder_input.setText(folder)
            self._save_folder()
            self._update_download_btn()

    def _on_download(self):
        url = self.url_input.text().strip()
        fmt = self.format_combo.currentText()
        quality = self.quality_combo.currentText()
        folder = self.folder_input.text().strip()

        if not url or not folder:
            return

        if self._pending_url_type == 'playlist':
            count = self._pending_playlist_count
            ok = self._confirm_playlist_download(count)
            if not ok:
                return
            noplaylist = False
        elif self._pending_url_type == 'video_in_playlist':
            noplaylist = True
        else:
            noplaylist = False

        self.playlist_notice.setVisible(False)

        output_format = fmt.lower()
        quality_label = quality
        icon = '🎬' if output_format == 'mp4' else '🎵'

        cookies_browser = self.config.get('cookies_browser')
        task_id = self.download_manager.enqueue(
            url, output_format, quality_label, folder,
            noplaylist=noplaylist,
            cookies_from_browser=cookies_browser,
        )

        item = DownloadItem(task_id, "Obteniendo información...", icon)
        item.set_retry_data(url, output_format, quality_label, folder)
        item.connect_action(lambda: self._handle_item_action(item, 'cancel'))
        item.connect_browser_action(lambda: self._handle_item_action(item, 'use_browser'))

        self.active_section.addWidget(item)
        self.active_items[task_id] = item
        self._update_section_visibility()

    def _confirm_playlist_download(self, count: int) -> bool:
        msg = QMessageBox(self)
        msg.setWindowTitle("Lista de reproducción detectada")
        text = f"Esta es una lista de reproducción con {count} videos."
        if count > 20:
            text += (
                "\n\n⚠️  Son más de 20 videos. Esto puede tardar bastante "
                "y ocupar mucho espacio en disco."
            )
        text += "\n\n¿Qué quieres hacer?"
        msg.setText(text)
        msg.setIcon(QMessageBox.Question)
        download_btn = msg.addButton(
            f"Descargar todos ({count})", QMessageBox.AcceptRole
        )
        msg.addButton("Cancelar", QMessageBox.RejectRole)
        msg.setDefaultButton(download_btn)
        msg.exec()
        return msg.clickedButton() == download_btn

    def _handle_item_action(self, item: DownloadItem, action: str = 'open'):
        if action == 'open':
            if item.filepath:
                self._open_file_location(item.filepath)

        elif action == 'retry':
            if item._retry_data:
                url, fmt, quality, out_dir = item._retry_data
                old_id = item.task_id
                cookies_browser = self.config.get('cookies_browser')
                new_id = self.download_manager.enqueue(
                    url, fmt, quality, out_dir,
                    cookies_from_browser=cookies_browser,
                )
                item.task_id = new_id
                self.active_items[new_id] = item
                self.active_items.pop(old_id, None)
                item.set_filepath('')
                item.update_progress(0, 0, "Reintentando...")

        elif action == 'use_browser':
            self._handle_use_browser(item)

        elif action == 'cancel':
            if item.state in (STATE_DOWNLOADING, STATE_CONVERTING):
                self.download_manager.cancel(item.task_id)

    def _handle_use_browser(self, item: DownloadItem):
        if not item._retry_data:
            return

        cookies_browser = self.config.get('cookies_browser')
        if not cookies_browser:
            if not self._installed_browsers:
                Toast(
                    self,
                    "No encontramos un navegador compatible con sesi\u00f3n "
                    "iniciada. Abre YouTube en Chrome o Firefox, "
                    "inicia sesi\u00f3n, y vuelve a intentar.",
                    'error',
                ).show()
                return
            if len(self._installed_browsers) == 1:
                cookies_browser = self._installed_browsers[0]
            else:
                chosen = self._ask_browser_selection()
                if not chosen:
                    return
                cookies_browser = chosen
            self.config.set('cookies_browser', cookies_browser)

        url, fmt, quality, out_dir = item._retry_data
        old_id = item.task_id
        new_id = self.download_manager.enqueue(
            url, fmt, quality, out_dir,
            cookies_from_browser=cookies_browser,
        )
        item.task_id = new_id
        self.active_items[new_id] = item
        self.active_items.pop(old_id, None)
        item.set_filepath('')
        item.update_progress(0, 0, "Reintentando con sesi\u00f3n...")

    def _ask_browser_selection(self) -> str | None:
        msg = QMessageBox(self)
        msg.setWindowTitle("Seleccionar navegador")
        msg.setText(
            "\u00bfCon qu\u00e9 navegador tienes sesi\u00f3n iniciada "
            "en YouTube?"
        )
        msg.setIcon(QMessageBox.Question)
        browser_buttons = {}
        for b in self._installed_browsers:
            browser_buttons[msg.addButton(
                b.capitalize(), QMessageBox.ActionRole
            )] = b
        msg.addButton("Cancelar", QMessageBox.RejectRole)
        msg.exec()
        clicked = msg.clickedButton()
        return browser_buttons.get(clicked)

    # ── DownloadManager signal handlers ──────────────────────────

    def _on_progress(
        self, task_id: str, percent: float, speed_mbps: float, text: str
    ):
        item = self.active_items.get(task_id)
        if item:
            item.update_progress(percent, speed_mbps, text)

    def _on_completed(self, task_id: str, filepath: str):
        item = self.active_items.pop(task_id, None)
        if not item:
            return

        idx = self.active_section.indexOf(item)
        if idx >= 0:
            self.active_section.removeWidget(item)

        item.set_completed(filepath)
        item.connect_action(lambda: self._handle_item_action(item, 'open'))
        self.completed_section.insertWidget(0, item)
        self._update_section_visibility()

        Toast(self, "\u00a1Descarga completada!", 'success').show()

    def _on_error(self, task_id: str, error_msg: str, category: str = 'unknown'):
        item = self.active_items.get(task_id)
        if not item:
            return

        if category == ErrorCategory.CANCELLED.value:
            self.active_section.removeWidget(item)
            self.active_items.pop(task_id, None)
            item.deleteLater()
            self._update_section_visibility()
            return

        act = actions_for_category(ErrorCategory(category))
        item.set_error(error_msg, actions=act)
        item.connect_action(
            lambda: self._handle_item_action(item, 'retry' if 'retry' in act else 'use_browser' if 'use_browser' in act else 'open')
        )
        item.connect_browser_action(
            lambda: self._handle_item_action(item, 'use_browser')
        )
        Toast(self, error_msg[:120], 'error').show()

    def _on_status_message(self, task_id: str, message: str):
        item = self.active_items.get(task_id)
        if item and "convirtiendo" in message.lower():
            item.update_progress(99.9, 0, message)

    # ── Browser detection ───────────────────────────────────────

    def _detect_installed_browsers(self):
        self._installed_browsers = []
        if sys.platform == 'win32':
            local = os.environ.get('LOCALAPPDATA', '')
            roaming = os.environ.get('APPDATA', '')
            paths = {
                'chrome': os.path.join(local, 'Google', 'Chrome', 'User Data'),
                'chromium': os.path.join(local, 'Chromium', 'User Data'),
                'edge': os.path.join(local, 'Microsoft', 'Edge', 'User Data'),
                'brave': os.path.join(local, 'BraveSoftware', 'Brave-Browser', 'User Data'),
                'opera': os.path.join(local, 'Opera Software', 'Opera Stable'),
                'vivaldi': os.path.join(local, 'Vivaldi', 'User Data'),
                'firefox': os.path.join(roaming, 'Mozilla', 'Firefox', 'Profiles'),
            }
        else:
            home = os.path.expanduser('~')
            xdg = os.environ.get('XDG_CONFIG_HOME', os.path.join(home, '.config'))
            paths = {
                'chrome': os.path.join(xdg, 'google-chrome'),
                'chromium': os.path.join(xdg, 'chromium'),
                'edge': os.path.join(xdg, 'microsoft-edge'),
                'brave': os.path.join(xdg, 'BraveSoftware', 'Brave-Browser'),
                'opera': os.path.join(home, '.config', 'opera'),
                'vivaldi': os.path.join(xdg, 'vivaldi'),
                'firefox': os.path.join(home, '.mozilla', 'firefox'),
            }

        for browser, profile_path in paths.items():
            if os.path.isdir(profile_path):
                if browser == 'firefox':
                    if os.path.exists(os.path.join(profile_path, 'profiles.ini')):
                        self._installed_browsers.append(browser)
                elif browser in ('opera',) and sys.platform != 'darwin':
                    if any(os.path.isdir(os.path.join(profile_path, d))
                           for d in os.listdir(profile_path)
                           if os.path.isdir(os.path.join(profile_path, d))):
                        self._installed_browsers.append(browser)
                else:
                    profiles = [d for d in os.listdir(profile_path)
                                if d.startswith(('Default', 'Profile'))
                                and os.path.isdir(os.path.join(profile_path, d))]
                    if profiles:
                        self._installed_browsers.append(browser)

        logger.info(f"Navegadores detectados: {self._installed_browsers}")

    # ── Helpers ──────────────────────────────────────────────────

    def _open_file_location(self, filepath: str):
        if platform.system() == 'Windows':
            subprocess.run(
                ['explorer', '/select,', os.path.normpath(filepath)],
                check=False,
            )
        else:
            dir_path = os.path.dirname(filepath)
            QDesktopServices.openUrl(QUrl.fromLocalFile(dir_path))

    def _update_section_visibility(self):
        has_active = self.active_section.count() > 0
        self.active_header.setVisible(has_active)
        self.cancel_all_btn.setVisible(has_active)
        self.completed_header.setVisible(self.completed_section.count() > 0)
