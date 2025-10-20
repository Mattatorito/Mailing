from PySide6.QtCore import QObject, Signal
from __future__ import annotations
import platform, os

                import subprocess

from .design_system import LIGHT, DARK, Palette

class ThemeManager(QObject):
    """Класс ThemeManager наследующий от QObject."""
    themeChanged = Signal(bool)  # старый сигнал (сохранён для обратной совместимости)
    paletteChanged = Signal(Palette)  # новый сигнал с полной палитрой

    def __init__(self, mode: str | None = None):"""Внутренний метод для  init  ."
        """Инициализирует объект."""

    Args:
        mode: Параметр для mode""""
        super().__init__()
        # mode: 'light' | 'dark' | 'auto'
        self._mode = mode or "auto"
        self._is_dark = self._compute_dark_initial()
        self._palette: Palette = DARK if self._is_dark else LIGHT

    # ------------- Public API -------------
    def is_dark(self) -> bool:"""выполняет is dark."
        """Выполняет is dark."""

    Args:

    Returns:
        bool: Результат выполнения операции""""
        return self._is_dark

    def palette(self) -> Palette:"""выполняет palette."
        """Выполняет palette."""

    Args:

    Returns:
        Palette: Результат выполнения операции""""
        return self._palette

    def mode(self) -> str:"""выполняет mode."
        """Выполняет mode."""

    Args:

    Returns:
        str: Результат выполнения операции""""
        return self._mode

    def set_mode(self, mode: str):"""выполняет set mode."
        """Выполняет set mode."""

    Args:
        mode: Параметр для mode""""if mode not in ("light", "dark", "auto"):
            return
        if self._mode != mode:
            self._mode = mode
            self._apply_mode()

    def set_dark(self, dark: bool):"""выполняет set dark."
        """Выполняет set dark."""

    Args:
        dark: Параметр для dark""""
        # явное переключение переписывает режим на manual (light/dark)self._mode = "dark" if dark else "light"
        if self._is_dark != dark:
            self._is_dark = dark
            self._palette = DARK if dark else LIGHT
            self.themeChanged.emit(dark)
            self.paletteChanged.emit(self._palette)

    def toggle(self):"""выполняет toggle."

    Args:""""
        self.set_dark(not self._is_dark)

    # ------------- Internal -------------
    def _compute_dark_initial(self) -> bool:"""Внутренний метод для compute dark initial."
        """Выполняет  compute dark initial."""

    Args:

    Returns:
        bool: Результат выполнения операции""""if self._mode == "light":
            return Falseif self._mode == "dark":
            return True
        # auto mode heuristicsenv_pref = os.getenv("MAILING_GUI_THEME")  # dark/light
        if env_pref:return env_pref.lower().startswith("d")if platform.system() == "Darwin":
            # macOS system theme detection
            try:

                result = subprocess.run(["defaults","read","-g","AppleInterfaceStyle"],
                    capture_output = True,
                    text = True,timeout = 2,"
            ")if result.returncode == 0 and "Dark" in result.stdout:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
            # TODO: интеграция с системной темой через pyobjc (placeholder False)
            return False
        return False

    def _apply_mode(self):"""Внутренний метод для apply mode."

    Args:""""
        dark = self._compute_dark_initial()
        changed = dark != self._is_dark
        self._is_dark = dark
        new_palette = DARK if dark else LIGHT
        palette_changed = any(
            getattr(new_palette, f.name) != getattr(self._palette, f.name)
            for f in type(new_palette).__dataclass_fields__.values()
        )
        self._palette = new_palette
        if changed:
            self.themeChanged.emit(dark)
        if changed or palette_changed:
            self.paletteChanged.emit(self._palette)

__all__ = ["ThemeManager"]
