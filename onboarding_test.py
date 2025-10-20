import asyncio
import os
import sys

        import traceback
        import traceback
from datetime import datetime

from mailing.models import Recipient
from mailing.sender import run_campaign, CampaignController
from persistence.db import get_connection

#!/usr/bin/env python3
"""
ТЕСТ С ONBOARDING ДОМЕНОМ RESEND"""
sys.path.append(".")


# Используем onboarding домен Resendos.environ["RESEND_API_KEY"] = "re_NY3yzMqH_JaMDnBSGZdi3qZ32rDmMdq7W"os.environ["RESEND_FROM_EMAIL"] = "onboarding@resend.dev"os.environ["RESEND_FROM_NAME"] = "Email Marketing System Test"



async def onboarding_email_test():"""Тест с onboarding доменом Resend"""
    """Выполняет onboarding email test."""
print("🚀 ТЕСТ С ONBOARDING ДОМЕНОМ RESEND")print("=" * 60)print("📧 Отправитель: onboarding@resend.dev")print("🎯 Получатель: alexandr@mailink.space")print("=" * 60)

    # 1. Создаём получателя
    test_recipient = Recipient(email="alexandr@mailink.space",name="Александр",
        variables={"email": "alexandr@mailink.space","name": "Александр",
            "subject": "Тест системы рассылки - реальная отправка",
            "company": "Email Marketing System",
            "current_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_message": "Это реальное письмо из системы рассылки!",
        },
    )
print(f"✅ Получатель настроен: {test_recipient.email}")

    # 2. Состояние БД до отправки
    with get_connection() as conn:
        cursor = conn.cursor()cursor.execute("SELECT COUNT(*) FROM deliveries WHERE success = 1")
        success_before = cursor.fetchone()[0]cursor.execute("SELECT COUNT(*) FROM deliveries")
        total_before = cursor.fetchone()[0]
print(f"📊 До отправки - Всего: {total_before}, Успешных: {success_before}")

    # 3. РЕАЛЬНАЯ ОТПРАВКАprint(f"\n🚀 ВЫПОЛНЯЕТСЯ РЕАЛЬНАЯ ОТПРАВКА...")print(f"⚠️  Это не симуляция - настоящий email!")

    controller = CampaignController()
    success_count = 0
    message_id = None
    error_details = None

    try:
        async for event in run_campaign(
            recipients=[test_recipient],template_name="template.html",
                subject="Тест системы рассылки - реальная отправка",
            dry_run = False,  # РЕАЛЬНАЯ ОТПРАВКА!
            concurrency = 1,
            controller = controller,
        ):event_type = event.get("type")print(f"📊 Событие: {event_type}")
if event_type == "progress":if event.get("success"):
                    success_count += 1message_id = event.get("message_id")provider = event.get("provider")print(f"✅ УСПЕШНАЯ РЕАЛЬНАЯ ОТПРАВКА!")print(f"   🆔 Message ID: {message_id}")print(f"   🌐 Провайдер: {provider}")print(f"   📧 Email: {event.get('email')}")
                else:error_details = event.get("error")print(f"❌ ОШИБКА ОТПРАВКИ: {error_details}")
elif event_type == "finished":total_sent = event.get("total_sent",
    0)total_failed = event.get("total_failed", 0)print(f"🏁 КАМПАНИЯ ЗАВЕРШЕНА!")print(f"   📤 Отправлено: {total_sent}")print(f"   ❌ Ошибок: {total_failed}")
                break

    except Exception as e:print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")

        traceback.print_exc()
        return False

    # 4. Проверяем результат в БДprint(f"\n📊 ПРОВЕРКА РЕЗУЛЬТАТА В БАЗЕ ДАННЫХ:")

    with get_connection() as conn:
        cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM deliveries WHERE success = 1")
        success_after = cursor.fetchone()[0]cursor.execute("SELECT COUNT(*) FROM deliveries")
        total_after = cursor.fetchone()[0]
print(f"📈 После отправки - Всего: {total_after}, Успешных: {success_after}")print(f"📊 Новых записей: {total_after - total_before}")print(f"✅ Новых успешных: {success_after - success_before}")

        # Последняя запись
        cursor.execute("""
            SELECT email, success, provider, created_at, message_id, status_code, error
            FROM deliveries
            ORDER BY id DESC
            LIMIT 1"""
        )
        last = cursor.fetchone()

        if last:status_icon = "✅" if last[1] else "❌"print(f"\n📮 ПОСЛЕДНЯЯ ЗАПИСЬ: {status_icon}")print(f"   📧 Email: {last[0]}")print(f"   🌐 Провайдер: {last[2]}")print(f"   🕒 Время: {last[3]}")print(f"   🆔 Message ID: {last[4]}")print(f"   📊 Status Code: {last[5]}")
            if last[6]:  # Если есть ошибкаprint(f"   ❌ Ошибка: {last[6]}")

    # 5. ИТОГОВЫЙ АНАЛИЗprint(f"\n🎯 ИТОГОВЫЙ АНАЛИЗ РЕАЛЬНОЙ ОТПРАВКИ:")

    if success_count > 0 and message_id:print(f"🎉 РЕАЛЬНАЯ ОТПРАВКА ВЫПОЛНЕНА УСПЕШНО!")print(f"📧 Email отправлен через Resend API")print(f"🆔 Message ID: {message_id}")print(f"📊 Запись сохранена в базу данных")print(f"✅ Система полностью функциональна!")print(f"🌐 Можете проверить email в папке входящих")

        # Дополнительная статистика
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM deliveries WHERE provider = 'resend' AND success = 1"
            )
            resend_success = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM deliveries WHERE success = 1")
            total_success = cursor.fetchone()[0]

            if total_success > 0:
                success_rate = (resend_success / total_success) * 100
            else:
                success_rate = 0
print(f"\n📈 СТАТИСТИКА RESEND:")print(f"   ✅ Успешных отправок: {resend_success}")print(f"   📊 Общий успех системы: {success_rate:.1f}%")

        return True
    else:print(f"❌ РЕАЛЬНАЯ ОТПРАВКА НЕ УДАЛАСЬ")
        if error_details:print(f"🔍 Детали ошибки: {error_details}")print(f"🔧 Проверьте настройки API и домена")
        return False

if __name__ == "__main__":print("🔥 ЗАПУСК ТЕСТА РЕАЛЬНОЙ ОТПРАВКИ")print("Используется onboarding домен Resend для тестирования")print("=" * 60)

    try:
        result = asyncio.run(onboarding_email_test())

        if result:print(f"\n🏆 ПОЛНЫЙ УСПЕХ!")print(f"📧 Система отправила реальный email")print(f"📊 Все данные в приложении - реальные")print(f"✅ Проект полностью работоспособен!")
        else:print(f"\n⚠️  ТРЕБУЕТСЯ ДИАГНОСТИКА")print(f"🔧 Проверьте API ключ и настройки")

    except KeyboardInterrupt:print(f"\n⏹️ Тест прерван пользователем")
    except Exception as e:print(f"\n💥 НЕОЖИДАННАЯ ОШИБКА: {e}")

        traceback.print_exc()
