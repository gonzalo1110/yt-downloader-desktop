import os
import platform
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QSizePolicy, QVBoxLayout,
)

STATE_QUEUED = 'queued'
STATE_DOWNLOADING = 'downloading'
STATE_CONVERTING = 'converting'
STATE_COMPLETED = 'completed'
STATE_ERROR = 'error'

_BTN_TEXTS = {
    'open': '\U0001F4C2 Abrir ubicaci\u00f3n',
    'retry': '\U0001F504 Reintentar',
    'cancel': '\u25a0 Cancelar',
    'use_browser': '\U0001F511 Usar sesi\u00f3n',
}


class DownloadItem(QFrame):
    def __init__(
        self, task_id: str, title: str, icon: str,
        filepath: str = '', parent=None,
    ):
        super().__init__(parent)
        self.task_id = task_id
        self._filepath = filepath
        self._retry_data = None
        self._error_actions: list[str] = []
        self.setObjectName('downloadItem')
        self.setProperty('state', 'normal')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        row1 = QHBoxLayout()
        row1.setSpacing(10)

        self.icon_label = QLabel(icon)
        self.icon_label.setFixedWidth(28)
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel(title)
        self.title_label.setObjectName('itemTitle')
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.title_label.setWordWrap(True)

        self.action_btn = QPushButton()
        self.action_btn.setObjectName('actionBtn')

        self.browser_btn = QPushButton()
        self.browser_btn.setObjectName('browserBtn')
        self.browser_btn.setText(_BTN_TEXTS['use_browser'])
        self.browser_btn.setVisible(False)

        row1.addWidget(self.icon_label)
        row1.addWidget(self.title_label, 1)
        row1.addWidget(self.action_btn)
        row1.addWidget(self.browser_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName('itemProgress')
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)

        self.status_label = QLabel("En cola...")
        self.status_label.setObjectName('itemStatus')

        layout.addLayout(row1)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)

        self._set_state(STATE_QUEUED)

    def set_filepath(self, path: str):
        self._filepath = path

    def update_progress(self, percent: float, speed_mbps: float, text: str):
        if self.property('state') == STATE_ERROR:
            return
        state = STATE_CONVERTING if 'convirtiendo' in text.lower() else STATE_DOWNLOADING
        self._set_state(state)
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(text)

    def set_completed(self, filepath: str = ''):
        if filepath:
            self._filepath = filepath
        self._set_state(STATE_COMPLETED)
        self.progress_bar.setValue(100)
        self.status_label.setText("Completado")

    def set_error(self, message: str, actions: list[str] | None = None):
        self._error_actions = actions or ['retry']
        self._set_state(STATE_ERROR)
        self.progress_bar.setProperty('class', 'error')
        self.status_label.setProperty('state', 'error')
        self.status_label.setText(message)

    def set_retry_data(self, url: str, fmt: str, quality: str, out_dir: str):
        self._retry_data = (url, fmt, quality, out_dir)

    @property
    def filepath(self) -> str:
        return self._filepath

    def _set_state(self, state: str):
        self.state = state
        btn_text = ''
        btn_action = ''
        show_browser = False
        if state == STATE_QUEUED:
            btn_text = ''
            self.action_btn.setVisible(False)
        elif state in (STATE_DOWNLOADING, STATE_CONVERTING):
            btn_text = _BTN_TEXTS['cancel']
            btn_action = 'cancel'
            self.action_btn.setVisible(True)
        elif state == STATE_COMPLETED:
            btn_text = _BTN_TEXTS['open']
            btn_action = 'open'
            self.action_btn.setVisible(True)
        elif state == STATE_ERROR:
            acts = self._error_actions
            show_browser = 'use_browser' in acts and 'retry' in acts
            if 'retry' in acts:
                btn_text = _BTN_TEXTS['retry']
                btn_action = 'retry'
            elif 'use_browser' in acts:
                btn_text = _BTN_TEXTS['use_browser']
                btn_action = 'use_browser'
            else:
                btn_text = ''
                btn_action = ''
            self.action_btn.setVisible(bool(btn_text))

        self.action_btn.setText(btn_text)
        self.action_btn.setProperty('action', btn_action)
        self.action_btn.style().unpolish(self.action_btn)
        self.action_btn.style().polish(self.action_btn)

        self.browser_btn.setVisible(show_browser)
        if show_browser:
            self.browser_btn.setProperty('action', 'use_browser')
            self.browser_btn.style().unpolish(self.browser_btn)
            self.browser_btn.style().polish(self.browser_btn)

        if state == STATE_ERROR:
            self.setProperty('state', 'error')
        else:
            self.setProperty('state', 'normal')
        self.style().unpolish(self)
        self.style().polish(self)

    def connect_action(self, slot):
        try:
            self.action_btn.clicked.disconnect()
        except RuntimeError:
            pass
        self.action_btn.clicked.connect(slot)

    def connect_browser_action(self, slot):
        try:
            self.browser_btn.clicked.disconnect()
        except RuntimeError:
            pass
        self.browser_btn.clicked.connect(slot)
