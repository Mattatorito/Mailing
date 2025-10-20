#!/usr/bin/env python3
"""
Агрессивный исправитель Python файлов.
Исправляет наиболее частые ошибки: отступы, docstring'и, синтаксис.
"""

import os
import re
from pathlib import Path


def fix_python_file_aggressively(file_path: str) -> bool:
    """Агрессивно исправляет Python файл."""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Если файл пустой или очень маленький - пропускаем
        if len(content.strip()) < 10:
            return True
        
        lines = content.split('\n')
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            original_line = line
            
            # 1. Убираем лишние отступы в начале файла (первые 15 строк)
            if i < 15 and line.startswith('    ') and not line.strip().startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except', 'with ', 'return', 'yield', '@')):
                if 'import' in line or 'from ' in line:
                    line = line.lstrip()
                elif line.strip() and not line.strip().startswith('#'):
                    line = line[4:]  # убираем 4 пробела
            
            # 2. Исправляем дублированные импорты
            if 'import' in line:
                # Паттерн: import xxxximport yyy
                line = re.sub(r'import\s+(\w+)import\s+(\w+)', r'import \1\nimport \2', line)
                # Паттерн: from xxx import yyfrom zzz
                line = re.sub(r'(from\s+\S+\s+import\s+\S+)(from\s+\S+\s+import\s+\S+)', r'\1\n\2', line)
            
            # 3. Исправляем классы без тела
            if line.strip().startswith('class ') and line.strip().endswith(':'):
                fixed_lines.append(line)
                # Проверяем следующую строку
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip().startswith('"""') and not next_line.startswith('    '):
                        # Добавляем отступ к docstring
                        fixed_lines.append('    ' + next_line.strip())
                        i += 1  # пропускаем следующую строку
                    elif next_line.strip() and not next_line.startswith('    '):
                        # Добавляем pass если нет тела
                        fixed_lines.append('    pass')
                i += 1
                continue
            
            # 4. Исправляем функции без тела
            if re.match(r'^\s*(def |async def )', line) and line.strip().endswith(':'):
                fixed_lines.append(line)
                # Проверяем следующую строку
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip().startswith('"""') and not next_line.strip().startswith('    """'):
                        # Исправляем отступ docstring
                        indent = len(line) - len(line.lstrip()) + 4
                        fixed_lines.append(' ' * indent + next_line.strip())
                        i += 1  # пропускаем следующую строку
                    elif next_line.strip() and not next_line.startswith(' ' * (len(line) - len(line.lstrip()) + 4)):
                        # Добавляем pass если нет тела
                        indent = len(line) - len(line.lstrip()) + 4
                        fixed_lines.append(' ' * indent + 'pass')
                i += 1
                continue
            
            # 5. Исправляем поврежденные docstring'и
            if '"""' in line:
                # Множественные docstring в одной строке
                if line.count('"""') > 2:
                    # Разбиваем на отдельные docstring'и
                    parts = line.split('"""')
                    first_part = parts[0]
                    if first_part.strip():
                        fixed_lines.append(first_part)
                    
                    # Каждый docstring на отдельной строке
                    for j in range(1, len(parts) - 1, 2):
                        if j + 1 < len(parts):
                            docstring_content = parts[j]
                            if docstring_content.strip():
                                fixed_lines.append('    """' + docstring_content + '"""')
                    
                    i += 1
                    continue
                
                # Исправляем незакрытые docstring'и
                if line.count('"""') == 1 and not line.strip().endswith('"""'):
                    line = line.rstrip() + '"""'
            
            # 6. Исправляем строки с def и docstring в одной линии
            if ('def ' in line or 'async def' in line) and ':"""' in line:
                # Разделяем определение функции и docstring
                parts = line.split(':"""', 1)
                if len(parts) == 2:
                    func_def = parts[0] + ':'
                    docstring_part = parts[1]
                    
                    fixed_lines.append(func_def)
                    
                    # Определяем отступ для docstring
                    func_indent = len(func_def) - len(func_def.lstrip())
                    docstring_indent = ' ' * (func_indent + 4)
                    
                    if docstring_part.strip():
                        fixed_lines.append(docstring_indent + '"""' + docstring_part.strip())
                    
                    i += 1
                    continue
            
            # 7. Исправляем проблемы с отступами после двоеточия
            if line.strip().endswith(':') and i + 1 < len(lines):
                next_line = lines[i + 1]
                current_indent = len(line) - len(line.lstrip())
                expected_indent = current_indent + 4
                
                if next_line.strip() and not next_line.startswith(' ' * expected_indent):
                    # Если следующая строка не имеет правильного отступа
                    if next_line.strip().startswith('"""'):
                        # Это docstring - исправляем отступ
                        fixed_lines.append(line)
                        fixed_lines.append(' ' * expected_indent + next_line.strip())
                        i += 2
                        continue
            
            # 8. Исправляем слипшиеся операторы
            line = re.sub(r'(\w+)\s*:\s*(\w+)', r'\1: \2', line)
            line = re.sub(r'(if\s+[^:]+):\s*([^"]\w+)', r'\1:\n    \2', line)
            
            # 9. Исправляем отступы в блоках
            if line.strip() and not line.startswith(' ') and i > 0:
                prev_line = lines[i - 1] if i > 0 else ''
                # Если предыдущая строка заканчивается двоеточием, нужен отступ
                if prev_line.strip().endswith(':') and not line.strip().startswith(('#', 'import', 'from')):
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    line = ' ' * (prev_indent + 4) + line.strip()
            
            fixed_lines.append(line)
            i += 1
        
        # Финальная обработка
        result_lines = []
        for line in fixed_lines:
            # Убираем пустые docstring'и
            if line.strip() == '""""""':
                continue
            # Исправляем двойные отступы
            if line.startswith('        ') and not ('def ' in line or 'class ' in line):
                line = line[4:]  # убираем лишние 4 пробела
            result_lines.append(line)
        
        # Записываем исправленный файл
        new_content = '\n'.join(result_lines)
        
        # Простая проверка синтаксиса
        try:
            compile(new_content, file_path, 'exec')
        except SyntaxError as e:
            print(f"⚠️  Синтаксическая ошибка в {file_path}: {e}")
            # Не записываем файл если есть синтаксические ошибки
            return False
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Исправлен: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении {file_path}: {e}")
        return False


