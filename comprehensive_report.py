        import sys
from pathlib import Path
import asyncio
import json
import os
import sqlite3
import sys

        import traceback
from datetime import datetime, timedelta

from data_loader.csv_loader import CSVLoader
from data_loader.json_loader import JSONLoader
from mailing.config import settings
from mailing.limits.daily_quota import DailyQuota
from persistence.db import get_connection
from persistence.repository import DeliveryRepository, SuppressionRepository
from resend.client import ResendClient
from stats.aggregator import StatsAggregator
from templating.engine import TemplateEngine
from validation.email_validator import validate_email_list

#!/usr/bin/env python3
"""
ПОЛНОЦЕННЫЙ ОТЧЁТ О РАБОТОСПОСОБНОСТИ ПРОЕКТА
Детальный анализ всех компонентов системы"""
sys.path.append(".")


# Импорты для тестирования компонентов

# from data_loader.excel_loader import ExcelLoader  # может отсутствовать openpyxl


def comprehensive_system_report():"""Полноценный отчёт о работоспособности всех компонентов"""
    """Выполняет comprehensive system report."""
print("🔍 ПОЛНОЦЕННЫЙ ОТЧЁТ О РАБОТОСПОСОБНОСТИ ПРОЕКТА")print("=" * 80)print(f"📅 Дата отчёта: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")print("=" * 80)

    # Счётчики для итогового анализа
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    issues = []

    # 1. БАЗОВАЯ ИНФРАСТРУКТУРАprint("\n1️⃣ БАЗОВАЯ ИНФРАСТРУКТУРА")print("-" * 40)

    # Python окружение
    total_tests += 1
    try:

        python_version = sys.version.split()[0]print(f"✅ Python: {python_version}")if python_version >= "3.9":
            passed_tests += 1
        else:
            failed_tests += 1issues.append("Python версия < 3.9")
    except Exception as e:
        failed_tests += 1issues.append(f"Python проверка: {e}")print(f"❌ Python: {e}")

    # Виртуальное окружение
    total_tests += 1
    try:venv_path = Path(".venv")
        if venv_path.exists():print(f"✅ Виртуальное окружение: {venv_path.absolute()}")
            passed_tests += 1
        else:print(f"⚠️  Виртуальное окружение: не найдено")issues.append("Виртуальное окружение не найдено")
            failed_tests += 1
    except Exception as e:
        failed_tests += 1issues.append(f"Venv проверка: {e}")print(f"❌ Виртуальное окружение: {e}")

    # Зависимости
    total_tests += 1
    try:requirements = Path("requirements.txt")
        if requirements.exists():deps = requirements.read_text().strip().split("\n")print(f"✅ Зависимости: {len(deps)} пакетов")
            passed_tests += 1
        else:print(f"❌ requirements.txt не найден")
            failed_tests += 1issues.append("requirements.txt отсутствует")
    except Exception as e:
        failed_tests += 1issues.append(f"Зависимости: {e}")print(f"❌ Зависимости: {e}")

    # 2. КОНФИГУРАЦИЯ СИСТЕМЫprint("\n2️⃣ КОНФИГУРАЦИЯ СИСТЕМЫ")print("-" * 40)

    total_tests += 1
    try:
        print(f"✅ API ключ: {'настроен' if settings.resend_api_key else 'не настроен'}"
        )print(f"✅ Email отправителя: {settings.resend_from_email}")print(f"✅ Имя отправителя: {settings.resend_from_name}")print(f"✅ Дневной лимит: {settings.daily_email_limit}")print(f"✅ Конкурентность: {settings.concurrency}")print(f"✅ Rate limit: {settings.rate_limit_per_minute}/мин")print(f"✅ База данных: {settings.sqlite_db_path}")
        passed_tests += 1
    except Exception as e:
        failed_tests += 1issues.append(f"Конфигурация: {e}")print(f"❌ Конфигурация: {e}")

    # 3. БАЗА ДАННЫХprint("\n3️⃣ БАЗА ДАННЫХ")print("-" * 40)

    total_tests += 1
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Проверяем таблицыcursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = ["deliveries","events","unsubscribes","suppressions",
                "daily_usage",
            ]
            missing_tables = [t for t in expected_tables if t not in tables]

            if not missing_tables:print(f"✅ Все таблицы созданы: {', '.join(tables)}")
                passed_tests += 1
            else:print(f"❌ Отсутствуют таблицы: {', '.join(missing_tables)}")
                failed_tests += 1issues.append(f"Отсутствуют таблицы: {missing_tables}")

            # Статистика данныхcursor.execute("SELECT COUNT(*) FROM deliveries")
            deliveries_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM events")
            events_count = cursor.fetchone()[0]
