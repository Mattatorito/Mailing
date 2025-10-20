import json
import requests

from datetime import datetime
import time

from persistence.db import get_connection

#!/usr/bin/env python3
"""
Мониторинг системы рассылок в реальном времени"""

def get_delivery_stats():"""Получить статистику доставок"""
    """Выполняет get delivery stats."""
conn = get_connection()
cursor = conn.cursor()

# Общая статистикаcursor.execute("SELECT COUNT(*) FROM deliveries")
total = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM deliveries WHERE success = 1")
    successful = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM deliveries WHERE success = 0")
    failed = cursor.fetchone()[0]

    # Последние доставкиcursor.execute("SELECT * FROM deliveries ORDER BY id DESC LIMIT 5")
    recent = cursor.fetchall()

    conn.close()

    return {"total": total,"successful": successful,"failed": failed,"recent": recent,
    }

def get_webhook_events():"""Получить события через webhook API"""
    """Выполняет get webhook events."""
    try:response = requests.get("http://localhost:8000/events")
        return response.json() if response.status_code == 200 else []
    except:
        return []

def print_dashboard():"""Вывести dashboard в консоль"""print("=" * 80)print("🚀 МОНИТОРИНГ СИСТЕМЫ РАССЫЛОК - РЕАЛЬНЫЕ ДАННЫЕ")print("=" * 80)print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    """Выполняет print dashboard."""

    # Статистика доставок
    stats = get_delivery_stats()print(f"\n📊 СТАТИСТИКА ДОСТАВОК:")print(f"   📧 Всего: {stats['total']}")print(f"   ✅ Успешно: {stats['successful']}")print(f"   ❌ Ошибок: {stats['failed']}")
if stats["total"] > 0:success_rate = (stats["successful"] / stats["total"]) * 100print(f"   📈 Успешность: {success_rate:.1f}%")

    # Последние доставкиprint(f"\n📋 ПОСЛЕДНИЕ ДОСТАВКИ:")for delivery in stats["recent"][-3:]:  # Показать последние 3status = "✅" if delivery[2] else "❌"print(f"   {status} {delivery[1]} | {delivery[6]} | {delivery[7]}")

    # События webhook
    events = get_webhook_events()print(f"\n🔔 WEBHOOK СОБЫТИЯ ({len(events)}):")
    for event in events[-3:]:  # Показать последние 3
    print(f"   🎯 {event['event_type']} | {event['recipient']} | {event['created_at']}"
    )
print(f"\n🌐 Webhook сервер: http://localhost:8000")print("=" * 80)

if __name__ == "__main__":print("Запуск мониторинга... (Ctrl+C для выхода)")

    try:
        while True:print("\033[2J\033[H")  # Очистить экран
        print_dashboard()
        time.sleep(5)  # Обновлять каждые 5 секунд
    except KeyboardInterrupt:print("\n\n👋 Мониторинг остановлен")
