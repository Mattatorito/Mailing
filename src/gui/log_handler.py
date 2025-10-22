from __future__ import annotations
import logging
from typing import Deque, Tuple
from collections import deque
from PySide6.QtCore import QObject, Signal

class QtLogEmitter(QObject):
    messageEmitted = Signal(str, str)  # level_name, formatted_text


class QtLogHandler(logging.Handler):
    """Лог-хендлер, пересылающий сообщения в Qt через сигнал.
    Хранит кольцевой буфер для начальной инициализации UI.
    """
    def __init__(self, capacity: int = 1000):
        super().__init__()
        self.emitter = QtLogEmitter()
        self.buffer: Deque[Tuple[str, str]] = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
        except Exception:  # noqa
            msg = record.getMessage()
        level = record.levelname
        self.buffer.append((level, msg))
        self.emitter.messageEmitted.emit(level, msg)

def install_qt_log_handler(handler: QtLogHandler):
    root = logging.getLogger()
    for h in root.handlers:
        if isinstance(h, QtLogHandler):
            return h
    root.addHandler(handler)
    return handler
