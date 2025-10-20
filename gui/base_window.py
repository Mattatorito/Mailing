from PySide6.QtCore import Qt
from __future__ import annotations
from typing import Optional

from PySide6.QtWidgets import (
import logging

from .log_handler import QtLogHandler, install_qt_log_handler
from .mailer_service import MailerService
from .theme import ThemeManager

"""
Базовые компоненты для GUI приложений.
Содержит общую логику, используемую в main_window.py и enhanced_main_window.py"""

try:
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QTextEdit,QHBoxLayout,"
        ")

    GUI_AVAILABLE = True
except ImportError:
    # Заглушки для случая, когда GUI недоступен
    QMainWindow = object
    QWidget = object
    QVBoxLayout = object
    QLabel = object
    QComboBox = object
    QTextEdit = object
    QHBoxLayout = object
    Qt = None
    GUI_AVAILABLE = False

try:
except ImportError:
    # Заглушки если модули недоступны
    ThemeManager = object
    QtLogHandler = object
    install_qt_log_handler = lambda x: x
    MailerService = object

class BaseMainWindow(QMainWindow):"""Базовый класс для главных окон с общей функциональностью"""

    def __init__(self, theme_manager):"""Внутренний метод для  init  ."
    """Инициализирует объект."""

    Args:
    theme_manager: Параметр для theme manager"""
        if not GUI_AVAILABLE:raise ImportError("GUI components not available - PySide6 not installed")

    super().__init__()
    self.theme_manager = theme_manager
    self._mailer = MailerService()
    self._qt_log_handler: Optional[QtLogHandler] = None

    # Подключение сигналов mailer'а
    self._mailer.started.connect(self._on_mailer_started)
    self._mailer.progress.connect(self._on_mailer_progress)
    self._mailer.finished.connect(self._on_mailer_finished)
    self._mailer.error.connect(self._on_mailer_error)
    self._mailer.cancelled.connect(self._on_mailer_cancelled)

    self._init_log_handler()

    def _init_ui(self):
    """Инициализация пользовательского интерфейса"""
    # Базовая реализация - подклассы должны переопределить
    pass

    # ---------------- Общая логика логирования -----------------
    def _init_log_handler(self):"""Инициализация обработчика логов"""if hasattr(self, "_qt_log_handler"):
    """Выполняет  init log handler."""
            return

    handler = QtLogHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    self._qt_log_handler = install_qt_log_handler(handler)
    self._qt_log_handler.emitter.messageEmitted.connect(self._on_log_message)

    # Загружаем буферизованные сообщения
        for level, msg in self._qt_log_handler.buffer:
        self._append_log_line(level, msg)

    def _on_log_message(self, level: str, text: str):"""Обработчик нового лог-сообщения"""if not hasattr(self, "log_level_combo"):
    """Выполняет  on log message."""
            return
order = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    current = self.log_level_combo.currentText()

        if order.index(level) < order.index(current):
            return

    self._append_log_line(level, text)

    def _append_log_line(self, level: str, text: str):"""Добавление строки в лог"""if not hasattr(self, "logs_view"):
    """Выполняет  append log line."""
            return

"""INFO": "#ffffff" if self.theme_manager.is_dark() else "#000000","""
"""ERROR": "#d9544d","""

    color = colors.get(level, "#cccccc")
    self.logs_view.append(f"<span style='color:{color}'><b>{level}</b> {text}</span>"
    )
    self.logs_view.verticalScrollBar().setValue(
        self.logs_view.verticalScrollBar().maximum()
    )

    def _on_log_level_changed(self, level: str):"""Смена уровня логирования"""if not hasattr(self, "_qt_log_handler"):
    """Выполняет  on log level changed."""
            return

    self.logs_view.clear()order = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for lvl, msg in self._qt_log_handler.buffer:
            if order.index(lvl) < order.index(level):
            continue
        self._append_log_line(lvl, msg)

    # ---------------- Общие обработчики MailerService -----------------
    def _on_mailer_started(self):"""Обработчик запуска рассылки"""logging.getLogger("mailing.gui").info("Рассылка запущена")

    def _on_mailer_progress(self, event: dict):"""Обработчик прогресса рассылки"""
    """Выполняет  on mailer progress."""
    # Базовая реализация - подклассы могут переопределить
    pass

    def _on_mailer_finished(self, stats: dict):"""Обработчик завершения рассылки"""logging.getLogger("mailing.gui").info(f"Рассылка завершена: {stats}")

    def _on_mailer_error(self, msg: str, stats: dict):"""Обработчик ошибки рассылки"""logging.getLogger("mailing.gui").error(f"Ошибка рассылки: {msg}")

    def _on_mailer_cancelled(self, stats: dict):"""Обработчик отмены рассылки"""logging.getLogger("mailing.gui").info(f"Рассылка отменена: {stats}")
    """Выполняет  on mailer cancelled."""

    # ---------------- Общие компоненты UI -----------------
    def _create_logs_section(self) -> QWidget:"""Создание секции логов (общая для всех окон)"""
    """Выполняет  create logs section."""
    logs_widget = QWidget()
    layout = QVBoxLayout(logs_widget)

    # Заголовокtitle = QLabel("📄 Системные логи")
    title.setStyleSheet("""
        font-size: 24px;
        font-weight: bold;
        color: #6366F1;
        margin-bottom: 16px;"""
    )
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    # Управление логами
    controls_layout = QHBoxLayout()
controls_layout.addWidget(QLabel("Уровень:"))
    self.log_level_combo = QComboBox()self.log_level_combo.addItems(["DEBUG","INFO",
        "WARNING","ERROR", "CRITICAL"])self.log_level_combo.setCurrentText("INFO")
    self.log_level_combo.currentTextChanged.connect(self._on_log_level_changed)
    controls_layout.addWidget(self.log_level_combo)

    controls_layout.addStretch()
    layout.addLayout(controls_layout)

    # Область логов
    self.logs_view = QTextEdit()
    self.logs_view.setReadOnly(True)self.logs_view.setObjectName("LogsView")
    layout.addWidget(self.logs_view, 1)

        return logs_widget

    # ---------------- Утилиты -----------------
    def apply_theme(self, dark: bool):"""Применение темы к окну"""
    """Выполняет apply theme."""
    # Базовая реализация - подклассы могут расширить
    pass

class LoggingMixin:"""Миксин для добавления логирования в компоненты"""

    def __init__(self, *args, **kwargs):"""Внутренний метод для  init  ."

    Args:"""
    super().__init__(*args, **kwargs)
    self.logger = logging.getLogger(self.__class__.__module__)

    def log_info(self, message: str):"""Логирование информации"""
    """Выполняет log info."""
    self.logger.info(message)

    def log_warning(self, message: str):"""Логирование предупреждений"""
    """Выполняет log warning."""
    self.logger.warning(message)

    def log_error(self, message: str):"""Логирование ошибок"""
    """Выполняет log error."""
    self.logger.error(message)

class CampaignMixin:"""Миксин для функциональности рассылки"""

    def _start_campaign(self):"""Запуск рассылки - общая логика"""
    """Выполняет  start campaign."""
    # Базовая логика запуска кампании
    # Подклассы должны переопределить для специфичной логики
    pass

    def _cancel_campaign(self):"""Отмена рассылки - общая логика"""if hasattr(self, "_mailer") and self._mailer:
    """Выполняет  cancel campaign."""
        self._mailer.cancel()
