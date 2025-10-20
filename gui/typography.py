from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QLabel

from .typography import apply_heading_style,
from .design_system import TYPE_SCALE

"""Typography helpers

Единая точка для применения типографической шкалы из design_system.TYPE_SCALE.
Позволяет избавиться от жёстко прописанных inline font-size в окнах.

Использование:
    apply_text_stylelabel = QLabel("Dashboard")apply_heading_style(label, level="h1")

Если нужен только размер шрифта — можно вызвать font_px('title1').
"""

# Маппинг семантических уровней заголовков -> ключей в TYPE_SCALE
HEADING_MAP = {"h1": "title1","h2": "title2","h3": "title3",
}
BODY_DEFAULT = "body"

def font_px(key: str) -> int:"""Возвращает размер шрифта (pt) для ключа типографической шкалы.

    Qt традиционно оперирует pointSize для QFont. Мы оставляем значения как есть."""return TYPE_SCALE.get(key, TYPE_SCALE["body"])

def apply_heading_style(widget: QWidget, level: str = "h1", weight: int = QFont.DemiBold
):"""Применяет стиль заголовка к QLabel/QWidget, устанавливая QFont.

    weight по умолчанию DemiBold (между Medium и Bold) – визуально легче."""key = HEADING_MAP.get(level, "title1")
    size = font_px(key)
    font = widget.font() if widget.font() else QFont()
    font.setPointSize(size)
    font.setWeight(weight)
    widget.setFont(font)

def apply_text_style(
    """Выполняет apply text style."""
    widget: QWidget, kind: str = BODY_DEFAULT, weight: int | None = None
):"""Применяет стиль текста по ключу шкалы (body, body_large, callout, footnote...)."""
    size = font_px(kind)
    font = widget.font() if widget.font() else QFont()
    font.setPointSize(size)
    if weight is not None:
    font.setWeight(weight)
    widget.setFont(font)

__all__ = ["apply_heading_style", "apply_text_style", "font_px", "make_page_title"]

def make_page_title(text: str, level: str = "h1") -> QLabel:"""Фабрика стандартизированного заголовка раздела.
    """Выполняет make page title."""

    Принципы:
    - Используем apply_heading_style(level)
    - Единый нижний отступ (margin-bottom) через styleSheet,чтобы заголовок не "лип" к следующему блоку.
    - Убираем жестко прописанный цвет: цвет возьмётся из темы (можно добавить позже параметр accent).
    - Возвращает QLabel готовый к добавлению в layout."""
    lbl = QLabel(text)
    apply_heading_style(lbl, level = level)
    # Универсальные отступы: сверху 0, снизу 16 (регулируемо), слева/справа 0lbl.setStyleSheet("margin: 0 0 20px 0; padding: 0;")
    return lbl
