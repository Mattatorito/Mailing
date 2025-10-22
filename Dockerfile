# Multi-stage Docker build для Professional Email Marketing Tool
# Поддерживает как production так и development окружения

FROM python:3.11-slim as base

# Метаданные
LABEL maintainer="Email Marketing Tool Team"
LABEL version="1.0.0"
LABEL description="Professional Email Marketing Tool with webhook support"

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN groupadd -r mailuser && useradd -r -g mailuser mailuser

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt pyproject.toml ./

# Development stage
FROM base as development

# Устанавливаем дополнительные dev зависимости
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-asyncio \
    black \
    flake8 \
    mypy \
    isort \
    pre-commit \
    bandit

# Копируем весь код
COPY . .

# Устанавливаем права
RUN chown -R mailuser:mailuser /app
USER mailuser

# Экспонируем порты
EXPOSE 8080 5000

# Команда по умолчанию для разработки
CMD ["python", "-m", "pytest", "--cov=mailing", "--cov-report=html"]

# Production stage
FROM base as production

# Устанавливаем только production зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только необходимые файлы для production (используем .dockerignore для исключения)
COPY src/ ./src/
COPY samples/ ./samples/
COPY pyproject.toml VERSION ./

# Создаем необходимые директории
RUN mkdir -p logs data

# Устанавливаем права
RUN chown -R mailuser:mailuser /app
USER mailuser

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Проверяем здоровье приложения
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Экспонируем порт для webhook сервера
EXPOSE 8080

# Команда по умолчанию для production
CMD ["python", "-m", "mailing.webhook_server"]

# Testing stage
FROM development as testing

# Запускаем тесты
RUN python -m pytest --cov=mailing --cov-report=term-missing

# CLI stage для запуска CLI команд
FROM production as cli

# Переопределяем команду для CLI использования
ENTRYPOINT ["python", "-m", "mailing.cli"]