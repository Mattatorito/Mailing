from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import os
import re
import sqlite3
import sys

        import traceback
from datetime import datetime
import ast
import importlib.util
import subprocess

#!/usr/bin/env python3
"""
🔍 ПОЛНЫЙ ДЕТАЛЬНЫЙ АУДИТ ПРОЕКТА
Комплексная проверка всех аспектов системы включая мелкие недочеты"""
sys.path.append(".")



class DetailedProjectAuditor:"""Детальный аудитор проекта с проверкой всех мелочей"""
    """Класс DetailedProjectAuditor."""

    def __init__(self):self.project_root = Path(".")
        """Инициализирует объект."""
        self.issues = []
        self.warnings = []
        self.suggestions = []
        self.stats = {}

    def log_issue(self, level: str, category: str, message: str, file_path: str = None):"""Логирует найденную проблему"""
        """Выполняет log issue."""
        entry = {"level": level,# critical,major,minor,suggestion"category": category,
            "message": message,"file": file_path,"timestamp": datetime.now().isoformat(),
        }
if level == "critical":
            self.issues.append(entry)elif level in ["major", "minor"]:
            self.warnings.append(entry)
        else:
            self.suggestions.append(entry)

    def audit_project_structure(self):"""Проверяет структуру проекта"""print("🏗️ АУДИТ СТРУКТУРЫ ПРОЕКТА")print("-" * 60)
        """Выполняет audit project structure."""

        # Проверяем обязательные файлы
        required_files = {"README.md": "Основная документация",
            "requirements.txt": "Зависимости Python",
            "pyproject.toml": "Конфигурация проекта","LICENSE": "Лицензия",
            ".gitignore": "Игнорируемые файлы Git","Makefile": "Автоматизация",
            "pytest.ini": "Конфигурация тестов",
        }

        for file_name, description in required_files.items():
            if (self.project_root / file_name).exists():print(f"   ✅ {file_name}: {description}")
            else:
                self.log_issue("major","structure", f"Отсутствует {file_name}: {description}"
                )

        # Проверяем структуру директорий
        expected_dirs = {"mailing": "Основная логика отправки",
            "templating": "Система шаблонов","persistence": "Работа с БД",
            "resend": "Интеграция с Resend API","validation": "Валидация данных",
            "data_loader": "Загрузка данных","stats": "Статистика",
            "gui": "Графический интерфейс","tests": "Тестирование",
            "samples": "Примеры данных","security": "Безопасность",
        }
print(f"\n📁 СТРУКТУРА ДИРЕКТОРИЙ:")
        for dir_name, description in expected_dirs.items():
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():file_count = len(list(dir_path.glob("*.py")))print(f"   ✅ {dir_name}/: {description} ({file_count} файлов)")
            else:
                self.log_issue("minor","structure",
                    f"Отсутствует директория {dir_name}: {description}",
                )

        # Проверяем __init__.py файлыprint(f"\n🐍 ПРОВЕРКА __init__.py:")
        python_dirs = [
            d
            for d in self.project_root.iterdir()if d.is_dir() and (d / "__init__.py").exists()
        ]

        for py_dir in python_dirs:init_file = py_dir / "__init__.py"
            if init_file.stat().st_size == 0:self.log_issue("minor","structure", f"Пустой __init__.py в {py_dir}")print(f"   ⚠️ {py_dir}/__init__.py: пустой файл")
            else:print(f"   ✅ {py_dir}/__init__.py: {init_file.stat().st_size} байт")

    def audit_code_quality(self):"""Детальный аудит качества кода"""print(f"\n💻 ДЕТАЛЬНЫЙ АУДИТ КАЧЕСТВА КОДА")print("-" * 60)
        """Выполняет audit code quality."""
python_files = list(self.project_root.rglob("*.py"))
        # Исключаем .venv и служебные файлы
        python_files = [f for f in python_files if ".venv" not in str(f) and "htmlcov" not in str(f)
        ]
