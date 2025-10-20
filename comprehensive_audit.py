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
🔍 ЧЕСТНЫЙ И ПОЛНЫЙ АУДИТ ПРОЕКТА
Объективная оценка всех аспектов системы"""
sys.path.append(".")

def comprehensive_project_audit():"""Проводит честный и полный аудит всего проекта"""
    """Выполняет comprehensive project audit."""
print("🔍 ЧЕСТНЫЙ И ПОЛНЫЙ АУДИТ ПРОЕКТА")print("=" * 80)print(f"📅 Дата аудита: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")print(f"🎯 Цель: Объективная оценка всех аспектов системы")print("=" * 80)

    audit_results = {"timestamp": datetime.now().isoformat(),"sections": {},"issues": [],
    "recommendations": [],"overall_score": 0,
    }

    # 1. АРХИТЕКТУРА И СТРУКТУРАprint("\n1️⃣ АУДИТ АРХИТЕКТУРЫ И СТРУКТУРЫ")print("-" * 60)

    architecture_score = 0
    architecture_issues = []

    # Проверяем структуру проектаproject_root = Path(".")
    expected_dirs = ["mailing","persistence","resend","templating","data_loader",
    "validation","stats","gui","tests","samples",
    ]

    existing_dirs = [
    d.name
        for d in project_root.iterdir()if d.is_dir() and not d.name.startswith(".")
    ]
    missing_dirs = [d for d in expected_dirs if d not in existing_dirs]
print(f"📁 СТРУКТУРА ДИРЕКТОРИЙ:")print(f"   ✅ Существующие: {len(existing_dirs)} из {len(expected_dirs)}")
    for d in existing_dirs:print(f"      📂 {d}")

    if missing_dirs:print(f"   ❌ Отсутствующие: {missing_dirs}")architecture_issues.append(f"Отсутствуют директории: {missing_dirs}")
    else:
    architecture_score += 25

    # Проверяем ключевые файлы
    key_files = ["requirements.txt","pyproject.toml","README.md","mailing/cli.py",
    "mailing/sender.py","persistence/db.py","resend/client.py",
    "templating/engine.py",
    ]
print(f"\n📄 КЛЮЧЕВЫЕ ФАЙЛЫ:")
    missing_files = []
    for file_path in key_files:
        if Path(file_path).exists():
        size = Path(file_path).stat().st_sizeprint(f"   ✅ {file_path}: {size} байт")
    else:print(f"   ❌ {file_path}: ОТСУТСТВУЕТ")
        missing_files.append(file_path)

    if not missing_files:
    architecture_score += 25
    else:architecture_issues.append(f"Отсутствуют файлы: {missing_files}")

    # Проверяем зависимостиif Path("requirements.txt").exists():with open("requirements.txt") as f:
            deps = [line.strip() for line in f if line.strip() and not line.startswith("#")
        ]print(f"\n📦 ЗАВИСИМОСТИ: {len(deps)} пакетов")
    architecture_score += 25
    else:architecture_issues.append("Отсутствует requirements.txt")

    # Проверяем модульностьpython_files = list(Path(".").rglob("*.py"))print(f"\n🐍 PYTHON ФАЙЛЫ: {len(python_files)} файлов")

    large_files = []
    for py_file in python_files:
        if py_file.stat().st_size > 10000:  # > 10KB
        large_files.append((py_file, py_file.stat().st_size))

    if large_files:print(f"   ⚠️ Крупные файлы (>10KB):")
        for file_path,size in sorted(large_files,key = lambda x: x[1], reverse = True)[
        :5
    ]:print(f"      📄 {file_path}: {size} байт")

    architecture_score += 25  # Базовый балл за наличие Python файлов
print(f"\n📊 ОЦЕНКА АРХИТЕКТУРЫ: {architecture_score}/100")

    # 2. КАЧЕСТВО КОДАprint(f"\n2️⃣ АУДИТ КАЧЕСТВА КОДА")print("-" * 60)

    code_quality_score = 0
    code_issues = []

    # Анализ импортов и структуры
    import_issues = 0
    syntax_issues = 0

    for py_file in python_files:if "test_" in py_file.name or py_file.name.startswith("."):
        continue

        try:with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Проверяем синтаксис
            try:
            ast.parse(content)
            except SyntaxError:
            syntax_issues += 1code_issues.append(f"Синтаксическая ошибка в {py_file}")

            # Проверяем импортыif "from __future__ import annotations" not in content:
            import_issues += 1

        except Exception as e:code_issues.append(f"Ошибка чтения {py_file}: {e}")
print(f"🔍 АНАЛИЗ КОДА:")print(f"   📄 Проанализировано файлов: {len(python_files)}")print(f"   ❌ Синтаксических ошибок: {syntax_issues}")print(f"   ⚠️ Проблем с импортами: {import_issues}")

    if syntax_issues == 0:
    code_quality_score += 40
    else:code_issues.append(f"Найдены синтаксические ошибки: {syntax_issues}")

    if import_issues < len(python_files) * 0.1:  # < 10% файлов
    code_quality_score += 30

    # Проверяем документацию
    documented_files = 0
    for py_file in python_files[:10]:  # Проверяем первые 10 файлов
        try:with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
            if '"""' in content or "'''" in content:
            documented_files += 1
        except:
        pass

    doc_score = (documented_files / min(10, len(python_files))) * 30
    code_quality_score += doc_score
