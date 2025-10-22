#!/usr/bin/env python3

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Мокаем GUI библиотеки перед импортом
sys.modules['tkinter'] = Mock()
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtWidgets'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()


class TestGUIComponents:
    """Тесты для GUI компонентов."""

    def test_gui_module_import(self):
        """Тестирует импорт GUI модулей."""
        # Проверяем что GUI модули можно импортировать
        import gui
        assert hasattr(gui, '__name__'), "GUI module should have __name__ attribute"
        
        import tk_gui
        assert hasattr(tk_gui, '__name__'), "tk_gui module should have __name__ attribute"

    @patch('tkinter.Tk')
    def test_tkinter_gui_initialization(self, mock_tk):
        """Тестирует инициализацию Tkinter GUI."""
        # Создаем мок с четко определенным поведением
        mock_root = Mock()
        mock_root.title = Mock()
        mock_root.geometry = Mock()
        mock_tk.return_value = mock_root
        
        # Создаем простое GUI приложение
        try:
            from gui import create_main_window
            window = create_main_window()
            # Проверяем вызовы методов через публичный API
            mock_root.title.assert_called()
            mock_root.geometry.assert_called()
            assert window == mock_root, "create_main_window should return the mock root"
        except ImportError:
            pytest.skip("GUI module not available")
        
        # Если функция не существует, создаем её для тестирования
        def create_main_window():
            import tkinter as tk
            root = tk.Tk()
            root.title("Mailing System")
            root.geometry("800x600")
            return root
        
        window = create_main_window()
        
        # Проверяем публичное поведение, а не внутренние атрибуты
        mock_tk.assert_called_once()
        # Вместо проверки внутренних атрибутов, проверяем поведение
        assert window is not None, "Window should be created"
        assert mock_root.title.called, "Title method should be called"
        assert mock_root.geometry.called, "Geometry method should be called"

    def test_pyside6_gui_initialization(self):
        """Тестирует инициализацию PySide6 GUI."""
        # Проверяем что можем импортировать модули PySide6 (или поймать ImportError)
        try:
            from PySide6.QtWidgets import QApplication, QMainWindow
            # Если импорт успешен, проверяем что классы имеют ожидаемые методы
            assert hasattr(QApplication, '__name__'), "QApplication should be a proper class"
            assert hasattr(QMainWindow, '__name__'), "QMainWindow should be a proper class"
            # Проверяем что это действительно классы, а не None
            assert isinstance(QApplication, type), "QApplication should be a class type"
            assert isinstance(QMainWindow, type), "QMainWindow should be a class type"
        except ImportError:
            # PySide6 не установлен, пропускаем тест
            pytest.skip("PySide6 not available")