print(f"📊 Найдено Python файлов: {len(python_files)}")

        total_lines = 0
        total_functions = 0
        documented_functions = 0
        classes_with_docstrings = 0
        total_classes = 0
        files_with_todos = 0
        files_with_fixmes = 0
        long_functions = []
        complex_functions = []

        for py_file in python_files:
            try:with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                lines = content.splitlines()
                total_lines += len(lines)

                # Проверяем TODOs и FIXMEsif any("TODO" in line or "FIXME" in line for line in lines):
                    todo_lines = [
                        i + 1
                        for i, line in enumerate(lines)if "TODO" in line or "FIXME" in line
                    ]if "TODO" in content:
                        files_with_todos += 1if "FIXME" in content:
                        files_with_fixmes += 1
                    self.log_issue("minor","code_quality",
                        f"TODO/FIXME в строках {todo_lines}",
                        str(py_file),
                    )

                # Анализ AST
                try:
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            total_functions += 1

                            # Проверяем документацию
                            if ast.get_docstring(node):
                                documented_functions += 1
                            else:
                                if not node.name.startswith("_"
                                ):  # Игнорируем приватные
                                    self.log_issue("minor","documentation",
                                        f"Функция {node.name} без docstring",
                                        str(py_file),
                                    )

                            # Проверяем длину функцииif hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                                func_length = node.end_lineno - node.lineno
                                if func_length > 50:
                                    long_functions.append(
                                        (str(py_file), node.name, func_length)
                                    )
                                    self.log_issue("minor","code_quality",
                                        f"Длинная функция {node.name}: {func_length} строк",

                                        str(py_file),
                                    )

                            # Проверяем сложность (количество if/for/while)
                            complexity = sum(
                                1
                                for n in ast.walk(node)
                                if isinstance(n, (ast.If, ast.For, ast.While, ast.Try))
                            )
                            if complexity > 10:
                                complex_functions.append(
                                    (str(py_file), node.name, complexity)
                                )
                                self.log_issue("minor","code_quality",
                                    f"Сложная функция {node.name}: {complexity} ветвлений",

                                    str(py_file),
                                )

                        elif isinstance(node, ast.ClassDef):
                            total_classes += 1
                            if ast.get_docstring(node):
                                classes_with_docstrings += 1
                            else:if not node.name.startswith("_"):
                                    self.log_issue("minor","documentation",
                                        f"Класс {node.name} без docstring",
                                        str(py_file),
                                    )

                except SyntaxError as e:
                    self.log_issue("critical","syntax",f"Синтаксическая ошибка: {e}",
                        str(py_file),
                    )

                # Проверяем стиль кода
                self._check_code_style(py_file, content)

            except Exception as e:
                self.log_issue("major","code_quality",f"Ошибка анализа файла: {e}", str(py_file)
                )

        # Статистика
        doc_coverage = (
            (documented_functions / total_functions * 100) if total_functions > 0 else 0
        )
        class_doc_coverage = (
            (classes_with_docstrings / total_classes * 100) if total_classes > 0 else 0
        )
print(f"\n📊 СТАТИСТИКА КОДА:")print(f"   📄 Всего строк кода: {total_lines:,}")
        print(f"   🔧 Функций: {total_functions} (документировано: {doc_coverage:.1f}%)"
        )
        print(f"   🏗️ Классов: {total_classes} (документировано: {class_doc_coverage:.1f}%)"
        )print(f"   📝 Файлов с TODO: {files_with_todos}")print(f"   🔧 Файлов с FIXME: {files_with_fixmes}")print(f"   📏 Длинных функций (>50 строк): {len(long_functions)}")print(f"   🌪️ Сложных функций (>10 ветвлений): {len(complex_functions)}")
