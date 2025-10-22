from __future__ import annotations
from PySide6.QtCore import Qt, QPropertyAnimation, Property, QEasingCurve, QRectF
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget
from .design_system import DURATION, LIGHT, Palette
from .themed import ThemedWidget
from .theme import ThemeManager

class IOSSwitch(QWidget, ThemedWidget):
    """Переключатель в стиле iOS с анимированным бегунком."""
    def __init__(self, checked: bool = False, parent=None, theme_manager: ThemeManager | None = None):
        super().__init__(parent)
        self._checked = checked
        self._hover = False
        self._progress = 1.0 if checked else 0.0
        self._anim = QPropertyAnimation(self, b"progress")
        self._anim.setDuration(DURATION['fast'])
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self.setFixedSize(54, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self._current_palette: Palette = LIGHT
        if theme_manager:
            self.bind_theme(theme_manager)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, state: bool, animate: bool = True):
        if state != self._checked:
            self._checked = state
            self._anim.stop()
            if animate:
                self._anim.setStartValue(self._progress)
                self._anim.setEndValue(1.0 if state else 0.0)
                self._anim.start()
            else:
                self._progress = 1.0 if state else 0.0
                self.update()

    def toggle(self):
        self.setChecked(not self._checked)

    def getProgress(self) -> float: return self._progress
    def setProgress(self, v: float): self._progress = v; self.update()
    progress = Property(float, getProgress, setProgress)

    def enterEvent(self, e):
        self._hover = True; self.update(); return super().enterEvent(e)
    def leaveEvent(self, e):
        self._hover = False; self.update(); return super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.toggle()
        return super().mousePressEvent(e)

    def _palette(self):
        return self._current_palette

    def paintEvent(self, event):
        pal = self._palette()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(1,1,-1,-1)
        # track color
        off_col = QColor(pal.border)
        off_col.setAlpha(130)
        on_col = QColor(pal.accent)
        track = QColor(off_col)
        track.setAlpha(off_col.alpha())
        # interpolate
        def lerp(a: float, b: float, t: float) -> float: return a + (b - a) * t
        col = QColor(
            int(lerp(off_col.red(), on_col.red(), self._progress)),
            int(lerp(off_col.green(), on_col.green(), self._progress)),
            int(lerp(off_col.blue(), on_col.blue(), self._progress)),
            int(lerp(off_col.alpha(), 255, self._progress))
        )
        p.setPen(Qt.NoPen)
        p.setBrush(col)
        p.drawRoundedRect(r, r.height()/2, r.height()/2)
        # thumb
        thumb_d = r.height() - 4
        x_min = r.left() + 2
        x_max = r.right() - thumb_d - 2
        thumb_x = lerp(x_min, x_max, self._progress)
        thumb_rect = QRectF(thumb_x, r.top()+2, thumb_d, thumb_d)
        thumb_col = QColor('white')
        if self._hover:
            thumb_col.setAlpha(245)
        p.setBrush(thumb_col)
        p.setPen(QPen(QColor(0,0,0,40), 1))
        p.drawEllipse(thumb_rect)
        p.end()

    def apply_palette(self, palette: Palette):
        self._current_palette = palette
        self.update()

__all__ = ["IOSSwitch"]
