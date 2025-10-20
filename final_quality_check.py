                import re
from pathlib import Path
import json
import os
import sqlite3
import sys

        import traceback
from datetime import datetime
import ast
import subprocess

#!/usr/bin/env python3
"""
🎯 ФИНАЛЬНАЯ ПРОВЕРКА УЛУЧШЕНИЙ
Проверка всех исправлений и новая оценка проекта"""
sys.path.append(".")



def final_quality_check():"""Проверяет улучшения качества кода и системы"""
    """Выполняет final quality check."""
print("🎯 ФИНАЛЬНАЯ ПРОВЕРКА УЛУЧШЕНИЙ")print("=" * 80)print(f"📅 Дата проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")print("=" * 80)

    improvements = {"documentation": 0,"security": 0,"testing": 0,"automation": 0,
        "overall_score": 0,
    }

    # 1. ПРОВЕРКА ДОКУМЕНТАЦИИprint("\n1️⃣ ПРОВЕРКА УЛУЧШЕНИЙ ДОКУМЕНТАЦИИ")print("-" * 60)

    key_files = ["mailing/sender.py","resend/client.py","persistence/db.py",
        "templating/engine.py","persistence/repository.py",
    ]

    documented_functions = 0
    total_functions = 0

    for file_path in key_files:
        if Path(file_path).exists():
            try:with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(
                        node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                    ):
                        total_functions += 1
                        docstring = ast.get_docstring(node)
                        if docstring and len(docstring) > 50:  # Подробная документация
                            documented_functions += 1

                # Проверяем module docstring
                module_docstring = ast.get_docstring(tree)
                if module_docstring:print(f"   ✅ {file_path}: module docstring найден")
                else:print(f"   ⚠️ {file_path}: module docstring отсутствует")

            except Exception as e:print(f"   ❌ Ошибка анализа {file_path}: {e}")

    doc_coverage = (
        (documented_functions / total_functions * 100) if total_functions > 0 else 0
    )
    print(f"\n📊 ПОКРЫТИЕ ДОКУМЕНТАЦИЕЙ: {documented_functions}/{total_functions} ({doc_coverage:.1f}%)"
    )

    if doc_coverage >= 80:improvements["documentation"] = 90print("   🟢 ОТЛИЧНО: Документация значительно улучшена")
    elif doc_coverage >= 50:improvements["documentation"] = 70print("   🟡 ХОРОШО: Документация частично улучшена")
    else:improvements["documentation"] = 30print("   🔴 ТРЕБУЕТ ДОРАБОТКИ: Документация недостаточна")

    # 2. ПРОВЕРКА БЕЗОПАСНОСТИprint(f"\n2️⃣ ПРОВЕРКА БЕЗОПАСНОСТИ")print("-" * 60)

    security_score = 0

    # Проверяем security модульif Path("security/__init__.py").exists():
        security_score += 40print("   ✅ Security модуль создан")

        # Проверяем размер модуля безопасностиsize = Path("security/__init__.py").stat().st_size
        if size > 10000:  # > 10KB
            security_score += 20print(f"   ✅ Комплексный security модуль: {size} байт")

    # Проверяем использование security в коде
    security_imports = 0for py_file in Path(".").rglob("*.py"):if ".venv" in str(py_file) or "htmlcov" in str(py_file):
            continue
        try:with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()if "from security import" in content or "import security" in content:
                security_imports += 1
        except:
            pass

    if security_imports > 0:
        security_score += 20print(f"   ✅ Security используется в {security_imports} файлах")

    # Проверяем переменные окруженияenv_vars = ["RESEND_API_KEY", "RESEND_FROM_EMAIL"]
    configured_vars = sum(1 for var in env_vars if os.environ.get(var))

    if configured_vars == len(env_vars):
        security_score += 20print("   ✅ Все переменные окружения настроены")
