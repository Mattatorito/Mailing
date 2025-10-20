import asyncio
import os
import sys

    import traceback
from datetime import datetime

from mailing.models import Recipient
from mailing.sender import run_campaign, CampaignController
from persistence.db import get_connection

#!/usr/bin/env python3
"""
УПРОЩЁННЫЙ ТЕСТ РЕАЛЬНОЙ ОТПРАВКИ"""
sys.path.append(".")

# Устанавливаем реальные настройки через переменные окруженияos.environ["RESEND_API_KEY"] = "re_NY3yzMqH_JaMDnBSGZdi3qZ32rDmMdq7W"os.environ["RESEND_FROM_EMAIL"] = "admin@mailink.space"os.environ["RESEND_FROM_NAME"] = "Email Marketing System"

async def simple_real_email_test():"""Простой тест реальной отправки"""
    """Выполняет simple real email test."""
print("🚀 ТЕСТ РЕАЛЬНОЙ ОТПРАВКИ EMAIL")print("=" * 50)

    # 1. Создаём получателя
    test_recipient = Recipient(email="alexandr@mailink.space",name="Александр",
    variables={"email": "alexandr@mailink.space","name": "Александр",
        "subject": "Тест реальной отправки из системы","company": "Test Company",
        "current_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    },
    )
print(f"📧 Получатель: {test_recipient.email}")print(f"👤 Имя: {test_recipient.name}")

    # 2. Состояние БД до отправки
    with get_connection() as conn:
    cursor = conn.cursor()cursor.execute("SELECT COUNT(*) FROM deliveries")
    before_count = cursor.fetchone()[0]print(f"📊 Доставок в БД до: {before_count}")

    # 3. РЕАЛЬНАЯ ОТПРАВКАprint(f"\n🚀 ЗАПУСК РЕАЛЬНОЙ ОТПРАВКИ...")

    controller = CampaignController()
    success_count = 0
    error_details = None

    try:
        async for event in run_campaign(
        recipients=[test_recipient],template_name="template.html",
            subject="Тест реальной отправки из системы",
        dry_run = False,  # РЕАЛЬНАЯ ОТПРАВКА!
        concurrency = 1,
        controller = controller,
    ):print(f"📊 Событие: {event.get('type')}")
if event.get("type") == "progress":if event.get("success"):
                success_count += 1print(f"✅ УСПЕШНАЯ ОТПРАВКА!")print(f"🆔 Message ID: {event.get('message_id')}")print(f"🌐 Провайдер: {event.get('provider')}")
            else:error_details = event.get("error")print(f"❌ ОШИБКА: {error_details}")
elif event.get("type") == "finished":print(f"🏁 Завершено!")
            break

    except Exception as e:print(f"💥 ОШИБКА: {e}")
        return False

    # 4. Состояние БД после отправки
    with get_connection() as conn:
    cursor = conn.cursor()cursor.execute("SELECT COUNT(*) FROM deliveries")
    after_count = cursor.fetchone()[0]
print(f"\n📊 Доставок в БД после: {after_count}")print(f"📈 Новых записей: {after_count - before_count}")

        if after_count > before_count:
        cursor.execute("""
            SELECT email, success, provider, created_at, message_id, status_code
            FROM deliveries
            ORDER BY id DESC
            LIMIT 1"""
        )
        last = cursor.fetchone()

            if last:status = "✅ УСПЕХ" if last[1] else "❌ ОШИБКА"print(f"\n📮 ПОСЛЕДНЯЯ ДОСТАВКА: {status}")print(f"   📧 Email: {last[0]}")print(f"   🌐 Провайдер: {last[2]}")print(f"   🕒 Время: {last[3]}")print(f"   🆔 Message ID: {last[4]}")print(f"   📊 Status: {last[5]}")

    # 5. Итог
    if success_count > 0:print(f"\n🎉 РЕАЛЬНАЯ ОТПРАВКА УСПЕШНА!")print(f"📧 Email отправлен через Resend API")print(f"📊 Данные сохранены в базу")print(f"✅ Система работает с настоящими письмами!")
        return True
    else:print(f"\n❌ ОТПРАВКА НЕ УДАЛАСЬ")
        if error_details:print(f"🔍 Ошибка: {error_details}")
        return False

if __name__ == "__main__":
    try:
    result = asyncio.run(simple_real_email_test())
        if result:print(f"\n🏆 СИСТЕМА РАБОТАЕТ С РЕАЛЬНЫМИ EMAIL!")
    else:print(f"\n💥 ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ ОШИБОК")
    except Exception as e:print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")

    traceback.print_exc()
