#!/usr/bin/env python3
"""
HTTPS конфигурация для production развертывания.
Поддерживает SSL/TLS сертификаты и безопасные настройки.
"""

import ssl
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class HTTPSConfig:
    """Конфигурация HTTPS."""
    enabled: bool = False
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    ca_file: Optional[str] = None
    verify_mode: int = ssl.CERT_NONE
    check_hostname: bool = False
    ssl_version: int = ssl.PROTOCOL_TLS_SERVER

def create_ssl_context(config: HTTPSConfig) -> Optional[ssl.SSLContext]:
    """Создает SSL контекст для HTTPS."""
    if not config.enabled:
        return None
        
    context = ssl.SSLContext(config.ssl_version)
    
    # Настройки безопасности
    context.check_hostname = config.check_hostname
    context.verify_mode = config.verify_mode
    
    # Загружаем сертификаты
    if config.cert_file and config.key_file:
        if not Path(config.cert_file).exists():
            raise FileNotFoundError(f"Certificate file not found: {config.cert_file}")
        if not Path(config.key_file).exists():
            raise FileNotFoundError(f"Key file not found: {config.key_file}")
            
        context.load_cert_chain(config.cert_file, config.key_file)
    
    # CA сертификат
    if config.ca_file and Path(config.ca_file).exists():
        context.load_verify_locations(config.ca_file)
    
    # Настройки cipher suites для безопасности
    context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
    
    return context

def load_https_config() -> HTTPSConfig:
    """Загружает HTTPS конфигурацию из переменных окружения."""
    return HTTPSConfig(
        enabled=os.getenv('HTTPS_ENABLED', 'false').lower() == 'true',
        cert_file=os.getenv('SSL_CERT_FILE', '/app/certs/cert.pem'),
        key_file=os.getenv('SSL_KEY_FILE', '/app/certs/key.pem'),
        ca_file=os.getenv('SSL_CA_FILE'),
        verify_mode=ssl.CERT_REQUIRED if os.getenv('SSL_VERIFY_CLIENT', 'false').lower() == 'true' else ssl.CERT_NONE,
        check_hostname=os.getenv('SSL_CHECK_HOSTNAME', 'false').lower() == 'true'
    )

def get_uvicorn_ssl_config() -> Dict[str, Any]:
    """Возвращает SSL конфигурацию для uvicorn."""
    config = load_https_config()
    
    if not config.enabled:
        return {}
    
    ssl_config = {}
    
    if config.cert_file and config.key_file:
        ssl_config['ssl_certfile'] = config.cert_file
        ssl_config['ssl_keyfile'] = config.key_file
    
    if config.ca_file:
        ssl_config['ssl_ca_certs'] = config.ca_file
    
    # SSL версия и cipher suites
    ssl_config['ssl_version'] = ssl.PROTOCOL_TLS_SERVER
    ssl_config['ssl_ciphers'] = 'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS'
    
    return ssl_config

# Middleware для принудительного HTTPS redirect
async def https_redirect_middleware(request, call_next):
    """Middleware для редиректа HTTP -> HTTPS."""
    if (
        os.getenv('FORCE_HTTPS', 'false').lower() == 'true' and 
        request.url.scheme == 'http' and 
        request.headers.get('x-forwarded-proto') != 'https'
    ):
        # Редирект на HTTPS
        https_url = request.url.replace(scheme='https')
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=str(https_url), status_code=301)
    
    response = await call_next(request)
    
    # Добавляем security headers
    if os.getenv('ADD_SECURITY_HEADERS', 'true').lower() == 'true':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    
    return response