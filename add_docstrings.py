from pathlib import Path
from typing import List, Tuple, Dict
import os

import ast

#!/usr/bin/env python3
"""
Скрипт для автоматического добавления docstrings к функциям и классам"""

class DocstringAdder(ast.NodeVisitor):"""Класс для анализа и добавления docstrings"""
"""Класс DocstringAdder."""

    def __init__(self):
    """Инициализирует объект."""
    self.functions_without_docs = []
    self.classes_without_docs = []

    def visit_FunctionDef(self, node):"""Посещает определения функций"""
    """Выполняет visit FunctionDef."""
        if not self._has_docstring(node):
        self.functions_without_docs.append({
            'name': node.name,'lineno': node.lineno,
                    'args': [arg.arg for arg in node.args.args],'returns': self._get_return_annotation(node)
        })
    self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
    """Посещает асинхронные функции"""
        if not self._has_docstring(node):
        self.functions_without_docs.append({
            'name': node.name,'lineno': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'returns': self._get_return_annotation(node),'async': True
        })
    self.generic_visit(node)

    def visit_ClassDef(self, node):
    """Посещает определения классов"""
        if not self._has_docstring(node):
        self.classes_without_docs.append({
            'name': node.name,'lineno': node.lineno,
                    'bases': [base.id if hasattr(base, 'id') else str(base) for base in node.bases]
        })
    self.generic_visit(node)

    def _has_docstring(self, node):
    """Проверяет наличие docstring"""
        return (node.body and
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str))

    def _get_return_annotation(self, node):"""Получает аннотацию возвращаемого типа"""
    """Выполняет  get return annotation."""
        if hasattr(node, 'returns') and node.returns:if hasattr(node.returns, 'id'):
                return node.returns.id
        else:
                return str(node.returns)
        return None

def generate_function_docstring(func_info: Dict) -> str:
    """Генерирует docstring для функции"""
    name = func_info['name']args = func_info.get('args',
        [])returns = func_info.get('returns')is_async = func_info.get('async', False)

    # Базовое описаниеif name.startswith('_'):
    desc = f"Внутренний метод для {name[1:].replace('_', ' ')}"
    elif name.startswith('test_'):
    desc = f"Тест для {name[5:].replace('_', ' ')}"
    elif name == '__init__':
    desc = "Инициализирует объект"
    else:desc = f"{'Асинхронно ' if is_async else ''}выполняет {name.replace('_', ' ')}"

    docstring = f'    """{desc}.'

    # Добавляем параметрыif args and args != ['self', 'cls']:docstring += '\n    \n    Args:'
        for arg in args:if arg not in ['self',
        'cls']:docstring += f'\n        {arg}: Параметр для {arg.replace("_", " ")}'

    # Добавляем возвращаемое значение
    if returns:docstring += f'\n    \n    Returns:\n        {returns}: Результат выполнения операции'
    docstring += '\n    """'
    return docstring

def generate_class_docstring(class_info: Dict) -> str:
    """Генерирует docstring для класса"""
    name = class_info['name']bases = class_info.get('bases', [])
    if name.startswith('Test'):
    desc = f"Тесты для {name[4:].replace('_', ' ')}"
    elif bases:desc = f"Класс {name} наследующий от {', '.join(bases)}"
    else:desc = f"Класс для работы с {name.lower().replace('_', ' ')}"

    return f'    """{desc}."""'

def add_docstrings_to_file(file_path: Path) -> int:
    """Добавляет docstrings в файл"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tree = ast.parse(content)
    visitor = DocstringAdder()
    visitor.visit(tree)

        if not visitor.functions_without_docs and not visitor.classes_without_docs:
            return 0
    lines = content.split('\n')
    modifications = 0

    # Обрабатываем в обратном порядке, чтобы не сбить номера строк
    all_missing = []

        for func in visitor.functions_without_docs:all_missing.append(('function', func))

        for cls in visitor.classes_without_docs:all_missing.append(('class', cls))

    # Сортируем по номеру строки в обратном порядкеall_missing.sort(key=lambda x: x[1]['lineno'], reverse=True)

        for item_type, item_info in all_missing:lineno = item_info['lineno']
            if item_type == 'function':
            docstring = generate_function_docstring(item_info)
        else:
            docstring = generate_class_docstring(item_info)

        # Найдем строку с определением
        def_line_idx = lineno - 1

        # Найдем следующую строку с кодом (пропустим пустые строки)
            insert_idx = def_line_idx + 1while insert_idx < len(lines) and lines[insert_idx].strip() == '':
            insert_idx += 1

        # Вставляем docstring
        lines.insert(insert_idx, docstring)
        modifications += 1

        if modifications > 0:with open(file_path,'w', encoding='utf-8') as f:f.write('\n'.join(lines))

        return modifications

    except Exception as e:
    print(f"Ошибка при обработке {file_path}: {e}")
        return 0

def main():"""Основная функция"""project_root = Path("/Users/alexandr/Desktop/Projects/Scripts/Mailing")
    """Выполняет main."""

    # Основные модули для документирования
    important_dirs = ["mailing","templating","persistence","resend","validation",
    "data_loader","stats", "gui"
    ]

    total_modifications = 0
    print("🔧 Добавление docstrings к недокументированным функциям и классам...")
    print()

    for dir_name in important_dirs:
    dir_path = project_root / dir_name
        if not dir_path.exists():
        continue
        python_files = list(dir_path.rglob("*.py"))

        for file_path in python_files:
            if '__pycache__' in str(file_path):
            continue

        modifications = add_docstrings_to_file(file_path)
        total_modifications += modifications

            if modifications > 0:
            print(f"✅ {file_path.relative_to(project_root)}: добавлено {modifications} docstrings")

    print()print(f"🎉 ДОБАВЛЕНИЕ DOCSTRINGS ЗАВЕРШЕНО:")print(f"   📚 Всего добавлено: {total_modifications} docstrings")print(f"   📊 Покрытие документацией улучшено")

if __name__ == "__main__":
    main()
