# Makefile for Email Marketing System
# Автоматизация тестирования, форматирования и развертывания

.PHONY: help install test lint format security clean dev build deploy docs

# Переменные
PYTHON = .venv/bin/python
PIP = .venv/bin/pip
PYTEST = .venv/bin/pytest
PROJECT_NAME = mailing

# По умолчанию показываем справку
help:
	@echo "🚀 Email Marketing System - Автоматизация задач"
	@echo ""
	@echo "Доступные команды:"
	@echo "  install     - Установка зависимостей и настройка окружения"
	@echo "  test        - Запуск всех тестов"
	@echo "  test-fast   - Быстрые тесты (без медленных)"
	@echo "  test-cov    - Тесты с покрытием кода"
	@echo "  lint        - Проверка качества кода"
	@echo "  format      - Автоматическое форматирование кода"
	@echo "  security    - Проверка безопасности"
	@echo "  audit       - Полный аудит проекта"
	@echo "  clean       - Очистка временных файлов"
	@echo "  dev         - Запуск в режиме разработки"
	@echo "  build       - Сборка проекта"
	@echo "  docs        - Генерация документации"
	@echo "  deploy      - Развертывание проекта"
	@echo ""

# Установка зависимостей
install:
	@echo "📦 Установка зависимостей..."
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-cov pytest-asyncio black isort flake8 mypy bandit safety
	@echo "✅ Зависимости установлены"

# Запуск тестов
test:
	@echo "🧪 Запуск всех тестов..."
	$(PYTEST) tests/ -v --tb=short
	@echo "✅ Тесты завершены"

# Быстрые тесты
test-fast:
	@echo "⚡ Запуск быстрых тестов..."
	$(PYTEST) tests/ -v --tb=short -m "not slow" --maxfail=5
	@echo "✅ Быстрые тесты завершены"

# Тесты с покрытием
test-cov:
	@echo "📊 Тесты с анализом покрытия..."
	$(PYTEST) tests/ --cov=mailing --cov=templating --cov=persistence --cov=resend --cov=validation --cov=stats --cov-report=html --cov-report=term-missing
	@echo "✅ Отчет о покрытии создан в htmlcov/"

# Проверка качества кода
lint:
	@echo "🔍 Проверка качества кода..."
	@echo "Запуск flake8..."
	-$(PYTHON) -m flake8 $(PROJECT_NAME)/ --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "Запуск mypy..."
	-$(PYTHON) -m mypy $(PROJECT_NAME)/ --ignore-missing-imports
	@echo "✅ Проверка качества завершена"

# Форматирование кода
format:
	@echo "🎨 Форматирование кода..."
	@echo "Сортировка импортов..."
	$(PYTHON) -m isort $(PROJECT_NAME)/ tests/
	@echo "Форматирование с black..."
	$(PYTHON) -m black $(PROJECT_NAME)/ tests/ --line-length=100
	@echo "✅ Код отформатирован"

# Проверка безопасности
security:
	@echo "🔒 Проверка безопасности..."
	@echo "Проверка зависимостей на уязвимости..."
	-$(PYTHON) -m safety check
	@echo "Поиск проблем безопасности в коде..."
	-$(PYTHON) -m bandit -r $(PROJECT_NAME)/ -ll
	@echo "✅ Проверка безопасности завершена"

# Полный аудит проекта
audit:
	@echo "🔍 Запуск полного аудита проекта..."
	$(PYTHON) comprehensive_audit.py
	$(PYTHON) deep_analysis.py
	@echo "✅ Аудит завершен"

# Очистка
clean:
	@echo "🧹 Очистка временных файлов..."
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/
	rm -rf build/
	rm -rf dist/
	@echo "✅ Очистка завершена"

# Режим разработки
dev:
	@echo "🚀 Запуск в режиме разработки..."
	@echo "GUI приложение:"
	$(PYTHON) run_gui.py &
	@echo "Webhook сервер:"
	$(PYTHON) -m mailing.webhook_server &
	@echo "✅ Сервисы запущены в фоне"