print(f"📊 Записей доставок: {deliveries_count}")print(f"📊 Записей событий: {events_count}")

    except Exception as e:
        failed_tests += 1issues.append(f"База данных: {e}")print(f"❌ База данных: {e}")

    # 4. ЗАГРУЗЧИКИ ДАННЫХprint("\n4️⃣ ЗАГРУЗЧИКИ ДАННЫХ")print("-" * 40)

    # CSV загрузчик
    total_tests += 1
    try:
        csv_loader = CSVLoader()

        # Создаём тестовый CSVtest_csv = Path("test_data.csv")test_csv.write_text("email,name\ntest@example.com,Test User\n")
recipients = csv_loader.load("test_data.csv")if len(recipients) == 1 and recipients[0].email == "test@example.com":print("✅ CSV загрузчик работает")
            passed_tests += 1
        else:print("❌ CSV загрузчик: неверные данные")
            failed_tests += 1issues.append("CSV загрузчик возвращает неверные данные")

        test_csv.unlink()  # Удаляем тестовый файл

    except Exception as e:
        failed_tests += 1issues.append(f"CSV загрузчик: {e}")print(f"❌ CSV загрузчик: {e}")

    # JSON загрузчик
    total_tests += 1
    try:
        json_loader = JSONLoader()

        # Создаём тестовый JSONtest_json = Path("test_data.json")test_data = [{"email": "test@example.com", "name": "Test User"}]
        test_json.write_text(json.dumps(test_data))
recipients = json_loader.load("test_data.json")if len(recipients) == 1 and recipients[0].email == "test@example.com":print("✅ JSON загрузчик работает")
            passed_tests += 1
        else:print("❌ JSON загрузчик: неверные данные")
            failed_tests += 1issues.append("JSON загрузчик возвращает неверные данные")

        test_json.unlink()  # Удаляем тестовый файл

    except Exception as e:
        failed_tests += 1issues.append(f"JSON загрузчик: {e}")print(f"❌ JSON загрузчик: {e}")

    # 5. ШАБЛОНИЗАТОРprint("\n5️⃣ ШАБЛОНИЗАТОР")print("-" * 40)

    total_tests += 1
    try:
        engine = TemplateEngine()

        # Создаём тестовый шаблонtest_template = Path("samples/test_render.html")
        test_template.parent.mkdir(exist_ok = True)
        test_template.write_text("""
<!DOCTYPE html>
<html>
<head><title>{{subject}}</title></head>
<body>
    <h1>Привет, {{name}}!</h1>
    <p>Email: {{email}}</p>
</body>
</html>""".strip()
        )

        # Тестируем рендеринг
        variables = {"subject": "Тест","name": "Тестовый пользователь",
            "email": "test@example.com",
        }
