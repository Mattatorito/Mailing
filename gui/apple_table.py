from PySide6.QtCore import Qt, QModelIndex, QRect, QSize
from __future__ import annotations

from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import QTableView, QStyledItemDelegate, QApplication

from .design_system import LIGHT, Palette
from .theme import ThemeManager
from .themed import ThemedWidget

class AppleTableDelegate(QStyledItemDelegate, ThemedWidget):
"""Класс AppleTableDelegate."""
    def __init__(self, parent = None, theme_manager: ThemeManager | None = None):
    """Инициализирует объект."""
    super().__init__(parent)
    self._current_palette: Palette = LIGHT
        if theme_manager:
    self.bind_theme(theme_manager)

    def paint(self, painter: QPainter, option, index: QModelIndex):
    """Выполняет paint."""
    painter.save()
    pal = self._current_palette
    r = option.rect
    is_sel = option.state & option.State_Selected
    is_hover = option.state & option.State_MouseOver
    # background layers
        if is_sel:
        sel = QColor(pal.accent)
        sel.setAlpha(90)
        painter.fillRect(r, sel)
        elif is_hover:
        hov = QColor(pal.accent)
        hov.setAlpha(40)
        painter.fillRect(r, hov)
    # text
    painter.setPen(QColor(pal.text))
    txt = index.data(Qt.DisplayRole)
    elided = option.fontMetrics.elidedText(str(txt), Qt.ElideRight, r.width() - 12)
    painter.drawText(
        r.adjusted(8, 0, -8, 0), Qt.AlignVCenter | Qt.AlignLeft, elided
    )
    # bottom separator
    sep = QColor(pal.border)
    sep.setAlpha(80)
    pen = QPen(sep, 1)
    pen.setCosmetic(True)
    painter.setPen(pen)
    painter.drawLine(r.left() + 8, r.bottom(), r.right() - 8, r.bottom())
    painter.restore()

    def sizeHint(self, option, index):
    """Выполняет sizeHint."""
    base = super().sizeHint(option, index)
        return QSize(base.width(), max(34, base.height()))

    def apply_palette(self, palette: Palette):
    """Выполняет apply palette."""
    self._current_palette = palette

class AppleTableView(QTableView, ThemedWidget):
    """QTableView стилизованный под macOS список: полупрозрачный фон,""мягкий hover/selection."""

    def __init__(self, parent = None, theme_manager: ThemeManager | None = None):
    """Инициализирует объект."""
    super().__init__(parent)
    self.setAlternatingRowColors(False)
    self.setShowGrid(False)
    self.setSelectionBehavior(self.SelectRows)
    self.setSelectionMode(self.SingleSelection)
    self.setSortingEnabled(False)
    self.setWordWrap(False)
    self.verticalHeader().setVisible(False)
    self.horizontalHeader().setStretchLastSection(True)
    self._current_palette: Palette = LIGHT
    delegate = AppleTableDelegate(self, theme_manager = theme_manager)
    self.setItemDelegate(delegate)
        if theme_manager:
        self.bind_theme(theme_manager)
    self.setStyleSheet("QTableView { background: transparent; border: none; }""QTableView::item { padding: 0px; }""QHeaderView::section { background: transparent; padding:6px 8px; border: none; border-bottom:1px solid rgba(255,
        ""255,255,40); }"
    )
    self.setMouseTracking(True)

    def viewportEvent(self, event):
    """Выполняет viewportEvent."""
        return super().viewportEvent(event)

    def apply_palette(self, palette: Palette):
    """Выполняет apply palette."""
    self._current_palette = palette
    self.viewport().update()

__all__ = ["AppleTableView"]
