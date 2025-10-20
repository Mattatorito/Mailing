from __future__ import annotations

from PySide6.QtGui import QColor
from dataclasses import dataclass

"""Design System (tokens)

Задача файла — предоставить централизованные «дизайн‑токены», чтобы:
1. Стили были консистентны (отступы, радиусы, цвета, тени, типографика)
2. Легко адаптировать тему (светлая / тёмная) без хаотичного QSS.
3. Позволить в дальнейшем строить генерацию стилей или динамические темы.

Содержимое:
    SPACING      – шкала отступов (8pt baseline)
    RADIUS       – скругления
    ELEVATION    – пресеты «теней» (значения используются в helper shadow_css)
    DURATION     – тайминги анимаций
    Palette      – структура цветовой палитры
    LIGHT / DARK – конкретные палитры
    TYPE_SCALE   – типографическая шкала (поинты)
    shadow_css() – утилита для генерации css‑подобного описания тени"""

# 8pt baseline scale (ключи выбраны семантически, не числа – для читаемости)
SPACING = {"0": 0,# иногда удобно для reset"xs": 4,# мелкие внутренние отступы (иконки,
    компактные элементы)"sm": 8,
    # базовый минимальный отступ между мелкими контролами"md": 16,
    # стандартный «ритм» между блоками"lg": 24,
    # крупные блоковые разделения / вертикальный ритм"xl": 32,
    # секционные границы / верхние отступы крупных зон"2xl": 48,  # hero‑блоки / большие отступы в верхней части страницы
}

# Радиусы скругления
RADIUS = {"sm": 6,# Чипы,метки"md": 12,# Кнопки,поля ввода"lg": 18,# Карточки,
    таблицы"xl": 24,  # Крупные панели / поверхности
}

# Elevation (теневые пресеты) – (y-offset, blur, spread, alpha255)
ELEVATION = {"subtle": (2,6,12,40),# легкая приподнятость"medium": (4,12,24,60),
    # карточки поверх фона"floating": (8,24,48,80),  # модальные / выплывающие
}

# Animation durations (ms)
DURATION = {"fast": 200,"normal": 300,"slow": 500,
}


# Base color palette (will be adjusted per theme)
@dataclass(frozen = True)
class Palette:"""Класс для работы с palette."""
    """Класс Palette."""
    bg: QColor
    bg_alt: QColor
    surface: QColor
    surface_alt: QColor
    primary: QColor
    primary_hover: QColor
    primary_active: QColor
    secondary: QColor
    secondary_hover: QColor
    accent: QColor
    success: QColor
    warning: QColor
    error: QColor
    text: QColor
    text_muted: QColor
    border: QColor
    separator: QColor


LIGHT = Palette(bg = QColor("#F5F6F8"),bg_alt = QColor("#FFFFFF"),
    surface = QColor("#FFFFFF"),surface_alt = QColor("#F2F3F5"),
    primary = QColor("#2563EB"),
    # Более современный синий (tailwind indigo/blue mix)primary_hover = QColor("#1D4ED8"),
    primary_active = QColor("#1E40AF"),secondary = QColor("#6366F1"),
    secondary_hover = QColor("#4F46E5"),accent = QColor("#06B6D4"),
    success = QColor("#16A34A"),warning = QColor("#D97706"),error = QColor("#DC2626"),
    text = QColor("#1F2937"),text_muted = QColor("#6B7280"),border = QColor("#E2E8F0"),
    separator = QColor("#E5E7EB"),
)

DARK = Palette(bg = QColor("#0F172A"),bg_alt = QColor("#1E293B"),
    surface = QColor("#1E293B"),surface_alt = QColor("#334155"),
    primary = QColor("#6366F1"),primary_hover = QColor("#7C3AED"),
    primary_active = QColor("#8B5CF6"),secondary = QColor("#8B5CF6"),
    secondary_hover = QColor("#A855F7"),accent = QColor("#06B6D4"),
    success = QColor("#10B981"),warning = QColor("#F59E0B"),error = QColor("#EF4444"),
    text = QColor("#F8FAFC"),text_muted = QColor("#94A3B8"),border = QColor("#475569"),
    separator = QColor("#334155"),
)

# Типографическая шкала (pt)
TYPE_SCALE = {"caption": 11,"footnote": 12,"subhead": 13,"callout": 14,"body": 15,
    "body_large": 17,"title3": 20,"title2": 22,"title1": 28,"large_title": 34,
}

# Utility helpers


def shadow_css(level: str) -> str:"""Возвращает css‑подобное описание тени по пресету.
    """Выполняет shadow css."""

    Используется там, где мы можем инжектировать QSS (например, в динамических стилях)
    или для документации. Само применение тени через QPainter может отличаться."""
    y,blur,spread,alpha = ELEVATION[level]return f"0 {y}px {blur}px {spread}px rgba(0,0,
        0,{alpha/255:.2f})"


__all__ = ["SPACING","RADIUS","ELEVATION","DURATION","Palette","LIGHT","DARK",
    "TYPE_SCALE","shadow_css",
]
