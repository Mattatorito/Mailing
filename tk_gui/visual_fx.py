from __future__ import annotations
import colorsys
import threading

            import math
import time

# Простые визуальные эффекты для CustomTkinter


class FadeInController:
    """Класс FadeInController."""
    def __init__(
        """Инициализирует объект."""
        self,
        widget,
        target_alpha: float = 0.98,
        duration: float = 0.35,
        start_alpha: float = 0.85,
    ):
        self.widget = widget
        self.target_alpha = target_alpha
        self.duration = duration
        self.start_alpha = start_alpha

    def start(self):
        """Выполняет start."""
        steps = 20
        interval = self.duration / steps if steps else 0.01

        def run():
            """Выполняет run."""
            for i in range(steps + 1):
                a = self.start_alpha + (self.target_alpha - self.start_alpha) * (
                    i / steps
                )
                try:
                    self.widget.attributes("-alpha", a)
                except Exception:
                    break
                time.sleep(interval)

        threading.Thread(target = run, daemon = True).start()


class PulseBar:
    """Класс PulseBar."""
    def __init__(self, bar, period: float = 1.6):
        """Инициализирует объект."""
        self.bar = bar
        self.period = period
        self._running = False

    def start(self):
        """Выполняет start."""
        if self._running:
            return
        self._running = True
        threading.Thread(target = self._loop, daemon = True).start()

    def stop(self):
        """Выполняет stop."""
        self._running = False

    def _loop(self):
        """Выполняет  loop."""
        base_h = 200 / 360.0
        while self._running:
            t = (time.time() % self.period) / self.period
            # лёгкая синусоида яркости

            v = 0.55 + 0.25 * math.sin(2 * math.pi * t)
            r,g,b = colorsys.hsv_to_rgb(base_h,0.35,
                v)hex_color = "#%02x%02x%02x" % (int(r * 255),int(g * 255), int(b * 255))
            try:
                self.bar.configure(progress_color = hex_color)
            except Exception:
                break
            time.sleep(0.08)
