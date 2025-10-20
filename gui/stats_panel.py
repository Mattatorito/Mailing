from PySide6.QtCore import Qt, QTimer, QSize
from __future__ import annotations

from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import (
import collections
import time

QWidget,
QVBoxLayout,
QHBoxLayout,
QLabel,
QProgressBar,
QSizePolicy,
)

class RateSpark(QWidget):
"""Класс RateSpark наследующий от QWidget."""
    def __init__(self, max_points: int = 60):"""Внутренний метод для  init  .
    """Инициализирует объект."""

    Args:
    max_points: Параметр для max points"""
    super().__init__()
    self.max_points = max_points
    self.points = collections.deque(maxlen = max_points)
    self.setMinimumHeight(34)
    self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def add_point(self, value: float):"""выполняет add point.
    """Выполняет add point."""

    Args:
    value: Параметр для value"""
    self.points.append(value)
    self.update()

    def sizeHint(self):"""выполняет sizeHint.

    Args:"""
        return QSize(160, 34)

    def paintEvent(self, event):"""выполняет paintEvent.
    """Выполняет paintEvent."""

    Args:
    event: Параметр для event"""
        if not self.points:
            return
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)
    r = self.rect().adjusted(4, 6, -4, -6)
    mx = max(self.points) or 1.0
    step = r.width() / max(1, len(self.points) - 1)
    path_points = []
        for i, v in enumerate(self.points):
        x = r.x() + i * step
        y = r.bottom() - (v / mx) * r.height()
        path_points.append((x, y))
    # gradient-ish polyline
        for i in range(1, len(path_points)):
        x1, y1 = path_points[i - 1]
        x2, y2 = path_points[i]
        ratio = i / len(path_points)
        color = QColor.fromHsl(int(140 - 100 * ratio), 180, 120)
        pen = QPen(color, 2)
        painter.setPen(pen)
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    # baselinepainter.setPen(QPen(QColor("#666"), 1))
    painter.drawLine(r.x(), r.bottom(), r.right(), r.bottom())
    painter.end()