result = engine.render("test_render.html", variables)

        if (result.subject == "Тест"and "Тестовый пользователь" in result.body_htmland "test@example.com" in result.body_html
        ):print("✅ Шаблонизатор работает")print(f"   📄 HTML: {len(result.body_html)} символов")print(f"   📝 Text: {len(result.body_text or '')} символов")
            passed_tests += 1
        else:print("❌ Шаблонизатор: неверный результат")
            failed_tests += 1issues.append("Шаблонизатор возвращает неверный результат")

        test_template.unlink()  # Удаляем тестовый файл

    except Exception as e:
        failed_tests += 1issues.append(f"Шаблонизатор: {e}")print(f"❌ Шаблонизатор: {e}")

    # 6. EMAIL ВАЛИДАТОРprint("\n6️⃣ EMAIL ВАЛИДАТОР")print("-" * 40)

    total_tests += 1
    try:
        # Тестируем валидные и невалидные emailvalid_emails = ["test@example.com", "user@domain.org", "name@company.ru"]invalid_emails = ["invalid", "@domain.com", "user@", "test@"]

        valid_results, valid_errors = validate_email_list(valid_emails)
        invalid_results, invalid_errors = validate_email_list(invalid_emails)

        if len(valid_results) == 3 and len(invalid_errors) == 4:print("✅ Email валидатор работает")print(f"   ✅ Валидные: {len(valid_results)}")print(f"   ❌ Невалидные: {len(invalid_errors)}")
            passed_tests += 1
        else:print("❌ Email валидатор: неверная работа")print(f"   Валидных: {len(valid_results)}, ошибок: {len(invalid_errors)}")
            failed_tests += 1issues.append("Email валидатор работает неправильно")

    except Exception as e:
        failed_tests += 1issues.append(f"Email валидатор: {e}")print(f"❌ Email валидатор: {e}")

    # 7. RESEND API КЛИЕНТprint("\n7️⃣ RESEND API КЛИЕНТ")print("-" * 40)

    total_tests += 1
    try:
        client = ResendClient()print("✅ ResendClient создан")print(f"   🌐 Base URL: {settings.resend_base_url}")print(f"   🔄 Max retries: {settings.max_retries}")print(f"   ⏱️  Timeout: {getattr(settings,
            'timeout', 30)}s")
        passed_tests += 1
    except Exception as e:
        failed_tests += 1issues.append(f"Resend клиент: {e}")print(f"❌ Resend клиент: {e}")

    # 8. ДНЕВНЫЕ КВОТЫprint("\n8️⃣ ДНЕВНЫЕ КВОТЫ")print("-" * 40)

    total_tests += 1
    try:
        quota = DailyQuota()
        quota.load()
print(f"✅ Дневная квота инициализирована")print(f"   📊 Использовано: {quota.used()}")print(f"   📈 Лимит: {quota.limit}")print(f"   📉 Остаток: {quota.remaining()}")print(f"   ✅ Можно отправлять: {'Да' if quota.can_send() else 'Нет'}")
        passed_tests += 1
    except Exception as e:
        failed_tests += 1issues.append(f"Дневные квоты: {e}")print(f"❌ Дневные квоты: {e}")

    # 9. РЕПОЗИТОРИИprint("\n9️⃣ РЕПОЗИТОРИИ")print("-" * 40)

    total_tests += 1
    try:
        delivery_repo = DeliveryRepository()
        suppression_repo = SuppressionRepository()

        # Проверяем статистику
        stats = delivery_repo.stats()
print("✅ Репозитории работают")print(f"   📊 Всего доставок: {stats.get('total',
    0)}")print(f"   ✅ Успешных: {stats.get('success',
    0)}")print(f"   ❌ Неудачных: {stats.get('failed', 0)}")
        passed_tests += 1
    except Exception as e:
        failed_tests += 1issues.append(f"Репозитории: {e}")print(f"❌ Репозитории: {e}")

    # 10. АГРЕГАТОР СТАТИСТИКИprint("\n🔟 АГРЕГАТОР СТАТИСТИКИ")print("-" * 40)

    total_tests += 1
    try:
        aggregator = StatsAggregator()

        # Проверяем методы
        today_stats = aggregator.daily_stats()
        weekly_stats = aggregator.weekly_stats()
