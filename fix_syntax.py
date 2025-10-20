from pathlib import Path
from typing import List
import os
import re

#!/usr/bin/env python3
"""
Скрипт для автоматического исправления синтаксических ошибок
связанных с незакрытыми строками после форматирования black"""

def fix_multiline_strings(file_path: Path) -> int:"""Исправляет проблемы с многострочными строками"""
    """Выполняет fix multiline strings."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

    original_content = content

    # Исправляем незакрытые строки в SQL запросах
    # Паттерн: строка заканчивается запятой и переносом, но не закрывается кавычкой
    content = re.sub(r'("[^"]*,)\s*\n\s*([^"]*")',r'\1"\n            "\2',
        content
    )

    # Исправляем f-строки с переносами
    content = re.sub(r'(f"[^"]*,)\s*\n\s*([^"]*")',r'\1"\n            f"\2',
        content
    )

    # Исправляем обычные строки с переносами
    content = re.sub(r'("INSERT [^"]*,)\s*\n\s*([^"]*")',r'\1"\n            "\2',
        content
    )

    content = re.sub(r'("SELECT [^"]*,)\s*\n\s*([^"]*")',r'\1"\n            "\2',
        content
    )

    changes = 0
        if content != original_content:with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        changes = 1

        return changes

    except Exception as e:
    print(f"Ошибка при обработке {file_path}: {e}")
        return 0

def check_syntax(file_path: Path) -> bool:"""Проверяет синтаксис Python файла"""
    """Выполняет check syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()compile(content, str(file_path), 'exec')
        return True
    except SyntaxError:
        return False
    except Exception:
        return True  # Если не можем проверить, считаем что норм

def main():
    """Основная функция"""project_root = Path("/Users/alexandr/Desktop/Projects/Scripts/Mailing")

    # Находим все Python файлыpython_files = list(project_root.rglob("*.py"))
    print("🔧 Исправление синтаксических ошибок...")
    print()

    fixed_files = 0
    syntax_errors_fixed = 0

    for file_path in python_files:
    # Пропускаем виртуальное окружение и кэш
        if '.venv' in str(file_path) or '__pycache__' in str(file_path):
        continue

    # Проверяем синтаксис до исправления
    syntax_ok_before = check_syntax(file_path)

        if not syntax_ok_before:
        # Пытаемся исправить
        changes = fix_multiline_strings(file_path)

        # Проверяем синтаксис после исправления
        syntax_ok_after = check_syntax(file_path)

            if syntax_ok_after and not syntax_ok_before:
            print(f"✅ {file_path.name}: исправлена синтаксическая ошибка")
            syntax_errors_fixed += 1
            elif changes > 0:print(f"🔧 {file_path.name}: внесены изменения")
            fixed_files += 1
        else:print(f"❌ {file_path.name}: синтаксическая ошибка не исправлена")

    print()print(f"🎉 ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКИХ ОШИБОК ЗАВЕРШЕНО:")print(f"   🔧 Исправлено синтаксических ошибок: {syntax_errors_fixed}")print(f"   📝 Обработано файлов: {fixed_files}")

if __name__ == "__main__":
    main()