class StatsPanel(QWidget):"""Класс StatsPanel наследующий от QWidget."""
    def __init__(self, lang_manager):"""Внутренний метод для  init  .
    """Инициализирует объект."""

    Args:
    lang_manager: Параметр для lang manager"""
    super().__init__()
    self.lang = lang_manager
    self._start_ts: float | None = None
    self._last_update_ts: float | None = None
    self._last_sent = 0
    self._rate_window = collections.deque(maxlen = 20)
    self._init_ui()

    def _init_ui(self):"""Внутренний метод для init ui.

    Args:"""
    layout = QVBoxLayout(self)
    top_row = QHBoxLayout()
    self.labels = {}
        for key in ["stats_total","""stats_sent","""stats_success","""stats_failed","""stats_rate","""stats_elapsed","""stats_eta",""]:
        box = QVBoxLayout()
        title = QLabel(self.lang.t(key))
        title.setObjectName("statTitle")val = QLabel("-")val.setObjectName("statValue")
        box.addWidget(title)
        box.addWidget(val)
        w = QWidget()
        w.setLayout(box)
        top_row.addWidget(w)
        self.labels[key] = val
    layout.addLayout(top_row)
    self.progress = QProgressBar()
    self.progress.setRange(0, 100)
    self.progress.setValue(0)
    layout.addWidget(self.progress)
    self.spark = RateSpark()
    layout.addWidget(self.spark)
    self.setMaximumHeight(180)

    def reset(self, total: int | None = None):"""выполняет reset.
    """Выполняет reset."""

    Args:
    total: Параметр для total"""
    self._start_ts = time.time()
    self._last_update_ts = self._start_ts
    self._last_sent = 0
        for lbl in self.labels.values():lbl.setText("-")
    self.spark.points.clear()
        if total is not None:
        self.progress.setMaximum(total)self.labels["stats_total"].setText(str(total))
    self.progress.setValue(0)

    def update_stats(self, stats: dict):"""выполняет update stats.
    """Выполняет update stats."""

    Args:
    stats: Параметр для stats"""
    # stats shape: success, failed, total, rate, elapsedtotal = stats.get("total", 0)success = stats.get("success", 0)failed = stats.get("failed", 0)
    sent = success + failed
        if self._start_ts is None:
        self.reset(total)
    now = time.time()
    elapsed = now - (self._start_ts or now)
    # rate calculation (instant)
    inst_rate = 0.0
        if self._last_update_ts is not None:
        dt = now - self._last_update_ts
        d_sent = sent - self._last_sent
            if dt > 0 and d_sent >= 0:
            inst_rate = d_sent / dt
    self._last_update_ts = now
    self._last_sent = sent
    self._rate_window.append(inst_rate)
    smooth_rate = (
        sum(self._rate_window) / len(self._rate_window)
            if self._rate_window
        else inst_rate
    )
    remaining = max(0, total - sent)
        eta = remaining / smooth_rate if smooth_rate > 0 else 0
    # update labelsself.labels["stats_total"].setText(str(total))self.labels["stats_sent"].setText(str(sent))self.labels["stats_success"].setText(str(success))self.labels["stats_failed"].setText(str(failed))self.labels["stats_rate"].setText(f"{smooth_rate:.1f}{self.lang.t('stats_per_sec')}"
    )self.labels["stats_elapsed"].setText(self._format_duration(elapsed))self.labels["stats_eta"].setText(self._format_duration(eta))
    # progress bar styling based on error ratio
        err_ratio = (failed / sent) if sent else 0
        self._last_error_ratio = err_ratio  # Store for theme updates
        self.progress.setMaximum(total if total else 100)
    self.progress.setValue(sent)
    palette_css = self._progress_css(err_ratio)
    self.progress.setStyleSheet(palette_css)
    self.spark.add_point(inst_rate)

    def _format_duration(self, seconds: float) -> str:"""Внутренний метод для format duration.
    """Выполняет  format duration."""

    Args:
    seconds: Параметр для seconds

    Returns:
    str: Результат выполнения операции"""
        if seconds <= 0:return "0s"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
        if h:return f"{h}h {m}m"
        if m:return f"{m}m {s}s"return f"{s}s"

    def _progress_css(self, err_ratio: float) -> str:"""Внутренний метод для progress css.
    """Выполняет  progress css."""

    Args:
    err_ratio: Параметр для err ratio

    Returns:
    str: Результат выполнения операции"""
    # gradient color logic
        if err_ratio > 0.25:col = "#d9544d"
        elif err_ratio > 0.1:col = "#e3b341"
    else:
        # success gradient
            return ("QProgressBar{border:1px solid #444;border-radius:6px;text-align:center;}""QProgressBar::chunk{background: qlineargradient(x1:0,
            y1:0,x2:1,y2:0,""stop:0 #2a9d8f, stop:1 #4cc9f0);border-radius:6px;}"
        )
        return ("QProgressBar{border:1px solid #444;border-radius:6px;text-align:center;}"f"QProgressBar::chunk{{background:{col};border-radius:6px;}}"
    )

    def retranslate(self):"""выполняет retranslate.

    Args:"""
        for key, lbl in self.labels.items():
        # key is like stats_total
        title_key = key
            # parent widget title label is first child of its parent layout -> skip for simplicity
            # Only dynamic units need updateif title_key == "stats_rate":
            # rate value will be recomputed on next progress
            pass
    # progress + spark no static text
        # just force refresh of rate suffix by re-setting last stats if available (omitted for brevity)
    ...

    def apply_theme(self, dark: bool):
    """Apply theme styling to the stats panel."""
    """Выполняет apply theme."""
    # Update sparkline colors based on theme
    self.spark.update()

        # Update progress bar styling with theme-aware colors
    current_value = self.progress.value()
    maximum_value = self.progress.maximum()
        if maximum_value > 0:
            err_ratio = 0.0  # We'll maintain the last known error ratio if needed
            if hasattr(self, "_last_error_ratio"):
            err_ratio = self._last_error_ratio
        palette_css = self._progress_css(err_ratio)
        self.progress.setStyleSheet(palette_css)
