from PySide6.QtCore import Qt, QPropertyAnimation, Property, QEasingCurve
from __future__ import annotations
from typing import Optional

from PySide6.QtGui import QPainter, QColor, QFont, QPen, QIcon
from PySide6.QtWidgets import QWidget, QSizePolicy

from .design_system import RADIUS, DURATION, LIGHT, Palette
from .theme import ThemeManager
from .themed import ThemedWidget

class StatsCard(QWidget, ThemedWidget):
    """Карта статистики.

    Поддерживает два режима отображения:
    1. Стандартный: внутри цветного круга выводится значение (короткий текст/число).
    2. Glyph mode: внутри круга отображается глиф / emoji / символ,
        а значение выводится справа под заголовком.
Переключение происходит автоматически,"
            "если передан параметр glyph (не пустая строка)."""

    def __init__("""Внутренний метод для  init  .
        """Инициализирует объект."""

    Args:
        title: Параметр для title
        value: Параметр для value
        trend: Параметр для trend
        icon: Параметр для icon
        accent: Параметр для accent
        parent: Параметр для parent
        theme_manager: Параметр для theme manager
        glyph: Параметр для glyph"""
        self,title: str,"
            "value: str = "-",
        trend: float | None = None,
        icon: Optional[QIcon] = None,
        accent: QColor | None = None,
        parent: QWidget | None = None,
        theme_manager: ThemeManager | None = None,glyph: str | None = None,"
            "):
        super().__init__(parent)
        self._title = title
        self._value = value
        self._trend = trend
        self._icon = icon or QIcon()
        self._accent = accent or LIGHT.accent
        self._current_palette: Palette = LIGHT
        self._glyph: Optional[str] = glyph if glyph else None
        if theme_manager:
            self.bind_theme(theme_manager)
        self._hover_progress = 0.0
        self.setMinimumHeight(150)  # Немного больше для вертикального пространства
        self.setMinimumWidth(220)  # Больше места для заголовка
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_Hover,True)self._anim = QPropertyAnimation(self, b"hoverProgress")self._anim.setDuration(DURATION["normal"])
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    # Property for hover animation
    def getHoverProgress(self) -> float:"""выполняет getHoverProgress.
        """Выполняет getHoverProgress."""

    Args:

    Returns:
        float: Результат выполнения операции"""
        return self._hover_progress

    def setHoverProgress(self, v: float):"""выполняет setHoverProgress.
        """Выполняет setHoverProgress."""

    Args:
        v: Параметр для v"""
        self._hover_progress = v
        self.update()

    hoverProgress = Property(float, getHoverProgress, setHoverProgress)

    def setValue(self, value: str):"""выполняет setValue.
        """Выполняет setValue."""

    Args:
        value: Параметр для value"""
        if self._value != value:
            self._value = value
            self.update()

    def setGlyph(self, glyph: Optional[str]):"""Устанавливает глиф (emoji/символ) для отображения в круге.
        """Выполняет setGlyph."""
        Если установлен, значение выводится сбоку, а не внутри круга.
        Передайте None или пустую строку, чтобы вернуться в стандартный режим."""
        g = glyph.strip() if glyph else None
        if self._glyph != g:
            self._glyph = g
            self.update()

    def setProgress(self, progress: float):"""Устанавливает прогресс (0.0 - 1.0) для визуального отображения"""
        """Выполняет setProgress."""
        # Добавляем базовую поддержку прогресса
        # Можно использовать для изменения цвета или добавления полосы прогресса
        pass

    def setTrend(self, trend: float | None):"""выполняет setTrend.
        """Выполняет setTrend."""

    Args:
        trend: Параметр для trend"""
        self._trend = trend
        self.update()

    def setTitle(self, title: str):"""выполняет setTitle.
        """Выполняет setTitle."""

    Args:
        title: Параметр для title"""
        self._title = title
        self.update()

    def enterEvent(self, e):"""выполняет enterEvent.
        """Выполняет enterEvent."""

    Args:
        e: Параметр для e"""
        self._anim.stop()
        self._anim.setEndValue(1.0)
        self._anim.start()
        return super().enterEvent(e)

    def leaveEvent(self, e):"""выполняет leaveEvent.
        """Выполняет leaveEvent."""

    Args:
        e: Параметр для e"""
        self._anim.stop()
        self._anim.setEndValue(0.0)
        self._anim.start()
        return super().leaveEvent(e)

    def _palette(self):"""Внутренний метод для palette.

    Args:"""
        return self._current_palette

    def paintEvent(self, e):"""выполняет paintEvent.
        """Выполняет paintEvent."""

    Args:
        e: Параметр для e"""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        pal = self._current_palette
        r = self.rect()
        circle_size = 72  # размер круга

        # Основной фон с улучшенными тенями
        bg_base = QColor(pal.surface)
        if self._hover_progress > 0:
            hover_influence = min(0.05, self._hover_progress * 0.05)
            bg_accent = QColor(self._accent)
            bg_accent.setAlphaF(hover_influence)
            # Смешиваем цвета для тонкого эффекта
            final_bg = QColor(
                int(
                    bg_base.red() * (1 - hover_influence)
                    + bg_accent.red() * hover_influence
                ),
                int(
                    bg_base.green() * (1 - hover_influence)
                    + bg_accent.green() * hover_influence
                ),
                int(
                    bg_base.blue() * (1 - hover_influence)
                    + bg_accent.blue() * hover_influence),"
            ")
        else:
            final_bg = bg_base

        p.setBrush(final_bg)

        # Улучшенная тень
        shadow_color = QColor(0, 0, 0, 15 + int(self._hover_progress * 25))
        p.setPen(shadow_color)
        shadow_rect = r.adjusted(1, 1, -1, -1)
        p.drawRoundedRect(shadow_rect, 12, 12)

        # Основная карточка
        border_color = QColor(pal.border)
        border_color.setAlpha(100)
        p.setPen(border_color)
        p.drawRoundedRect(r.adjusted(0, 0, -1, -1), 12, 12)

        # Акцентная полоска сверху
        accent_rect = r.adjusted(0, 0, 0, -(r.height() - 4))
        p.setBrush(QColor(self._accent))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(accent_rect, 12, 12)
        # Убираем нижние углы
        p.drawRect(accent_rect.adjusted(0, 8, 0, 0))

        # Круг с содержимым (значение или глиф)
        circle_size = 72  # Размер круга синхронизирован
        circle_rect = r.adjusted(
            20, 20, -(r.width() - 20 - circle_size), -(r.height() - 20 - circle_size)
        )

        # Основной цветной круг
        circle_bg = QColor(self._accent)
        p.setBrush(circle_bg)
        p.setPen(Qt.NoPen)
        p.drawEllipse(circle_rect)

        # Содержимое круга
        if self._glyph:  # glyph mode
            glyph_font = QFont()
            glyph_font.setPointSize(30)
            glyph_font.setWeight(QFont.Weight.DemiBold)
            p.setFont(glyph_font)
            p.setPen(QColor(255, 255, 255))
            p.drawText(circle_rect, Qt.AlignCenter, self._glyph)
        else:  # стандартный режим – значение внутри круга
            val_font = QFont()
            length = len(self._value)
            if length <= 2:
                val_font.setPointSize(22)
            elif length <= 4:
                val_font.setPointSize(18)
            elif length <= 6:
                val_font.setPointSize(15)
            else:
                val_font.setPointSize(13)
            val_font.setWeight(QFont.Weight.Bold)
            p.setFont(val_font)
            p.setPen(QColor(255, 255, 255))
            value_text = self._value
            metrics = p.fontMetrics()
            max_width = circle_size - 18
            if metrics.horizontalAdvance(value_text) > max_width:
                value_text = metrics.elidedText(value_text, Qt.ElideRight, max_width)
            p.drawText(circle_rect, Qt.AlignCenter, value_text)

        # Если есть иконка, рисуем её в маленьком уголке (опционально)
        if not self._icon.isNull():
            icon_rect = circle_rect.adjusted(circle_size - 20, circle_size - 20, -4, -4)
            icon_bg = QColor(255, 255, 255, 200)  # Полупрозрачный белый фон
            p.setBrush(icon_bg)
            p.drawEllipse(icon_rect)
            self._icon.paint(p, icon_rect.adjusted(2, 2, -2, -2))

        # Текстовая часть справа от круга
        content_x = 20 + circle_size + 20
        # Заголовок
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setWeight(QFont.Weight.Bold)
        p.setFont(title_font)
        p.setPen(QColor(pal.text))
        title_rect = r.adjusted(content_x, 25, -16, -20)
        title_text = p.fontMetrics().elidedText(
            self._title, Qt.ElideRight, title_rect.width()
        )
        p.drawText(title_rect, Qt.AlignTop | Qt.AlignLeft, title_text)

        next_y = 25 + p.fontMetrics().height() + 4

        # Value (в режиме glyph рисуем здесь, иначе уже нарисовано в круге)
        if self._glyph:
            value_font = QFont()
            value_font.setPointSize(18)
            value_font.setWeight(QFont.Weight.DemiBold)
            p.setFont(value_font)
            value_rect = r.adjusted(content_x, next_y, -16, -20)
            value_text = p.fontMetrics().elidedText(
                self._value, Qt.ElideRight, value_rect.width()
            )
            p.drawText(value_rect, Qt.AlignTop | Qt.AlignLeft, value_text)
            next_y += p.fontMetrics().height() + 4

        # Тренд – под значением (или под заголовком, если стандартный режим)
        if self._trend is not None:
            trend_font = QFont()
            trend_font.setPointSize(11)
            trend_font.setWeight(QFont.Weight.Medium)
            p.setFont(trend_font)arrow = "▲" if self._trend >= 0 else "▼"trend_col = QColor("#10B981") if self._trend >= 0 else QColor("#EF4444")
            p.setPen(trend_col)
            trend_rect = r.adjusted(content_x, next_y if self._glyph else 50, -16, -20)
            p.drawText(
                trend_rect,Qt.AlignTop | Qt.AlignLeft,"
            "f"{arrow} {abs(self._trend):.1f}%","")

        p.end()

    def apply_palette(self, palette: Palette):
    """выполняет apply palette.

    Args:
        palette: Параметр для palette"""
        self._current_palette = palette
        self.update()

__all__ = ["StatsCard"]
