#!/usr/bin/env python3

import asyncio
import sys
import traceback

# Тестируем основную функциональность
def test_imports():
    """Проверяем основные импорты."""
    try:
        from src.mailing.config import settings
        from src.mailing.models import Recipient, DeliveryResult
        from src.mailing.sender import CampaignController
        from src.templating.engine import TemplateEngine
        from src.validation.email_validator import EmailValidator
        
        print("✅ Все модули импортированы успешно")
        return True  # Return success status
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        traceback.print_exc()
        return False  # Return failure status

def test_config():
    """Проверяем конфигурацию."""
    try:
        from src.mailing.config import settings
        print(f"✅ Конфигурация загружена, database: {settings.sqlite_db_path}")
        return True  # Return success status
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False  # Return failure status

def test_models():
    """Проверяем модели данных."""
    try:
        from src.mailing.models import Recipient, DeliveryResult
        
        # Создаем тестовые объекты
        recipient = Recipient(
            email="test@example.com",
            name="Test User"
        )
        
        result = DeliveryResult(
            success=True,
            status_code=200,
            message_id="test-123",
            provider="resend"
        )
        
        print("✅ Модели данных работают корректно")
        print(f"   Recipient: {recipient.email} ({recipient.name})")
        print(f"   DeliveryResult: {result.success}")
        return True  # Если дошли сюда, модели работают
    except Exception as e:
        print(f"❌ Ошибка моделей: {e}")
        traceback.print_exc()
        return False

def test_campaign_controller():
    """Проверяем CampaignController."""
    try:
        from mailing.sender import CampaignController
        
        # Создаем контроллер
        controller = CampaignController()
        
        # Проверяем начальное состояние
        if not controller.cancelled():
            print("✅ CampaignController работает корректно")
            return True  # Контроллер работает правильно
        else:
            print("❌ CampaignController: неожиданное начальное состояние")
            return False
    except Exception as e:
        print(f"❌ Ошибка CampaignController: {e}")
        traceback.print_exc()
        return False

def test_template_engine():
    """Проверяем шаблонизатор."""
    try:
        from templating.engine import TemplateEngine
        
        engine = TemplateEngine("samples")
        
        # Тестируем строковый шаблон
        result = engine.render_string(
            "Hello {{ name }}!",
            {"name": "World"}
        )
        
        if result == "Hello World!":
            print("✅ Шаблонизатор работает корректно")
            return True  # Шаблонизатор работает правильно
        else:
            print(f"❌ Неожиданный результат шаблонизации: {result}")
            return False
    except Exception as e:
        print(f"❌ Ошибка шаблонизатора: {e}")
        traceback.print_exc()
        return False

async def main():
    """Запускает все тесты."""
    print("🧪 Тестируем основную функциональность системы...")
    print("=" * 50)
    
    tests = [
        ("Импорты", test_imports),
        ("Конфигурация", test_config),
        ("Модели данных", test_models),
        ("Шаблонизатор", test_template_engine),
        ("CampaignController", test_campaign_controller),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Неожиданная ошибка в тесте {test_name}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Вся основная функциональность работает!")
        # Возвращаем значение только для скрипта, не для pytest
        return True
    else:
        print("⚠️ Некоторые тесты не прошли")
        # Возвращаем значение только для скрипта, не для pytest
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
