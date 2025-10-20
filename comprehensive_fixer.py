from pathlib import Path
from typing import List, Dict, Set
import os
import re

import ast
import subprocess

#!/usr/bin/env python3
"""
Комплексный скрипт для исправления всех косметических недочетов"""

class ComprehensiveFixer:"""Класс для комплексного исправления недочетов"""
"""Класс ComprehensiveFixer."""

    def __init__(self, project_root: str):
    """Инициализирует объект."""
    self.project_root = Path(project_root)
    self.fixed_files = set()
    self.total_fixes = 0

    def fix_syntax_errors(self, file_path: Path) -> int:"""Исправляет синтаксические ошибки"""
    """Выполняет fix syntax errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes = 0

        # Исправляем некорректные docstringslines = content.split('\n')
        fixed_lines = []
        i = 0

            while i < len(lines):
            line = lines[i]

                # Исправляем неправильные docstringsif line.strip().startswith('"""') and not line.strip().endswith('"""'):
                # Проверяем следующие строки для завершения docstring
                docstring_lines = [line]
                    j = i + 1while j < len(lines) and not lines[j].strip().endswith('"""'):
                    docstring_lines.append(lines[j])
                    j += 1

                    if j < len(lines):
                    docstring_lines.append(lines[j])

                    # Объединяем в правильный docstring
                        if len(docstring_lines) == 1:
                        # Однострочный docstringtext = line.strip().replace('"""', '').strip()
                            if text:
                            indent = len(line) - len(line.lstrip())fixed_lines.append(' ' * indent + f'"""{text}"""')
                        else:
                            fixed_lines.append(line)
                    else:
                        # Многострочный docstring - просто добавляем как есть
                        fixed_lines.extend(docstring_lines)

                    i = j + 1
                    fixes += 1
                    continue

            fixed_lines.append(line)
            i += 1

            if fixes > 0:content = '\n'.join(fixed_lines)

        # Исправляем оборванные строкиcontent = re.sub(r'(["\'])([^"\']*)\n\s*([^"\']*)\1', r'\1\2\3\1', content)

            # Исправляем trailing whitespacelines = content.split('\n')content = '\n'.join(line.rstrip() for line in lines)

            if content != original_content:with open(file_path,'w', encoding='utf-8') as f:
                f.write(content)
                return fixes

            return 0

        except Exception as e:
        print(f"Ошибка при исправлении {file_path}: {e}")
            return 0

    def fix_style_issues(self, file_path: Path) -> int:"""Исправляет проблемы стиля"""
    """Выполняет fix style issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        fixed_lines = []
        fixes = 0

            for i, line in enumerate(lines):
            original_line = line

                # Убираем trailing whitespaceline = line.rstrip() + '\n' if line.strip() else '\n'

            # Исправляем множественные пустые строки (максимум 2 подряд)
                if (i > 0 and i < len(lines) - 1 and
                not line.strip() and not lines[i-1].strip() and
                not lines[i+1].strip()):
                continue  # Пропускаем лишние пустые строки

                # Добавляем пробелы вокруг операторовif '=' in line and not line.strip().startswith('#'):
                # Исправляем пробелы вокруг =line = re.sub(r'(\w)=(\w)', r'\1 = \2', line)line = re.sub(r'(\w) = = (\w)', r'\1 == \2', line)  # Исправляем ==

                if line != original_line:
                fixes += 1

            fixed_lines.append(line)

            if fixes > 0:with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)

            return fixes

        except Exception as e:
        print(f"Ошибка при исправлении стиля {file_path}: {e}")
            return 0

    def fix_long_lines(self, file_path: Path, max_length: int = 88) -> int:"""Исправляет длинные строки"""
    """Выполняет fix long lines."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        fixed_lines = []
        fixes = 0

            for line in lines:if len(line.rstrip()) > max_length and not line.strip().startswith('#'):
                    # Пытаемся разбить строкуif ',' in line and not any(op in line for op in ['"""', "'''"]):
                    # Разбиваем по запятым
                    indent = len(line) - len(line.lstrip())
                    parts = line.split(',')

                        if len(parts) > 2:
                        new_lines = []
                        current = parts[0].rstrip()

                            for part in parts[1:-1]:if len(current + ',
                            ' + part.strip()) <= max_length:current += ',' + part.strip()
                            else:new_lines.append(current + ',\n')current = ' ' * (indent + 4) + part.strip()

                        # Последняя часть
                            if parts[-1].strip():current += ',' + parts[-1].rstrip()
                        else:current += ','
                        new_lines.append(current + '\n')
                        fixed_lines.extend(new_lines)
                        fixes += 1
                        continue

            fixed_lines.append(line)

            if fixes > 0:with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)

            return fixes

        except Exception as e:
        print(f"Ошибка при исправлении длинных строк {file_path}: {e}")
            return 0

    def add_missing_docstrings(self, file_path: Path) -> int:"""Добавляет недостающие docstrings"""
    """Выполняет add missing docstrings."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Простые эвристики для добавления docstringslines = content.split('\n')
        fixed_lines = []
        fixes = 0

        i = 0
            while i < len(lines):
            line = lines[i]

                # Проверяем определения функций/классов без docstringif re.match(r'^\s*(def |class |async def )', line):
                # Проверяем, есть ли уже docstring
                next_line_idx = i + 1
                    while (next_line_idx < len(lines) and
                       not lines[next_line_idx].strip()):
                    next_line_idx += 1

                has_docstring = (next_line_idx < len(lines) and '"""' in lines[next_line_idx])

                    if not has_docstring:
                    # Добавляем простой docstring
                        indent = len(line) - len(line.lstrip())func_name = re.search(r'(def |class )(\w+)', line)

                        if func_name:
                            name = func_name.group(2)if name.startswith('test_'):docstring = f'"""Тест для {name[5:].replace("_", " ")}."""'elif name == '__init__':docstring = '"""Инициализирует объект."""'elif line.strip().startswith('class'):docstring = f'"""Класс {name}."""'
                        else:docstring = f'"""Выполняет {name.replace("_", " ")}."""'

                        fixed_lines.append(line)fixed_lines.append(' ' * (indent + 4) + docstring)
                        fixes += 1
                        i += 1
                        continue

            fixed_lines.append(line)
            i += 1

            if fixes > 0:content = '\n'.join(fixed_lines)with open(file_path,'w', encoding='utf-8') as f:
                f.write(content)

            return fixes

        except Exception as e:
        print(f"Ошибка при добавлении docstrings {file_path}: {e}")
            return 0

    def fix_imports(self, file_path: Path) -> int:"""Исправляет импорты"""
    """Выполняет fix imports."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')
        import_lines = []
        other_lines = []
        in_imports = True

            for line in lines:if line.strip().startswith(('import ', 'from ')) or (not line.strip() and in_imports):
                import_lines.append(line)
            else:
                    if in_imports and line.strip():
                    in_imports = False
                other_lines.append(line)

            # Сортируем импортыimports = [line for line in import_lines if line.strip().startswith(('import ', 'from '))]
            empty_lines = [line for line in import_lines if not line.strip()]

        imports.sort()

        # Группируем импорты
        stdlib_imports = []
        third_party_imports = []
        local_imports = []

            for imp in imports:if 'from .' in imp or any(local in imp for local in ['mailing',
            'templating','persistence','resend','validation','data_loader','stats', 'gui']):
                    local_imports.append(imp)elif any(stdlib in imp for stdlib in ['os',
                    'sys','json','sqlite3','asyncio','pathlib','re', 'typing']):
                stdlib_imports.append(imp)
            else:
                third_party_imports.append(imp)

        # Собираем правильный порядок импортов
        organized_imports = []
            if stdlib_imports:
            organized_imports.extend(stdlib_imports)organized_imports.append('')
            if third_party_imports:
            organized_imports.extend(third_party_imports)organized_imports.append('')
            if local_imports:
            organized_imports.extend(local_imports)organized_imports.append('')
        new_content = '\n'.join(organized_imports + other_lines)

            if new_content != content:with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                return 1

            return 0

        except Exception as e:
        print(f"Ошибка при исправлении импортов {file_path}: {e}")
            return 0

    def fix_file(self, file_path: Path) -> Dict[str, int]:"""Исправляет все проблемы в файле"""
    """Выполняет fix file."""
    fixes = {
        'syntax': 0,'style': 0,'long_lines': 0,'docstrings': 0,'imports': 0
    }
        if '.venv' in str(file_path) or '__pycache__' in str(file_path):
            return fixes

        try:fixes['syntax'] = self.fix_syntax_errors(file_path)fixes['style'] = self.fix_style_issues(file_path)fixes['long_lines'] = self.fix_long_lines(file_path)fixes['docstrings'] = self.add_missing_docstrings(file_path)fixes['imports'] = self.fix_imports(file_path)

        total = sum(fixes.values())
            if total > 0:
            self.fixed_files.add(str(file_path))
            self.total_fixes += total

        except Exception as e:
        print(f"Ошибка при обработке {file_path}: {e}")

        return fixes

    def fix_all(self):"""Исправляет все файлы проекта"""print("🔧 КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ КОСМЕТИЧЕСКИХ НЕДОЧЕТОВ")print("=" * 80)
    """Выполняет fix all."""

    # Основные Python файлыpython_files = list(self.project_root.rglob("*.py"))

    total_syntax = 0
    total_style = 0
    total_long_lines = 0
    total_docstrings = 0
    total_imports = 0

        for file_path in python_files:
        fixes = self.fix_file(file_path)

        total_syntax += fixes['syntax']total_style += fixes['style']total_long_lines += fixes['long_lines']total_docstrings += fixes['docstrings']total_imports += fixes['imports']

            if sum(fixes.values()) > 0:
            file_rel = file_path.relative_to(self.project_root)
            print(f"✅ {file_rel}: "f"syntax:{fixes['syntax']},
                "f"style:{fixes['style']},"f"lines:{fixes['long_lines']},
                "f"docs:{fixes['docstrings']}, "f"imports:{fixes['imports']}")

    print()print("🎉 КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО:")print(f"   🔧 Синтаксические ошибки: {total_syntax}")print(f"   🎨 Проблемы стиля: {total_style}")print(f"   📏 Длинные строки: {total_long_lines}")print(f"   📚 Недостающие docstrings: {total_docstrings}")print(f"   📦 Проблемы импортов: {total_imports}")print(f"   📊 Всего исправлений: {self.total_fixes}")print(f"   📁 Обработано файлов: {len(self.fixed_files)}")

def main():"""Основная функция"""project_root = "/Users/alexandr/Desktop/Projects/Scripts/Mailing"
    """Выполняет main."""
    fixer = ComprehensiveFixer(project_root)
    fixer.fix_all()

if __name__ == "__main__":
    main()