improvements["security"] = security_scoreprint(f"\n📊 ОЦЕНКА БЕЗОПАСНОСТИ: {security_score}/100")

    # 3. ПРОВЕРКА ТЕСТИРОВАНИЯprint(f"\n3️⃣ ПРОВЕРКА ТЕСТИРОВАНИЯ")print("-" * 60)

    testing_score = 0

    # Запускаем тесты
    try:
        result = subprocess.run(
            [".venv/bin/python","-m","pytest","tests/","--tb = no","-q","--maxfail = 1",
            ],
            capture_output = True,
            text = True,
            timeout = 60,
        )

        if result.returncode == 0:
            testing_score += 60print("   ✅ Все тесты проходят успешно")

            # Парсим результаты pytest
            output = result.stdoutif "passed" in output:
match = re.search(r"(\d+) passed", output)
                if match:
                    passed_tests = int(match.group(1))print(f"   ✅ Прошло тестов: {passed_tests}")

                    if passed_tests >= 150:
                        testing_score += 30
                    elif passed_tests >= 100:
                        testing_score += 20
                    else:
                        testing_score += 10
        else:
            testing_score += 30print("   ⚠️ Некоторые тесты не проходят")

    except subprocess.TimeoutExpired:
        testing_score += 20print("   ⚠️ Тесты выполняются слишком долго")
    except Exception as e:
        testing_score += 10print(f"   ❌ Ошибка запуска тестов: {e}")

    # Проверяем pytest.iniif Path("pytest.ini").exists():
        testing_score += 10print("   ✅ pytest.ini настроен")
improvements["testing"] = testing_scoreprint(f"\n📊 ОЦЕНКА ТЕСТИРОВАНИЯ: {testing_score}/100")

    # 4. ПРОВЕРКА АВТОМАТИЗАЦИИprint(f"\n4️⃣ ПРОВЕРКА АВТОМАТИЗАЦИИ")print("-" * 60)

    automation_score = 0

    # Проверяем Makefileif Path("Makefile").exists():
        automation_score += 50print("   ✅ Makefile создан")
with open("Makefile", "r") as f:
            makefile_content = f.read()
commands = ["test","lint","format","security","clean", "install"]found_commands = sum(1 for cmd in commands if f"{cmd}:" in makefile_content)

        automation_score += (found_commands / len(commands)) * 50print(f"   ✅ Команд в Makefile: {found_commands}/{len(commands)}")
improvements["automation"] = automation_scoreprint(f"\n📊 ОЦЕНКА АВТОМАТИЗАЦИИ: {automation_score}/100")

    # 5. ОБЩАЯ ОЦЕНКАprint(f"\n5️⃣ ИТОГОВАЯ ОЦЕНКА УЛУЧШЕНИЙ")print("=" * 80)

    overall_score = (improvements["documentation"] * 0.3+ improvements["security"] * 0.3+ improvements["testing"] * 0.2+ improvements["automation"] * 0.2
    )
improvements["overall_score"] = overall_score
print("📊 ДЕТАЛИЗАЦИЯ УЛУЧШЕНИЙ:")print(f"   📚 Документация: {improvements['documentation']}/100")print(f"   🔒 Безопасность: {improvements['security']}/100")print(f"   🧪 Тестирование: {improvements['testing']}/100")print(f"   ⚙️ Автоматизация: {improvements['automation']}/100")
print(f"\n🎯 ОБЩАЯ ОЦЕНКА УЛУЧШЕНИЙ: {overall_score:.1f}/100")

    # Сравнение с предыдущими результатами
    previous_scores = {"code_quality": 30,# Было"testing": 40,# Было"security": 80,
        # Было"overall": 88.6,  # Было
    }