def main():
    """Исправляет только файлы с известными ошибками."""
    
    # Файлы с известными ошибками из вывода get_errors
    problem_files = [
        "gui/base_window.py",
        "data_loader/streaming.py", 
        "gui/error_handling.py",
        "templating/engine.py",
        "resend/client.py",
        "resend/retry.py",
        "mailing/preflight.py",
        "mailing/webhook_server.py",
        "mailing/models.py",
        "mailing/cli.py",
        "data_loader/base.py",
        "data_loader/excel_loader.py",
        "data_loader/csv_loader.py",
        "persistence/events_repository.py",
        "persistence/repository.py",
        "persistence/db.py",
        "mailing/logging_config.py",
        "resend/rate_limiter.py",
        "validation/email_validator.py",
        "security/__init__.py",
        "test_full_cycle.py"
    ]
    
    # Добавляем тестовые файлы
    for test_file in [
        "tests/test_additional.py",
        "tests/test_system_complete.py", 
        "tests/test_interfaces.py",
        "tests/test_performance.py",
        "tests/test_quick.py",
        "tests/test_final.py",
        "tests/test_core.py",
        "tests/test_template_persistence.py",
        "tests/test_cli_comprehensive.py",
        "tests/test_preflight_comprehensive.py",
        "tests/test_webhook_comprehensive.py",
        "tests/test_excel_comprehensive.py",
        "tests/test_remaining_coverage.py",
        "tests/test_additional_coverage.py",
        "tests/test_improved_code.py"
    ]:
        problem_files.append(test_file)
    
    # Добавляем файлы отчетов
    for report_file in [
        "monitor_real.py",
        "show_real_status.py", 
        "real_time_monitor.py",
        "final_report.py",
        "real_email_test.py",
        "comprehensive_report.py",
        "simple_real_test.py",
        "onboarding_test.py",
        "final_real_test.py",
        "comprehensive_project_report.py",
        "optimize_performance.py",
        "perfect_performance_report.py",
        "comprehensive_audit.py",
        "deep_analysis.py"
    ]:
        problem_files.append(report_file)
    
    print(f"🔧 Исправление {len(problem_files)} проблемных файлов...")
    
    fixed_count = 0
    
    for file_path in problem_files:
        if os.path.exists(file_path):
            if fix_python_file_aggressively(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  Файл не найден: {file_path}")
    
    print(f"\n📊 Результат: исправлено {fixed_count} из {len(problem_files)} файлов")


if __name__ == "__main__":
    main()