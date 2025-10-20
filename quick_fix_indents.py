#!/usr/bin/env python3

import os
import ast

def fix_file_indents(file_path):
    """Быстро исправляет отступы в файле."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        for line in lines:
            # Убираем лишние отступы в начале файла для импортов
            if line.lstrip().startswith('import ') or line.lstrip().startswith('from '):
                if line.startswith('    ') and not any(fixed_lines):
                    # Первые импорты не должны иметь отступов
                    fixed_lines.append(line.lstrip())
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        # Проверяем что исправленный код валиден
        try:
            ast.parse(''.join(fixed_lines))
        except:
            return False
        
        # Сохраняем исправленный файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        return True
    except:
        return False

# Исправляем проблемные файлы
files_to_fix = [
    'persistence/db.py',
    'validation/email_validator.py',
    'persistence/events_repository.py',
    'templating/html_highlighter.py'
]

for file_path in files_to_fix:
    if os.path.exists(file_path):
        if fix_file_indents(file_path):
            print(f"✅ Fixed: {file_path}")
        else:
            print(f"❌ Failed: {file_path}")

print("Done!")