self.stats["code_quality"] = {"total_lines": total_lines,
    "total_functions": total_functions,"documented_functions": documented_functions,
    "doc_coverage": doc_coverage,"total_classes": total_classes,
    "classes_with_docstrings": classes_with_docstrings,
    "class_doc_coverage": class_doc_coverage,"files_with_todos": files_with_todos,
    "long_functions": len(long_functions),"complex_functions": len(complex_functions),
        }

    def _check_code_style(self, file_path: Path, content: str):"""Проверяет стиль кода"""
        """Выполняет  check code style."""
        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            # Проверяем длину строк
            if len(line) > 120:
                self.log_issue("minor","style",
                    f"Длинная строка ({len(line)} символов) в строке {i}",
                    str(file_path),
                )

            # Проверяем trailing whitespaceif line.endswith(" ") or line.endswith("\t"):
                self.log_issue("minor","style",f"Trailing whitespace в строке {i}",
                    str(file_path),
                )

            # Проверяем множественные пустые строки
            if i > 1 and not line.strip() and not lines[i - 2].strip():
                self.log_issue("minor","style",
                    f"Множественные пустые строки в строке {i}",
                    str(file_path),
                )

        # Проверяем imports
        try:
            tree = ast.parse(content)
            imports_after_code = False
            had_non_import = False

            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if had_non_import:
                        imports_after_code = True
                        self.log_issue("minor","style","Импорты после кода", str(file_path)
                        )
                        break
                elif not isinstance(node, (ast.Expr)) or not isinstance(
                    node.value, ast.Constant
                ):
                    # Игнорируем строковые константы (docstrings)
                    had_non_import = True

        except:
            pass  # Игнорируем ошибки парсинга для проверки стиля

    def audit_security_detailed(self):"""Детальный аудит безопасности"""print(f"\n🔒 ДЕТАЛЬНЫЙ АУДИТ БЕЗОПАСНОСТИ")print("-" * 60)
        """Выполняет audit security detailed."""

        # Проверяем секреты в коде
        python_files = [f for f in self.project_root.rglob("*.py") if ".venv" not in str(f)
        ]

        secret_patterns = [
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "Возможный хардкод API ключа"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Возможный хардкод пароля"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Возможный хардкод секрета"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Возможный хардкод токена"),
            (r'["\'][a-zA-Z0-9]{32,}["\']', "Возможный хардкод токена/ключа"),
        ]

        for py_file in python_files:
            try:with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                for pattern, description in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Исключаем очевидно безопасные случаи
                        matched_text = match.group(0).lower()
                        if any(
                            safe in matched_text
                            for safe in ["test","example","dummy","placeholder","xxx",
                            ]
                        ):
                            continue
line_num = content[: match.start()].count("\n") + 1
                        self.log_issue("major","security",
                            f"{description} в строке {line_num}: {match.group(0)[:50]}...",

                            str(py_file),
                        )
            except:
                pass

        # Проверяем SQL инъекции
        sql_patterns = [
            r'\.execute\s*\(\s*f["\']',# f-string в executer'\.execute\s*\(\s*["\'].*%s',  # % форматирование
            r"\.execute\s*\(\s*.*\.format\(",  # .format()
        ]

        for py_file in python_files:
            try:with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                for pattern in sql_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:line_num = content[: match.start()].count("\n") + 1
                        self.log_issue("major","security",
                            f"Потенциальная SQL инъекция в строке {line_num}",
                            str(py_file),
                        )
            except:
                pass

        # Проверяем переменные окруженияenv_vars = ["RESEND_API_KEY", "RESEND_FROM_EMAIL"]print(f"\n🔐 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
        for var in env_vars:
            if os.environ.get(var):print(f"   ✅ {var}: настроен")
            else:
                self.log_issue("critical","security", f"Переменная окружения {var} не настроена"
                )print(f"   ❌ {var}: НЕ НАСТРОЕН")

        # Проверяем .env файлif (self.project_root / ".env").exists():
            self.log_issue("major","security",
                ".env файл в репозитории (должен быть в .gitignore)",
            )

        # Проверяем права на файлы БДdb_files = list(self.project_root.glob("*.sqlite*"))
        for db_file in db_files:
            try:
                permissions = oct(db_file.stat().st_mode)[-3:]if permissions != "644":
                    self.log_issue("minor","security",
                        f"Небезопасные права на БД {db_file}: {permissions}",
                    )
            except:
                pass

    def audit_dependencies(self):"""Аудит зависимостей"""print(f"\n📦 АУДИТ ЗАВИСИМОСТЕЙ")print("-" * 60)
        """Выполняет audit dependencies."""

        # Читаем requirements.txtif (self.project_root / "requirements.txt").exists():with open("requirements.txt", "r") as f:
                deps = [
                    line.strip()
                    for line in fif line.strip() and not line.startswith("#")
                ]