print(f"   📚 Документированных файлов: {documented_files}/10")print(f"\n📊 ОЦЕНКА КАЧЕСТВА КОДА: {code_quality_score:.0f}/100")

    # 3. ТЕСТИРОВАНИЕprint(f"\n3️⃣ АУДИТ ТЕСТИРОВАНИЯ")print("-" * 60)

    testing_score = 0
    testing_issues = []

    # Ищем тестовые файлыtest_files = list(Path("tests").glob("test_*.py")) if Path("tests").exists() else []
print(f"🧪 ТЕСТОВЫЕ ФАЙЛЫ: {len(test_files)}")
    for test_file in test_files:
    size = test_file.stat().st_sizeprint(f"   📋 {test_file.name}: {size} байт")

    if len(test_files) >= 10:
    testing_score += 40
    elif len(test_files) >= 5:
    testing_score += 25
    elif len(test_files) > 0:
    testing_score += 15
    else:testing_issues.append("Отсутствуют тестовые файлы")

    # Проверяем pytest
    try:
    result = subprocess.run(["python", "-m", "pytest", "--version"],
        capture_output = True,
        text = True,cwd=".",
    )
        if result.returncode == 0:print(f"   ✅ pytest установлен")
        testing_score += 20
    else:testing_issues.append("pytest не установлен")
    except:testing_issues.append("Не удалось проверить pytest")

    # Пробуем запустить тесты
    if test_files:
        try:
        result = subprocess.run(["python", "-m", "pytest", "--tb = no", "-q"],
            capture_output = True,
            text = True,cwd=".",
            timeout = 30,
        )
            if result.returncode == 0:print(f"   ✅ Тесты проходят успешно")
            testing_score += 40
        else:print(f"   ⚠️ Некоторые тесты не проходят")
            testing_score += 20testing_issues.append("Есть падающие тесты")
        except subprocess.TimeoutExpired:testing_issues.append("Тесты выполняются слишком долго")
        except Exception as e:testing_issues.append(f"Ошибка запуска тестов: {e}")
print(f"\n📊 ОЦЕНКА ТЕСТИРОВАНИЯ: {testing_score}/100")

    # 4. БАЗА ДАННЫХ И ДАННЫЕprint(f"\n4️⃣ АУДИТ БАЗЫ ДАННЫХ И ДАННЫХ")print("-" * 60)

    database_score = 0
    database_issues = []

    # Проверяем базу данныхdb_files = list(Path(".").glob("*.sqlite*")) + list(Path(".").glob("*.db"))

    if db_files:print(f"💾 ФАЙЛЫ БД: {len(db_files)}")

        for db_file in db_files:
        size = db_file.stat().st_sizeprint(f"   📊 {db_file}: {size} байт")

            try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Получаем список таблицcursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
print(f"      📋 Таблиц: {len(tables)}")

            total_records = 0
                for (table_name,) in tables:cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                total_records += count
                    if count > 0:print(f"         {table_name}: {count} записей")
print(f"      📊 Всего записей: {total_records}")

                if len(tables) >= 3:
                database_score += 30
                if total_records > 0:
                database_score += 40

            conn.close()

            except Exception as e:database_issues.append(f"Ошибка чтения БД {db_file}: {e}")

    database_score += 30  # За наличие БД файлов
    else:database_issues.append("Отсутствуют файлы базы данных")

    # Проверяем тестовые данныеsample_files = list(Path("samples").glob("*")) if Path("samples").exists() else []
    if sample_files:print(f"\n📂 ТЕСТОВЫЕ ДАННЫЕ: {len(sample_files)} файлов")
        for sample in sample_files:
        size = sample.stat().st_sizeprint(f"   📄 {sample.name}: {size} байт")