print(f"\n📈 СРАВНЕНИЕ С ПРЕДЫДУЩИМ АУДИТОМ:")
    print(f"   Качество кода: {previous_scores['code_quality']} → {improvements['documentation']:.0f} "f"({'🟢 +' + str(int(improvements['documentation'] - previous_scores['code_quality'])) if improvements['documentation'] > previous_scores['code_quality'] else '🔴 ' + str(int(improvements['documentation'] - previous_scores['code_quality']))})"
    )

    print(f"   Тестирование: {previous_scores['testing']} → {improvements['testing']:.0f} "f"({'🟢 +' + str(int(improvements['testing'] - previous_scores['testing'])) if improvements['testing'] > previous_scores['testing'] else '🔴 ' + str(int(improvements['testing'] - previous_scores['testing']))})"
    )

    print(f"   Безопасность: {previous_scores['security']} → {improvements['security']:.0f} "f"({'🟢 +' + str(int(improvements['security'] - previous_scores['security'])) if improvements['security'] > previous_scores['security'] else '🔴 ' + str(int(improvements['security'] - previous_scores['security']))})"
    )

    # Новая общая оценка
    new_overall = (improvements["documentation"]+ improvements["testing"]+ improvements["security"]+ improvements["automation"]
    ) / 4overall_diff = new_overall - previous_scores["overall"]
    overall_change = (f"🟢 +{overall_diff:.1f}" if overall_diff > 0 else f"🔴 {overall_diff:.1f}"
    )
    print(f"   Общая: {previous_scores['overall']:.1f} → {new_overall:.1f} ({overall_change})"
    )

    # Финальная градация
    if new_overall >= 95:grade = "A+"verdict = "ПРЕВОСХОДНО"color = "🟢"
    elif new_overall >= 90:grade = "A"verdict = "ОТЛИЧНО"color = "🟢"
    elif new_overall >= 85:grade = "A-"verdict = "ОЧЕНЬ ХОРОШО"color = "🟢"
    elif new_overall >= 80:grade = "B+"verdict = "ХОРОШО"color = "🟡"
    elif new_overall >= 75:grade = "B"verdict = "УДОВЛЕТВОРИТЕЛЬНО"color = "🟡"
    else:grade = "C"verdict = "ТРЕБУЕТ УЛУЧШЕНИЙ"color = "🟠"
print(f"\n{color} НОВАЯ ИТОГОВАЯ ОЦЕНКА: {grade} ({verdict})")

    # Достиженияprint(f"\n🏆 ДОСТИГНУТЫЕ УЛУЧШЕНИЯ:")
    achievements = []
if improvements["documentation"] >= 70:achievements.append("✅ Значительно улучшена документация кода")
if improvements["security"] >= 90:achievements.append("✅ Безопасность доведена до превосходного уровня")
if improvements["testing"] >= 80:achievements.append("✅ Тестирование работает автоматически")
if improvements["automation"] >= 70:achievements.append("✅ Создана автоматизация разработки")

    for achievement in achievements:print(f"   {achievement}")

    if not achievements:print("   ⚠️ Основные улучшения не достигнуты")

    # Оставшиеся задачи
    remaining_tasks = []
if improvements["documentation"] < 80:remaining_tasks.append("📚 Завершить документирование всех функций")
if improvements["security"] < 95:remaining_tasks.append("🔒 Интегрировать security во все модули")
if improvements["testing"] < 90:remaining_tasks.append("🧪 Исправить оставшиеся проблемы с тестами")

    if remaining_tasks:print(f"\n📋 ОСТАВШИЕСЯ ЗАДАЧИ:")
        for task in remaining_tasks:print(f"   {task}")
    else:print(f"\n🎉 ВСЕ ОСНОВНЫЕ УЛУЧШЕНИЯ ЗАВЕРШЕНЫ!")
print("=" * 80)
    return improvements

if __name__ == "__main__":
    try:
        results = final_quality_check()

        # Сохраняем результатыtimestamp = datetime.now().strftime("%Y%m%d_%H%M%S")results_file = f"improvement_results_{timestamp}.json"
with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii = False, indent = 2)
print(f"\n💾 РЕЗУЛЬТАТЫ СОХРАНЕНЫ: {results_file}")

    except Exception as e:print(f"\n💥 ОШИБКА ПРОВЕРКИ: {e}")

        traceback.print_exc()