print(f"📋 Зависимостей в requirements.txt: {len(deps)}")

            # Проверяем закрепленные версии
            unpinned = []
            for dep in deps:if "==" not in dep and ">=" not in dep and "~=" not in dep:
                    unpinned.append(dep)
                    self.log_issue("minor","dependencies", f"Незакрепленная версия: {dep}"
                    )

            if unpinned:print(f"   ⚠️ Незакрепленных версий: {len(unpinned)}")
            else:print(f"   ✅ Все версии закреплены")

            # Проверяем дублирование с pyproject.tomlif (self.project_root / "pyproject.toml").exists():
                try:with open("pyproject.toml", "r") as f:
                        pyproject_content = f.read()
if "dependencies" in pyproject_content:
                        self.log_issue("minor","dependencies",
                            "Дублирование зависимостей в requirements.txt и pyproject.toml",

                        )
                except:
                    pass

        # Проверяем неиспользуемые импорты
        self._check_unused_imports()

    def _check_unused_imports(self):"""Проверяет неиспользуемые импорты"""
        """Выполняет  check unused imports."""
        python_files = [
            ffor f in self.project_root.rglob("*.py")if ".venv" not in str(f) and "test_" not in f.name
        ]

        for py_file in python_files[:10]:  # Проверяем первые 10 файлов
            try:with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)
                imports = []
                used_names = set()

                # Собираем импорты
                for node in tree.body:
                    if isinstance(node, ast.Import):
                        for alias in node.names:imports.append(alias.name.split(".")[0])
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            imports.append(alias.name)

                # Собираем используемые имена
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name):
                        used_names.add(node.id)
                    elif isinstance(node, ast.Attribute):
                        if isinstance(node.value, ast.Name):
                            used_names.add(node.value.id)

                # Находим неиспользуемые
                unused = [imp for imp in imports if imp not in used_names]
                for unused_import in unused:
                    self.log_issue("minor","code_quality",
                        f"Возможно неиспользуемый импорт: {unused_import}",
                        str(py_file),
                    )

            except:
                pass

    def audit_testing_detailed(self):"""Детальный аудит тестирования"""print(f"\n🧪 ДЕТАЛЬНЫЙ АУДИТ ТЕСТИРОВАНИЯ")print("-" * 60)
        """Выполняет audit testing detailed."""

        test_files = (list((self.project_root / "tests").glob("test_*.py"))if (self.project_root / "tests").exists()
            else []
        )
print(f"📋 Тестовых файлов: {len(test_files)}")

        total_test_functions = 0
        test_files_stats = {}

        for test_file in test_files:
            try:with open(test_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                test_functions = []
                setup_functions = []
                teardown_functions = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):if node.name.startswith("test_"):
                            test_functions.append(node.name)
                            total_test_functions += 1elif node.name in ["setUp",
                                "setup_method", "setup_function"]:
                            setup_functions.append(node.name)
                        elif node.name in ["tearDown","teardown_method",
                            "teardown_function",
                        ]:
                            teardown_functions.append(node.name)

                test_files_stats[test_file.name] = {"test_functions": len(test_functions),
                    "setup_functions": len(setup_functions),
                    "teardown_functions": len(teardown_functions),
                    "size": test_file.stat().st_size,
                }

                # Проверяем качество тестов
                if len(test_functions) == 0:
                    self.log_issue("minor","testing", f"Нет тестовых функций в {test_file.name}"
                    )
                elif len(test_functions) < 3:
                    self.log_issue("minor","testing",
                        f"Мало тестов в {test_file.name}: {len(test_functions)}",
                    )

                # Проверяем assertionsassertion_count = content.count("assert")
                if assertion_count < len(test_functions):
                    self.log_issue("minor","testing",
                        f"Мало assertions в {test_file.name}: {assertion_count} для {len(test_functions)} тестов",

                    )

            except Exception as e:
                self.log_issue("major","testing", f"Ошибка анализа {test_file.name}: {e}"
                )
