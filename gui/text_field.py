from PySide6.QtCore import Qt, QPropertyAnimation, Property, QEasingCurve, QRectF
from __future__ import annotations
from typing import Optional

from PySide6.QtGui import QPainter, QColor, QFont, QPen, QFocusEvent, QPaintEvent
from PySide6.QtWidgets import QWidget

from .design_system import RADIUS, DURATION, LIGHT, Palette
from .theme import ThemeManager
from .themed import ThemedWidget

class FloatingTextField(QWidget, ThemedWidget):
"""TextField с плавающим лейблом и анимированным фокусом.
Стадия 1: без валидации и иконок, только базовое API."""

    def __init__("""Внутренний метод для  init  .
    """Инициализирует объект."""

Args:
    label: Параметр для label
    text: Параметр для text
    placeholder: Параметр для placeholder
    parent: Параметр для parent
    theme_manager: Параметр для theme manager"""
    self,label: str,"
        "text: str = "",""placeholder: str = "",
    parent: Optional[QWidget] = None,theme_manager: ThemeManager | None = None,"
        "):
    super().__init__(parent)
    self._label = label
    self._text = text
    self._placeholder = placeholder
    self._focused = False
    self._hover = False
        self._label_progress = 1.0 if self._text else 0.0self._anim = QPropertyAnimation(self, b"labelProgress")self._anim.setDuration(DURATION["fast"])
    self._anim.setEasingCurve(QEasingCurve.OutCubic)
    self.setAttribute(Qt.WA_InputMethodEnabled, True)
    self.setMouseTracking(True)
    self.setMinimumHeight(54)
    self._cursor_pos = len(self._text)
    self._current_palette: Palette = LIGHT
        if theme_manager:
        self.bind_theme(theme_manager)

    # Property for animation
    def getLabelProgress(self) -> float:"""выполняет getLabelProgress.
    """Выполняет getLabelProgress."""

    Args:

    Returns:
    float: Результат выполнения операции"""
        return self._label_progress

    def setLabelProgress(self, v: float):"""выполняет setLabelProgress.
    """Выполняет setLabelProgress."""

    Args:
    v: Параметр для v"""
    self._label_progress = v
    self.update()

    labelProgress = Property(float, getLabelProgress, setLabelProgress)

    def text(self) -> str:"""выполняет text.
    """Выполняет text."""

    Args:

    Returns:
    str: Результат выполнения операции"""
        return self._text

    def setText(self, t: str):"""выполняет setText.
    """Выполняет setText."""

    Args:
    t: Параметр для t"""
        if t != self._text:
        self._text = t
            if self._text and self._label_progress < 1.0:
            self._animate_label(1.0)
            elif not self._text and not self._focused:
            self._animate_label(0.0)
        self._cursor_pos = min(len(self._text), self._cursor_pos)
        self.update()

    def _animate_label(self, target: float):"""Внутренний метод для animate label.
    """Выполняет  animate label."""

    Args:
    target: Параметр для target"""
    self._anim.stop()
    self._anim.setStartValue(self._label_progress)
    self._anim.setEndValue(target)
    self._anim.start()

    def focusInEvent(self, e: QFocusEvent):"""выполняет focusInEvent.
    """Выполняет focusInEvent."""

    Args:
    e: Параметр для e"""
    self._focused = True
    self._animate_label(1.0)
    super().focusInEvent(e)

    def focusOutEvent(self, e: QFocusEvent):"""выполняет focusOutEvent.
    """Выполняет focusOutEvent."""

    Args:
    e: Параметр для e"""
    self._focused = False
        if not self._text:
        self._animate_label(0.0)
    super().focusOutEvent(e)

    def enterEvent(self, e):"""выполняет enterEvent.
    """Выполняет enterEvent."""

    Args:
    e: Параметр для e"""
    self._hover = True
    self.update()
    super().enterEvent(e)

    def leaveEvent(self, e):"""выполняет leaveEvent.
    """Выполняет leaveEvent."""

    Args:
    e: Параметр для e"""
    self._hover = False
    self.update()
    super().leaveEvent(e)

    def mousePressEvent(self, e):"""выполняет mousePressEvent.
    """Выполняет mousePressEvent."""

    Args:
    e: Параметр для e"""
    self.setFocus()
        return super().mousePressEvent(e)

    def keyPressEvent(self, e):"""выполняет keyPressEvent.
    """Выполняет keyPressEvent."""

    Args:
    e: Параметр для e"""
        if e.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            if self._cursor_pos > 0 and e.key() == Qt.Key_Backspace:
            self._text = (
                self._text[: self._cursor_pos - 1] + self._text[self._cursor_pos :]
            )
            self._cursor_pos -= 1
            elif e.key() == Qt.Key_Delete and self._cursor_pos < len(self._text):
            self._text = (
                self._text[: self._cursor_pos] + self._text[self._cursor_pos + 1 :]
            )
        self.setText(self._text)
            return
        elif e.key() == Qt.Key_Left:
        self._cursor_pos = max(0, self._cursor_pos - 1)
        self.update()
            return
        elif e.key() == Qt.Key_Right:
        self._cursor_pos = min(len(self._text), self._cursor_pos + 1)
        self.update()
            return
        elif e.key() in (Qt.Key_Return, Qt.Key_Enter):
        self.clearFocus()
            return
    txt = e.text()
        if txt and not txt.isspace():
        self._text = (
            self._text[: self._cursor_pos] + txt + self._text[self._cursor_pos :]
        )
        self._cursor_pos += len(txt)
        self.setText(self._text)
    else:
        super().keyPressEvent(e)

    def inputMethodQuery(self, query):"""выполняет inputMethodQuery.
    """Выполняет inputMethodQuery."""

    Args:
    query: Параметр для query"""
        return super().inputMethodQuery(query)

    def _palette(self):"""Внутренний метод для palette.

    Args:"""
        return self._current_palette

    def paintEvent(self, event: QPaintEvent):"""выполняет paintEvent.
    """Выполняет paintEvent."""

    Args:
    event: Параметр для event"""
    pal = self._current_palette
    p = QPainter(self)
    p.setRenderHint(QPainter.Antialiasing)
    r = self.rect().adjusted(12, 8, -12, -8)
    # background
    base = QColor(pal.surface)  # Используем surface вместо background
    base.setAlpha(90)
    p.setPen(Qt.NoPen)
    p.setBrush(base)p.drawRoundedRect(r, RADIUS["md"], RADIUS["md"])
    # border
    border = QColor(pal.border)
        if self._focused:
        border = QColor(pal.accent)
        elif self._hover:
        border.setAlpha(180)
    else:
        border.setAlpha(120)
    pen = QPen(border, 1.5)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)p.drawRoundedRect(r, RADIUS["md"], RADIUS["md"])
    # label animation: y shift & size
    label_font = p.font()
    base_pt = 14
    small_pt = 11
    size_pt = base_pt - (base_pt - small_pt) * self._label_progress
    label_font.setPointSize(int(size_pt))
    label_font.setBold(True)
    p.setFont(label_font)

    # Улучшенное позиционирование лейбла
        if self._label_progress > 0.5:  # Анимированное состояние - лейбл вверху
        label_y_offset = 0 - 14 * self._label_progress
        label_alignment = Qt.AlignLeft | Qt.AlignTop
        label_rect = r.adjusted(14, 18 + label_y_offset, -14, 0)
    else:  # Обычное состояние - лейбл по центру поля
        label_y_offset = 0
        label_alignment = Qt.AlignLeft | Qt.AlignVCenter
        label_rect = r.adjusted(14, 0, -14, 0)

    label_color = QColor(pal.text)
    label_color.setAlpha(200)
    p.setPen(label_color)
    p.drawText(label_rect, label_alignment, self._label)
    # text content
    text_rect = r.adjusted(14, 26, -14, -10)
        if self._text:
        txt_font = p.font()
        txt_font.setPointSize(14)
        txt_font.setBold(False)
        p.setFont(txt_font)
        p.setPen(QColor(pal.text))
        p.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self._text)
    # Убираем placeholder чтобы не создавать визуальный шум под лейблом
        # elif not self._focused and self._placeholder:
    #     ph_font = p.font(); ph_font.setPointSize(14)
    #     p.setFont(ph_font)
    #     ph_col = QColor(pal.text); ph_col.setAlpha(100)
    #     p.setPen(ph_col)
    #     p.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self._placeholder)
    # cursor
        if self._focused:
        metrics = p.fontMetrics()
        cursor_x = metrics.horizontalAdvance(self._text[: self._cursor_pos])
        cx = text_rect.left() + cursor_x
        p.setPen(QPen(QColor(pal.accent), 2))
        p.drawLine(cx, text_rect.top() + 4, cx, text_rect.bottom() - 4)
    p.end()

    def apply_palette(self, palette: Palette):"""выполняет apply palette.
    """Выполняет apply palette."""

    Args:
    palette: Параметр для palette"""
    self._current_palette = palette
    self.update()

__all__ = ["FloatingTextField"]
