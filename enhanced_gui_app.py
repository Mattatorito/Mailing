#!/usr/bin/env python3
"""
Улучшенное GUI приложение для полного управления системой массовой рассылки

Возможности:
- Полное управление рассылками
- Мониторинг системы в реальном времени
- Управление webhook сервером
- Редактирование конфигурации
- Просмотр логов и статистики
- Управление шаблонами
"""

from __future__ import annotations
import sys
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from gui.theme import ThemeManager
from gui.enhanced_main_window import EnhancedMainWindow
from gui import styles

def main():
    """Запуск улучшенного GUI приложения"""
    app = QApplication(sys.argv)
    
    # Установка метаданных приложения
    app.setApplicationName("Mass Mailing System")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Mail System")
    
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