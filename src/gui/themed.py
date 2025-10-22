from __future__ import annotations
from PySide6.QtCore import QObject
from .design_system import LIGHT, Palette
from .theme import ThemeManager

class ThemedWidget:
    """Mixin для привязки к ThemeManager.

    Использование:
        class MyWidget(QWidget, ThemedWidget):
            def __init__(..., theme_manager: ThemeManager, ...):
                ...
                self.bind_theme(theme_manager)
            def apply_palette(self, palette: Palette):
                ... обновить свои цвета ...
    """
    theme_manager: ThemeManager | None = None
    _current_palette: Palette = LIGHT

    def bind_theme(self, theme_manager: ThemeManager):
        if self.theme_manager is theme_manager:
            return
        if self.theme_manager:
            try:
                self.theme_manager.paletteChanged.disconnect(self._on_palette_changed)  # type: ignore[arg-type]
            except Exception:
                pass
        self.theme_manager = theme_manager
        theme_manager.paletteChanged.connect(self._on_palette_changed)  # type: ignore[arg-type]
        self.apply_palette(theme_manager.palette())  # type: ignore[arg-type]

    # --- Slots / hooks ---
    def _on_palette_changed(self, palette: Palette):  # slot
        self.apply_palette(palette)

    def apply_palette(self, palette: Palette):  # override
        self._current_palette = palette

__all__ = ["ThemedWidget"]