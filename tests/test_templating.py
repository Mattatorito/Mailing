#!/usr/bin/env python3

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.templating.engine import TemplateEngine, TemplateError, HTMLToTextParser


@pytest.fixture
def temp_template_dir():
    """Создает временную директорию для шаблонов."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Создаем несколько тестовых шаблонов
        template_path = Path(temp_dir)
        
        # Простой HTML шаблон
        (template_path / "simple.html").write_text(
            "<html><body>Hello, {{ name }}!</body></html>"
        )
        
        # Шаблон с переменными
        (template_path / "variables.html").write_text(
            "<html><body><h1>{{ title }}</h1><p>Dear {{ name }}, welcome to {{ company }}!</p></body></html>"
        )
        
        # Некорректный шаблон
        (template_path / "broken.html").write_text(
            "<html><body>{{ unclosed_variable</body></html>"
        )
        
        yield temp_dir


def test_template_engine_initialization():
    """Тестирует инициализацию движка шаблонов."""
    engine = TemplateEngine()
    assert engine.template_dir == "samples"
    
    engine_custom = TemplateEngine("custom_templates")
    assert engine_custom.template_dir == "custom_templates"


def test_html_to_text_parser():
    """Тестирует парсер HTML в текст."""
    parser = HTMLToTextParser()
    html_content = "<html><body><h1>Title</h1><p>Some text</p><br><div>More content</div></body></html>"
    
    parser.feed(html_content)
    text = parser.get_text()
    
    assert "Title" in text
    assert "Some text" in text
    assert "More content" in text
    assert "<h1>" not in text  # HTML теги должны быть удалены


def test_render_template_success(temp_template_dir):
    """Тестирует успешный рендеринг шаблона."""
    engine = TemplateEngine(temp_template_dir)
    
    result = engine.render_template("simple.html", {"name": "John Doe"})
    
    assert "Hello, John Doe!" in result
    assert "<html>" in result
    assert "<body>" in result


def test_render_template_with_variables(temp_template_dir):
    """Тестирует рендеринг шаблона с несколькими переменными."""
    engine = TemplateEngine(temp_template_dir)
    
    context = {
        "title": "Welcome",
        "name": "Alice",
        "company": "TechCorp"
    }
    
    result = engine.render_template("variables.html", context)
    
    assert "Welcome" in result
    assert "Dear Alice" in result
    assert "TechCorp" in result


def test_render_template_nonexistent(temp_template_dir):
    """Тестирует рендеринг несуществующего шаблона."""
    engine = TemplateEngine(temp_template_dir)
    
    with pytest.raises(TemplateError):
        engine.render_template("nonexistent.html", {})


def test_render_template_broken(temp_template_dir):
    """Тестирует рендеринг сломанного шаблона."""
    engine = TemplateEngine(temp_template_dir)
    
    with pytest.raises(TemplateError):
        engine.render_template("broken.html", {})


def test_render_string_success():
    """Тестирует рендеринг строкового шаблона."""
    engine = TemplateEngine()
    
    template_string = "Hello, {{ name }}! Your role is {{ role }}."
    context = {"name": "Bob", "role": "Developer"}
    
    result = engine.render_string(template_string, context)
    
    assert result == "Hello, Bob! Your role is Developer."


def test_render_string_empty_context():
    """Тестирует рендеринг с пустым контекстом."""
    engine = TemplateEngine()
    
    template_string = "Static content without variables"
    result = engine.render_string(template_string, {})
    
    assert result == "Static content without variables"


def test_render_method(temp_template_dir):
    """Тестирует основной метод render (возвращает tuple)."""
    engine = TemplateEngine(temp_template_dir)
    
    html_content, text_content = engine.render("simple.html", {"name": "Charlie"})
    
    # Проверяем HTML версию
    assert "Hello, Charlie!" in html_content
    assert "<html>" in html_content
    
    # Проверяем текстовую версию
    assert "Hello, Charlie!" in text_content
    assert "<html>" not in text_content  # HTML теги должны быть удалены


def test_html_to_text():
    """Тестирует конвертацию HTML в текст."""
    engine = TemplateEngine()
    
    html = "<html><body><h1>Title</h1><p>Paragraph 1</p><p>Paragraph 2</p></body></html>"
    text = engine.html_to_text(html)
    
    assert "Title" in text
    assert "Paragraph 1" in text
    assert "Paragraph 2" in text
    assert "<h1>" not in text
    assert "<p>" not in text


def test_preview_template(temp_template_dir):
    """Тестирует создание превью шаблона."""
    engine = TemplateEngine(temp_template_dir)
    
    sample_context = {"name": "Preview User"}
    preview = engine.preview_template("simple.html", sample_context)
    
    assert "html" in preview
    assert "text" in preview
    assert "preview_size" in preview
    
    assert "Preview User" in preview["html"]
    assert "Preview User" in preview["text"]
    assert isinstance(preview["preview_size"], int)
    assert preview["preview_size"] > 0


def test_validate_template_success(temp_template_dir):
    """Тестирует валидацию корректного шаблона."""
    engine = TemplateEngine(temp_template_dir)
    
    validation = engine.validate_template("simple.html")
    
    assert validation["valid"] == True
    assert "message" in validation
    assert "variables" in validation


def test_validate_template_broken(temp_template_dir):
    """Тестирует валидацию некорректного шаблона."""
    engine = TemplateEngine(temp_template_dir)
    
    validation = engine.validate_template("broken.html")
    
    assert validation["valid"] == False
    assert "message" in validation
    assert validation["variables"] == []


def test_validate_template_nonexistent(temp_template_dir):
    """Тестирует валидацию несуществующего шаблона."""
    engine = TemplateEngine(temp_template_dir)
    
    validation = engine.validate_template("nonexistent.html")
    
    assert validation["valid"] == False
    assert "message" in validation


def test_template_error_exception():
    """Тестирует исключение TemplateError."""
    error = TemplateError("Test error message")
    assert str(error) == "Test error message"
    assert isinstance(error, Exception)


def test_engine_with_autoescape(temp_template_dir):
    """Тестирует автоэскейпинг HTML."""
    engine = TemplateEngine(temp_template_dir)
    
    # Создаем шаблон с потенциально опасным содержимым
    template_path = Path(temp_template_dir) / "escape_test.html"
    template_path.write_text("<div>{{ user_input }}</div>")
    
    dangerous_input = "<script>alert('xss')</script>"
    result = engine.render_template("escape_test.html", {"user_input": dangerous_input})
    
    # Проверяем что опасный контент был экранирован
    assert "&lt;script&gt;" in result
    assert "<script>" not in result


def test_render_with_missing_variables(temp_template_dir):
    """Тестирует рендеринг с отсутствующими переменными."""
    engine = TemplateEngine(temp_template_dir)
    
    # Рендерим шаблон с переменными, но передаем неполный контекст
    result = engine.render_template("variables.html", {"name": "John"})
    
    # Jinja2 должен обработать отсутствующие переменные как пустые строки
    assert "Dear John" in result
    # title и company должны быть пустыми или обработаны как undefined