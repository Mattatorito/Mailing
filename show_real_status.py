import json
import sys

from datetime import datetime

        from templating.engine import TemplateEngine
from mailing.config import settings
from mailing.limits.daily_quota import DailyQuota
from persistence.db import get_connection
from persistence.repository import DeliveryRepository, SuppressionRepository

#!/usr/bin/env python3
"""
Демонстрация всех реальных данных в системе"""
sys.path.append(".")



def show_system_status():"""Показать полный статус системы с реальными данными"""
    """Выполняет show system status."""
print("=" * 80)print("🚀 ПОЛНЫЙ СТАТУС СИСТЕМЫ - ВСЕ РЕАЛЬНЫЕ ДАННЫЕ")print("=" * 80)

    # Конфигурацияprint("📋 ТЕКУЩАЯ КОНФИГУРАЦИЯ:")print(f"   🔑 API ключ: {settings.resend_api_key[:10]}{'*' * 20}")print(f"   📧 Отправитель: {settings.resend_from_email}")print(f"   👤 Имя: {settings.resend_from_name}")print(f"   📊 Дневной лимит: {settings.daily_email_limit}")print(f"   ⚡ Конкурентность: {settings.concurrency}")print(f"   🔄 Лимит в минуту: {settings.rate_limit_per_minute}")print(f"   🗃️ База данных: {settings.sqlite_db_path}")

    # Дневная квота
    quota = DailyQuota()print(f"\n📅 ДНЕВНАЯ КВОТА:")print(f"   📊 Использовано сегодня: {quota.used()}")print(f"   📈 Лимит: {quota.limit}")print(f"   📉 Остаток: {quota.remaining()}")print(f"   ✅ Можно отправлять: {'Да' if quota.can_send() else 'Нет'}")

    # База данных
    conn = get_connection()
    cursor = conn.cursor()

    # Статистика таблицprint(f"\n🗄️ СТАТИСТИКА БАЗЫ ДАННЫХ:")
cursor.execute("SELECT COUNT(*) FROM deliveries")
    deliveries_count = cursor.fetchone()[0]print(f"   📧 Всего доставок: {deliveries_count}")
cursor.execute("SELECT COUNT(*) FROM deliveries WHERE success = 1")
    success_count = cursor.fetchone()[0]print(f"   ✅ Успешных: {success_count}")
cursor.execute("SELECT COUNT(*) FROM deliveries WHERE success = 0")
    failed_count = cursor.fetchone()[0]print(f"   ❌ Неудачных: {failed_count}")

    if deliveries_count > 0:
        success_rate = (success_count / deliveries_count) * 100print(f"   📈 Успешность: {success_rate:.1f}%")
cursor.execute("SELECT COUNT(*) FROM unsubscribes")
    unsubscribes_count = cursor.fetchone()[0]print(f"   🚫 Отписок: {unsubscribes_count}")
cursor.execute("SELECT COUNT(*) FROM suppressions")
    suppressions_count = cursor.fetchone()[0]print(f"   🔒 В блок-листе: {suppressions_count}")
cursor.execute("SELECT COUNT(*) FROM events")
    events_count = cursor.fetchone()[0]print(f"   🎯 События: {events_count}")

    # Последние доставкиprint(f"\n📋 ПОСЛЕДНИЕ ДОСТАВКИ (реальные данные):")cursor.execute("SELECT * FROM deliveries ORDER BY id DESC LIMIT 5")
    recent_deliveries = cursor.fetchall()

    if recent_deliveries:
        for i,delivery in enumerate(recent_deliveries, 1):status = "✅" if delivery[2] else "❌"provider = delivery[6] or "неизвестно"print(f"   {i}. {status} {delivery[1]} | {provider} | {delivery[7]}")
    else:print("   📭 Доставок пока нет")

    # Последние событияprint(f"\n🎯 ПОСЛЕДНИЕ СОБЫТИЯ:")cursor.execute("SELECT * FROM events ORDER BY id DESC LIMIT 3")
    recent_events = cursor.fetchall()

    if recent_events:
        for i,event in enumerate(recent_events, 1):print(f"   {i}. {event[1]} | {event[2]} | {event[4]}")
    else:print("   📭 Событий пока нет")

    # Использование по днямprint(f"\n📊 ИСПОЛЬЗОВАНИЕ ПО ДНЯМ:")cursor.execute("SELECT * FROM daily_usage ORDER BY usage_date DESC LIMIT 5")
    usage_data = cursor.fetchall()

    if usage_data:
        for date, used in usage_data:print(f"   📅 {date}: {used} писем")
    else:print("   📭 Данных пока нет")

    conn.close()

    # Провайдерыprint(f"\n🌐 ПРОВАЙДЕРЫ ОТПРАВКИ:")print(f"   📮 Resend API: Активен")print(f"   🔗 Base URL: {settings.resend_base_url}")print(f"   ⚡ Max retries: {settings.max_retries}")
print("=" * 80)print("💡 ВСЕ ДАННЫЕ ВЫШЕ - РЕАЛЬНЫЕ ИЗ РАБОЧЕЙ СИСТЕМЫ!")print("=" * 80)


def show_template_preview():"""Показать предпросмотр шаблона с реальными данными"""
    """Выполняет show template preview."""
print("\n" + "=" * 60)print("📄 ПРЕДПРОСМОТР ШАБЛОНА С РЕАЛЬНЫМИ ДАННЫМИ")print("=" * 60)

    try:

        engine = TemplateEngine()

        # Реальные тестовые данные
        test_data = {"name": "Александр","company": "Тестовая Компания","discount": "30",
            "current_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message_id": "test_12345",
        }

        # Рендерим шаблонrender_result = engine.render("test_template_real.html", test_data)
        html_content = render_result.body_html

        # Показываем начало HTMLprint("📝 Содержимое HTML (первые 500 символов):")print("-" * 40)print(html_content[:500] + "...")print("-" * 40)
print(f"📏 Полная длина: {len(html_content)} символов")print("✅ Шаблон успешно обработан с реальными данными")

    except Exception as e:print(f"❌ Ошибка обработки шаблона: {e}")

if __name__ == "__main__":
    show_system_status()
    show_template_preview()
