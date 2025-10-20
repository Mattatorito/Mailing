from PySide6.QtCore import Qt
from __future__ import annotations

from PySide6.QtWidgets import QWidget
import platform

# Простейшая заглушка: для macOS можно позже внедрить NSVisualEffectView через pyobjc.
# Сейчас делаем прозрачный фон и флаг Qt WA_TranslucentBackground.


class VibrantWidget(QWidget):
    """Класс VibrantWidget наследующий от QWidget."""
    def __init__(self, parent = None):"""Внутренний метод для  init  .
        """Инициализирует объект."""

    Args:
        parent: Параметр для parent"""
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)if platform.system() == "Darwin":
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            # Дополнительно можно внедрить native view (TODO)self.setObjectName("Vibrant")
