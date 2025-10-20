import os
import sys

from mailing.cli import main

#!/usr/bin/env python3
"""
Тест реальной отправки с подробными логами"""
sys.path.append(".")

def test_real_sending():"""Тест реальной отправки"""
    """Тест для real sending."""
print("🚀 ТЕСТИРОВАНИЕ РЕАЛЬНОЙ ОТПРАВКИ")print("=" * 50)

# Создадим тестовый файл с вашим email для безопасностиtest_email = input("Введите ваш email для тестирования: ")
with open("test_real_recipient.csv","w") as f:f.write(f"email,name,company,
discount\n")f.write(f"{test_email},Тестер,Реальная Компания,30\n")
print(f"✅ Создан файл с получателем: {test_email}")

    # Проверим конфигурациюprint("\n📋 ПРОВЕРКА КОНФИГУРАЦИИ...")
    argv_check = ["--file","test_real_recipient.csv","--template",
    "test_template_real.html","--check",
    ]

    try:
    main(argv_check)print("✅ Конфигурация корректна")
    except SystemExit as e:
        if e.code != 0:print("❌ Ошибка конфигурации")
            return

    # Dry-run тестprint("\n🧪 DRY-RUN ТЕСТ...")
    argv_dry = ["--file","test_real_recipient.csv","--template",
    "test_template_real.html","--subject","🧪 Тест системы рассылок (DRY-RUN)",
    "--dry-run",
    ]

    try:
    main(argv_dry)print("✅ Dry-run тест успешен")
    except Exception as e:print(f"❌ Ошибка dry-run: {e}")
        return

    # Предупреждение о реальной отправкеprint("\n⚠️  ВНИМАНИЕ: РЕАЛЬНАЯ ОТПРАВКА")print("Это отправит реальное письмо на указанный email!")

    # Проверяем API ключapi_key = os.getenv("RESEND_API_KEY", "test_resend_key_for_testing_only")if api_key.startswith("test_") or api_key == "test_resend_key_for_testing_only":print("\n🔑 ВНИМАНИЕ: Используется тестовый API ключ")print("Для реальной отправки нужно установить настоящий RESEND_API_KEY")print("Текущий ключ:", api_key)
choice = input("\nПродолжить с тестовым ключом (будет ошибка)? [y/N]: ")if choice.lower() != "y":print("❌ Отменено пользователем")
            return
print(f"\n🚀 ОТПРАВКА НА: {test_email}")confirm = input("Подтвердите отправку [y/N]: ")
if confirm.lower() == "y":
    argv_real = ["--file","test_real_recipient.csv","--template",
        "test_template_real.html","--subject","🚀 РЕАЛЬНЫЙ тест системы рассылок!",
        "--concurrency","1",# Медленнее, но надежнее
    ]

        try:print("\n📤 ОТПРАВЛЯЕМ...")
        main(argv_real)print("✅ Отправка завершена! Проверьте почту.")
        except Exception as e:print(f"❌ Ошибка отправки: {e}")
    else:print("❌ Отправка отменена")

if __name__ == "__main__":
    test_real_sending()
