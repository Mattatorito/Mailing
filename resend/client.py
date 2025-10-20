#!/usr/bin/env python3

from __future__ import annotations
from typing import Dict, Any, Optional
import aiohttp
import asyncio

from mailing.config import settings
from mailing.models import DeliveryResult


class ResendError(Exception):
    """Исключение для ошибок Resend API."""
    pass


class ResendClient:
    """Асинхронный клиент для Resend API."""
    
    def __init__(self, api_key: str = None):
        """Инициализирует клиент."""
        self.api_key = api_key or settings.resend_api_key
        self.base_url = settings.resend_base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получает HTTP сессию."""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self.session
    
    async def send_message(
        self,
        to_email: str,
        subject: str,
        html_content: str = "",
        text_content: str = "",
        from_email: str = None,
        from_name: str = None
    ) -> DeliveryResult:
        """Отправляет email через Resend API."""
        
        # Формируем данные для отправки
        payload = {
            "from": f"{from_name or settings.resend_from_name} <{from_email or settings.resend_from_email}>",
            "to": [to_email],
            "subject": subject
        }
        
        if html_content:
            payload["html"] = html_content
        if text_content:
            payload["text"] = text_content
        
        try:
            session = await self._get_session()
            
            async with session.post(f"{self.base_url}/emails", json=payload) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    return DeliveryResult(
                        email=to_email,
                        success=True,
                        status_code=response.status,
                        message_id=response_data.get("id", ""),
                        provider="resend"
                    )
                else:
                    error_message = response_data.get("message", f"HTTP {response.status}")
                    return DeliveryResult(
                        email=to_email,
                        success=False,
                        status_code=response.status,
                        error=error_message,
                        provider="resend"
                    )
                    
        except Exception as e:
            return DeliveryResult(
                email=to_email,
                success=False,
                status_code=0,
                error=str(e),
                provider="resend"
            )
    
    async def close(self):
        """Закрывает HTTP сессию."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
