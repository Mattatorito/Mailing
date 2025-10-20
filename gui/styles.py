from PySide6.QtCore import Qt
from __future__ import annotations

from PySide6.QtGui import QPalette, QColor

LIGHT_BG = QColor(245, 246, 248)
DARK_BG = QColor(28, 29, 31)
ACCENT = QColor(0, 122, 255)

def apply_palette(app, dark: bool):
    """выполняет apply palette.

Args:
    app: Параметр для app
    dark: Параметр для dark"""
pal = QPalette()
    if dark:
    pal.setColor(QPalette.Window, DARK_BG)
    pal.setColor(QPalette.Base, QColor(40, 41, 43))
    pal.setColor(QPalette.AlternateBase, QColor(46, 47, 49))
    pal.setColor(QPalette.Text, QColor(230, 231, 232))
    pal.setColor(QPalette.WindowText, QColor(230, 231, 232))
    pal.setColor(QPalette.Button, QColor(52, 53, 55))
    pal.setColor(QPalette.ButtonText, QColor(235, 235, 235))
    else:
    pal.setColor(QPalette.Window, LIGHT_BG)
    pal.setColor(QPalette.Base, QColor(255, 255, 255))
    pal.setColor(QPalette.AlternateBase, QColor(250, 250, 251))
    pal.setColor(QPalette.Text, QColor(30, 30, 32))
    pal.setColor(QPalette.WindowText, QColor(30, 30, 32))
    pal.setColor(QPalette.Button, QColor(255, 255, 255))
    pal.setColor(QPalette.ButtonText, QColor(30, 30, 32))
    pal.setColor(QPalette.Highlight, ACCENT)
    pal.setColor(QPalette.HighlightedText, QColor(Qt.white))
    app.setPalette(pal)

QSS_BASE = """
QWidget { font-family: 'SF Pro Text', 'Helvetica Neue', 'Helvetica', 'Arial'; }
QMainWindow { background: transparent; }
#Vibrant { background: rgba(255,255,255,0.30); border: 1px solid rgba(255,255,255,0.18); border-radius: 16px; }
.dark #Vibrant { background: rgba(30,30,32,0.25); border: 1px solid rgba(255,255,255,
    0.08); }
#Sidebar { background: rgba(255,255,255,0.55); border-radius: 18px; }
.dark #Sidebar { background: rgba(30,30,32,0.30); }
QPushButton { border-radius: 10px; padding:7px 16px; background: linear-gradient(180deg,
    rgba(0,132,255,0.95),rgba(0,102,220,0.90)); color: #fff; border: 1px solid rgba(255,
    255,255,0.25); font-weight:500; }
QPushButton:hover { background: linear-gradient(180deg,rgba(0,142,255,1.0),rgba(0,112,
    230,0.95)); }
QPushButton:pressed { background: linear-gradient(180deg,rgba(0,112,230,1.0),rgba(0,92,
    200,0.95)); }
QPushButton:disabled { background: rgba(120,120,120,0.35); border: 1px solid rgba(255,
    255,255,0.10); }
QListWidget { border:0; background: transparent; }
QListWidget::item { padding:8px 10px; border-radius: 8px; }
QListWidget::item:selected { background: rgba(0,122,255,0.18); color: #007aff; }
.dark QListWidget::item:selected { background: rgba(0,122,255,0.25); }
"""
