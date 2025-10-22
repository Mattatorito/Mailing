#!/usr/bin/env python3

from __future__ import annotations
import asyncio
import json
from typing import Dict, Any, Optional
from aiohttp import web, ClientSession
from src.mailing.config import settings
from src.mailing.logging_config import logger
from src.persistence.repository import EventRepository


class WebhookServer:
    """Сервер для обработки webhook'ов от Resend."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        """Инициализирует webhook сервер."""
        self.host = host
        self.port = port
        self.app = web.Application()
        self.event_repo = EventRepository()
        self._setup_routes()
    
    def _setup_routes(self):
        """Настраивает маршруты."""
        self.app.router.add_post("/webhook/resend", self.handle_resend_webhook)
        self.app.router.add_get("/health", self.health_check)
        self.app.router.add_get("/", self.root_handler)
    
    async def handle_resend_webhook(self, request: web.Request) -> web.Response:
        """Обрабатывает webhook от Resend."""
        try:
            data = await request.json()
            
            # Логируем полученные данные
            logger.info(f"Received webhook: {data}")
            
            # Извлекаем информацию о событии
            event_type = data.get('type', 'unknown')
            email = data.get('data', {}).get('to', ['unknown'])[0]
            message_id = data.get('data', {}).get('id', '')
            
            # Сохраняем событие в базу данных
            await self.event_repo.save_event(
                event_type=event_type,
                email=email,
                message_id=message_id,
                data=data
            )
            
            logger.info(f"Processed webhook event: {event_type} for {email}")
            
            return web.json_response({"status": "ok"})
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return web.json_response(
                {"status": "error", "message": str(e)}, 
                status=500
            )
    
    async def health_check(self, request: web.Request) -> web.Response:
        """Проверка здоровья сервера."""
        return web.json_response({
            "status": "healthy",
            "service": "mailing-webhook-server",
            "version": "1.0.0"
        })
    
    async def root_handler(self, request: web.Request) -> web.Response:
        """Корневой обработчик."""
        return web.json_response({
            "service": "Mailing Webhook Server",
            "endpoints": {
                "webhook": "/webhook/resend",
                "health": "/health"
            }
        })
    
    async def start(self):
        """Запускает webhook сервер."""
        logger.info(f"Starting webhook server on {self.host}:{self.port}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"Webhook server started on http://{self.host}:{self.port}")
        
        # Держим сервер запущенным
        try:
            while True:
                await asyncio.sleep(3600)  # Спим по часу
        except KeyboardInterrupt:
            logger.info("Shutting down webhook server...")
            await runner.cleanup()


async def run_webhook_server(host: str = "0.0.0.0", port: int = 8080):
    """Запускает webhook сервер."""
    server = WebhookServer(host, port)
    await server.start()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Webhook Server for Resend events")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    
    asyncio.run(run_webhook_server(args.host, args.port))
