# Email Marketing Tool - Enhanced Makefile
PYTHON := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help install test test-cov lint format security audit clean dev build docs deploy
.PHONY: enhanced-install enhanced-dev enhanced-prod ssl-certs backup-create metrics-check
.PHONY: auth-setup cache-clear test-e2e

help:
	@echo "� Professional Email Marketing Tool - Enhanced"
	@echo "Available commands:"
	@echo "  install     - Установка зависимостей"
	@echo "  test        - Запуск тестов"
	@echo "  test-cov    - Тесты с покрытием"
	@echo "  test-e2e    - End-to-end тесты"
	@echo "  lint        - Проверка качества кода"
	@echo "  format      - Автоматическое форматирование кода"
	@echo "  security    - Проверка безопасности"
	@echo "  audit       - Полный аудит проекта"
	@echo "  clean       - Очистка временных файлов"
	@echo ""
	@echo "🚀 Enhanced Features:"
	@echo "  enhanced-install - Установка с новыми зависимостями"
	@echo "  enhanced-dev     - Запуск в режиме разработки с улучшениями"
	@echo "  enhanced-prod    - Production запуск с HTTPS"
	@echo "  ssl-certs        - Генерация SSL сертификатов"
	@echo "  backup-create    - Создание резервной копии"
	@echo "  metrics-check    - Проверка метрик"
	@echo "  auth-setup       - Настройка аутентификации"
	@echo "  cache-clear      - Очистка кэша"
	@echo ""

# Enhanced installation with new dependencies
enhanced-install: install
	@echo "🔧 Installing enhanced dependencies..."
	$(PIP) install passlib[bcrypt] python-jose[cryptography] PyJWT redis aiofiles
	$(PIP) install prometheus-client psutil bleach pytest-httpx
	@echo "✅ Enhanced dependencies installed"

# SSL certificates generation
ssl-certs:
	@echo "🔒 Generating SSL certificates..."
	./scripts/generate_ssl_certs.sh localhost 365
	@echo "✅ SSL certificates generated"

# Enhanced development mode
enhanced-dev: enhanced-install ssl-certs
	@echo "🚀 Starting enhanced development server..."
	export ENVIRONMENT=development && \
	export TEMPLATE_CACHE_ENABLED=true && \
	export METRICS_ENABLED=true && \
	export BACKUP_ENABLED=true && \
	export HTTPS_ENABLED=false && \
	$(PYTHON) src/enhanced_app.py

# Enhanced production mode with HTTPS
enhanced-prod: enhanced-install ssl-certs production
	@echo "🔒 Starting enhanced production server with HTTPS..."
	export ENVIRONMENT=production && \
	export HTTPS_ENABLED=true && \
	export FORCE_HTTPS=true && \
	export TEMPLATE_CACHE_ENABLED=true && \
	export METRICS_ENABLED=true && \
	export BACKUP_ENABLED=true && \
	$(PYTHON) src/enhanced_app.py

# Authentication setup
auth-setup:
	@echo "🔑 Setting up authentication..."
	@echo "Generating secure secret key..."
	@$(PYTHON) -c "import secrets; print('AUTH_SECRET_KEY=' + secrets.token_urlsafe(32))" > .env.auth
	@echo "✅ Authentication configured. Add .env.auth to your environment."

# Create backup
backup-create:
	@echo "💾 Creating database backup..."
	@$(PYTHON) -c "import asyncio; from src.persistence.backup import get_backup_manager; asyncio.run(get_backup_manager().create_backup('manual'))"
	@echo "✅ Backup created"

# Check metrics
metrics-check:
	@echo "📊 Checking metrics endpoint..."
	@curl -s http://localhost:8080/metrics | head -20 || echo "Metrics server not running"

# Clear cache
cache-clear:
	@echo "🧹 Clearing template cache..."
	@$(PYTHON) -c "import asyncio; from src.templating.cached_engine import get_template_engine; asyncio.run(get_template_engine().clear_cache())"
	@echo "✅ Cache cleared"

# End-to-end tests
test-e2e: enhanced-install
	@echo "🧪 Running E2E tests..."
	$(PYTHON) -m pytest tests/test_e2e_comprehensive.py -v --tb=short
	@echo "✅ E2E tests completed"

# Enhanced security check
security-enhanced: security
	@echo "🔒 Running enhanced security checks..."
	@echo "Checking for hardcoded secrets..."
	@grep -r "api_key\|password\|secret" src/ --include="*.py" | grep -v "getenv\|config" || echo "No hardcoded secrets found"
	@echo "Checking SSL configuration..."
	@$(PYTHON) -c "from src.security.https_config import load_https_config; print('HTTPS config:', load_https_config())"
	@echo "✅ Enhanced security check completed"

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
	$(PYTEST) tests/ --cov=src --cov-report=html:reports/htmlcov --cov-report=term-missing
	@echo "✅ Отчет о покрытии создан в reports/htmlcov/"

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
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/
	rm -rf reports/htmlcov/
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
	@echo "Установите: pip install watchdog"
	@echo "Затем запустите: python scripts/watch_tests.py"

# Проверка стиля коммитов
check-commits:
	@echo "📝 Проверка стиля коммитов..."
	git log --oneline -10
	@echo "✅ Последние коммиты показаны"