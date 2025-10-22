"""Layout / spacing utilities.

Единая точка для работы с отступами и spacing в приложении.
Использует токены из design_system (SPACING), но предоставляет удобные функции.
"""
from __future__ import annotations
from typing import Tuple
from .design_system import SPACING

# Предустановленные профили отступов (L = left, T = top, R = right, B = bottom)
MARGIN_PAGE: Tuple[int,int,int,int] = (SPACING['xl'], SPACING['xl'], SPACING['xl'], SPACING['xl'])
MARGIN_SECTION: Tuple[int,int,int,int] = (SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
MARGIN_COMPACT: Tuple[int,int,int,int] = (SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
MARGIN_NONE: Tuple[int,int,int,int] = (0,0,0,0)

def margins(kind: str = 'page') -> Tuple[int,int,int,int]:
    mapping = {
        'page': MARGIN_PAGE,
        'section': MARGIN_SECTION,
        'compact': MARGIN_COMPACT,
        'none': MARGIN_NONE,
    }
    return mapping.get(kind, MARGIN_COMPACT)

def apply_margins(layout, kind: str = 'section'):
    l,t,r,b = margins(kind)
    layout.setContentsMargins(l,t,r,b)
    return layout

def apply_spacing(layout, level: str = 'md'):
    layout.setSpacing(SPACING.get(level, 16))
    return layout

__all__ = [
    'margins', 'apply_margins', 'apply_spacing',
    'MARGIN_PAGE', 'MARGIN_SECTION', 'MARGIN_COMPACT', 'MARGIN_NONE'
]
