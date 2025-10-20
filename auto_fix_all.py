#!/usr/bin/env python3

import os
import ast
import re
import textwrap
from pathlib import Path
from typing import List, Tuple, Optional

class SmartIndentationFixer:
    """Умный фиксер отступов для Python файлов."""
    
    def __init__(self):
        self.fixed_files = 0
        self.failed_files = 0
        
    def fix_file(self, file_path: str) -> bool:
        """Исправляет один файл."""
        try:
            print(f"🔧 Исправляем {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Попробуем несколько стратегий исправления
            fixed_content = self._apply_fixes(content)
            
            # Проверим что исправленный код синтаксически корректен
            try:
                ast.parse(fixed_content)
            except (SyntaxError, IndentationError) as e:
                print(f"  ❌ Не удалось исправить: {e}")
                return False
            
            # Сохраняем исправленный файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"  ✅ Исправлено")
            return True
            
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            return False
    
    def _apply_fixes(self, content: str) -> str:
        """Применяет различные стратегии исправления."""
        lines = content.splitlines()
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Исправляем различные типичные проблемы
            fixed_line = self._fix_line(line, i, lines)
            
            # Проверяем специальные случаи
            if self._is_docstring_line(fixed_line) and not self._is_properly_indented(fixed_line, fixed_lines):
                # Исправляем отступы для docstring
                fixed_line = self._fix_docstring_indent(fixed_line, fixed_lines)
            
            if self._is_function_def_broken(line, i, lines):
                # Исправляем разорванные определения функций
                fixed_line = self._fix_broken_function_def(i, lines)
                if isinstance(fixed_line, tuple):
                    # Если вернули кортеж, значит объединили несколько строк
                    fixed_lines.append(fixed_line[0])
                    i += fixed_line[1]  # Пропускаем объединенные строки
                    continue
            
            fixed_lines.append(fixed_line)
            i += 1
        
        return '\n'.join(fixed_lines)
    
    def _fix_line(self, line: str, line_num: int, all_lines: List[str]) -> str:
        """Исправляет одну строку."""
        # Убираем лишние пробелы в начале, если это не отступы
        if line.lstrip().startswith('import ') and line.startswith('    '):
            # Импорты в начале файла не должны иметь отступов
            if line_num < 10:
                return line.lstrip()
        
        # Исправляем случаи где docstring склеен с определением
        if '"""' in line and ('def ' in line or 'class ' in line):
            parts = line.split('"""')
            if len(parts) >= 2:
                # Разделяем на определение и docstring
                definition = parts[0].rstrip()
                docstring = '"""' + '"""'.join(parts[1:])
                return definition
        
        # Исправляем неправильные отступы для docstring
        if line.strip().startswith('"""') and not line.startswith('    '):
            # Добавляем правильный отступ для docstring
            return '    ' + line.lstrip()
        
        return line
    
    def _is_docstring_line(self, line: str) -> bool:
        """Проверяет является ли строка docstring."""
        stripped = line.strip()
        return stripped.startswith('"""') or stripped.startswith("'''")
    
    def _is_properly_indented(self, line: str, previous_lines: List[str]) -> bool:
        """Проверяет правильно ли проставлены отступы."""
        if not previous_lines:
            return True
        
        # Ищем последнее определение функции или класса
        for prev_line in reversed(previous_lines[-10:]):  # Смотрим только последние 10 строк
            if prev_line.strip().startswith(('def ', 'class ', 'async def ')):
                # docstring должен иметь отступ на 4 пробела больше чем определение
                expected_indent = len(prev_line) - len(prev_line.lstrip()) + 4
                actual_indent = len(line) - len(line.lstrip())
                return actual_indent == expected_indent
        
        return True
    
    def _fix_docstring_indent(self, line: str, previous_lines: List[str]) -> str:
        """Исправляет отступ для docstring."""
        if not previous_lines:
            return line
        
        # Ищем последнее определение
        for prev_line in reversed(previous_lines[-5:]):
            if prev_line.strip().startswith(('def ', 'class ', 'async def ')):
                base_indent = len(prev_line) - len(prev_line.lstrip())
                expected_indent = base_indent + 4
                return ' ' * expected_indent + line.lstrip()
        
        return line
    
    def _is_function_def_broken(self, line: str, line_num: int, all_lines: List[str]) -> bool:
        """Проверяет разорвано ли определение функции."""
        if ':"""' in line and ('def ' in line or 'class ' in line):
            return True
        return False
    
    def _fix_broken_function_def(self, line_num: int, all_lines: List[str]) -> Tuple[str, int]:
        """Исправляет разорванное определение функции."""
        line = all_lines[line_num]
        
        if ':"""' in line:
            # Разделяем определение и docstring
            parts = line.split(':"""')
            definition = parts[0] + ':'
            docstring_content = '"""' + '"""'.join(parts[1:])
            
            # Возвращаем только определение, docstring пропускаем
            return definition, 0
        
        return line, 0


def main():
    """Главная функция для исправления всех файлов."""
    print("🚀 Начинаем массовое исправление отступов...")
    
    fixer = SmartIndentationFixer()
    root_dir = Path(".")
    
    # Получаем список всех проблемных файлов
    error_files = []
    
    for py_file in root_dir.rglob("*.py"):
        if any(skip_dir in str(py_file) for skip_dir in ['.venv', '__pycache__', '.git']):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
        except (SyntaxError, IndentationError):
            error_files.append(str(py_file))
    
    print(f"📋 Найдено {len(error_files)} файлов с ошибками")
    
    # Исправляем каждый файл
    for file_path in error_files:
        if fixer.fix_file(file_path):
            fixer.fixed_files += 1
        else:
            fixer.failed_files += 1
    
    print(f"\n📊 Результат:")
    print(f"✅ Исправлено: {fixer.fixed_files} файлов")
    print(f"❌ Не удалось: {fixer.failed_files} файлов")
    
    # Финальная проверка
    remaining_errors = 0
    for py_file in root_dir.rglob("*.py"):
        if any(skip_dir in str(py_file) for skip_dir in ['.venv', '__pycache__', '.git']):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
        except (SyntaxError, IndentationError):
            remaining_errors += 1
    
    print(f"🔍 Осталось ошибок: {remaining_errors}")
    
    if remaining_errors == 0:
        print("🎉 Все файлы успешно исправлены!")
    else:
        print("⚠️ Некоторые файлы требуют ручного исправления")


if __name__ == "__main__":
    main()