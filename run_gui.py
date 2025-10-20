from __future__ import annotations
from pathlib import Path
import os
import sys

        from interactive_run import main as interactive_main
import subprocess

        from enhanced_gui_app import main
        from gui.app import main

#!/usr/bin/env python3
"""
Универсальная точка входа для запуска приложения"""


# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def try_web_gui():"""Попытка запуска веб-интерфейса"""
    """Выполняет try web gui."""
    try:print("🌐 Запуск веб-интерфейса...")print("📍 Откроется в браузере: http://localhost:5001")

        # Запускаем веб-интерфейс
        subprocess.run([sys.executable,"minimal_web_gui.py"], cwd = Path(__file__).parent
        )
        return True
    except Exception as e:print(f"❌ Веб-интерфейс не работает: {e}")
        return False


def try_enhanced_gui():"""Попытка запуска улучшенного GUI"""
    """Выполняет try enhanced gui."""
    try:
print("✅ Запуск улучшенного GUI приложения...")
        main()
        return True
    except Exception as e:print(f"❌ Улучшенное GUI не работает: {e}")
        return False


def try_basic_gui():"""Попытка запуска базового GUI"""
    """Выполняет try basic gui."""
    try:
print("✅ Запуск основного GUI приложения...")
        main()
        return True
    except Exception as e:print(f"❌ Основное GUI не работает: {e}")
        return False


def run_interactive_cli():"""Запуск интерактивной CLI версии"""
    """Выполняет run interactive cli."""
    try:print("💻 Запуск интерактивной CLI версии...")

        interactive_main()
    except Exception as e:print(f"❌ Интерактивная CLI не работает: {e}")print("\n💡 Используйте команды напрямую:")print("python -m mailing.cli --help")


def main():"""Главная функция с выбором интерфейса"""print("🚀 Универсальный запуск приложения для почтовой рассылки")print("=" * 60)
    """Выполняет main."""

    # Определяем доступные варианты
    options = []

    # Проверяем наличие файлов
    current_dir = Path(__file__).parent
if (current_dir / "minimal_web_gui.py").exists():options.append(("1",
    "🌐 Веб-интерфейс (рекомендуется)", try_web_gui))
if (current_dir / "enhanced_gui_app.py").exists():options.append(("2",
    "🖥  Улучшенное GUI (Qt)", try_enhanced_gui))
if (current_dir / "gui" / "app.py").exists():options.append(("3","📱 Базовое GUI", try_basic_gui))
options.append(("4", "💻 Интерактивная консоль", run_interactive_cli))

    # Если есть варианты GUI, предлагаем выбор
    if len(options) > 1:print("\nДоступные варианты запуска:")
        for num, desc, _ in options:print(f"{num}. {desc}")
print(f"{len(options) + 1}. ❌ Выход")

        try:
            choice = input(f"\nВыберите вариант (1-{len(options) + 1}) или нажмите Enter для автоматического выбора: "
            ).strip()
if choice == "":
                # Автоматический выбор - пробуем по порядкуprint("🔄 Автоматический выбор лучшего варианта...")
                for _, desc, func in options:print(f"Попытка: {desc}")
                    if func():
                        return

            elif choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    _, desc, func = options[choice_num - 1]print(f"Запуск: {desc}")
                    func()
                    return
                elif choice_num == len(options) + 1:print("👋 До свидания!")
                    return
print("❌ Неверный выбор")

        except KeyboardInterrupt:print("\n👋 Выход по запросу пользователя")
            return
        except Exception as e:print(f"❌ Ошибка ввода: {e}")

    # Если нет выбора или что-то пошло не так, пробуем автоматическиprint("🔄 Автоматический поиск работающего интерфейса...")

    for _, desc, func in options:print(f"Пробую: {desc}")
        if func():
            return
print("\n❌ Не удалось запустить ни один интерфейс")print("💡 Попробуйте установить зависимости:")print("pip install -r requirements.txt")

if __name__ == "__main__":
    main()
