from __future__ import annotations
from PySide6.QtCore import Qt, QTimer, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget
from typing import Optional
from .design_system import DURATION, LIGHT, Palette
from .themed import ThemedWidget
from .theme import ThemeManager

class ProgressRing(QWidget, ThemedWidget):
    """iOS/macOS style circular progress.

    Modes:
      - determinate: set maximum/value
      - indeterminate: animated spinning arc
    """
    def __init__(self, size: int = 44, thickness: int = 4, parent: Optional[QWidget] = None, theme_manager: ThemeManager | None = None):
        super().__init__(parent)
        self._size = size
        self._thickness = thickness
        self._value = 0
        self._maximum = 100
        self._indeterminate = False
        self._spin_angle = 0.0
        self._arc_span = 110  # degrees of arc in indeterminate mode
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(16)  # ~60fps
        self._pulse_anim = QPropertyAnimation(self, b"arcSpan")
        self._pulse_anim.setDuration(DURATION['slow'])
        self._pulse_anim.setStartValue(80)
        self._pulse_anim.setEndValue(320)
        self._pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse_anim.setLoopCount(-1)
        self.setMinimumSize(size, size)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._current_palette: Palette = LIGHT
        if theme_manager:
            self.bind_theme(theme_manager)

    # ---------- Properties ----------
    def getValue(self) -> int: return self._value
    def setValue(self, v: int):
        v = max(0, min(v, self._maximum))
        if self._value != v:
            self._value = v
            self.update()
    value = Property(int, getValue, setValue)

    def getMaximum(self) -> int: return self._maximum
    def setMaximum(self, m: int):
        self._maximum = max(1, m)
        if self._value > self._maximum:
            self._value = self._maximum
        self.update()
    maximum = Property(int, getMaximum, setMaximum)

    def getArcSpan(self) -> float: return self._arc_span
    def setArcSpan(self, span: float):
        self._arc_span = span
        self.update()
    arcSpan = Property(float, getArcSpan, setArcSpan)

    def isIndeterminate(self) -> bool: return self._indeterminate
    def setIndeterminate(self, flag: bool):
        if self._indeterminate != flag:
            self._indeterminate = flag
            if flag:
                if not self._pulse_anim.state():
                    self._pulse_anim.start()
            else:
                self._pulse_anim.stop()
            self.update()

    # ---------- Animation tick ----------
    def _on_tick(self):
        if self._indeterminate:
            self._spin_angle = (self._spin_angle + 4.2) % 360.0
            self.update()

    # ---------- Painting ----------
    def sizeHint(self):
        return self.minimumSize()

    def _palette(self):
        return self._current_palette

    def apply_palette(self, palette: Palette):
        self._current_palette = palette
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pal = self._palette()
        rect = self.rect().adjusted(self._thickness, self._thickness, -self._thickness, -self._thickness)
        # track
        track_pen = QPen(QColor(pal.separator))
        track_pen.setWidth(self._thickness)
        p.setPen(track_pen)
        p.drawEllipse(rect)
        # progress
        prog_pen = QPen(QColor(pal.primary))
        prog_pen.setCapStyle(Qt.RoundCap)
        prog_pen.setWidth(self._thickness)
        p.setPen(prog_pen)
        if self._indeterminate:
            # draw spinning arc
            start_angle = int(self._spin_angle * 16)
            span_angle = int(self._arc_span * 16)
            p.drawArc(rect, start_angle, span_angle)
        else:
            if self._maximum <= 0: return
            frac = self._value / self._maximum
            span_angle = int(360 * frac * 16)
            p.drawArc(rect, 90*16, -span_angle)  # start at top, go clockwise
        p.end()

__all__ = ["ProgressRing"]
