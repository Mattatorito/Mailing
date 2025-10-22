from __future__ import annotations
from PySide6.QtCore import Qt, QEasingCurve, Property, QPropertyAnimation, QRect
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QIcon
from PySide6.QtWidgets import QPushButton, QWidget, QStyleOptionButton
from typing import Optional
from .design_system import RADIUS, DURATION, LIGHT, Palette
from .theme import ThemeManager
from .themed import ThemedWidget
from .animation_utils import scale_pulse


class ModernButton(QPushButton, ThemedWidget):
    """Apple-inspired button with variants and subtle press/hover animations.

    Теперь поддерживает динамическую палитру через ThemeManager (bind_theme).
    """
    def __init__(self, text: str = '', variant: str = 'primary', icon: Optional[QIcon] = None,
                 parent: QWidget | None = None, theme_manager: ThemeManager | None = None):
        super().__init__(text, parent)
        self._variant = variant
        if icon:
            self.setIcon(icon)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(34)
        self._bg_progress = 0.0  # 0..1 for hover overlay
        self._press_progress = 0.0
        self._anim_hover = QPropertyAnimation(self, b"bgProgress")
        self._anim_hover.setDuration(DURATION['fast'])
        self._anim_hover.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_press = QPropertyAnimation(self, b"pressProgress")
        self._anim_press.setDuration(DURATION['fast'])
        self._anim_press.setEasingCurve(QEasingCurve.OutCubic)
        self.setStyleSheet("border: none; padding: 0 16px; font-weight:500;")
        self._current_palette: Palette = LIGHT  # fallback до бинда
        if theme_manager:
            self.bind_theme(theme_manager)

    # Animated properties
    def getBgProgress(self) -> float:
        return self._bg_progress
    def setBgProgress(self, v: float):
        self._bg_progress = v
        self.update()
    bgProgress = Property(float, getBgProgress, setBgProgress)

    def getPressProgress(self) -> float:
        return self._press_progress
    def setPressProgress(self, v: float):
        self._press_progress = v
        self.update()
    pressProgress = Property(float, getPressProgress, setPressProgress)

    def enterEvent(self, e):
        self._anim_hover.stop()
        self._anim_hover.setEndValue(1.0)
        self._anim_hover.start()
        return super().enterEvent(e)

    def leaveEvent(self, e):
        self._anim_hover.stop()
        self._anim_hover.setEndValue(0.0)
        self._anim_hover.start()
        return super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._anim_press.stop()
            self._anim_press.setEndValue(1.0)
            self._anim_press.start()
            # легкий scale pulse
            try:
                scale_pulse(self, factor=0.92, duration=110)
            except Exception:
                pass
        return super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._anim_press.stop()
        self._anim_press.setEndValue(0.0)
        self._anim_press.start()
        return super().mouseReleaseEvent(e)

    def _palette(self):
        pal = self._current_palette
        if self._variant == 'primary':
            base = pal.primary
            hover = pal.primary_hover
            text = pal.bg_alt  # белый текст на синем фоне
        elif self._variant == 'secondary':
            base = pal.secondary
            hover = pal.secondary_hover
            text = pal.text
        else:  # tertiary
            base = pal.surface_alt
            hover = pal.surface
            text = pal.accent
        return base, hover, text

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        base, hover_col, text_col = self._palette()
        rect = self.rect().adjusted(1,1,-1,-1)
        radius = RADIUS['md']
        
        # Тень для глубины
        if self._variant == 'primary':
            shadow_color = QColor(base)
            shadow_color.setAlpha(30 + int(self._bg_progress * 20))
            shadow_rect = rect.adjusted(0, 2, 0, 0)
            p.setBrush(shadow_color)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(shadow_rect, radius, radius)
        
        # Основной фон
        bg = QColor(base)
        if not self.isEnabled():
            bg.setAlpha(100)
        
        # Эффект нажатия
        if self._press_progress > 0:
            press_offset = int(self._press_progress * 2)
            rect = rect.adjusted(0, press_offset, 0, press_offset)
        
        p.setBrush(bg)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(rect, radius, radius)
        
        # Улучшенный эффект наведения
        if self._bg_progress > 0:
            hov = QColor(hover_col)
            hov.setAlpha(int(30 + 50*self._bg_progress))
            p.setBrush(hov)
            p.drawRoundedRect(rect, radius, radius)
        # press overlay
        if self._press_progress > 0:
            press = QColor(0,0,0, int(60*self._press_progress))
            p.setBrush(press)
            p.drawRoundedRect(rect, radius, radius)
        # text/icon
        p.setPen(text_col)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        # Draw icon+text manually for crisp alignment
        contents = self.rect().adjusted(12,0,-12,0)
        x = contents.x()
        if not self.icon().isNull():
            icon_size = 18
            self.icon().paint(p, x, contents.center().y()-icon_size//2, icon_size, icon_size)
            x += icon_size + 8
        font = p.font()
        font.setPointSizeF(font.pointSizeF()+0.5)
        p.setFont(font)
        p.drawText(QRect(x, contents.y(), contents.width()-(x-contents.x()), contents.height()), Qt.AlignVCenter|Qt.AlignLeft, self.text())
        p.end()

    # ThemedWidget override
    def apply_palette(self, palette: Palette):
        self._current_palette = palette
        self.update()

__all__ = ["ModernButton"]
