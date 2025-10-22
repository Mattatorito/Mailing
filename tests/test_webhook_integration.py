#!/usr/bin/env python3

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
import tempfile
from pathlib import Path

from src.mailing.webhook_server import WebhookServer, run_webhook_server


class TestWebhookServer(AioHTTPTestCase):
    """Интеграционные тесты для webhook сервера."""

    async def get_application(self):
        """Создает тестовое приложение."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            self.test_db_path = f.name
        
        with patch('mailing.webhook_server.EventRepository') as mock_repo_class:
            self.mock_repo = Mock()
            self.mock_repo.save_event = AsyncMock()
            mock_repo_class.return_value = self.mock_repo
            
            self.server = WebhookServer()
            return self.server.app

    def tearDown(self):
        """Очистка после тестов."""
        super().tearDown()
        Path(self.test_db_path).unlink(missing_ok=True)

    async def test_health_check_endpoint(self):
        """Тестирует endpoint проверки здоровья."""
        resp = await self.client.request("GET", "/health")
        assert resp.status == 200
        
        data = await resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "mailing-webhook-server"
        assert "version" in data

    async def test_root_endpoint(self):
        """Тестирует корневой endpoint."""
        resp = await self.client.request("GET", "/")
        assert resp.status == 200
        
        data = await resp.json()
        assert data["service"] == "Mailing Webhook Server"
        assert "endpoints" in data
        assert data["endpoints"]["webhook"] == "/webhook/resend"

    async def test_resend_webhook_success(self):
        """Тестирует успешную обработку webhook от Resend."""
        webhook_data = {
            "type": "email.delivered",
            "data": {
                "id": "msg_123456",
                "to": ["test@example.com"],
                "subject": "Test Email",
                "created_at": "2023-10-21T12:00:00Z"
            }
        }
        
        resp = await self.client.request(
            "POST", 
            "/webhook/resend",
            data=json.dumps(webhook_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
        
        # Проверяем что событие было сохранено
        self.mock_repo.save_event.assert_called_once()

    async def test_resend_webhook_invalid_json(self):
        """Тестирует обработку невалидного JSON."""
        resp = await self.client.request(
            "POST", 
            "/webhook/resend",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert resp.status == 500
        data = await resp.json()
        assert data["status"] == "error"

    async def test_resend_webhook_missing_data(self):
        """Тестирует обработку webhook с отсутствующими данными."""
        webhook_data = {
            "type": "email.delivered"
            # Отсутствует секция data
        }
        
        resp = await self.client.request(
            "POST", 
            "/webhook/resend",
            data=json.dumps(webhook_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert resp.status == 200  # Должно обрабатываться gracefully
        data = await resp.json()
        assert data["status"] == "ok"

    async def test_resend_webhook_different_events(self):
        """Тестирует различные типы событий."""
        event_types = [
            "email.sent",
            "email.delivered", 
            "email.delivery_delayed",
            "email.bounced",
            "email.complained"
        ]
        
        for event_type in event_types:
            webhook_data = {
                "type": event_type,
                "data": {
                    "id": f"msg_{event_type}",
                    "to": [f"test_{event_type}@example.com"],
                    "subject": f"Test {event_type}"
                }
            }
            
            resp = await self.client.request(
                "POST", 
                "/webhook/resend",
                data=json.dumps(webhook_data),
                headers={"Content-Type": "application/json"}
            )
            
            assert resp.status == 200


class TestWebhookServerIntegration:
    """Интеграционные тесты серверного запуска."""

    @pytest.mark.asyncio
    async def test_server_startup_and_shutdown(self):
        """Тестирует запуск и остановку сервера."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            test_db_path = f.name
        
        try:
            with patch('mailing.webhook_server.EventRepository'):
                server = WebhookServer(host="127.0.0.1", port=0)  # Порт 0 для автовыбора
                
                # Тестируем что сервер создается без ошибок
                assert server.host == "127.0.0.1"
                assert server.port == 0
                assert server.app is not None
                assert server.event_repo is not None
                
        finally:
            Path(test_db_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_run_webhook_server_function(self):
        """Тестирует функцию запуска сервера."""
        with patch('mailing.webhook_server.WebhookServer') as mock_server_class:
            mock_server = Mock()
            mock_server.start = AsyncMock()
            mock_server_class.return_value = mock_server
            
            # Мокаем asyncio.sleep чтобы не ждать реально
            with patch('asyncio.sleep', side_effect=KeyboardInterrupt):
                try:
                    await run_webhook_server("localhost", 8081)
                except KeyboardInterrupt:
                    pass  # Ожидаемое исключение
            
            mock_server_class.assert_called_once_with("localhost", 8081)
            mock_server.start.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_server_error_handling():
    """Тестирует обработку ошибок в webhook сервере."""
    with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
        test_db_path = f.name
    
    try:
        with patch('mailing.webhook_server.EventRepository') as mock_repo_class:
            # Настраиваем мок для генерации ошибки
            mock_repo = Mock()
            mock_repo.save_event = AsyncMock(side_effect=Exception("Database error"))
            mock_repo_class.return_value = mock_repo
            
            server = WebhookServer()
            
            # Создаем тестовый запрос
            request = Mock()
            request.json = AsyncMock(return_value={
                "type": "email.delivered",
                "data": {"to": ["test@example.com"]}
            })
            
            # Вызываем обработчик
            response = await server.handle_resend_webhook(request)
            
            # Проверяем что ошибка обработана корректно
            assert response.status == 500
            response_data = json.loads(response.text)
            assert response_data["status"] == "error"
            assert "Database error" in response_data["message"]
            
    finally:
        Path(test_db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])