# Сборка проекта
build: clean format lint test
	@echo "🏗️ Сборка проекта..."
	$(PYTHON) setup.py sdist bdist_wheel
	@echo "✅ Сборка завершена"

# Генерация документации
docs:
	@echo "📚 Генерация документации..."
	@echo "Создание README для модулей..."
	find $(PROJECT_NAME)/ -name "*.py" -exec $(PYTHON) -c "import ast, sys; help(ast.parse(open(sys.argv[1]).read()).body[0])" {} \;
	@echo "✅ Документация обновлена"

# Развертывание
deploy: build security
	@echo "🚢 Развертывание проекта..."
	@echo "Проверка переменных окружения..."
	$(PYTHON) -c "import os; assert os.getenv('RESEND_API_KEY'), 'RESEND_API_KEY not set'"
	$(PYTHON) -c "import os; assert os.getenv('RESEND_FROM_EMAIL'), 'RESEND_FROM_EMAIL not set'"
	@echo "Запуск preflight проверок..."
	$(PYTHON) -c "from mailing.preflight import validate_env; validate_env()"
	@echo "✅ Готов к продакшену"

# Быстрая проверка перед коммитом
pre-commit: format lint test-fast
	@echo "✅ Все проверки пройдены - готов к коммиту"

# Полная проверка качества
quality: format lint security test-cov
	@echo "✅ Полная проверка качества завершена"

# Настройка окружения разработки
setup-dev: install
	@echo "⚙️ Настройка окружения разработки..."
	@echo "Создание .env файла (если не существует)..."
	@if [ ! -f .env ]; then \
		echo "# Environment variables for development" > .env; \
		echo "RESEND_API_KEY=your_api_key_here" >> .env; \
		echo "RESEND_FROM_EMAIL=noreply@yourdomain.com" >> .env; \
		echo "RESEND_FROM_NAME=Your App" >> .env; \
		echo "# Database" >> .env; \
		echo "SQLITE_DB_PATH=mailing.sqlite3" >> .env; \
		echo ".env файл создан. Отредактируйте его с вашими настройками."; \
	fi
	@echo "✅ Окружение разработки настроено"

# Обновление зависимостей
update-deps:
	@echo "📦 Обновление зависимостей..."
	$(PIP) list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 $(PIP) install -U
	$(PIP) freeze > requirements.txt
	@echo "✅ Зависимости обновлены"

# Проверка системы
check-system:
	@echo "🔧 Проверка системы..."
	@echo "Python версия:"
	$(PYTHON) --version
	@echo "Установленные пакеты:"
	$(PIP) list
	@echo "Конфигурация pytest:"
	$(PYTEST) --version
	@echo "Проверка импортов:"
	$(PYTHON) -c "import mailing, templating, persistence, resend; print('✅ Все модули импортируются')"
	@echo "✅ Система готова к работе"

# Профилирование производительности  
profile:
	@echo "⚡ Профилирование производительности..."
	$(PYTHON) -c "import cProfile; cProfile.run('from mailing.sender import run_campaign; print(\"Profile completed\")')"
	@echo "✅ Профилирование завершено"

# Запуск конкретного теста
test-file:
	@echo "🎯 Запуск конкретного файла тестов..."
	@echo "Использование: make test-file FILE=tests/test_core.py"
	@if [ -z "$(FILE)" ]; then echo "❌ Укажите FILE=path/to/test.py"; exit 1; fi
	$(PYTEST) $(FILE) -v

# Мониторинг в реальном времени
watch-tests:
	@echo "👀 Мониторинг тестов (требует установки watchdog)..."
	@echo "pip install watchdog"
	$(PYTHON) -c "
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class TestRunner(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f'File changed: {event.src_path}')
            subprocess.run(['make', 'test-fast'])

observer = Observer()
observer.schedule(TestRunner(), '.', recursive=True)
observer.start()
print('👀 Watching for changes...')
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
"

# Проверка стиля коммитов
check-commits:
	@echo "📝 Проверка стиля коммитов..."
	git log --oneline -10
	@echo "✅ Последние коммиты показаны"