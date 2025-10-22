#!/usr/bin/env python3
"""
Инициализация и интеграция всех улучшений безопасности и производительности.
Этот модуль связывает все новые компоненты вместе.
"""

import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.security import HTTPBearer

# Новые модули
from src.security.auth import get_auth_manager, get_current_user, require_https
from src.security.https_config import load_https_config, get_uvicorn_ssl_config
from src.monitoring.metrics import get_metrics, start_metrics_collection, stop_metrics_collection
from src.persistence.backup import initialize_backup_system, start_backup_scheduler, stop_backup_scheduler
from src.templating.cached_engine import get_template_engine

logger = logging.getLogger(__name__)

class EnhancedApplication:
    """Улучшенное приложение с новыми возможностями."""
    
    def __init__(self):
        self.app: Optional[FastAPI] = None
        self.backup_manager = None
        self.backup_scheduler = None
        self.metrics = None
        self.auth_manager = None
        self.template_engine = None
        
    async def initialize(self):
        """Инициализация всех компонентов."""
        logger.info("🚀 Initializing enhanced email marketing application...")
        
        # Инициализация метрик
        self.metrics = get_metrics()
        if self.metrics.enabled:
            await start_metrics_collection()
            logger.info("📊 Metrics collection started")
        
        # Инициализация системы бэкапов
        db_path = os.getenv('SQLITE_DB_PATH', './data/mailing.sqlite3')
        self.backup_manager, self.backup_scheduler = initialize_backup_system(db_path)
        
        if self.backup_manager.config.enabled:
            await start_backup_scheduler()
            logger.info("💾 Backup system started")
        
        # Инициализация аутентификации
        self.auth_manager = get_auth_manager()
        logger.info("🔒 Authentication system initialized")
        
        # Инициализация движка шаблонов с кэшированием
        self.template_engine = get_template_engine()
        
        # Предзагрузка шаблонов
        if self.template_engine.cache_config.enabled:
            await self.template_engine.preload_templates()
            logger.info("🎨 Template engine with caching initialized")
        
        logger.info("✅ All systems initialized successfully")
    
    async def create_app(self) -> FastAPI:
        """Создание FastAPI приложения с улучшениями."""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            await self.initialize()
            yield
            # Shutdown
            await self.shutdown()
        
        self.app = FastAPI(
            title="Professional Email Marketing Tool - Enhanced",
            description="Enhanced version with authentication, caching, metrics, and backups",
            version="2.0.0",
            lifespan=lifespan
        )
        
        # Middleware для HTTPS redirect (простая реализация)
        @self.app.middleware("http")
        async def https_redirect(request: Request, call_next):
            if os.getenv('FORCE_HTTPS', 'false').lower() == 'true':
                if request.url.scheme == 'http':
                    https_url = request.url.replace(scheme='https')
                    return RedirectResponse(url=str(https_url), status_code=301)
            return await call_next(request)
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"] if os.getenv('ENVIRONMENT') == 'development' else ["https://yourdomain.com"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Добавляем роуты
        self._add_routes()
        
        return self.app
    
    def _add_routes(self):
        """Добавление маршрутов."""
        
        @self.app.get("/health")
        async def health_check():
            """Расширенная проверка здоровья."""
            status = {
                "status": "healthy",
                "timestamp": "2025-10-22T00:00:00Z",
                "version": "2.0.0",
                "environment": os.getenv('ENVIRONMENT', 'development'),
                "features": {
                    "authentication": self.auth_manager is not None,
                    "metrics": self.metrics.enabled if self.metrics else False,
                    "backups": self.backup_manager.config.enabled if self.backup_manager else False,
                    "template_cache": self.template_engine.cache_config.enabled if self.template_engine else False,
                    "https": load_https_config().enabled
                }
            }
            return status
        
        @self.app.get("/metrics")
        async def get_metrics_endpoint():
            """Endpoint для Prometheus метрик."""
            if not self.metrics or not self.metrics.enabled:
                raise HTTPException(status_code=404, detail="Metrics not enabled")
            
            return PlainTextResponse(
                self.metrics.get_metrics(),
                media_type=self.metrics.get_content_type()
            )
        
        @self.app.get("/admin/cache/stats")
        async def get_cache_stats(current_user=Depends(get_current_user)):
            """Статистика кэша (требует аутентификации)."""
            if not self.template_engine:
                raise HTTPException(status_code=404, detail="Template engine not available")
            
            return self.template_engine.get_cache_stats()
        
        @self.app.post("/admin/cache/clear")
        async def clear_cache(current_user=Depends(get_current_user)):
            """Очистка кэша (требует аутентификации)."""
            if not self.template_engine:
                raise HTTPException(status_code=404, detail="Template engine not available")
            
            await self.template_engine.clear_cache()
            return {"message": "Cache cleared successfully"}
        
        @self.app.get("/admin/backup/list")
        async def list_backups(current_user=Depends(get_current_user)):
            """Список бэкапов (требует аутентификации)."""
            if not self.backup_manager:
                raise HTTPException(status_code=404, detail="Backup system not available")
            
            backups = await self.backup_manager.list_backups()
            return [
                {
                    "filename": backup.filename,
                    "timestamp": backup.timestamp.isoformat(),
                    "size_bytes": backup.size_bytes,
                    "compressed": backup.compressed,
                    "verified": backup.verified
                }
                for backup in backups
            ]
        
        @self.app.post("/admin/backup/create")
        async def create_backup(current_user=Depends(get_current_user)):
            """Создание бэкапа (требует аутентификации)."""
            if not self.backup_manager:
                raise HTTPException(status_code=404, detail="Backup system not available")
            
            backup_info = await self.backup_manager.create_backup("manual")
            if backup_info:
                return {
                    "message": "Backup created successfully",
                    "filename": backup_info.filename,
                    "size_bytes": backup_info.size_bytes
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to create backup")
        
        @self.app.post("/auth/login")
        async def login(request: Request):
            """Аутентификация пользователя."""
            require_https(request)
            
            data = await request.json()
            username = data.get("username")
            password = data.get("password")
            
            if not username or not password:
                raise HTTPException(status_code=400, detail="Username and password required")
            
            try:
                user = self.auth_manager.authenticate_user(username, password)
                if not user:
                    raise HTTPException(status_code=401, detail="Invalid credentials")
                
                # Создаем токены
                access_token = self.auth_manager.create_access_token(user)
                refresh_token = self.auth_manager.create_refresh_token(user)
                
                # Создаем сессию
                session_id = self.auth_manager.create_session(user, request)
                
                response = {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "user": {
                        "username": user.username,
                        "email": user.email,
                        "is_admin": user.is_admin
                    }
                }
                
                return response
                
            except Exception as e:
                logger.error(f"Login error: {e}")
                raise HTTPException(status_code=500, detail="Authentication failed")
        
        @self.app.get("/admin/stats")
        async def get_admin_stats(current_user=Depends(get_current_user)):
            """Административная статистика."""
            stats = {}
            
            # Статистика кэша
            if self.template_engine:
                stats["cache"] = self.template_engine.get_cache_stats()
            
            # Статистика метрик
            if self.metrics and self.metrics.enabled:
                stats["metrics"] = {
                    "enabled": True,
                    "prometheus_endpoint": "/metrics"
                }
            
            # Статистика бэкапов
            if self.backup_manager:
                backups = await self.backup_manager.list_backups()
                stats["backups"] = {
                    "total_backups": len(backups),
                    "latest_backup": backups[0].timestamp.isoformat() if backups else None,
                    "backup_enabled": self.backup_manager.config.enabled
                }
            
            return stats
    
    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("🛑 Shutting down enhanced application...")
        
        if self.backup_scheduler:
            await stop_backup_scheduler()
            logger.info("💾 Backup scheduler stopped")
        
        if self.metrics and self.metrics.enabled:
            await stop_metrics_collection()
            logger.info("📊 Metrics collection stopped")
        
        logger.info("✅ Shutdown complete")

# Глобальный экземпляр
enhanced_app: Optional[EnhancedApplication] = None

async def get_enhanced_app() -> FastAPI:
    """Получает улучшенное приложение."""
    global enhanced_app
    if not enhanced_app:
        enhanced_app = EnhancedApplication()
    return await enhanced_app.create_app()

def create_production_app() -> FastAPI:
    """Создает production приложение."""
    import asyncio
    
    async def _create():
        return await get_enhanced_app()
    
    # Получаем или создаем event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_create())

# Alias для совместимости
create_enhanced_app = create_production_app

if __name__ == "__main__":
    import uvicorn
    
    # Настройки сервера
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8080'))
    https_port = int(os.getenv('HTTPS_PORT', '8443'))
    
    # SSL конфигурация
    ssl_config = get_uvicorn_ssl_config()
    
    if ssl_config:
        # Запуск с HTTPS
        logger.info(f"🔒 Starting HTTPS server on {host}:{https_port}")
        uvicorn.run(
            "src.enhanced_app:create_production_app",
            host=host,
            port=https_port,
            factory=True,
            **ssl_config
        )
    else:
        # Запуск с HTTP
        logger.info(f"🌐 Starting HTTP server on {host}:{port}")
        uvicorn.run(
            "src.enhanced_app:create_production_app",
            host=host,
            port=port,
            factory=True
        )