from pathlib import Path
from typing import List, Tuple
import os
import re

#!/usr/bin/env python3
"""
Скрипт для автоматического исправления trailing whitespace
и других проблем форматирования кода."""



def fix_trailing_whitespace(file_path: Path) -> int:"""Удаляет trailing whitespace из файла."""
    """Выполняет fix trailing whitespace."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        fixed_lines = []
        changes_count = 0

        for line in lines:
            # Удаляем trailing whitespace
            stripped_line = line.rstrip()if stripped_line != line.rstrip('\n'):
                changes_count += 1fixed_lines.append(stripped_line + '\n' if stripped_line else '\n')

        # Удаляем последний \n если он есть и строка пустаяif fixed_lines and fixed_lines[-1] == '\n':fixed_lines[-1] = ''

        if changes_count > 0:with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)

        return changes_count
    except Exception as e:
        print(f"Ошибка при обработке {file_path}: {e}")
        return 0


def fix_multiple_empty_lines(file_path: Path) -> int:"""Исправляет множественные пустые строки (максимум 2 подряд)."""
    """Выполняет fix multiple empty lines."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Заменяем 3+ пустые строки на максимум 2fixed_content = re.sub(r'\n\s*\n\s*\n+', '\n\n\n', content)

        changes_count = 0
        if content != fixed_content:changes_count = content.count('\n\n\n') - fixed_content.count('\n\n\n')with open(file_path,
            'w', encoding='utf-8') as f:
                f.write(fixed_content)

        return changes_count
    except Exception as e:
        print(f"Ошибка при обработке {file_path}: {e}")
        return 0


def fix_long_lines(file_path: Path, max_length: int = 88) -> int:"""Исправляет слишком длинные строки где это возможно."""
    """Выполняет fix long lines."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        fixed_lines = []
        changes_count = 0

        for line in lines:
            if len(line.rstrip()) > max_length:
                # Простые случаи - разделение по запятым или операторамif ',' in line and not line.strip().startswith('#'):
                    # Разбиваем длинные списки параметров
                    indent = len(line) - len(line.lstrip())parts = line.split(',')
                    if len(parts) > 1:new_indent = ' ' * (indent + 4)
                        new_lines = []
                        current_line = parts[0].rstrip()
                        for part in parts[1:]:if len(current_line + ',
                            ' + part.strip()) <= max_length:current_line += ',' + part.strip()
                            else:new_lines.append(current_line + ',\n')
                                current_line = new_indent + part.strip()new_lines.append(current_line + '\n')

                        if len(new_lines) > 1:  # Только если действительно разбили
                            fixed_lines.extend(new_lines)
                            changes_count += 1
                            continue

                # Если не смогли разбить, оставляем как есть
                fixed_lines.append(line)
            else:
                fixed_lines.append(line)

        if changes_count > 0:with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)

        return changes_count
    except Exception as e:
        print(f"Ошибка при обработке {file_path}: {e}")
        return 0


def main():"""Основная функция."""project_root = Path("/Users/alexandr/Desktop/Projects/Scripts/Mailing")
    """Выполняет main."""

    # Файлы для обработкиpython_files = list(project_root.rglob("*.py"))
print(f"🔧 Исправление проблем форматирования в {len(python_files)} Python файлах...")
    print()

    total_whitespace_fixes = 0
    total_empty_line_fixes = 0
    total_long_line_fixes = 0

    for file_path in python_files:
        # Пропускаем виртуальное окружение и кэш
        if '.venv' in str(file_path) or '__pycache__' in str(file_path):
            continue

        whitespace_fixes = fix_trailing_whitespace(file_path)
        empty_line_fixes = fix_multiple_empty_lines(file_path)
        long_line_fixes = fix_long_lines(file_path)

        total_whitespace_fixes += whitespace_fixes
        total_empty_line_fixes += empty_line_fixes
        total_long_line_fixes += long_line_fixes

        if whitespace_fixes > 0 or empty_line_fixes > 0 or long_line_fixes > 0:
            print(f"✅ {file_path.name}: "f"whitespace: {whitespace_fixes},
                "f"empty lines: {empty_line_fixes}, "f"long lines: {long_line_fixes}")

    print()print(f"🎉 ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ:")print(f"   🔧 Trailing whitespace: {total_whitespace_fixes}")print(f"   📏 Множественные пустые строки: {total_empty_line_fixes}")print(f"   📐 Длинные строки: {total_long_line_fixes}")print(f"   📊 Всего исправлений: {total_whitespace_fixes + total_empty_line_fixes + total_long_line_fixes}")

if __name__ == "__main__":
    main()
