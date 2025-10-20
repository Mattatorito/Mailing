#!/usr/bin/env python3

from __future__ import annotations
from typing import Dict, Any, Optional
import re
import html
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from html.parser import HTMLParser


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


class TemplateEngine:
    """Движок для обработки HTML и текстовых шаблонов."""
    
    def __init__(self, template_dir: str = "samples"):
        """Инициализирует движок."""
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """Рендерит шаблон с переданным контекстом."""
        try:
            template = self.env.get_template(template_path)
            return template.render(**context)
        except Exception as e:
            raise TemplateError(f"Ошибка рендеринга шаблона {template_path}: {e}")
    
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """Рендерит строковый шаблон."""
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)
        except Exception as e:
            raise TemplateError(f"Ошибка рендеринга строкового шаблона: {e}")
    
    def html_to_text(self, html_content: str) -> str:
        """Конвертирует HTML в простой текст."""
        parser = HTMLToTextParser()
        parser.feed(html_content)
        return parser.get_text()
    
    def preview_template(self, template_path: str, sample_context: Dict[str, Any]) -> Dict[str, str]:
        """Создает превью шаблона с примерными данными."""
        html_content = self.render_template(template_path, sample_context)
        text_content = self.html_to_text(html_content)
        
        return {
            'html': html_content,
            'text': text_content,
            'preview_size': len(html_content)
        }
    
    def validate_template(self, template_path: str) -> Dict[str, Any]:
        """Проверяет корректность шаблона."""
        try:
            template = self.env.get_template(template_path)
            
            # Получаем список переменных в шаблоне
            variables = list(template.new_context().get_exported())
            
            return {
                'valid': True,
                'variables': variables,
                'message': 'Шаблон корректен'
            }
        except Exception as e:
            return {
                'valid': False,
                'variables': [],
                'message': str(e)
            }


class TemplateError(Exception):
    """Исключение для ошибок шаблонизации."""
    pass
