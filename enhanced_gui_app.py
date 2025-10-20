from __future__ import annotations
import asyncio
import sys

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from gui import styles
from gui.enhanced_main_window import EnhancedMainWindow
from gui.theme import ThemeManager

#!/usr/bin/env python3
"""
Улучшенное GUI приложение для полного управления системой массовой рассылки

Возможности:
- Полное управление рассылками
- Мониторинг системы в реальном времени
- Управление webhook сервером
- Редактирование конфигурации
- Просмотр логов и статистики
- Управление шаблонами"""




def main():"""Запуск улучшенного GUI приложения"""
    """Выполняет main."""
    app = QApplication(sys.argv)

    # Установка метаданных приложенияapp.setApplicationName("Mass Mailing System")app.setApplicationVersion("2.0.0")app.setOrganizationName("Mail System")

    # Инициализация менеджеров
    theme_mgr = ThemeManager()
    # Принудительно устанавливаем темную тему
    theme_mgr.set_dark(True)

    # Применение стилей
    styles.apply_palette(app, True)  # Всегда темная тема
    app.setStyleSheet(styles.QSS_BASE)

    # Настройка асинхронного event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Создание главного окна
    window = EnhancedMainWindow(theme_mgr)

    # Подключение событий темы
    theme_mgr.themeChanged.connect(lambda dark: styles.apply_palette(app, dark))

    # Показ окна
    window.show()

    # Запуск приложения
    with loop:
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            window.close()

if __name__ == "__main__":
    main()
