"""Dark theme and styling for the mailforen GUI."""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

ACCENT = "#4fc3f7"
BG_DARK = "#1e2229"
BG_PANEL = "#262b33"
BG_INPUT = "#2f353f"
BORDER = "#3a414d"
TEXT = "#d8dee9"
TEXT_DIM = "#8a93a3"

RISK_COLORS = {
    "high": "#ef5350",
    "medium": "#ffb74d",
    "low": "#66bb6a",
    "info": "#4fc3f7",
}

STYLESHEET = f"""
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT};
    font-size: 13px;
}}
QMainWindow, QDialog {{
    background-color: {BG_DARK};
}}
QLabel#sidebarTitle {{
    color: {ACCENT};
    font-size: 17px;
    font-weight: bold;
    padding: 12px 4px 4px 4px;
}}
QLabel#disclaimer {{
    color: #ffb74d;
    font-size: 11px;
    padding: 6px;
}}
QListWidget#sidebar {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 6px;
    outline: none;
    min-width: 190px;
    max-width: 220px;
}}
QListWidget#sidebar::item {{
    padding: 9px 12px;
    border-radius: 4px;
    margin: 2px 4px;
}}
QListWidget#sidebar::item:selected {{
    background-color: {ACCENT};
    color: #102027;
}}
QListWidget#sidebar::item:hover:!selected {{
    background-color: {BG_INPUT};
}}
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 8px;
    selection-background-color: {ACCENT};
    selection-color: #102027;
}}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border-color: {ACCENT};
}}
QComboBox QAbstractItemView {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    selection-color: #102027;
}}
QPushButton {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 7px 14px;
}}
QPushButton:hover {{
    border-color: {ACCENT};
    color: {ACCENT};
}}
QPushButton:pressed {{
    background-color: {BORDER};
}}
QPushButton:disabled {{
    color: {TEXT_DIM};
}}
QPushButton#primary {{
    background-color: {ACCENT};
    color: #102027;
    font-weight: bold;
    border: none;
}}
QPushButton#primary:hover {{
    background-color: #73d3ff;
}}
QPushButton#primary:disabled {{
    background-color: {BG_INPUT};
    color: {TEXT_DIM};
}}
QTreeWidget, QTableWidget, QListWidget {{
    background-color: {BG_PANEL};
    alternate-background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    outline: none;
}}
QTreeWidget::item:selected, QTableWidget::item:selected, QListWidget::item:selected {{
    background-color: {ACCENT};
    color: #102027;
}}
QHeaderView::section {{
    background-color: {BG_INPUT};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 6px;
    font-weight: bold;
}}
QProgressBar {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 3px;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 4px;
}}
QTabBar::tab {{
    background-color: {BG_PANEL};
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {BG_INPUT};
    color: {ACCENT};
    border-bottom: 2px solid {ACCENT};
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {ACCENT};
}}
QScrollBar:vertical {{
    background: {BG_PANEL};
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_DIM};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
}}
QStatusBar {{
    background: {BG_PANEL};
    border-top: 1px solid {BORDER};
}}
QToolTip {{
    background-color: {BG_INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 4px;
}}
"""


def apply_theme(app: QApplication) -> None:
    """Apply the dark Fusion theme to the application."""
    from PySide6.QtCore import Qt

    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BG_DARK))
    palette.setColor(QPalette.WindowText, QColor(TEXT))
    palette.setColor(QPalette.Base, QColor(BG_PANEL))
    palette.setColor(QPalette.AlternateBase, QColor(BG_INPUT))
    palette.setColor(QPalette.ToolTipBase, QColor(BG_INPUT))
    palette.setColor(QPalette.ToolTipText, QColor(TEXT))
    palette.setColor(QPalette.Text, QColor(TEXT))
    palette.setColor(QPalette.Button, QColor(BG_INPUT))
    palette.setColor(QPalette.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.BrightText, QColor("#ff5252"))
    palette.setColor(QPalette.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.HighlightedText, QColor("#102027"))
    palette.setColor(QPalette.PlaceholderText, QColor(TEXT_DIM))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(TEXT_DIM))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(TEXT_DIM))
    palette.setColor(QPalette.Link, QColor(ACCENT))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)
