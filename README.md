# 📧 Professional Email Marketing Tool

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 🚀 Описание

Профессиональный инструмент для массовой email рассылки с современным веб-интерфейсом и мощными возможностями автоматизации.

### ✨ Основные возможности

- 📧 **Массовая email рассылка** через Resend API
- 🌐 **Современный веб-интерфейс** - удобное управление через браузер  
- 📊 **Аналитика и статистика** - детальные отчеты о доставке
- 🎨 **Шаблоны Jinja2** - гибкая настройка содержимого писем
- 📁 **Множественные форматы данных** - CSV, Excel, JSON
- 🚀 **Высокая производительность** - асинхронная обработка
- 🔄 **Retry механизм** - автоматические повторы при ошибках
- 📈 **Rate limiting** - соблюдение лимитов провайдера
- 💾 **База данных SQLite** - хранение истории и статистики
- 🔒 **Безопасность** - валидация email адресов

## 🖥️ Интерфейсы

### 1. Веб-интерфейс (Рекомендуется)
- Современный responsive дизайн
- Интуитивно понятный интерфейс
- Работает в любом браузере
- Не требует установки дополнительных GUI библиотек

### 2. Command Line Interface (CLI)
- Полнофункциональный интерфейс командной строки
- Идеален for автоматизации и скриптов
- Подробная справочная система

### 3. Desktop GUI (Qt-based)
- Нативное desktop приложение
- Полнофункциональный интерфейс
- Поддержка drag & drop

## 📦 Быстрый старт

### Установка

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

## 🎯 Форматы файлов

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

## 📊 Аналитика

Инструмент предоставляет детальную аналитику:

- ✅ **Успешные отправки** - количество доставленных писем
- ❌ **Ошибки доставки** - failed deliveries с причинами
- 📈 **Статистика по времени** - производительность рассылки
- 💾 **История кампаний** - архив всех рассылок
- 📋 **Детальные логи** - для отладки и аудита

## 🔧 Системные требования

- **Python**: 3.9+
- **ОС**: Windows, macOS, Linux
- **RAM**: 512MB (для больших списков - больше)
- **Диского место**: 100MB
- **Интернет**: Стабильное подключение

## 📝 Лицензия

MIT License - свободное использование для коммерческих целей.

## 🆘 Поддержка

- 📖 **Документация**: Полная документация в README
- 💡 **Примеры**: Готовые примеры в папке `samples/`
- 🔧 **CLI справка**: `python -m mailing.cli --help`

## 🔄 Обновления

### v1.0.0
- ✨ Веб-интерфейс
- 📧 Resend API интеграция
- 📊 Система аналитики
- 🎨 Jinja2 шаблоны
- 📁 Множественные форматы данных

---

**Создано с ❤️ для эффективного email маркетинга**