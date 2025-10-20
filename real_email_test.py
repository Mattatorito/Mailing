from pathlib import Path
import asyncio
import json
import sys

    import traceback
from datetime import datetime

from data_loader.csv_loader import CSVLoader
from mailing.config import settings
from mailing.models import Recipient
from mailing.sender import run_campaign, CampaignController
from persistence.db import get_connection
from resend.client import ResendClient
from templating.engine import TemplateEngine

#!/usr/bin/env python3
"""
РЕАЛЬНАЯ ОТПРАВКА EMAIL - НЕ СИМУЛЯЦИЯ
Этот скрипт выполняет настоящую отправку через Resend API"""
sys.path.append(".")

# Импорты системы

async def test_real_email_sending():"""РЕАЛЬНАЯ отправка email - без dry-run режима"""
    """Тест для real email sending."""
print("🚀 РЕАЛЬНАЯ ОТПРАВКА EMAIL - БЕЗ СИМУЛЯЦИИ")print("=" * 70)print("⚠️  ВНИМАНИЕ: Это настоящая отправка через Resend API!")print("=" * 70)

    # 1. Проверка API ключаprint("1️⃣ ПРОВЕРКА API КОНФИГУРАЦИИ:")
if not settings.resend_api_key or settings.resend_api_key.startswith("test_"):print("❌ КРИТИЧЕСКАЯ ОШИБКА: Нужен настоящий API ключ!")print("💡 Установите реальный ключ Resend в переменную RESEND_API_KEY")print("🔗 Получить ключ: https://resend.com/api-keys")

    # Запрашиваем у пользователяprint("\n🔑 Введите ваш реальный API ключ Resend:")api_key = input("API ключ: ").strip()
if not api_key or api_key.startswith("test_"):print("❌ Некорректный API ключ. Отмена отправки.")
            return False

    # Обновляем настройки
    settings.resend_api_key = api_keyprint("✅ API ключ обновлён")
print(f"   🔑 API ключ: {settings.resend_api_key[:20]}...")

    # 2. Проверка домена отправителяprint(f"\n2️⃣ ПРОВЕРКА ДОМЕНА ОТПРАВИТЕЛЯ:")print(f"   📧 Отправитель: {settings.resend_from_email}")
if "example.com" in settings.resend_from_email:print("⚠️  ВНИМАНИЕ: Используется тестовый домен!")print("💡 Введите реальный email с верифицированного домена:")
real_email = input("Email отправителя: ").strip()if "@" not in real_email:print("❌ Некорректный email. Отмена отправки.")
            return False

    settings.resend_from_email = real_emailprint("✅ Email отправителя обновлён")

    # 3. Тест подключения к APIprint(f"\n3️⃣ ТЕСТ ПОДКЛЮЧЕНИЯ К RESEND API:")

    try:
    client = ResendClient()print("✅ ResendClient создан успешно")print(f"   🌐 Base URL: {settings.resend_base_url}")print(f"   🔄 Max retries: {settings.max_retries}")
    except Exception as e:print(f"❌ Ошибка создания клиента: {e}")
        return False

    # 4. Подготовка получателейprint(f"\n4️⃣ ПОДГОТОВКА ПОЛУЧАТЕЛЕЙ:")

    # Создаём тестового получателяprint("💡 Введите email для тестовой отправки:")test_email = input("Email получателя: ").strip()
