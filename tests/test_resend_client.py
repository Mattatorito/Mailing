#!/usr/bin/env python3
"""
Comprehensive tests for resend/client.py
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any
from aioresponses import aioresponses

from src.resend.client import ResendClient, ResendError
from src.mailing.models import DeliveryResult


class TestResendError:
    """Тесты для исключения ResendError."""
    
    def test_exception_creation(self):
        """Тест создания исключения."""
        error = ResendError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_exception_inheritance(self):
        """Тест наследования от Exception."""
        error = ResendError("Test")
        assert isinstance(error, Exception)


class TestResendClient:
    """Тесты для ResendClient."""
    
    @pytest.fixture
    def client(self):
        """Фикстура клиента."""
        return ResendClient(api_key="test_api_key")
    
    @pytest.fixture
    def mock_settings(self):
        """Фикстура настроек."""
        with patch('resend.client.settings') as mock_settings:
            mock_settings.resend_api_key = "default_api_key"
            mock_settings.resend_base_url = "https://api.resend.com"
            mock_settings.resend_from_name = "Test Sender"
            mock_settings.resend_from_email = "test@example.com"
            yield mock_settings
    
    def test_init_with_api_key(self):
        """Тест инициализации с API ключом."""
        client = ResendClient(api_key="custom_key")
        assert client.api_key == "custom_key"
        assert client.session is None
    
    def test_init_without_api_key(self, mock_settings):
        """Тест инициализации без API ключа (из настроек)."""
        client = ResendClient()
        assert client.api_key == "default_api_key"
        assert client.base_url == "https://api.resend.com"
        assert client.session is None
    
    @pytest.mark.asyncio
    async def test_get_session_creation(self, client):
        """Тест создания HTTP сессии."""
        session = await client._get_session()
        
        assert isinstance(session, aiohttp.ClientSession)
        assert not session.closed
        assert session.headers.get("Authorization") == "Bearer test_api_key"
        assert session.headers.get("Content-Type") == "application/json"
        assert session.timeout.total == 30
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_get_session_reuse(self, client):
        """Тест переиспользования HTTP сессии."""
        session1 = await client._get_session()
        session2 = await client._get_session()
        
        assert session1 is session2
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_get_session_after_close(self, client):
        """Тест создания новой сессии после закрытия."""
        session1 = await client._get_session()
        await client.close()
        
        session2 = await client._get_session()
        
        assert session1 is not session2
        assert session1.closed
        assert not session2.closed
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, client, mock_settings):
        """Тест успешной отправки сообщения."""
        with aioresponses() as m:
            m.post(
                'https://api.resend.com/emails',
                status=200,
                payload={"id": "msg_123456"}
            )
            
            result = await client.send_message(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test text"
            )
        
        assert isinstance(result, DeliveryResult)
        assert result.success is True
        assert result.email == "test@example.com"
        assert result.status_code == 200
        assert result.message_id == "msg_123456"
        assert result.provider == "resend"
        assert result.error == ""
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_send_message_custom_from(self, client, mock_settings):
        """Тест отправки с кастомным отправителем."""
        with aioresponses() as m:
            m.post(
                'https://api.resend.com/emails',
                status=200,
                payload={"id": "msg_123456"}
            )
            
            await client.send_message(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                from_email="custom@example.com",
                from_name="Custom Sender"
            )
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_send_message_only_html(self, client, mock_settings):
        """Тест отправки только с HTML контентом."""
        with aioresponses() as m:
            m.post(
                'https://api.resend.com/emails',
                status=200,
                payload={"id": "msg_123456"}
            )
            
            await client.send_message(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<h1>Test</h1>"
            )
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_send_message_only_text(self, client, mock_settings):
        """Тест отправки только с текстовым контентом."""
        with aioresponses() as m:
            m.post(
                'https://api.resend.com/emails',
                status=200,
                payload={"id": "msg_123456"}
            )
            
            await client.send_message(
                to_email="test@example.com",
                subject="Test Subject",
                text_content="Test text"
            )
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_send_message_api_error(self, client, mock_settings):
        """Тест обработки ошибки API."""
        with aioresponses() as m:
            m.post(
                'https://api.resend.com/emails',
                status=400,
                payload={"message": "Invalid email address"}
            )
            
            result = await client.send_message(
                to_email="invalid-email",
                subject="Test Subject",
                html_content="<h1>Test</h1>"
            )
        
        assert isinstance(result, DeliveryResult)
        assert result.success is False
        assert result.email == "invalid-email"
        assert result.status_code == 400
        assert result.error == "Invalid email address"
        assert result.provider == "resend"
        assert result.message_id == ""
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_send_message_api_error_no_message(self, client, mock_settings):
        """Тест обработки ошибки API без сообщения."""
        with aioresponses() as m:
            m.post(
                'https://api.resend.com/emails',
                status=500,
                payload={}
            )
            
            result = await client.send_message(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<h1>Test</h1>"
            )
        
        assert result.success is False
        assert result.status_code == 500
        assert result.error == "HTTP 500"
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_send_message_network_error(self, client, mock_settings):
        """Тест обработки сетевой ошибки."""
        with aioresponses() as m:
            m.post(
                'https://api.resend.com/emails',
                exception=aiohttp.ClientError("Network error")
            )
            
            result = await client.send_message(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<h1>Test</h1>"
            )
        
        assert result.success is False
        assert result.status_code == 0
        assert "Network error" in result.error
        assert result.provider == "resend"
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_send_message_general_exception(self, client, mock_settings):
        """Тест обработки общих исключений."""
        # Для этого теста используем реальное исключение во время отправки
        with patch.object(client, '_get_session') as mock_get_session:
            mock_get_session.side_effect = Exception("Connection failed")
            
            result = await client.send_message(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<h1>Test</h1>"
            )
        
        assert result.success is False
        assert result.status_code == 0
        assert "Connection failed" in result.error
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_close_session(self, client):
        """Тест закрытия сессии."""
        session = await client._get_session()
        assert not session.closed
        
        await client.close()
        assert session.closed
    
    @pytest.mark.asyncio
    async def test_close_no_session(self, client):
        """Тест закрытия без открытой сессии."""
        await client.close()  # Не должно вызывать ошибку
    
    @pytest.mark.asyncio
    async def test_close_already_closed_session(self, client):
        """Тест закрытия уже закрытой сессии."""
        session = await client._get_session()
        await session.close()
        
        await client.close()  # Не должно вызывать ошибку
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Тест использования как контекстный менеджер."""
        async with client as ctx_client:
            assert ctx_client is client
            session = await ctx_client._get_session()
            assert not session.closed
        
        # После выхода из контекста сессия должна быть закрыта
        assert session.closed
    
    @pytest.mark.asyncio
    async def test_context_manager_with_exception(self, client):
        """Тест контекстного менеджера с исключением."""
        session = None
        
        try:
            async with client as ctx_client:
                session = await ctx_client._get_session()
                assert not session.closed
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Сессия должна быть закрыта даже при исключении
        assert session.closed
    
    @pytest.mark.asyncio
    async def test_multiple_send_requests(self, client, mock_settings):
        """Тест множественных запросов с переиспользованием сессии."""
        with aioresponses() as m:
            for i in range(3):
                m.post(
                    'https://api.resend.com/emails',
                    status=200,
                    payload={"id": "msg_123456"}
                )
            
            # Отправляем несколько сообщений
            for i in range(3):
                result = await client.send_message(
                    to_email=f"test{i}@example.com",
                    subject=f"Test Subject {i}",
                    html_content=f"<h1>Test {i}</h1>"
                )
                assert result.success is True
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client, mock_settings):
        """Тест конкурентных запросов."""
        with aioresponses() as m:
            for i in range(5):
                m.post(
                    'https://api.resend.com/emails',
                    status=200,
                    payload={"id": "msg_123456"}
                )
            
            # Отправляем запросы конкурентно
            tasks = [
                client.send_message(
                    to_email=f"test{i}@example.com",
                    subject=f"Test Subject {i}",
                    html_content=f"<h1>Test {i}</h1>"
                )
                for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
        
        # Все запросы должны быть успешными
        for result in results:
            assert result.success is True
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_session_timeout_configuration(self, client):
        """Тест конфигурации таймаута сессии."""
        session = await client._get_session()
        
        assert session.timeout.total == 30
        
        await client.close()