#!/usr/bin/env python3
"""
Улучшенный движок шаблонов с кэшированием для повышения производительности.
Заменяет существующий engine.py с добавлением кэширования.
"""

import os
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
import html
import re
import bleach
from html.parser import HTMLParser

from jinja2 import Environment, FileSystemLoader, Template, TemplateError, select_autoescape
from jinja2.exceptions import TemplateNotFound, TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment
import aiofiles

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Конфигурация кэширования шаблонов."""
    enabled: bool = True
    ttl_seconds: int = 3600  # 1 час
    max_cache_size: int = 1000  # Максимальное количество кэшированных шаблонов
    memory_cache_enabled: bool = True
    file_watch_enabled: bool = True  # Отслеживание изменений файлов

@dataclass
class CacheEntry:
    """Запись в кэше шаблонов."""
    template: Template
    content_hash: str
    created_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    file_mtime: Optional[float] = None  # Время модификации файла

class HTMLToTextParser(HTMLParser):
    """Внутренний HTML парсер для извлечения текста из HTML."""
    
    def __init__(self):
        super().__init__()
        self.text_content = []
    
    def handle_data(self, data):
        """Обрабатывает текстовые данные."""
        self.text_content.append(data.strip())
    
    def get_text(self) -> str:
        """Возвращает извлеченный текст."""
        return '\n'.join(filter(None, self.text_content))

class TemplateCache:
    """Кэш шаблонов с поддержкой TTL и LRU."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # Для LRU
        self._lock = asyncio.Lock()
    
    async def get(self, template_path: str, content_hash: str, file_mtime: Optional[float] = None) -> Optional[Template]:
        """Получает шаблон из кэша."""
        if not self.config.enabled or not self.config.memory_cache_enabled:
            return None
        
        async with self._lock:
            entry = self._memory_cache.get(template_path)
            
            if not entry:
                return None
            
            # Проверяем TTL
            if datetime.now() - entry.created_at > timedelta(seconds=self.config.ttl_seconds):
                del self._memory_cache[template_path]
                self._access_order.remove(template_path)
                return None
            
            # Проверяем изменение файла
            if (self.config.file_watch_enabled and 
                file_mtime and 
                entry.file_mtime and 
                file_mtime > entry.file_mtime):
                del self._memory_cache[template_path]
                self._access_order.remove(template_path)
                return None
            
            # Проверяем хеш контента
            if entry.content_hash != content_hash:
                del self._memory_cache[template_path]
                self._access_order.remove(template_path)
                return None
            
            # Обновляем статистику доступа
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            
            # Перемещаем в конец для LRU
            self._access_order.remove(template_path)
            self._access_order.append(template_path)
            
            return entry.template
    
    async def put(self, template_path: str, template: Template, content_hash: str, file_mtime: Optional[float] = None):
        """Сохраняет шаблон в кэш."""
        if not self.config.enabled or not self.config.memory_cache_enabled:
            return
        
        async with self._lock:
            # Проверяем размер кэша
            if len(self._memory_cache) >= self.config.max_cache_size:
                # Удаляем старый элемент (LRU)
                oldest_key = self._access_order.pop(0)
                del self._memory_cache[oldest_key]
            
            # Создаем запись
            entry = CacheEntry(
                template=template,
                content_hash=content_hash,
                created_at=datetime.now(),
                file_mtime=file_mtime
            )
            
            self._memory_cache[template_path] = entry
            
            # Добавляем в порядок доступа
            if template_path in self._access_order:
                self._access_order.remove(template_path)
            self._access_order.append(template_path)
    
    async def clear(self):
        """Очищает весь кэш."""
        async with self._lock:
            self._memory_cache.clear()
            self._access_order.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кэша."""
        total_entries = len(self._memory_cache)
        total_accesses = sum(entry.access_count for entry in self._memory_cache.values())
        
        if self._memory_cache:
            avg_access_count = total_accesses / total_entries
            oldest_entry = min(self._memory_cache.values(), key=lambda e: e.created_at)
            newest_entry = max(self._memory_cache.values(), key=lambda e: e.created_at)
        else:
            avg_access_count = 0
            oldest_entry = newest_entry = None
        
        return {
            "total_entries": total_entries,
            "total_accesses": total_accesses,
            "avg_access_count": avg_access_count,
            "oldest_entry_age": (datetime.now() - oldest_entry.created_at).total_seconds() if oldest_entry else 0,
            "newest_entry_age": (datetime.now() - newest_entry.created_at).total_seconds() if newest_entry else 0,
            "max_cache_size": self.config.max_cache_size,
            "cache_utilization": (total_entries / self.config.max_cache_size) * 100
        }

class TemplateEngine:
    """Улучшенный движок шаблонов с кэшированием и безопасностью."""
    
    def __init__(self, templates_dir: str = None, cache_config: Optional[CacheConfig] = None):
        # Импорт настроек
        try:
            from src.mailing.config import settings
            self.templates_dir = Path(templates_dir or settings.templates_dir)
        except ImportError:
            self.templates_dir = Path(templates_dir or './templates')
        
        self.cache_config = cache_config or CacheConfig()
        self.cache = TemplateCache(self.cache_config)
        
        # Статистика для мониторинга
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "renders_total": 0,
            "errors_total": 0
        }
        
        # Настройка Jinja2 environment с безопасностью
        self.env = SandboxedEnvironment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            enable_async=True
        )
        
        # Ограничения для безопасности
        self.allowed_tags = {
            'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'div', 'span', 'ul', 'ol', 'li', 'a', 'img', 'table', 'tr', 'td', 'th',
            'thead', 'tbody', 'tfoot'
        }
        
        self.allowed_attributes = {
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'width', 'height'],
            '*': ['style', 'class']
        }
        
        # Добавляем кастомные фильтры
        self._add_custom_filters()
    
    def _add_custom_filters(self):
        """Добавляет кастомные фильтры в Jinja2."""
        
        def format_date(value, format='%Y-%m-%d'):
            """Форматирует дату."""
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value)
                except ValueError:
                    return value
            return value.strftime(format) if hasattr(value, 'strftime') else value
        
        def truncate_words(value, length=50):
            """Обрезает текст по словам."""
            words = str(value).split()
            if len(words) <= length:
                return value
            return ' '.join(words[:length]) + '...'
        
        def safe_email(value):
            """Безопасное отображение email (скрывает часть)."""
            if '@' not in str(value):
                return value
            local, domain = str(value).split('@', 1)
            if len(local) <= 2:
                return value
            return f"{local[:2]}***@{domain}"
        
        def sanitize_html(value):
            """Санитизация HTML."""
            return bleach.clean(str(value), tags=self.allowed_tags, attributes=self.allowed_attributes)
        
        self.env.filters['format_date'] = format_date
        self.env.filters['truncate_words'] = truncate_words
        self.env.filters['safe_email'] = safe_email
        self.env.filters['sanitize_html'] = sanitize_html
    
    async def render(self, template_name: str, variables: Dict[str, Any]) -> Tuple[str, str]:
        """Рендерит шаблон с кэшированием."""
        self.stats["renders_total"] += 1
        
        try:
            # Санитизация входных данных
            safe_variables = self._sanitize_variables(variables)
            
            # Получаем шаблон (с кэшированием)
            template = await self._get_template(template_name)
            
            # Рендерим HTML и текстовую версию
            html_content = await template.render_async(**safe_variables)
            
            # Дополнительная санитизация HTML
            html_content = bleach.clean(
                html_content, 
                tags=self.allowed_tags, 
                attributes=self.allowed_attributes
            )
            
            # Пытаемся найти текстовую версию шаблона
            text_template_name = template_name.replace('.html', '.txt')
            text_content = ""
            
            try:
                text_template = await self._get_template(text_template_name)
                text_content = await text_template.render_async(**safe_variables)
            except TemplateNotFound:
                # Создаем простую текстовую версию из HTML
                parser = HTMLToTextParser()
                parser.feed(html_content)
                text_content = parser.get_text()
            
            return html_content, text_content
            
        except Exception as e:
            self.stats["errors_total"] += 1
            logger.error(f"Template rendering error for {template_name}: {e}")
            raise TemplateError(f"Failed to render template {template_name}: {str(e)}")
    
    def _sanitize_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Санитизирует входные переменные."""
        safe_variables = {}
        
        for key, value in variables.items():
            # Санитизация ключа
            safe_key = re.sub(r'[^a-zA-Z0-9_]', '', str(key))
            
            # Санитизация значения
            if isinstance(value, str):
                # HTML escape для строк
                safe_value = html.escape(value)
                # Удаляем потенциально опасные символы
                safe_value = re.sub(r'[\r\n]', '', safe_value)
            elif isinstance(value, dict):
                # Рекурсивная санитизация для словарей
                safe_value = self._sanitize_variables(value)
            elif isinstance(value, list):
                # Санитизация списков
                safe_value = [self._sanitize_variables({0: item})[0] if isinstance(item, (dict, list)) 
                             else html.escape(str(item)) if isinstance(item, str) 
                             else item for item in value]
            else:
                safe_value = value
            
            safe_variables[safe_key] = safe_value
        
        return safe_variables
    
    async def _get_template(self, template_name: str) -> Template:
        """Получает шаблон с использованием кэша."""
        template_path = self.templates_dir / template_name
        
        # Получаем информацию о файле
        try:
            stat = template_path.stat()
            file_mtime = stat.st_mtime
        except FileNotFoundError:
            raise TemplateNotFound(template_name)
        
        # Читаем содержимое файла
        try:
            async with aiofiles.open(template_path, 'r', encoding='utf-8') as f:
                content = await f.read()
        except Exception as e:
            logger.error(f"Failed to read template {template_name}: {e}")
            raise TemplateError(f"Cannot read template file: {template_name}")
        
        # Вычисляем хеш содержимого
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        # Проверяем кэш
        cached_template = await self.cache.get(template_name, content_hash, file_mtime)
        
        if cached_template:
            self.stats["cache_hits"] += 1
            return cached_template
        
        # Кэш промах - компилируем шаблон
        self.stats["cache_misses"] += 1
        
        try:
            template = self.env.from_string(content)
            template.filename = str(template_path)  # Для отладки
            
            # Сохраняем в кэш
            await self.cache.put(template_name, template, content_hash, file_mtime)
            
            return template
            
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error in {template_name}: {e}")
            raise TemplateError(f"Syntax error in template {template_name}: {str(e)}")
    
    async def validate_template(self, template_name: str, sample_variables: Dict[str, Any]) -> Dict[str, Any]:
        """Валидирует шаблон с примерными данными."""
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "used_variables": [],
            "missing_variables": []
        }
        
        try:
            template = await self._get_template(template_name)
            
            # Анализируем используемые переменные
            from jinja2.meta import find_undeclared_variables
            template_source = self.env.parse(template.source)
            used_variables = find_undeclared_variables(template_source)
            result["used_variables"] = list(used_variables)
            
            # Проверяем отсутствующие переменные
            missing_variables = used_variables - set(sample_variables.keys())
            result["missing_variables"] = list(missing_variables)
            
            if missing_variables:
                result["warnings"].append(f"Missing variables: {', '.join(missing_variables)}")
            
            # Пробуем рендерить
            try:
                safe_variables = self._sanitize_variables(sample_variables)
                await template.render_async(**safe_variables)
                result["valid"] = True
            except Exception as render_error:
                result["errors"].append(f"Render error: {str(render_error)}")
            
        except TemplateNotFound:
            result["errors"].append(f"Template not found: {template_name}")
        except TemplateError as e:
            result["errors"].append(str(e))
        except Exception as e:
            result["errors"].append(f"Validation error: {str(e)}")
        
        return result
    
    async def list_templates(self) -> List[Dict[str, Any]]:
        """Возвращает список доступных шаблонов."""
        templates = []
        
        for template_file in self.templates_dir.rglob("*.html"):
            try:
                relative_path = template_file.relative_to(self.templates_dir)
                stat = template_file.stat()
                
                template_info = {
                    "name": str(relative_path),
                    "path": str(template_file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "is_cached": str(relative_path) in self.cache._memory_cache
                }
                
                templates.append(template_info)
                
            except Exception as e:
                logger.warning(f"Error reading template {template_file}: {e}")
        
        return sorted(templates, key=lambda t: t["name"])
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кэша."""
        cache_stats = self.cache.get_stats()
        
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_ratio = (self.stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **cache_stats,
            "hit_ratio": hit_ratio,
            "total_renders": self.stats["renders_total"],
            "total_errors": self.stats["errors_total"],
            "cache_enabled": self.cache_config.enabled
        }
    
    async def clear_cache(self):
        """Очищает кэш шаблонов."""
        await self.cache.clear()
        logger.info("Template cache cleared")
    
    async def preload_templates(self, template_names: Optional[List[str]] = None):
        """Предзагружает шаблоны в кэш."""
        if not template_names:
            templates = await self.list_templates()
            template_names = [t["name"] for t in templates]
        
        for template_name in template_names:
            try:
                await self._get_template(template_name)
                logger.debug(f"Preloaded template: {template_name}")
            except Exception as e:
                logger.warning(f"Failed to preload template {template_name}: {e}")
        
        logger.info(f"Preloaded {len(template_names)} templates")

# Глобальный экземпляр для использования в приложении
template_engine: Optional[TemplateEngine] = None

def get_template_engine() -> TemplateEngine:
    """Получает экземпляр движка шаблонов."""
    global template_engine
    if not template_engine:
        templates_dir = os.getenv('TEMPLATES_DIR', './templates')
        
        # Конфигурация кэширования
        cache_config = CacheConfig(
            enabled=os.getenv('TEMPLATE_CACHE_ENABLED', 'true').lower() == 'true',
            ttl_seconds=int(os.getenv('TEMPLATE_CACHE_TTL', '3600')),
            max_cache_size=int(os.getenv('TEMPLATE_CACHE_SIZE', '1000')),
            file_watch_enabled=os.getenv('TEMPLATE_FILE_WATCH', 'true').lower() == 'true'
        )
        
        template_engine = TemplateEngine(templates_dir, cache_config)
    
    return template_engine

# Обратная совместимость
class TemplateError(Exception):
    """Исключение для ошибок в работе с шаблонами."""
    pass