print(f"\n📊 ОЦЕНКА БД И ДАННЫХ: {database_score}/100")

    # 5. КОНФИГУРАЦИЯ И БЕЗОПАСНОСТЬprint(f"\n5️⃣ АУДИТ КОНФИГУРАЦИИ И БЕЗОПАСНОСТИ")print("-" * 60)

    security_score = 0
    security_issues = []

    # Проверяем переменные окруженияenv_vars = ["RESEND_API_KEY", "RESEND_FROM_EMAIL"]
    configured_vars = []

    for var in env_vars:
        if os.environ.get(var):
        configured_vars.append(var)print(f"   ✅ {var}: настроен")
    else:print(f"   ❌ {var}: не настроен")security_issues.append(f"Переменная окружения {var} не настроена")

    if len(configured_vars) == len(env_vars):
    security_score += 40
    elif len(configured_vars) > 0:
    security_score += 20

    # Проверяем на хардкод секретов
    hardcoded_secrets = 0secret_patterns = ["api_key", "password", "secret", "token"]

    for py_file in python_files[:20]:  # Проверяем первые 20 файлов
        try:with open(py_file, "r", encoding="utf-8") as f:
            content = f.read().lower()

            for pattern in secret_patterns:if f"{pattern}=" in content or f'{pattern}"' in content:
                hardcoded_secrets += 1
                break
        except:
        pass

    if hardcoded_secrets == 0:
    security_score += 30
    print(f"   ✅ Хардкод секретов не найден")
    else:
    security_score += 10
    security_issues.append(f"Возможный хардкод секретов в {hardcoded_secrets} файлах"
    )

    # Проверяем .gitignoreif Path(".gitignore").exists():with open(".gitignore") as f:
        gitignore_content = f.read()
important_patterns = [".env", "*.sqlite", "*.db", "__pycache__", ".venv"]
    ignored_patterns = sum(
            1 for pattern in important_patterns if pattern in gitignore_content
    )

    security_score += (ignored_patterns / len(important_patterns)) * 30
    print(f"   📝 .gitignore покрывает {ignored_patterns}/{len(important_patterns)} важных паттернов"
    )
    else:security_issues.append("Отсутствует .gitignore")
print(f"\n📊 ОЦЕНКА БЕЗОПАСНОСТИ: {security_score:.0f}/100")

    # 6. ПРОИЗВОДИТЕЛЬНОСТЬ И МОНИТОРИНГprint(f"\n6️⃣ АУДИТ ПРОИЗВОДИТЕЛЬНОСТИ И МОНИТОРИНГА")print("-" * 60)

    performance_score = 0
    performance_issues = []

    # Проверяем асинхронность
    async_files = 0
    for py_file in python_files[:10]:
        try:with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()if "async def" in content or "await " in content:
            async_files += 1
        except:
        pass

    if async_files > 0:
    performance_score += 40print(f"   ✅ Асинхронность: найдена в {async_files} файлах")
    else:performance_issues.append("Асинхронность не обнаружена")

    # Проверяем логирование
    logging_files = 0
    for py_file in python_files[:10]:
        try:with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()if "logging" in content or "logger" in content:
            logging_files += 1
        except:
        pass

    if logging_files > 0:
    performance_score += 30print(f"   ✅ Логирование: найдено в {logging_files} файлах")
    else:performance_issues.append("Логирование не настроено")

    # Проверяем мониторингmonitoring_keywords = ["stats", "metrics", "monitor", "webhook"]
    monitoring_found = any(
        Path(d).exists() for d in monitoring_keywords if Path(d).is_dir()
    )

    if monitoring_found:
    performance_score += 30print(f"   ✅ Мониторинг: компоненты найдены")
    else:performance_issues.append("Мониторинг не обнаружен")
