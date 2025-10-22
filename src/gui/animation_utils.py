from __future__ import annotations
from typing import Callable, Optional
from PySide6.QtCore import QObject, QEasingCurve, QPropertyAnimation, QRect, QPoint, QSize
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect

# Простые хелперы для унификации анимаций
# Все возвращают объект анимации (caller может сохранить при необходимости)

DEFAULT_DURATION = 220


def fade(widget: QWidget, start: float = 1.0, end: float = 0.0, duration: int = DEFAULT_DURATION,
         easing: QEasingCurve.Type = QEasingCurve.InOutCubic, delete_on_end: bool = False,
         finished: Optional[Callable[[], None]] = None) -> QPropertyAnimation:
    if not widget.graphicsEffect() or not isinstance(widget.graphicsEffect(), QGraphicsOpacityEffect):
        eff = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(eff)
    eff = widget.graphicsEffect()
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(start); anim.setEndValue(end)
    anim.setEasingCurve(easing)
    def _cleanup():
        if finished:
            finished()
        if delete_on_end:
            widget.deleteLater()
    anim.finished.connect(_cleanup)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    return anim


def scale_pulse(widget: QWidget, factor: float = 0.94, duration: int = 140,
                easing_out: QEasingCurve.Type = QEasingCurve.OutCubic,
                easing_in: QEasingCurve.Type = QEasingCurve.OutBack) -> tuple[QPropertyAnimation, QPropertyAnimation]:
    # Выполняем лёгкий scale через изменение геометрии (без QGraphicsTransform для простоты)
    rect = widget.geometry()
    w, h = rect.width(), rect.height()
    dw, dh = int(w * (1-factor) / 2), int(h * (1-factor) / 2)
    shrink_rect = QRect(rect.x()+dw, rect.y()+dh, int(w*factor), int(h*factor))

    anim_out = QPropertyAnimation(widget, b"geometry", widget)
    anim_out.setDuration(duration)
    anim_out.setStartValue(rect); anim_out.setEndValue(shrink_rect)
    anim_out.setEasingCurve(easing_out)

    anim_in = QPropertyAnimation(widget, b"geometry", widget)
    anim_in.setDuration(duration+80)
    anim_in.setStartValue(shrink_rect); anim_in.setEndValue(rect)
    anim_in.setEasingCurve(easing_in)

    def _play_back():
        anim_in.start(QPropertyAnimation.DeleteWhenStopped)
    anim_out.finished.connect(_play_back)
    anim_out.start(QPropertyAnimation.DeleteWhenStopped)
    return anim_out, anim_in


def cross_fade(old_widget: QWidget, new_widget: QWidget, duration: int = DEFAULT_DURATION,
               easing: QEasingCurve.Type = QEasingCurve.OutCubic,
               delete_old: bool = False) -> tuple[QPropertyAnimation, QPropertyAnimation]:
    # new_widget предполагается уже в layout (но может быть скрыт)
    if not old_widget.graphicsEffect() or not isinstance(old_widget.graphicsEffect(), QGraphicsOpacityEffect):
        old_widget.setGraphicsEffect(QGraphicsOpacityEffect(old_widget))
    if not new_widget.graphicsEffect() or not isinstance(new_widget.graphicsEffect(), QGraphicsOpacityEffect):
        new_widget.setGraphicsEffect(QGraphicsOpacityEffect(new_widget))
    new_widget.setVisible(True)
    old_eff = old_widget.graphicsEffect(); new_eff = new_widget.graphicsEffect()
    fade_out = QPropertyAnimation(old_eff, b"opacity", old_widget)
    fade_out.setDuration(duration); fade_out.setStartValue(1.0); fade_out.setEndValue(0.0); fade_out.setEasingCurve(easing)
    fade_in = QPropertyAnimation(new_eff, b"opacity", new_widget)
    fade_in.setDuration(duration); fade_in.setStartValue(0.0); fade_in.setEndValue(1.0); fade_in.setEasingCurve(easing)
    def _cleanup():
        if delete_old:
            old_widget.hide(); old_widget.deleteLater()
        else:
            old_widget.hide()
    fade_out.finished.connect(_cleanup)
    fade_out.start(QPropertyAnimation.DeleteWhenStopped)
    fade_in.start(QPropertyAnimation.DeleteWhenStopped)
    return fade_out, fade_in

__all__ = ["fade", "scale_pulse", "cross_fade"]
