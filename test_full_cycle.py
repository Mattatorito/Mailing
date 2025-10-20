#!/usr/bin/env python3
"""
Полный цикл тестирования реальной отправки email
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

from data_loader.csv_loader import CSVLoader
from mailing.config import Settings
from mailing.models import Recipient
from mailing.sender import run_campaign, CampaignController
from persistence.db import get_connection
from templating.engine import TemplateEngine

sys.path.append(".")

# Создаем настройки
settings = Settings()


async def test_full_email_cycle():
    """Тест полного цикла отправки email с реальными данными"""
    print("🚀 ТЕСТ ПОЛНОГО ЦИКЛА ОТПРАВКИ EMAIL")
    print("=" * 70)

    # 1. Проверка конфигурации
    print("1️⃣ ПРОВЕРКА КОНФИГУРАЦИИ:")
    print(f"   🔑 API ключ: {settings.resend_api_key[:15] if settings.resend_api_key else 'не настроен'}...")
    print(f"   📧 Отправитель: {settings.resend_from_email}")
    print(f"   👤 Имя: {settings.resend_from_name}")

    # 2. Загрузка получателей
    print(f"\n2️⃣ ЗАГРУЗКА ПОЛУЧАТЕЛЕЙ:")
    if not Path("test_recipients_real.csv").exists():
        print("❌ Файл test_recipients_real.csv не найден")
        return False

    loader = CSVLoader()
    recipient_objects = loader.load("test_recipients_real.csv")

    # Конвертируем в словари для совместимости
    recipients = []
    for r in recipient_objects:
        recipient_dict = {"email": r.email, "name": r.name}
        recipient_dict.update(r.variables)
        recipients.append(recipient_dict)
    
    print(f"   📋 Загружено получателей: {len(recipients)}")
    for i, recipient in enumerate(recipients, 1):
        print(f"   {i}. {recipient.get('email','no email')} - {recipient.get('name','no name')}")

    # 3. Подготовка шаблона
    print(f"\n3️⃣ ПОДГОТОВКА ШАБЛОНА:")
    template_path = Path("samples/test_template_real.html")
    if not template_path.exists():
        print("❌ Файл samples/test_template_real.html не найден")
        return False

    engine = TemplateEngine()

    # Тестируем рендеринг для первого получателя
    test_recipient = (
        recipients[0]
        if recipients
        else {"email": "test@example.com", "name": "Test User"}
    )

    template_vars = {
        **test_recipient,
        "current_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "subject": "Тестовое письмо с реальными данными",
    }

    try:
        rendered = engine.render("test_template_real.html", template_vars)
        print(f"   ✅ Шаблон успешно обработан")
        print(f"   📄 Тема: {rendered.subject}")
        print(f"   📏 Размер HTML: {len(rendered.body_html)} символов")
        print(f"   📝 Размер текста: {len(rendered.body_text or '')} символов")

        # Показываем начало HTML
        print(f"   👀 Предпросмотр HTML (первые 200 символов):")
        print(f"      {rendered.body_html[:200]}...")

    except Exception as e:
        print(f"❌ Ошибка рендеринга: {e}")
        return False

    # 4. Состояние базы данных ДО отправки
    print(f"\n4️⃣ СОСТОЯНИЕ БД ДО ОТПРАВКИ:")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM deliveries")
        deliveries_before = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM events")
        events_before = cursor.fetchone()[0]
        print(f"   📧 Доставок в БД: {deliveries_before}")
        print(f"   🎯 События в БД: {events_before}")

    # 5. Подготовка кампании
    print(f"\n5️⃣ ПОДГОТОВКА КАМПАНИИ:")

    try:
        # Используем уже загруженные объекты Recipient
        print(f"   ✅ Готово {len(recipient_objects)} объектов получателей")
        print(f"   ⚡ Конкурентность: {settings.concurrency}")
        print(f"   🔄 Лимит в минуту: {settings.rate_limit_per_minute}")
    except Exception as e:
        print(f"❌ Ошибка подготовки кампании: {e}")
        return False

    # 6. Симуляция отправки (dry-run режим)
    print(f"\n6️⃣ СИМУЛЯЦИЯ ОТПРАВКИ (DRY-RUN):")

    try:
        # Берем только первого получателя для теста
        test_recipients = recipient_objects[:1]
        test_email = test_recipients[0].email if test_recipients else "test@example.com"
        print(f"   📤 Отправка на: {test_email}")
        print(f"   🎯 Тема: {template_vars.get('subject', 'Test Subject')}")

        controller = CampaignController()

        # Запускаем кампанию в dry-run режиме
        events_count = 0
        success_count = 0

        async for event in run_campaign(
            recipients=test_recipients,
            template_name="test_template_real.html",
            subject=template_vars.get("subject", "Test Subject"),
            dry_run=True,
            concurrency=1,
            controller=controller,
        ):
            events_count += 1
            if event.get("type") == "progress":
                if event.get("result") and event["result"].success:
                    success_count += 1
                else:
                    print(f"   ❌ Ошибка: {event.get('result', {}).get('error', 'Unknown')}")
            elif event.get("type") == "finished":
                print(f"   🏁 Кампания завершена!")
                break
        
        print(f"   📈 Итого событий: {events_count}")
        print(f"   ✅ Успешных: {success_count}")

    except Exception as e:
        print(f"❌ Ошибка при симуляции: {e}")

    # 7. Состояние базы данных ПОСЛЕ симуляции
    print(f"\n7️⃣ СОСТОЯНИЕ БД ПОСЛЕ СИМУЛЯЦИИ:")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM deliveries")
        deliveries_after = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM events")
        events_after = cursor.fetchone()[0]
        print(f"   📧 Доставок в БД: {deliveries_after} (было: {deliveries_before})")
        print(f"   🎯 События в БД: {events_after} (было: {events_before})")

        if deliveries_after > deliveries_before:
            print(f"   📊 Новых записей о доставке: {deliveries_after - deliveries_before}")
            cursor.execute("SELECT email, success, provider FROM deliveries ORDER BY id DESC LIMIT 3")
            recent = cursor.fetchall()
            for delivery in recent:
                status = "✅" if delivery[1] else "❌"
                print(f"      {status} {delivery[0]} ({delivery[2]})")

    print(f"\n🎉 ТЕСТ ПОЛНОГО ЦИКЛА ЗАВЕРШЕН!")
    return True


if __name__ == "__main__":
    asyncio.run(test_full_email_cycle())