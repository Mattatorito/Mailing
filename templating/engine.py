from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

from html.parser import HTMLParser
from jinja2 import Environment, FileSystemLoader, select_autoescape

from mailing.models import TemplateRender

"""
Email Template Rendering Engine

Этот модуль предоставляет движок для рендеринга email шаблонов с использованием Jinja2.
Поддерживает HTML шаблоны с автоматической генерацией текстовой версии."""


class _Stripper(HTMLParser):
    """Внутренний HTML парсер для извлечения текста из HTML.

    Используется для автоматической генерации текстовой версии
    email сообщений из HTML шаблонов.
    """

    def __init__(self) -> None:
        """Инициализирует HTML stripper."""
        super().__init__()
        self._text: list[str] = []

    def handle_data(self, data: str) -> None:
        """Обрабатывает текстовые данные из HTML.

        Args:
            data: Текстовый контент из HTML тега
        """
        if data:
            self._text.append(data)

    def get_text(self) -> str:
        """Возвращает извлеченный текст из HTML.

        Returns:
            str: Очищенный текст без HTML тегов
        """
        return " ".join(s.strip() for s in self._text if s.strip())


class TemplateEngine:
    """Движок для рендеринга email шаблонов на основе Jinja2.

    Поддерживает загрузку шаблонов из файлов или директорий,
    автоматическое экранирование HTML и генерацию текстовых версий.

    Attributes:
        templates_dir: Директория с шаблонами
        env: Jinja2 Environment для рендеринга"""

    def __init__(self, templates_dir: str | None = None) -> None:
        """Инициализирует template engine.

        Args:
            templates_dir: Путь к директории с шаблонами (по умолчанию ./samples)
        """
        self.templates_dir = templates_dir or str(Path.cwd() / "samples")
        self.env = Environment(
            loader = FileSystemLoader(self.templates_dir),
                autoescape = select_autoescape(["html","xml"]),
        )

    def render(self, template_name: str, variables: Dict[str, Any]) -> TemplateRender:
        """Рендерит email шаблон с переданными переменными.

        Поддерживает два режима загрузки шаблонов:
        1. Относительный путь - загрузка из templates_dir
        2. Абсолютный путь - прямое чтение файла

        Автоматически генерирует текстовую версию из HTML для лучшей доставляемости.

        Args:
            template_name: Имя шаблона или путь к файлу
            variables: Словарь переменных для подстановки в шаблон

        Returns:
            TemplateRender: Объект с отрендеренными subject, HTML и текстовой версией

        Raises:
            FileNotFoundError: Если файл шаблона не найден
            jinja2.TemplateError: При ошибках в синтаксисе шаблона

        Example:
            engine = TemplateEngine()
            render = engine.render('welcome.html', {
                'subject': 'Welcome!',
                'name': 'John',
                'url': 'https://example.com'
            })
            print(render.subject)     # 'Welcome!'
            print(render.body_html)   # '<h1>Hello John!</h1>...'
            print(render.body_text)   # 'Hello John!...'
        """
        # Если передан полный путь к файлу, читаем его напрямую
        if template_name.startswith("/") or "\\" in template_name:
            template_path = Path(template_name)
            if template_path.exists():
                template_content = template_path.read_text(encoding="utf-8")
                tmpl = self.env.from_string(template_content)
            else:
                raise FileNotFoundError(f"Template file not found: {template_name}")
        else:
            # Обычная загрузка из директории шаблонов
            tmpl = self.env.get_template(template_name)

        # Извлекаем subject из переменных (поддержка разных регистров)
        subject = variables.get("subject") or variables.get("Subject") or "No subject"

        # Рендерим HTML версию
        body_html = tmpl.render(**variables)

        # Генерируем текстовую версию из HTML для лучшей доставляемости
        stripper = _Stripper()
        stripper.feed(body_html)
        body_text = stripper.get_text() or None

        return TemplateRender(subject=subject, body_html=body_html, body_text=body_text)

    def render_string(self, template_string: str, variables: Dict[str, Any]) -> str:
        """Рендерит строку шаблона с переменными.

        Args:
            template_string: Строка шаблона
            variables: Словарь переменных для подстановки

        Returns:
            str: Отрендеренная строка
        """
        tmpl = self.env.from_string(template_string)
        return tmpl.render(**variables)