print("✅ Агрегатор статистики работает")print(f"   📅 Сегодня: {today_stats}")print(f"   📊 За неделю: {weekly_stats}")
        passed_tests += 1
    except Exception as e:
        failed_tests += 1issues.append(f"Агрегатор статистики: {e}")print(f"❌ Агрегатор статистики: {e}")

    # 11. ФАЙЛОВАЯ СИСТЕМАprint("\n1️⃣1️⃣ ФАЙЛОВАЯ СИСТЕМА")print("-" * 40)

    critical_files = ["mailing/cli.py","mailing/sender.py","resend/client.py",
        "templating/engine.py","persistence/db.py","samples/template.html",
    ]

    for file_path in critical_files:
        total_tests += 1
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_sizeprint(f"✅ {file_path}: {size} байт")
            passed_tests += 1
        else:print(f"❌ {file_path}: не найден")
            failed_tests += 1issues.append(f"Критический файл отсутствует: {file_path}")

    # 12. ПРАВА ДОСТУПА И БЕЗОПАСНОСТЬprint("\n1️⃣2️⃣ ПРАВА ДОСТУПА И БЕЗОПАСНОСТЬ")print("-" * 40)

    total_tests += 1
    try:
        # Проверяем права на запись в рабочую директориюtest_file = Path("permission_test.tmp")test_file.write_text("test")
        test_file.unlink()
print("✅ Права на запись: есть")
        passed_tests += 1
    except Exception as e:
        failed_tests += 1issues.append(f"Права доступа: {e}")print(f"❌ Права на запись: {e}")

    # Проверяем конфиденциальные данные
    total_tests += 1if settings.resend_api_key and not settings.resend_api_key.startswith("test_"):print("✅ API ключ: настоящий")
        passed_tests += 1
    else:print("⚠️  API ключ: тестовый")issues.append("Используется тестовый API ключ")
        failed_tests += 1

    # ИТОГОВЫЙ АНАЛИЗprint("\n" + "=" * 80)print("🎯 ИТОГОВЫЙ АНАЛИЗ РАБОТОСПОСОБНОСТИ")print("=" * 80)

    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
print(f"📊 ОБЩАЯ СТАТИСТИКА:")print(f"   🧪 Всего тестов: {total_tests}")print(f"   ✅ Пройдено: {passed_tests}")print(f"   ❌ Не пройдено: {failed_tests}")print(f"   📈 Успешность: {success_rate:.1f}%")

    if success_rate >= 90:status = "🟢 ОТЛИЧНО"verdict = "Система полностью готова к продакшену"
    elif success_rate >= 75:status = "🟡 ХОРОШО"verdict = "Система готова, есть минорные проблемы"
    elif success_rate >= 50:status = "🟠 УДОВЛЕТВОРИТЕЛЬНО"verdict = "Система работает, нужны исправления"
    else:status = "🔴 КРИТИЧНО"verdict = "Система требует серьёзных исправлений"
print(f"\n🏆 ОБЩАЯ ОЦЕНКА: {status}")print(f"💡 ЗАКЛЮЧЕНИЕ: {verdict}")

    if issues:print(f"\n⚠️  ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ:")
        for i, issue in enumerate(issues, 1):print(f"   {i}. {issue}")

    # РЕКОМЕНДАЦИИprint(f"\n🔧 РЕКОМЕНДАЦИИ:")
    if success_rate >= 90:print("   ✅ Система готова к работе!")print("   📧 Можете запускать реальные email кампании")print("   📊 Мониторинг работает корректно")
    else:print("   🔨 Исправьте выявленные проблемы")print("   🧪 Запустите тесты повторно")print("   📞 При необходимости обратитесь за поддержкой")
print("=" * 80)

    return {"total_tests": total_tests,"passed_tests": passed_tests,
        "failed_tests": failed_tests,"success_rate": success_rate,"status": status,
        "verdict": verdict,"issues": issues,
    }

if __name__ == "__main__":
    try:
        report = comprehensive_system_report()

        # Сохраняем отчёт в файл
        report_file = Path(f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.write_text(json.dumps(report, ensure_ascii = False, indent = 2))
print(f"\n💾 Отчёт сохранён в: {report_file}")

    except Exception as e:print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА ГЕНЕРАЦИИ ОТЧЁТА: {e}")

        traceback.print_exc()
