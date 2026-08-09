from PySide6.QtCore import QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import QGraphicsOpacityEffect
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel


class Toast(QFrame):
    def __init__(self, parent, message: str, toast_type: str = 'success'):
        super().__init__(parent)
        self.setObjectName('toast')
        self.setWindowFlags(Qt.WindowFlags(
            Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        ))
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        icon = '✓' if toast_type == 'success' else '✕'
        self.label = QLabel(f"{icon}  {message}")
        self.label.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: white;"
        )
        layout.addWidget(self.label)

        if toast_type == 'success':
            bg = "#2ECC71"
        else:
            bg = "#E74C3C"

        self.setStyleSheet(
            f"background-color: {bg}; border-radius: 8px;"
        )
        self.adjustSize()
        self.setFixedWidth(min(self.width() + 32, 420))

        parent_rect = parent.rect()
        x = parent_rect.width() - self.width() - 20
        y = 24
        self.move(x, y)

        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(0.0)

        self.fade_in = QPropertyAnimation(self.effect, b"opacity")
        self.fade_in.setDuration(250)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.start()

        QTimer.singleShot(3000, self._fade_out)

    def _fade_out(self):
        self.fade_out_anim = QPropertyAnimation(self.effect, b"opacity")
        self.fade_out_anim.setDuration(300)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.finished.connect(self.deleteLater)
        self.fade_out_anim.start()
