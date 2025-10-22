# Professional Email Marketing Platform

![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)
![Tests](https://img.shields.io/badge/tests-417%20passed-brightgreen)

## Overview

Enterprise-grade email marketing platform built with modern Python architecture. Delivers high-performance mass email campaigns with comprehensive analytics, advanced templating, and robust security features.

### Core Features

- **📧 Mass Email Delivery** - High-throughput campaign processing via Resend API
- **🌐 Modern Web Interface** - Responsive dashboard with real-time analytics  
- **Advanced Analytics** - Comprehensive delivery tracking and performance metrics
- **🎨 Template Engine** - Powerful Jinja2-based email templating system
- **📁 Multi-format Support** - CSV, Excel, JSON data source integration
- **Async Processing** - High-performance concurrent email delivery
- **🔄 Intelligent Retry** - Exponential backoff with circuit breaker protection
- **📈 Rate Limiting** - Advanced throttling and quota management
- **💾 Data Persistence** - SQLite-based delivery tracking and analytics
- **Security First** - Comprehensive input validation and injection protection

## Architecture

### System Components

#### 1. Web Interface (Primary)
- Modern responsive design with Material-UI components
- Real-time campaign monitoring and analytics dashboard
- Cross-platform compatibility with zero client-side dependencies

#### 2. Command Line Interface
- Full-featured CLI with comprehensive automation support
- Pipeline-friendly with JSON output formats
- Extensive help system and configuration validation

#### 3. Desktop Application
- Native Qt-based application with advanced GUI features
- Drag-and-drop file handling and visual campaign builder
- Offline capability with synchronized cloud operations

## Quick Start

### System Requirements

- Python 3.10+ (recommended: 3.11)
- 2GB RAM minimum (4GB recommended for large campaigns)
- 1GB disk space for application and logs
- Network connectivity for API operations

### Installation

```bash
# Создайте виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или .venv\\Scripts\\activate  # Windows

# Установите зависимости
pip install -r requirements.txt
```

### Настройка

1. **Скопируйте файл конфигурации:**
   ```bash
   cp .env.example .env
   ```

2. **Настройте API ключ Resend:**
   ```bash
   # Откройте .env и добавьте ваш API ключ
   RESEND_API_KEY=your_api_key_here
   SENDER_EMAIL=noreply@yourdomain.com
   ```

### Запуск

```bash
# Веб-интерфейс (рекомендуется)
python run_gui.py

# CLI версия
python -m mailing.cli --help

# Прямой запуск веб-интерфейса
python minimal_web_gui.py
```

## 📋 Использование

### Веб-интерфейс

1. Запустите `python run_gui.py`
2. Откройте http://localhost:5001 в браузере
3. Загрузите файл получателей (CSV/Excel/JSON)
4. Выберите шаблон письма
5. Настройте тему и параметры
6. Запустите рассылку

### CLI

```bash
# Тестовая рассылка
python -m mailing.cli --file samples/recipients.csv --template template.html --subject "Test Campaign" --dry-run

# Реальная рассылка
python -m mailing.cli --file recipients.csv --template newsletter.html --subject "Monthly Newsletter"

# С настройкой параллельности
python -m mailing.cli --file large_list.csv --template promo.html --subject "Special Offer" --concurrency 5
```

## Форматы файлов

### Recipients (Получатели)

**CSV формат:**
```csv
email,name,company
john@example.com,John Doe,Acme Corp
jane@example.com,Jane Smith,Tech Inc
```

**JSON формат:**
```json
[
  {"email": "john@example.com", "name": "John Doe", "company": "Acme Corp"},
  {"email": "jane@example.com", "name": "Jane Smith", "Tech Inc"}
]
```

### Templates (Шаблоны)

**HTML с Jinja2:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ subject }}</title>
</head>
<body>
    <h1>Привет, {{ name }}!</h1>
    <p>Специальное предложение для {{ company }}...</p>
</body>
</html>
```

## ⚙️ Конфигурация

Основные параметры в `.env`:

```bash
# Resend API
RESEND_API_KEY=your_resend_api_key
SENDER_EMAIL=noreply@yourdomain.com

# Лимиты
CONCURRENCY=3
DAILY_QUOTA=1000

# Логирование
LOG_LEVEL=INFO
DEBUG=false
```

## Аналитика

Инструмент предоставляет детальную аналитику:

- **Успешные отправки** - количество доставленных писем
- **Ошибки доставки** - failed deliveries с причинами
- 📈 **Статистика по времени** - производительность рассылки
- 💾 **История кампаний** - архив всех рассылок
- 📋 **Детальные логи** - для отладки и аудита

## 🔧 Системные требования

- **Python**: 3.9+
- **ОС**: Windows, macOS, Linux
- **RAM**: 512MB (для больших списков - больше)
- **Диского место**: 100MB
- **Интернет**: Стабильное подключение

## Лицензия

MIT License - свободное использование для коммерческих целей.

## 🆘 Поддержка

- 📖 **Документация**: Полная документация в README
- **Примеры**: Готовые примеры в папке `samples/`
- **CLI справка**: `python -m mailing.cli --help`

## Обновления

### v1.0.0
- Веб-интерфейс
- Resend API интеграция
- Система аналитики
- Jinja2 шаблоны
- Множественные форматы данных

---

**Создано для эффективного email маркетинга**