print(f"\n📊 ОЦЕНКА ПРОИЗВОДИТЕЛЬНОСТИ: {performance_score}/100")

    # 7. ДОКУМЕНТАЦИЯ И ПОЛЬЗОВАТЕЛЬСКИЙ ОПЫТprint(f"\n7️⃣ АУДИТ ДОКУМЕНТАЦИИ")print("-" * 60)

    documentation_score = 0
    documentation_issues = []

    # Основные документы
    docs = {"README.md": 40,"CHANGELOG.md": 15,"INSTALL.md": 15,"LICENSE": 10,
    "requirements.txt": 20,
    }

    for doc, points in docs.items():
        if Path(doc).exists():
        size = Path(doc).stat().st_size
        documentation_score += pointsprint(f"   ✅ {doc}: {size} байт")
    else:documentation_issues.append(f"Отсутствует {doc}")
print(f"\n📊 ОЦЕНКА ДОКУМЕНТАЦИИ: {documentation_score}/100")

    # 8. ИТОГОВАЯ ОЦЕНКАprint(f"\n8️⃣ ИТОГОВАЯ ОЦЕНКА ПРОЕКТА")print("=" * 80)

    # Рассчитываем общий балл
    scores = {"Архитектура": architecture_score,"Качество кода": code_quality_score,
    "Тестирование": testing_score,"База данных": database_score,
    "Безопасность": security_score,"Производительность": performance_score,
    "Документация": documentation_score,
    }

    overall_score = sum(scores.values()) / len(scores)
print(f"📊 ДЕТАЛИЗАЦИЯ ПО РАЗДЕЛАМ:")
    for section, score in scores.items():
        if score >= 80:icon = "🟢"
        elif score >= 60:icon = "🟡"
        elif score >= 40:icon = "🟠"
    else:icon = "🔴"
print(f"   {icon} {section}: {score:.0f}/100")
print(f"\n🎯 ОБЩАЯ ОЦЕНКА: {overall_score:.1f}/100")

    # Градация оценок
    if overall_score >= 90:grade = "A+"verdict = "ПРЕВОСХОДНО"color = "🟢"
    elif overall_score >= 80:grade = "A"verdict = "ОТЛИЧНО"color = "🟢"
    elif overall_score >= 70:grade = "B+"verdict = "ХОРОШО"color = "🟡"
    elif overall_score >= 60:grade = "B"verdict = "УДОВЛЕТВОРИТЕЛЬНО"color = "🟡"
    elif overall_score >= 50:grade = "C"verdict = "ПОСРЕДСТВЕННО"color = "🟠"
    else:grade = "D"verdict = "НЕУДОВЛЕТВОРИТЕЛЬНО"color = "🔴"
print(f"\n{color} ИТОГОВАЯ ОЦЕНКА: {grade} ({verdict})")

    # Собираем все проблемы
    all_issues = (
    architecture_issues
    + code_issues
    + testing_issues
    + database_issues
    + security_issues
    + performance_issues
    + documentation_issues
    )

    if all_issues:print(f"\n⚠️ ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ ({len(all_issues)}):")
        for i, issue in enumerate(all_issues, 1):print(f"   {i}. {issue}")

    # Рекомендации
    recommendations = []

    if architecture_score < 80:recommendations.append("Улучшить структуру проекта и организацию файлов")

    if code_quality_score < 70:recommendations.append("Повысить качество кода и добавить документацию")

    if testing_score < 60:recommendations.append("Расширить покрытие тестами")

    if database_score < 70:recommendations.append("Улучшить работу с базой данных")

    if security_score < 80:recommendations.append("Усилить меры безопасности")

    if performance_score < 70:recommendations.append("Оптимизировать производительность и мониторинг")

    if documentation_score < 70:recommendations.append("Улучшить документацию проекта")

    if recommendations:print(f"\n💡 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
        for i, rec in enumerate(recommendations, 1):print(f"   {i}. {rec}")

    # Сохраняем результаты
    audit_results.update(
    {"overall_score": overall_score,"grade": grade,"verdict": verdict,
        "sections": scores,"issues": all_issues,"recommendations": recommendations,
    }
    )
print("=" * 80)

    return audit_results

if __name__ == "__main__":
    try:
    results = comprehensive_project_audit()

    # Сохраняем отчётtimestamp = datetime.now().strftime("%Y%m%d_%H%M%S")audit_file = f"project_audit_{timestamp}.json"
with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii = False, indent = 2)
print(f"\n💾 АУДИТ СОХРАНЁН: {audit_file}")

    except Exception as e:print(f"\n💥 ОШИБКА АУДИТА: {e}")

    traceback.print_exc()
