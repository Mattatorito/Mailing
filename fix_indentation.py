#!/usr/bin/env python3
"""
Автоматическое исправление ошибок отступов в Python файлах.
"""

import os
import re
from pathlib import Path

def fix_indentation_errors(file_path: str) -> bool:
    """Исправляет основные ошибки отступов в Python файле."""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

    lines = content.split('\n')
    fixed_lines = []

        for i, line in enumerate(lines):
        # Исправляем отступы в начале файла
            if i < 10 and line.startswith('    '):
            line = line[4:]  # Убираем лишние 4 пробела

        # Исправляем дублированные импорты
            if 'import' in line:
            # Ищем паттерн 'import xxxx
import yyy'
            line = re.sub(r'import\s+(\w+)import\s+(\w+)', r'import \1\nimport \2', line)
            # Ищем паттерн 'from xxx import yy
from zzz import www'
            line = re.sub(r'from\s+([^\s]+)\s+import\s+([^\s]+)from\s+([^\s]+)\s+import\s+([^\s]+)', 
                         r'from \1 import \2\n
from \3 import \4', line)

        # Исправляем поврежденные строки документации
            if '"""' in line and line.count('"""') > 2:
            # Разделяем множественные docstrings
            parts = line.split('"""')
            new_lines = []
                for j in range(0, len(parts)-1, 2):
                    if j+1 < len(parts):
                    new_lines.append(f'"""{parts[j+1]}"""')
            line = '\n'.join(new_lines)

        # Исправляем синтаксические ошибки с функциями
            if 'async def' in line and ':
    """' in line:
            # Разделяем определение функции и docstring
                func_def = line.split(':"""')[0] + ':'
            docstring = '"""' + line.split(':"""')[1]
                line = func_def + '\n    ' + docstring

        # Исправляем проблемы с dict literals
            if '{"' in line and '"""}' in line:
            line = re.sub(r'\{"([^"]+)"\s*:\s*([^,}]+),"""\}', r'{"\1": \2}', line)

        fixed_lines.append(line)

    # Объединяем и разделяем снова для обработки многострочных исправлений
    fixed_content = '\n'.join(fixed_lines)
    final_lines = fixed_content.split('\n')

    # Записываем исправленный файл
        with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_lines))

    print(f"✅ Исправлен файл: {file_path}")
        return True

    except Exception as e:
    print(f"❌ Ошибка при исправлении {file_path}: {e}")
        return False

def main():
    """Основная функция для исправления всех файлов с ошибками."""

    # Список файлов с известными ошибками отступов
    problem_files = [
    "mailing/cli.py",
    "mailing/preflight.py", 
    "mailing/webhook_server.py",
    "data_loader/excel_loader.py",
    "data_loader/streaming.py",
    "persistence/events_repository.py",
    "templating/html_highlighter.py",
    "gui/base_window.py",
    "gui/error_handling.py",
    ]

    # Также исправляем все тестовые файлы
    test_files = []
    test_dir = Path("tests")
    if test_dir.exists():
        test_files = [str(f) for f in test_dir.glob("*.py")]

    all_files = problem_files + test_files

    fixed_count = 0

    for file_path in all_files:
        if os.path.exists(file_path):
            if fix_indentation_errors(file_path):
            fixed_count += 1
    else:
        print(f"⚠️  Файл не найден: {file_path}")

    print(f"\n📊 Результат: исправлено {fixed_count} из {len(all_files)} файлов")

if __name__ == "__main__":
    main()