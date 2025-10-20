#!/usr/bin/env python3

import os
import re
from pathlib import Path

def fix_indentation_errors(file_path):
    """Исправляет IndentationError в файле."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.splitlines()
        fixed_lines = []
        
        for i, line in enumerate(lines):
            original_line = line
            
            # Убираем лишние отступы в начале файла
            if i < 5 and line.startswith('    ') and (line.lstrip().startswith('import ') or line.lstrip().startswith('from ')):
                fixed_lines.append(line.lstrip())
            # Исправляем склеенные docstring с определениями
            elif '"""' in line and any(keyword in line for keyword in ['def ', 'class ', 'async def']):
                # Разделяем на определение и docstring
                if ':"""' in line:
                    definition_part = line.split(':"""')[0] + ':'
                    fixed_lines.append(definition_part)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        # Сохраняем исправленный файл
        fixed_content = '\n'.join(fixed_lines)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        return True
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

# Список файлов для исправления
error_files = [
    'tests/test_additional.py',
    'tests/test_system_complete.py', 
    'tests/test_interfaces.py',
    'tests/test_performance.py',
    'tests/test_quick.py',
    'tests/test_final.py',
    'tests/test_core.py',
    'tests/test_template_persistence.py',
    'tests/test_cli_comprehensive.py',
    'tests/test_preflight_comprehensive.py',
    'tests/test_webhook_comprehensive.py',
    'tests/test_excel_comprehensive.py',
    'tests/test_remaining_coverage.py',
    'tests/test_additional_coverage.py',
    'tests/test_improved_code.py',
    'persistence/events_repository.py',
    'templating/html_highlighter.py'
]

fixed_count = 0
for file_path in error_files:
    if os.path.exists(file_path):
        if fix_indentation_errors(file_path):
            print(f"✅ Fixed: {file_path}")
            fixed_count += 1
        else:
            print(f"❌ Failed: {file_path}")

print(f"\nFixed {fixed_count} files!")
