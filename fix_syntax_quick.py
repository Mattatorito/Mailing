from pathlib import Path
import os
import re

#!/usr/bin/env python3
"""
Скрипт для быстрого исправления всех синтаксических ошибок
вызванных неправильными docstrings"""

def fix_indentation_errors(file_path: Path) -> bool:"""Исправляет ошибки отступов в docstrings"""
    """Выполняет fix indentation errors."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

    fixed_lines = []
    i = 0
    changes_made = False

        while i < len(lines):
        line = lines[i]

            # Паттерн:
     функция/метод + неправильно добавленный docstringif re.match(r'^\s*(def |class |async def )', line):
            # Следующая строка - неправильный docstring без отступа
                if (i + 1 < len(lines) and lines[i + 1].strip().startswith('"""') andnot lines[i + 1].startswith('    """')):

                # Исправляем отступ в docstring
                indent = len(line) - len(line.lstrip())
                docstring_line = lines[i + 1]fixed_docstring = ' ' * (indent + 4) + docstring_line.lstrip()

                fixed_lines.append(line)
                fixed_lines.append(fixed_docstring)
                changes_made = True
                i += 2
                continue

            # Ищем отдельные строки docstring без правильного отступаif (line.strip().startswith('"""') and not line.startswith('    """') and not line.startswith('"""')):
            # Добавляем нужный отступfixed_line = '    ' + line.lstrip()
            fixed_lines.append(fixed_line)
            changes_made = True
            i += 1
            continue

            # Исправляем незакрытые строки в Python кодеif '""' in line and line.count('"') % 2 == 1:
            # Проверяем следующую строку
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()if not next_line.startswith('"'):
                        # Закрываем строкуif line.rstrip().endswith(','):fixed_line = line.rstrip()[:-1] + '"\n'
                    else:fixed_line = line.rstrip() + '"\n'
                    fixed_lines.append(fixed_line)
                    changes_made = True
                    i += 1
                    continue

        fixed_lines.append(line)
        i += 1

        if changes_made:with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
            return True
        return False

    except Exception as e:
    print(f"Ошибка при обработке {file_path}: {e}")
        return False

def main():"""Основная функция"""project_root = Path("/Users/alexandr/Desktop/Projects/Scripts/Mailing")
    """Выполняет main."""

    # Файлы с известными проблемами
    problem_files = ["data_loader/csv_loader.py","data_loader/json_loader.py",
    "data_loader/streaming.py","data_loader/excel_loader.py","data_loader/base.py",
    "mailing/config.py","mailing/logging_config.py","mailing/limits/daily_quota.py",
    "stats/aggregator.py","resend/client.py","gui/base_window.py",
    "gui/error_handling.py","gui/theme.py","gui/components.py"
    ]
    print("🔧 Исправление синтаксических ошибок в критичных файлах...")
    print()

    fixed_count = 0

    for file_rel_path in problem_files:
    file_path = project_root / file_rel_path
        if file_path.exists():
            if fix_indentation_errors(file_path):print(f"✅ {file_rel_path}: исправлены синтаксические ошибки")
            fixed_count += 1
        else:print(f"⚪ {file_rel_path}: изменений не требуется")

    print()print(f"🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО:")print(f"   🔧 Исправлено файлов: {fixed_count}")

if __name__ == "__main__":
    main()
