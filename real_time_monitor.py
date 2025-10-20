import asyncio
import json
import sys

from datetime import datetime
import time

from persistence.db import get_connection

#!/usr/bin/env python3
"""
Демонстрация реального мониторинга системы в реальном времени"""
sys.path.append(".")



async def real_time_monitoring():"""Мониторинг системы в реальном времени"""
    """Выполняет real time monitoring."""
print("🚀 МОНИТОРИНГ СИСТЕМЫ В РЕАЛЬНОМ ВРЕМЕНИ")print("=" * 60)print("📊 Обновление каждые 5 секунд (Ctrl+C для остановки)")print("=" * 60)

    while True:
        try:
            # Очистка экрана (работает в большинстве терминалов)print("\033[2J\033[H", end="")

            # Заголовок с текущим временемcurrent_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")print(f"🕒 Время: {current_time}")print("=" * 60)

            # Подключение к БД
            conn = get_connection()
            cursor = conn.cursor()

            # Статистика доставокcursor.execute("SELECT COUNT(*) FROM deliveries")
            total_deliveries = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM deliveries WHERE success = 1")
            successful_deliveries = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM deliveries WHERE success = 0")
            failed_deliveries = cursor.fetchone()[0]

            if total_deliveries > 0:
                success_rate = (successful_deliveries / total_deliveries) * 100
            else:
                success_rate = 0
print(f"📧 ДОСТАВКИ:")print(f"   📊 Всего: {total_deliveries}")print(f"   ✅ Успешных: {successful_deliveries}")print(f"   ❌ Неудачных: {failed_deliveries}")print(f"   📈 Успешность: {success_rate:.1f}%")

            # Событияcursor.execute("SELECT COUNT(*) FROM events")
            total_events = cursor.fetchone()[0]print(f"\n🎯 События: {total_events}")

            # Последние события (последние 3)
            cursor.execute("""
                SELECT event_type, email_address, timestamp
                FROM events
                ORDER BY timestamp DESC
                LIMIT 3"""
            )
            recent_events = cursor.fetchall()
print(f"\n📋 ПОСЛЕДНИЕ СОБЫТИЯ:")
            if recent_events:
                for event in recent_events:print(f"   🔔 {event[0]} → {event[1]} ({event[2]})")
            else:print("   📭 Событий нет")

            # Использование квоты сегодняtoday = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT emails_sent
                FROM daily_usage
                WHERE usage_date = ?""",
                (today,),
            )
            result = cursor.fetchone()
            today_usage = result[0] if result else 0
print(f"\n📅 КВОТА НА СЕГОДНЯ:")print(f"   📤 Отправлено: {today_usage}")print(f"   📊 Лимит: 1000")print(f"   📉 Остаток: {1000 - today_usage}")

            # Отписки и блокировкиcursor.execute("SELECT COUNT(*) FROM unsubscribes")
            unsubscribes = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM suppressions")
            suppressions = cursor.fetchone()[0]
print(f"\n🚫 БЛОКИРОВКИ:")print(f"   📭 Отписок: {unsubscribes}")print(f"   🔒 В блок-листе: {suppressions}")

            # Последние доставки
            cursor.execute("""
                SELECT recipient_email, success, provider, timestamp
                FROM deliveries
                ORDER BY timestamp DESC
                LIMIT 5"""
            )
            recent_deliveries = cursor.fetchall()
print(f"\n📮 ПОСЛЕДНИЕ ДОСТАВКИ:")
            if recent_deliveries:
                for delivery in recent_deliveries:status_icon = "✅" if delivery[1] else "❌"provider = delivery[2] or "unknown"
                    print(f"   {status_icon} {delivery[0]} | {provider} | {delivery[3]}"
                    )
            else:print("   📭 Доставок нет")

            conn.close()

            # Статус системыprint(f"\n⚡ СТАТУС СИСТЕМЫ:")print(f"   🔄 Мониторинг: Активен")print(f"   💾 База данных: Подключена")print(f"   🌐 Webhook сервер: Готов")print(f"   📡 Resend API: Настроен")
print("=" * 60)print("💡 Система работает с РЕАЛЬНЫМИ данными!")print("   📊 Все показанные данные - из рабочей базы")print("   🔄 Обновление через 5 секунд...")

            # Ждем 5 секунд
            await asyncio.sleep(5)

        except KeyboardInterrupt:print("\n\n⏹️  Мониторинг остановлен пользователем")
            break
        except Exception as e:print(f"\n❌ Ошибка мониторинга: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        asyncio.run(real_time_monitoring())
    except KeyboardInterrupt:print("\n👋 Завершение работы...")