print(f"🔧 Всего тестовых функций: {total_test_functions}")

        # Проверяем покрытие модулей тестамиmain_modules = ["mailing", "templating", "persistence", "resend", "validation"]
        modules_with_tests = set()

        for test_file in test_files:
            try:with open(test_file, "r") as f:
                    content = f.read()
                for module in main_modules:if f"from {module}" in content or f"import {module}" in content:
                        modules_with_tests.add(module)
            except:
                pass

        untested_modules = set(main_modules) - modules_with_tests
        if untested_modules:
            for module in untested_modules:self.log_issue("major","testing", f"Модуль {module} не покрыт тестами")

        # Пытаемся запустить тесты
        try:
            result = subprocess.run([".venv/bin/python","-m","pytest","--collect-only",
                "-q"],
                capture_output = True,
                text = True,
                timeout = 30,
            )

            if result.returncode == 0:print("✅ Тесты корректно собираются pytest")
            else:
                self.log_issue("major","testing", f"Ошибки сборки тестов: {result.stderr}"
                )

        except Exception as e:self.log_issue("minor","testing", f"Не удалось запустить pytest: {e}")

    def audit_documentation(self):"""Аудит документации"""print(f"\n📚 АУДИТ ДОКУМЕНТАЦИИ")print("-" * 60)
        """Выполняет audit documentation."""

        # Проверяем основные документы
        docs = {"README.md": "Основная документация",
            "INSTALL.md": "Инструкции по установке","CHANGELOG.md": "История изменений",
            "CONTRIBUTING.md": "Руководство для разработчиков",
            "SECURITY.md": "Политика безопасности","API.md": "Документация API",
        }

        for doc_file, description in docs.items():
            file_path = self.project_root / doc_file
            if file_path.exists():
                size = file_path.stat().st_sizeprint(f"   ✅ {doc_file}: {description} ({size} байт)")

                # Проверяем содержимое READMEif doc_file == "README.md":
                    self._check_readme_quality(file_path)
            else:if doc_file in ["README.md", "INSTALL.md"]:
                    self.log_issue("major","documentation",
                        f"Отсутствует {doc_file}: {description}",
                    )
                else:
                    self.log_issue("minor","documentation",
                        f"Рекомендуется добавить {doc_file}: {description}",
                    )

        # Проверяем docstrings в модулях
        self._check_module_documentation()

    def _check_readme_quality(self, readme_path: Path):"""Проверяет качество README"""
        """Выполняет  check readme quality."""
        try:with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Проверяем обязательные разделы
            required_sections = [("# ","Заголовок проекта"),("## Installation",
                "Раздел установки"),("## Usage","Раздел использования"),
                ("## Requirements","Требования"),
            ]

            for pattern, description in required_sections:
                if pattern.lower() not in content.lower():
                    self.log_issue("minor","documentation", f"В README отсутствует {description}"
                    )

            # Проверяем длину
            if len(content) < 1000:
                self.log_issue("minor","documentation", "README слишком краткий (< 1000 символов)"
                )

            # Проверяем примеры кодаif "```" not in content:self.log_issue("minor", "documentation", "В README нет примеров кода")

        except Exception as e:self.log_issue("minor","documentation", f"Ошибка анализа README: {e}")

    def _check_module_documentation(self):"""Проверяет документацию модулей"""
        """Выполняет  check module documentation."""
        main_modules = ["mailing","templating","persistence","resend","validation",
            "security",
        ]

        for module_name in main_modules:
            module_path = self.project_root / module_name
            if module_path.exists():init_file = module_path / "__init__.py"
                if init_file.exists():
                    try:with open(init_file, "r", encoding="utf-8") as f:
                            content = f.read()

                        if not content.strip():
                            self.log_issue("minor","documentation",
                                f"Пустой __init__.py в модуле {module_name}",
                            )
                        elif '"""' not in content:
                            self.log_issue(
                                "minor","documentation",
                                    f"Нет module docstring в {module_name}",
                            )

                    except Exception as e:
                        self.log_issue("minor","documentation",
                            f"Ошибка чтения {module_name}/__init__.py: {e}",
                        )

    def audit_database(self):"""Аудит базы данных"""print(f"\n💾 АУДИТ БАЗЫ ДАННЫХ")print("-" * 60)
        """Выполняет audit database."""
db_files = list(self.project_root.glob("*.sqlite*"))

        for db_file in db_files:print(f"\n📊 Анализ {db_file}:")
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()

                # Получаем список таблицcursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
