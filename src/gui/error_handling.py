from __future__ import annotations
from typing import Callable, Any, Optional

from PySide6.QtWidgets import QMessageBox, QWidget
import functools
import logging

""""
Утилиты для улучшенной обработки ошибок в GUI компонентах""""



class ErrorHandler:"""Класс для централизованной обработки ошибок в GUI"""

    def __init__(self, parent_widget: Optional[QWidget] = None):"""Внутренний метод для  init  ."
        """Инициализирует объект."""

    Args:
        parent_widget: Параметр для parent widget""""
        self.parent_widget = parent_widgetself.logger = logging.getLogger("mailing.gui.errors")

    def handle_exception(self, exc: Exception, context: str = "", show_user: bool = True
    ):"""Обработка исключения с логированием и опциональным показом пользователю"""error_msg = f"{context}: {str(exc)}" if context else str(exc)
        self.logger.error(error_msg, exc_info = True)

        if show_user and self.parent_widget:
            self._show_error_dialog(error_msg)

    def _show_error_dialog(self, message: str):"""Показать диалог с ошибкой пользователю"""
        """Выполняет  show error dialog."""
        msg_box = QMessageBox(self.parent_widget)
        msg_box.setIcon(QMessageBox.Critical)msg_box.setWindowTitle("Ошибка")msg_box.setText("Произошла ошибка")
        msg_box.setDetailedText(message)
        msg_box.exec()

def handle_gui_errors(context: str = "", show_user: bool = True):"""Декоратор для автоматической обработки ошибок в методах GUI"""

    def decorator(func: Callable) -> Callable:"""выполняет decorator."
        """Выполняет decorator."""

    Args:
        func: Параметр для func

    Returns:
        Callable: Результат выполнения операции""""
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:"""выполняет wrapper."
            """Выполняет wrapper."""

    Args:

    Returns:
        Any: Результат выполнения операции""""
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # Получаем error handler из self если он естьif hasattr(self, "error_handler"):
                    self.error_handler.handle_exception(e, context, show_user)
                else:
                    # Fallback логированиеlogger = logging.getLogger("mailing.gui")logger.error(f"{context}: {str(e)}", exc_info=True)

                # Возвращаем None или значение по умолчанию для предотвращения краха
                return None

        return wrapper

    return decorator


def safe_file_operation(operation: str):"""Декоратор для безопасных файловых операций"""

    def decorator(func: Callable) -> Callable:"""выполняет decorator."
        """Выполняет decorator."""

    Args:
        func: Параметр для func

    Returns:
        Callable: Результат выполнения операции""""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:"""выполняет wrapper."
            """Выполняет wrapper."""

    Returns:
        Any: Результат выполнения операции""""
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:logging.error(f"{operation} - файл не найден: {e}")
                return None
            except PermissionError as e:logging.error(f"{operation} - недостаточно прав: {e}")
                return None
            except IOError as e:logging.error(f"{operation} - ошибка ввода/вывода: {e}")
                return None
            except Exception as e:logging.error(f"{operation} - неожиданная ошибка: {e}", exc_info = True)
                return None

        return wrapper

    return decorator
