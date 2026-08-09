STYLESHEET = """
QMainWindow, QWidget {
    background-color: #F5F5F7;
    color: #1D1D1F;
    font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #F5F5F7;
}

QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #D1D1D6;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    color: #1D1D1F;
}

QLineEdit:focus {
    border: 2px solid #2ECC71;
    padding: 7px 11px;
}

QLineEdit:disabled {
    background-color: #F0F0F2;
    color: #8E8E93;
}

QPushButton {
    background-color: #E8E8ED;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
    color: #1D1D1F;
}

QPushButton:hover {
    background-color: #D1D1D6;
}

QPushButton:pressed {
    background-color: #C7C7CC;
}

QPushButton:disabled {
    background-color: #F0F0F2;
    color: #B2B2B2;
}

QPushButton#downloadBtn {
    background-color: #2ECC71;
    color: #FFFFFF;
    font-size: 16px;
    font-weight: bold;
    padding: 14px 32px;
    border-radius: 10px;
    letter-spacing: 0.5px;
}

QPushButton#downloadBtn:hover {
    background-color: #27AE60;
}

QPushButton#downloadBtn:pressed {
    background-color: #219A52;
}

QPushButton#downloadBtn:disabled {
    background-color: #B2B2B2;
    color: #E8E8ED;
}

QPushButton#pasteBtn {
    background-color: #2ECC71;
    color: #FFFFFF;
    font-weight: 600;
    padding: 8px 18px;
}

QPushButton#pasteBtn:hover {
    background-color: #27AE60;
}

QPushButton#browseBtn {
    font-size: 18px;
    padding: 8px 14px;
}

QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #D1D1D6;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    color: #1D1D1F;
    min-width: 120px;
}

QComboBox:hover {
    border-color: #2ECC71;
}

QComboBox:disabled {
    background-color: #F0F0F2;
    color: #8E8E93;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #D1D1D6;
    border-radius: 6px;
    padding: 4px;
    selection-background-color: #E8F8F0;
    selection-color: #1D1D1F;
    outline: none;
}

QProgressBar {
    background-color: #E8E8ED;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: left;
    font-size: 11px;
    color: transparent;
}

QProgressBar::chunk {
    background-color: #2ECC71;
    border-radius: 4px;
}

QProgressBar#errorProgress::chunk {
    background-color: #E74C3C;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #C7C7CC;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #AEAEB2;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QFrame#downloadItem {
    background-color: #FFFFFF;
    border: 1px solid #E8E8ED;
    border-radius: 8px;
    padding: 0px;
    margin: 4px 0px;
}

QFrame#downloadItem:hover {
    border-color: #D1D1D6;
}

QFrame#downloadItem[state="error"] {
    border-color: #F5C6CB;
    background-color: #FDF2F2;
}

QLabel#sectionHeader {
    font-size: 13px;
    font-weight: 600;
    color: #8E8E93;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 12px 4px 4px 4px;
    margin: 0;
}

QLabel#itemTitle {
    font-size: 13px;
    font-weight: 500;
    color: #1D1D1F;
}

QLabel#itemStatus {
    font-size: 12px;
    color: #8E8E93;
}

QLabel#itemStatus[state="error"] {
    color: #E74C3C;
    font-weight: 500;
}

QPushButton#actionBtn {
    padding: 6px 12px;
    font-size: 12px;
    border-radius: 4px;
    min-width: 80px;
}

QPushButton#actionBtn[action="cancel"] {
    background-color: #FFE0E0;
    color: #C0392B;
}

QPushButton#actionBtn[action="cancel"]:hover {
    background-color: #FFCACA;
}

QPushButton#actionBtn[action="open"] {
    background-color: #E8F8F0;
    color: #27AE60;
}

QPushButton#actionBtn[action="open"]:hover {
    background-color: #D0F0E0;
}

QPushButton#actionBtn[action="retry"] {
    background-color: #FFF3E0;
    color: #E67E22;
}

QPushButton#actionBtn[action="retry"]:hover {
    background-color: #FFE8C0;
}

QPushButton#browserBtn {
    padding: 6px 12px;
    font-size: 12px;
    border-radius: 4px;
    min-width: 80px;
}

QPushButton#browserBtn[action="use_browser"] {
    background-color: #E8F0FE;
    color: #1A73E8;
}

QPushButton#browserBtn[action="use_browser"]:hover {
    background-color: #D2E3FC;
}
"""