print(f"   📋 Таблиц: {len(tables)}")

                total_records = 0
                for (table_name,) in tables:
                    # Проверяем количество записей (безопасно для PRAGMA/системных запросов)cursor.execute("SELECT COUNT(*) FROM " + table_name)
                    count = cursor.fetchone()[0]
                    total_records += count

                    if count > 0:print(f"      {table_name}: {count:,} записей")
                    else:print(f"      {table_name}: пустая")

                    # Проверяем схемуcursor.execute("PRAGMA table_info(" + table_name + ")")
                    columns = cursor.fetchall()

                    # Проверяем индексыcursor.execute("PRAGMA index_list(" + table_name + ")")
                    indexes = cursor.fetchall()

                    if len(columns) > 5 and len(indexes) == 0:
                        self.log_issue("minor","database",
                            f"Таблица {table_name} без индексов ({len(columns)} колонок)",

                        )

                    # Проверяем foreign keyscursor.execute("PRAGMA foreign_key_list(" + table_name + ")")
                    fks = cursor.fetchall()

                    # Проверяем типы данных
                    for col in columns:
                        col_name, col_type = col[1], col[2]
                        if not col_type:  # Пустой тип данных
                            self.log_issue("minor","database",
                                f"Колонка {table_name}.{col_name} без типа данных",
                            )
print(f"   📊 Всего записей: {total_records:,}")

                # Проверяем настройки БДcursor.execute("PRAGMA foreign_keys")
                fk_enabled = cursor.fetchone()[0]
                if not fk_enabled:
                    self.log_issue("minor","database", f"Foreign keys не включены в {db_file}"
                    )
cursor.execute("PRAGMA journal_mode")
                journal_mode = cursor.fetchone()[0]if journal_mode != "wal":
                    self.log_issue("minor","database",
                        f"Неоптимальный journal_mode в {db_file}: {journal_mode}",
                    )

                conn.close()

            except Exception as e:self.log_issue("major","database", f"Ошибка анализа БД {db_file}: {e}")

    def audit_performance(self):"""Аудит производительности"""print(f"\n⚡ АУДИТ ПРОИЗВОДИТЕЛЬНОСТИ")print("-" * 60)
        """Выполняет audit performance."""

        # Проверяем размеры файлов
        large_files = []
        total_size = 0
for file_path in self.project_root.rglob("*"):if file_path.is_file() and ".venv" not in str(file_path):
                size = file_path.stat().st_size
                total_size += size

                if size > 100000:  # > 100KB
                    large_files.append((file_path, size))
print(f"📊 Общий размер проекта: {total_size / 1024 / 1024:.1f} MB")

        if large_files:print(f"📄 Крупные файлы (>100KB):")
            for file_path, size in sorted(
                large_files, key = lambda x: x[1], reverse = True
            )[:10]:print(f"   {file_path}: {size / 1024:.1f} KB")
                if size > 1000000:  # > 1MB
                    self.log_issue("minor","performance",
                        f"Очень большой файл: {file_path} ({size / 1024 / 1024:.1f} MB)",

                    )

        # Проверяем асинхронный код
        python_files = [f for f in self.project_root.rglob("*.py") if ".venv" not in str(f)
        ]
        async_functions = 0
        sync_functions = 0

        for py_file in python_files:
            try:with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.AsyncFunctionDef):
                        async_functions += 1
                    elif isinstance(node, ast.FunctionDef):
                        sync_functions += 1

            except:
                pass

        if async_functions > 0:print(f"🔄 Асинхронных функций: {async_functions}")print(f"🔄 Синхронных функций: {sync_functions}")
        else:self.log_issue("minor", "performance", "Отсутствует асинхронный код")

    def generate_report(self):"""Генерирует финальный отчет"""print(f"\n" + "=" * 80)print("📋 ФИНАЛЬНЫЙ ОТЧЕТ ДЕТАЛЬНОГО АУДИТА")print("=" * 80)
        """Выполняет generate report."""

        # Сводка по уровням проблемcritical_count = len([i for i in self.issues if i["level"] == "critical"])major_count = len([i for i in self.warnings if i["level"] == "major"])minor_count = len([i for i in self.warnings if i["level"] == "minor"])
        suggestions_count = len(self.suggestions)

        total_issues = critical_count + major_count + minor_count
