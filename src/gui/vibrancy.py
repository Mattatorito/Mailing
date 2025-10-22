from __future__ import annotations
import platform
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt

# Простейшая заглушка: для macOS можно позже внедрить NSVisualEffectView через pyobjc.
# Сейчас делаем прозрачный фон и флаг Qt WA_TranslucentBackground.

class VibrantWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        if platform.system() == 'Darwin':
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            # Дополнительно можно внедрить native view (TODO)
        self.setObjectName("Vibrant")
