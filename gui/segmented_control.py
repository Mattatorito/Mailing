from __future__ import annotations
from PySide6.QtCore import Qt, QRectF, QPropertyAnimation, Property, QEasingCurve, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QPen
from PySide6.QtWidgets import QWidget
from typing import List
from .design_system import RADIUS, DURATION, LIGHT, Palette
from .themed import ThemedWidget
from .theme import ThemeManager

class SegmentedControl(QWidget, ThemedWidget):
    """Горизонтальный SegmentedControl в стиле macOS/iOS с анимированной 'pill'."""
    changed = Signal(int)

    def __init__(self, segments: List[str], current: int = 0, parent: QWidget | None = None, theme_manager: ThemeManager | None = None):
        super().__init__(parent)
        self._segments = segments
        self._current = current if 0 <= current < len(segments) else 0
        self._hover_index = -1
        self._pill_progress = 1.0  # reserved for future morph
        self._pill_anim = QPropertyAnimation(self, b"pillX")
        self._pill_anim.setDuration(DURATION['fast'])
        self._pill_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._pill_x = 0.0
        self.setMinimumHeight(40)
        self.setAttribute(Qt.WA_Hover, True)
        self._update_pill_target(initial=True)
        self._current_palette: Palette = LIGHT
        if theme_manager:
            self.bind_theme(theme_manager)

    # Pill X position property (animation target)
    def getPillX(self) -> float: return self._pill_x
    def setPillX(self, v: float):
        self._pill_x = v
        self.update()
    pillX = Property(float, getPillX, setPillX)

    def setCurrentIndex(self, idx: int, animate: bool = True):
        if 0 <= idx < len(self._segments) and idx != self._current:
            self._current = idx
            self.changed.emit(idx)
            self._update_pill_target(animate=animate)
            self.update()

    def currentIndex(self) -> int:
        return self._current

    def segments(self) -> List[str]:
        return list(self._segments)

    def _palette(self):
        return self._current_palette

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        return self._compute_geometry()[0].toRect().size()

    def _compute_geometry(self):
        # Returns (total_rect, list_of_segment_rects)
        w = self.width() or 1
        h = self.height() or 1
        count = max(1, len(self._segments))
        seg_w = w / count
        rects = []
        for i in range(count):
            rects.append(QRectF(i * seg_w, 0, seg_w, h))
        return QRectF(0,0,w,h), rects

    def _update_pill_target(self, animate: bool = True, initial: bool = False):
        total, rects = self._compute_geometry()
        if not rects: return
        target = rects[self._current].x()
        if initial:
            self._pill_x = target
        else:
            self._pill_anim.stop()
            if animate:
                self._pill_anim.setStartValue(self._pill_x)
                self._pill_anim.setEndValue(target)
                self._pill_anim.start()
            else:
                self._pill_x = target

    def resizeEvent(self, e):
        self._update_pill_target(animate=False)
        return super().resizeEvent(e)

    def leaveEvent(self, e):
        self._hover_index = -1
        self.update()
        return super().leaveEvent(e)

    def mouseMoveEvent(self, e):
        _, rects = self._compute_geometry()
        pos = e.position().toPoint()
        hover = -1
        for i, r in enumerate(rects):
            if r.contains(pos):
                hover = i
                break
        if hover != self._hover_index:
            self._hover_index = hover
            self.update()
        return super().mouseMoveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            _, rects = self._compute_geometry()
            pos = e.position().toPoint()
            for i, r in enumerate(rects):
                if r.contains(pos):
                    self.setCurrentIndex(i)
                    break
        return super().mousePressEvent(e)

    def paintEvent(self, event):
        pal = self._palette()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        total, rects = self._compute_geometry()
        radius = RADIUS['xl']
        # background capsule
        bg = QColor(pal.background)
        bg.setAlpha(160)
        p.setPen(Qt.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(total.adjusted(1,1,-1,-1), radius, radius)
        # pill rect
        current_rect = rects[self._current] if rects else QRectF()
        pill_rect = QRectF(self._pill_x, current_rect.y(), current_rect.width(), current_rect.height())
        pill_color = QColor(pal.accent)
        pill_color.setAlpha(230)
        p.setBrush(pill_color)
        p.drawRoundedRect(pill_rect.adjusted(2,2,-2,-2), radius-4, radius-4)
        # segment separators (optional subtle)
        sep_pen = QPen(QColor(pal.border))
        sep_pen.setWidthF(1.0)
        sep_pen.setCosmetic(True)
        p.setPen(sep_pen)
        for r in rects[:-1]:
            x = r.right()
            p.drawLine(int(x), int(total.top()+6), int(x), int(total.bottom()-6))
        # labels
        label_font = p.font(); label_font.setPointSize(13); label_font.setBold(True)
        p.setFont(label_font)
        for i, r in enumerate(rects):
            text_col = QColor(pal.text)
            if i == self._current:
                text_col = QColor(pal.on_accent)
            elif i == self._hover_index:
                text_col.setAlpha(220)
            else:
                text_col.setAlpha(180)
            p.setPen(text_col)
            p.drawText(r, Qt.AlignCenter, self._segments[i])
        p.end()

    def apply_palette(self, palette: Palette):
        self._current_palette = palette
        self.update()

__all__ = ["SegmentedControl"]