print(f"🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ: {critical_count}")print(f"⚠️ СЕРЬЕЗНЫЕ ПРОБЛЕМЫ: {major_count}")print(f"ℹ️ МЕЛКИЕ НЕДОЧЕТЫ: {minor_count}")print(f"💡 ПРЕДЛОЖЕНИЯ: {suggestions_count}")print(f"📊 ВСЕГО ПРОБЛЕМ: {total_issues}")

        # Детальный список проблем
        if critical_count > 0:print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")for issue in [i for i in self.issues if i["level"] == "critical"]:print(f"   ❌ [{issue['category']}] {issue['message']}")if issue["file"]:print(f"      📁 {issue['file']}")

        if major_count > 0:print(f"\n⚠️ СЕРЬЕЗНЫЕ ПРОБЛЕМЫ:")for issue in [i for i in self.warnings if i["level"] == "major"]:print(f"   🟡 [{issue['category']}] {issue['message']}")if issue["file"]:print(f"      📁 {issue['file']}")

        if minor_count > 0:print(f"\n ℹ️ МЕЛКИЕ НЕДОЧЕТЫ (первые 20):")minor_issues = [i for i in self.warnings if i["level"] == "minor"]
            for issue in minor_issues[:20]:print(f"   🔹 [{issue['category']}] {issue['message']}")if issue["file"]:print(f"      📁 {issue['file']}")

            if len(minor_issues) > 20:print(f"   ... и еще {len(minor_issues) - 20} мелких недочетов")

        # Общая оценка
        if total_issues == 0:grade = "A+"verdict = "ИДЕАЛЬНО"color = "🟢"
        elif critical_count == 0 and major_count == 0 and minor_count <= 5:grade = "A"verdict = "ОТЛИЧНО"color = "🟢"
        elif critical_count == 0 and major_count <= 2 and minor_count <= 15:grade = "B+"verdict = "ОЧЕНЬ ХОРОШО"color = "🟡"
        elif critical_count == 0 and major_count <= 5:grade = "B"verdict = "ХОРОШО"color = "🟡"
        elif critical_count <= 2:grade = "C"verdict = "УДОВЛЕТВОРИТЕЛЬНО"color = "🟠"
        else:grade = "D"verdict = "ТРЕБУЕТ СЕРЬЕЗНОЙ ДОРАБОТКИ"color = "🔴"
print(f"\n{color} ИТОГОВАЯ ОЦЕНКА ДЕТАЛЬНОГО АУДИТА: {grade} ({verdict})")

        # Рекомендации по улучшению
        categories = {}
        for issue in self.issues + self.warnings:cat = issue["category"]
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1

        if categories:print(f"\n🎯 ПРИОРИТЕТНЫЕ ОБЛАСТИ ДЛЯ УЛУЧШЕНИЯ:")
            for category, count in sorted(
                categories.items(), key = lambda x: x[1], reverse = True
            )[:5]:print(f"   🔧 {category}: {count} проблем")

        # Сохраняем детальный отчет
        report_data = {"timestamp": datetime.now().isoformat(),
            "summary": {"critical": critical_count,"major": major_count,
            "minor": minor_count,"suggestions": suggestions_count,"total": total_issues,
            "grade": grade,"verdict": verdict,
            },"issues": self.issues,"warnings": self.warnings,
                "suggestions": self.suggestions,"stats": self.stats,
        }
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")report_file = f"detailed_audit_report_{timestamp}.json"
with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii = False, indent = 2)
print(f"\n💾 ДЕТАЛЬНЫЙ ОТЧЕТ СОХРАНЕН: {report_file}")

        return report_data


def main():"""Запускает полный детальный аудит"""print("🔍 ЗАПУСК ПОЛНОГО ДЕТАЛЬНОГО АУДИТА ПРОЕКТА")print("=" * 80)
    """Выполняет main."""

    auditor = DetailedProjectAuditor()

    # Проводим все виды аудита
    auditor.audit_project_structure()
    auditor.audit_code_quality()
    auditor.audit_security_detailed()
    auditor.audit_dependencies()
    auditor.audit_testing_detailed()
    auditor.audit_documentation()
    auditor.audit_database()
    auditor.audit_performance()

    # Генерируем отчет
    report = auditor.generate_report()

    return report

if __name__ == "__main__":
    try:
        report = main()print(f"\n✅ ДЕТАЛЬНЫЙ АУДИТ ЗАВЕРШЕН")

    except Exception as e:print(f"\n💥 ОШИБКА АУДИТА: {e}")

        traceback.print_exc()
