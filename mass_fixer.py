#!/usr/bin/env python3
"""
Мощный инструмент для исправления всех ошибок отступов и синтаксиса в Python файлах.
"""

import os
import re
from pathlib import Path

def fix_file_completely(file_path: str) -> bool:
    """Полностью исправляет файл Python от всех видов синтаксических ошибок."""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

    # Исправляем основные проблемы
    lines = content.split('\n')
    fixed_lines = []

        for i, line in enumerate(lines):
        original_line = line

        # 1. Убираем лишние отступы в начале файла (первые 20 строк)
            if i < 20 and line.startswith('    ') and not any(x in line for x in ['def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except', 'with ', 'return', 'yield']):
            line = line[4:]

        # 2. Исправляем отступы в очень глубоких уровнях
            if line.startswith('        ') and not any(x in line for x in ['def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except', 'with ', 'return', 'yield']):
            line = line[4:]

        # 3. Исправляем дублированные импорты в одной строке
        line = re.sub(r'import\s+(\w+)import\s+(\w+)', r'import \1\nimport \2', line)
        line = re.sub(r'from\s+([^\s]+)\s+import\s+([^\s]+)from\s+([^\s]+)\s+import\s+([^\s]+)', 
                     r'from \1 import \2\n
from \3 import \4', line)

        # 4. Исправляем незаконченные строки с docstring
            if '"""' in line:
            line = line.replace('"""', '"""')

        # 5. Исправляем поврежденные функции с docstring в одной строке
            if 'def ' in line and ':
    """' in line and '."""' in line:
            parts = line.split(':"""')
                if len(parts) == 2:
                    func_def = parts[0] + ':'
                docstring_part = parts[1]
                    if '."""' in docstring_part:
                    docstring = '"""' + docstring_part.replace('."""', '."""')
                        line = func_def + '\n    ' + docstring

            # 6. Исправляем строки, где docstring идет сразу после def без отступа
            if line.strip().startswith('"""') and i > 0 and 'def ' in lines[i-1]:
            line = '    ' + line.strip()

        # 7. Исправляем классы без body
            if line.strip().startswith('class ') and line.strip().endswith(':'):
            # Проверяем следующую строку
                if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                    if next_line.startswith('"""') and not next_line.startswith('    '):
                    # Добавляем отступ к docstring
                    pass  # обработаем в следующей итерации

            # 8. Исправляем async def проблемы
            if 'async def' in line and line.count(':
    ') > 1:
            # Разделяем на функцию и что-то еще
            parts = line.split(':', 2)
                if len(parts) >= 2:
                line = parts[0] + ':'
                    if len(parts) > 2:
                    # Добавляем остальное как новую строку с отступом
                    fixed_lines.append(line)
                    line = '    ' + ':'.join(parts[1:])

        fixed_lines.append(line)

    # Обрабатываем результат для устранения пустых строк и нормализации
    final_lines = []
    prev_was_empty = False

        for line in fixed_lines:
        # Убираем множественные пустые строки
            if line.strip() == '':
                if not prev_was_empty:
                final_lines.append('')
            prev_was_empty = True
        else:
            final_lines.append(line)
            prev_was_empty = False

    # Записываем исправленный файл
        with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_lines))

    print(f"✅ Исправлен: {file_path}")
        return True

    except Exception as e:
    print(f"❌ Ошибка при исправлении {file_path}: {e}")
        return False

def main():
    """Исправляет все файлы в проекте."""

    # Получаем все Python файлы
    all_py_files = []

    # Основные директории
    for root, dirs, files in os.walk('.'):
    # Пропускаем .venv, __pycache__ и .git
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

        for file in files:
            if file.endswith('.py') and not file.startswith('.'):
            full_path = os.path.join(root, file)
            all_py_files.append(full_path)

    print(f"Найдено {len(all_py_files)} Python файлов для исправления...")

    fixed_count = 0

    for file_path in all_py_files:
        if fix_file_completely(file_path):
        fixed_count += 1

    print(f"\n📊 Результат: исправлено {fixed_count} из {len(all_py_files)} файлов")

if __name__ == "__main__":
    main()