if "@" not in test_email:print("❌ Некорректный email получателя")
        return False

    # Создаём объект получателя
    test_recipient = Recipient(
    email = test_email,name="Тестовый получатель",
    variables={"email": test_email,"name": "Тестовый получатель",
        "company": "Test Company",
        "current_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    },
    )
print(f"   ✅ Получатель: {test_recipient.email}")print(f"   👤 Имя: {test_recipient.name}")

    # 5. Проверка шаблонаprint(f"\n5️⃣ ПРОВЕРКА ШАБЛОНА:")
template_path = Path("samples/template.html")
    if not template_path.exists():print("❌ Основной шаблон не найден, создаём простой тестовый")
simple_template = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
    <title>Тестовое письмо</title>
</head>
<body>
    <h1>Привет, {{name}}!</h1>
    <p>Это реальное тестовое письмо от системы рассылки.</p>
    <p>Email: {{email}}</p>
    <p>Дата отправки: {{current_date}}</p>
    <hr>
    <p><small>Это автоматическое письмо для тестирования системы.</small></p>
</body></html>"""
template_path.write_text(simple_template, encoding="utf-8")print("✅ Создан простой тестовый шаблон")

    # Тестируем рендеринг
    engine = TemplateEngine()
    try:rendered = engine.render("template.html", test_recipient.variables)print(f"   ✅ Шаблон обработан успешно")print(f"   📄 Тема: {rendered.subject}")print(f"   📏 HTML: {len(rendered.body_html)} символов")print(f"   📝 Text: {len(rendered.body_text or '')} символов")
    except Exception as e:print(f"❌ Ошибка рендеринга: {e}")
        return False

    # 6. Состояние БД перед отправкойprint(f"\n6️⃣ СОСТОЯНИЕ БД ПЕРЕД ОТПРАВКОЙ:")

    with get_connection() as conn:
    cursor = conn.cursor()cursor.execute("SELECT COUNT(*) FROM deliveries")
    deliveries_before = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM deliveries WHERE success = 1")
    success_before = cursor.fetchone()[0]
print(f"   📊 Доставок до отправки: {deliveries_before}")print(f"   ✅ Успешных до отправки: {success_before}")

    # 7. ФИНАЛЬНОЕ ПОДТВЕРЖДЕНИЕprint(f"\n7️⃣ ФИНАЛЬНОЕ ПОДТВЕРЖДЕНИЕ:")print(f"   📤 Отправитель: {settings.resend_from_email}")print(f"   📧 Получатель: {test_recipient.email}")print(f"   🎯 Шаблон: template.html")print(f"   ⚠️  ЭТО РЕАЛЬНАЯ ОТПРАВКА!")
confirm = input("\n❓ Подтвердите отправку (введите 'ДА'): ").strip()if confirm.upper() not in ["ДА",
    "YES", "Y"]:print("❌ Отправка отменена пользователем")
        return False

    # 8. РЕАЛЬНАЯ ОТПРАВКАprint(f"\n8️⃣ ВЫПОЛНЯЕТСЯ РЕАЛЬНАЯ ОТПРАВКА:")print(f"   🚀 Запуск кампании...")

    controller = CampaignController()

    try:
    event_count = 0
    success_count = 0
    error_details = None

    # Запускаем РЕАЛЬНУЮ кампанию (dry_run=False!)
        async for event in run_campaign(
        recipients=[test_recipient],template_name="template.html",
            subject="Тестовое письмо - реальная отправка",
        dry_run = False,  # ЭТО РЕАЛЬНАЯ ОТПРАВКА!
        concurrency = 1,
        controller = controller,
    ):
        event_count += 1print(f"   📊 Событие {event_count}: {event.get('type')}")
if event.get("type") == "progress":if event.get("success"):
                success_count += 1print(f"   ✅ УСПЕШНАЯ ОТПРАВКА!")print(f"   🆔 Message ID: {event.get('message_id')}")print(f"   📧 Email: {event.get('email')}")print(f"   🌐 Провайдер: {event.get('provider', 'unknown')}")
            else:error_details = event.get("error", "unknown error")print(f"   ❌ ОШИБКА ОТПРАВКИ: {error_details}")
elif event.get("type") == "finished":print(f"   🏁 Кампания завершена!")
            break
print(f"\n   📈 ИТОГИ ОТПРАВКИ:")print(f"   📊 Всего событий: {event_count}")print(f"   ✅ Успешных: {success_count}")
    print(f"   ❌ Ошибок: {event_count - success_count - 1}"
    )  # -1 для события finished

        if error_details:print(f"   🔍 Детали ошибки: {error_details}")

    except Exception as e:print(f"❌ КРИТИЧЕСКАЯ ОШИБКА ПРИ ОТПРАВКЕ: {e}")
        return False

    # 9. Состояние БД после отправкиprint(f"\n9️⃣ СОСТОЯНИЕ БД ПОСЛЕ ОТПРАВКИ:")

    with get_connection() as conn:
    cursor = conn.cursor()cursor.execute("SELECT COUNT(*) FROM deliveries")
    deliveries_after = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM deliveries WHERE success = 1")
    success_after = cursor.fetchone()[0]
print(f"   📊 Доставок после отправки: {deliveries_after}")print(f"   ✅ Успешных после отправки: {success_after}")print(f"   📈 Новых записей: {deliveries_after - deliveries_before}")

        if deliveries_after > deliveries_before:
        # Показываем последнюю запись
        cursor.execute("""
            SELECT email, success, provider, created_at, message_id, status_code
            FROM deliveries
            ORDER BY id DESC
            LIMIT 1"""
        )
        last_delivery = cursor.fetchone()

            if last_delivery:status = "✅ УСПЕХ" if last_delivery[1] else "❌ ОШИБКА"print(f"\n   📮 ПОСЛЕДНЯЯ ДОСТАВКА: {status}")print(f"      📧 Email: {last_delivery[0]}")print(f"      🌐 Провайдер: {last_delivery[2]}")print(f"      🕒 Время: {last_delivery[3]}")print(f"      🆔 Message ID: {last_delivery[4]}")print(f"      📊 Status Code: {last_delivery[5]}")

    # 10. Итоговый статусprint(f"\n🎯 ИТОГОВЫЙ СТАТУС РЕАЛЬНОЙ ОТПРАВКИ:")

    if success_count > 0:print(f"   🎉 РЕАЛЬНАЯ ОТПРАВКА ВЫПОЛНЕНА УСПЕШНО!")print(f"   📧 Письмо отправлено на: {test_recipient.email}")print(f"   📊 Данные сохранены в базу")print(f"   ✅ Система работает с настоящими email!")

        return True
    else:print(f"   ❌ ОТПРАВКА НЕ УДАЛАСЬ")print(f"   🔍 Проверьте API ключ и домен отправителя")print(f"   📊 Ошибка записана в базу для анализа")

        return False

if __name__ == "__main__":print("🔥 ВНИМАНИЕ: РЕАЛЬНАЯ ОТПРАВКА EMAIL")print("Этот скрипт отправит настоящее письмо через Resend API!")print("=" * 60)

    try:
    success = asyncio.run(test_real_email_sending())

        if success:print(f"\n🏆 РЕАЛЬНАЯ ОТПРАВКА ЗАВЕРШЕНА УСПЕШНО!")print(f"📧 Email доставлен получателю")print(f"📊 Все данные в системе - реальные")
    else:print(f"\n💥 РЕАЛЬНАЯ ОТПРАВКА НЕ УДАЛАСЬ")print(f"🔧 Проверьте настройки и попробуйте снова")

    except KeyboardInterrupt:print(f"\n⏹️ Отправка прервана пользователем")
    except Exception as e:print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")

    traceback.print_exc()
