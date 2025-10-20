#!/usr/bin/env python3
"""
Тест реальной отправки email (не dry-run)
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

from mailing.config import Settings
from mailing.models import Recipient
from mailing.sender import run_campaign, CampaignController
from templating.engine import TemplateEngine

sys.path.append(".")

# Создаем настройки
settings = Settings()

async def test_real_sending():
    """Тест реальной отправки email (ОСТОРОЖНО!)"""
    print("🚨 ТЕСТ РЕАЛЬНОЙ ОТПРАВКИ EMAIL")
    print("=" * 70)
    print("⚠️  ВНИМАНИЕ: Этот тест отправляет РЕАЛЬНЫЕ email!")
    print("⚠️  Убедитесь что у вас есть разрешение получателей!")
    print("=" * 70)

    # 1. Проверка конфигурации
    print("1️⃣ ПРОВЕРКА КОНФИГУРАЦИИ:")
    if not settings.resend_api_key:
    print("❌ RESEND_API_KEY не настроен")
        return False

    print(f"   🔑 API ключ: {settings.resend_api_key[:15]}...")
    print(f"   📧 Отправитель: {settings.resend_from_email}")
    print(f"   👤 Имя: {settings.resend_from_name}")

    # 2. Проверка шаблона
    print(f"\n2️⃣ ПРОВЕРКА ШАБЛОНА:")
    template_path = Path("samples/test_template.html")
    if not template_path.exists():
    print("❌ Файл samples/test_template.html не найден")
        return False

    engine = TemplateEngine()

    # 3. Подготовка тестового получателя
    print(f"\n3️⃣ ПОДГОТОВКА ТЕСТОВОГО ПОЛУЧАТЕЛЯ:")

    # ВНИМАНИЕ: измените на реальный email для тестирования
    test_email = "your-test-email@example.com"  # ИЗМЕНИТЕ ЭТО!

    if test_email == "your-test-email@example.com":
    print("❌ Пожалуйста, измените test_email на реальный адрес в коде")
        return False

    test_recipient = Recipient(
    email=test_email,
    name="Test User",
    company="Test Company"
    )

    print(f"   📧 Тестовый получатель: {test_recipient.email}")
    print(f"   👤 Имя: {test_recipient.name}")

    # 4. Рендеринг шаблона
    print(f"\n4️⃣ РЕНДЕРИНГ ШАБЛОНА:")

    template_vars = {
    **test_recipient.variables,
    "email": test_recipient.email,
    "current_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "subject": "Тестовое письмо от Mailing System",
    }

    try:
    rendered = engine.render("test_template.html", template_vars)
    print(f"   ✅ Шаблон успешно обработан")
    print(f"   📄 Тема: {rendered.subject}")
    print(f"   📏 Размер HTML: {len(rendered.body_html)} символов")

    # Показываем начало HTML
    print(f"   👀 Предпросмотр HTML (первые 200 символов):")
    print(f"      {rendered.body_html[:200]}...")

    except Exception as e:
    print(f"❌ Ошибка рендеринга: {e}")
        return False

    # 5. Подтверждение отправки
    print(f"\n5️⃣ ПОДТВЕРЖДЕНИЕ ОТПРАВКИ:")
    print(f"   📧 Email будет отправлен на: {test_recipient.email}")
    print(f"   📄 Тема: {rendered.subject}")

    confirm = input("   ❓ Продолжить отправку? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y', 'да']:
    print("   ⏹️ Отправка отменена пользователем")
        return False

    # 6. Реальная отправка
    print(f"\n6️⃣ РЕАЛЬНАЯ ОТПРАВКА:")

    controller = CampaignController()

    try:
    events_count = 0
    success_count = 0

        async for event in run_campaign(
        recipients=[test_recipient],
        template_name="test_template.html",
        subject=template_vars.get("subject", "Test Subject"),
        dry_run=False,  # РЕАЛЬНАЯ ОТПРАВКА!
        concurrency=1,
        controller=controller,
    ):
        events_count += 1

            if event.get("type") == "progress":
            result = event.get("result")
                if result:
                    if result.success:
                    success_count += 1
                    print(f"   ✅ Отправлено: {result.email} (ID: {result.message_id})")
                else:
                    print(f"   ❌ Ошибка: {result.email} - {result.error}")

            elif event.get("type") == "finished":
            print(f"   🏁 Кампания завершена!")
            stats = event.get("stats", {})
            print(f"   📊 Статистика: {stats}")
            break

            elif event.get("type") == "error":
            print(f"   💥 Ошибка кампании: {event.get('error')}")
            break

    print(f"\n📈 ИТОГИ:")
    print(f"   📧 Всего событий: {events_count}")
    print(f"   ✅ Успешных отправок: {success_count}")

        if success_count > 0:
        print(f"   🎉 Email успешно отправлен!")
    else:
        print(f"   😞 Отправка не удалась")

    except Exception as e:
    print(f"❌ Ошибка при отправке: {e}")
        return False

    print(f"\n🎯 ТЕСТ РЕАЛЬНОЙ ОТПРАВКИ ЗАВЕРШЕН!")
    return True

if __name__ == "__main__":
    asyncio.run(test_real_sending())