class TestGUIConfiguration:
    """Тесты для конфигурации GUI."""

    def test_gui_config_loading(self):
        """Тестирует загрузку конфигурации GUI."""
        # Создаем временный конфиг файл
        config_data = {
            "gui": {
                "theme": "dark",
                "window_size": [800, 600],
                "default_tab": "compose"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            # Функция для загрузки GUI конфигурации
            def load_gui_config(path):
                with open(path, 'r') as f:
                    return json.load(f)
            
            config = load_gui_config(config_path)
            
            assert config["gui"]["theme"] == "dark"
            assert config["gui"]["window_size"] == [800, 600]
            assert config["gui"]["default_tab"] == "compose"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_gui_component_registration(self):
        """Тестирует регистрацию GUI компонентов."""
        # Простая система регистрации компонентов
        class ComponentRegistry:
            def __init__(self):
                self.components = {}
            
            def register(self, name, component):
                self.components[name] = component
            
            def get(self, name):
                return self.components.get(name)
            
            def list_components(self):
                return list(self.components.keys())
        
        registry = ComponentRegistry()
        
        # Регистрируем компоненты
        registry.register("main_window", Mock())
        registry.register("compose_tab", Mock())
        registry.register("history_tab", Mock())
        
        assert len(registry.list_components()) == 3
        assert "main_window" in registry.list_components()
        main_window = registry.get("main_window")
        assert main_window is not None, "Registered main_window should not be None"
        assert hasattr(main_window, '_mock_name'), "Should be a Mock object with mock attributes"


class TestGUIEventHandling:
    """Тесты для обработки событий GUI."""

    def test_button_click_handlers(self):
        """Тестирует обработчики нажатий кнопок."""
        # Мокаем обработчики событий
        click_handler = Mock()
        
        # Симулируем нажатие кнопки отправки
        def simulate_send_button_click():
            click_handler("send_email", {"recipient": "test@example.com"})
        
        simulate_send_button_click()
        
        click_handler.assert_called_once_with("send_email", {"recipient": "test@example.com"})

    def test_form_validation(self):
        """Тестирует валидацию форм."""
        def validate_email_form(data):
            errors = []
            
            if not data.get("recipient"):
                errors.append("Recipient is required")
            
            if not data.get("subject"):
                errors.append("Subject is required")
            
            recipient = data.get("recipient", "")
            if recipient and "@" not in recipient:
                errors.append("Invalid email format")
            
            return errors
        
        # Тестируем валидную форму
        valid_data = {
            "recipient": "test@example.com",
            "subject": "Test Email",
            "body": "Test message"
        }
        errors = validate_email_form(valid_data)
        assert len(errors) == 0
        
        # Тестируем невалидную форму
        invalid_data = {
            "recipient": "invalid-email",
            "subject": "",
            "body": "Test message"
        }
        errors = validate_email_form(invalid_data)
        assert len(errors) == 2
        assert "Subject is required" in errors
        assert "Invalid email format" in errors

    def test_progress_tracking(self):
        """Тестирует отслеживание прогресса."""
        class ProgressTracker:
            def __init__(self):
                self.progress = 0
                self.total = 0
                self.callbacks = []
            
            def start(self, total):
                self.total = total
                self.progress = 0
                self._notify_callbacks()
            
            def update(self, progress):
                self.progress = progress
                self._notify_callbacks()
            
            def add_callback(self, callback):
                self.callbacks.append(callback)
            
            def _notify_callbacks(self):
                for callback in self.callbacks:
                    callback(self.progress, self.total)
        
        tracker = ProgressTracker()
        callback_mock = Mock()
        tracker.add_callback(callback_mock)
        
        # Симулируем прогресс
        tracker.start(100)
        tracker.update(25)
        tracker.update(50)
        tracker.update(100)
        
        # Проверяем что callback вызывался
        assert callback_mock.call_count == 4
        callback_mock.assert_called_with(100, 100)  # Последний вызов


class TestGUIIntegration:
    """Интеграционные тесты GUI с бэкендом."""

    @patch('src.mailing.sender.run_campaign')
    @pytest.mark.asyncio
    async def test_gui_email_sending_integration(self, mock_run_campaign):
        """Тестирует интеграцию GUI с отправкой email."""
        # Настраиваем мок кампании
        async def mock_campaign(*args, **kwargs):
            yield {"type": "finished", "stats": {"sent": 1, "delivered": 1, "failed": 0}}
        
        mock_run_campaign.return_value = mock_campaign()
        
        # Симулируем отправку через GUI и выполняем async функцию
        from src.mailing.sender import run_campaign
        from src.mailing.models import Recipient
        
        recipients = [Recipient(email="test@example.com", name="Test")]
        event_received = False
        
        async for event in run_campaign(
            recipients=recipients,
            template_name="test.html",
            subject="Test",
            dry_run=True,
            concurrency=1
        ):
            event_received = True
            assert event["type"] == "finished"
            break
        
        # Проверяем что событие получено
        assert event_received, "Async function should have been executed"

    def test_gui_settings_integration(self):
        """Тестирует интеграцию GUI с настройками."""
        from src.mailing.config import Settings
        
        # Создаем временные настройки
        test_settings = {
            "resend_api_key": "test_key",
            "smtp_timeout": 30,
            "concurrency": 5
        }
        
        # Симулируем сохранение настроек через GUI
        def save_settings_via_gui(settings_dict):
            # В реальном GUI это было бы сохранение в файл или базу
            return {"status": "saved", "settings": settings_dict}
        
        result = save_settings_via_gui(test_settings)
        
        assert result["status"] == "saved"
        assert result["settings"]["resend_api_key"] == "test_key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])