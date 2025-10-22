# 📦 Инструкция по установке# 📦 Инструкция по установке



## 🚀 Быстрая установка## 🚀 Быстрая установка



### 1. Системные требования### 1. Системные требования



- **Python 3.10+** (Проверьте: `python --version`)- **Python 3.10+** (Проверьте: `python --version`)

- **200 МБ** свободного места на диске- **200 МБ** свободного места на диске

- **Интернет соединение** для API доступа- **Интернет соединение** для API доступа



### 2. Подготовка окружения### 2. Подготовка окружения



```bash```bash

# Создание виртуального окружения# Создание виртуального окружения

python -m venv .venvpython -m venv .venv



# Активация окружения# Активация окружения

# macOS/Linux:# macOS/Linux:

source .venv/bin/activatesource .venv/bin/activate



# Windows:# Windows:

.venv\Scripts\activate.venv\Scripts\activate

``````



### 3. Установка зависимостей### 3. Установка зависимостей



```bash```bash

pip install -r requirements.txtpip install -r requirements.txt

``````



### 4. Конфигурация



```bash```bash### 4. Настройка API ключей

# Скопируйте файл с примером настроек

cp .env.example .env# Копирование файла конфигурации

```

cp .env.example .env#### Resend (рекомендуется)

**Обязательные настройки в `.env`:**

1. Зарегистрируйтесь на https://resend.com

```env

# Resend API ключ (получите на resend.com)# Редактирование настроек2. Создайте API ключ в панели управления

RESEND_API_KEY=re_your_key_here

RESEND_FROM_EMAIL=noreply@yourdomain.com# Linux/Mac: nano .env3. Настройте домен для отправки

RESEND_FROM_NAME=Your Company

# Windows: notepad .env

# Опциональные настройки

DAILY_EMAIL_LIMIT=100```### 5. Конфигурация

CONCURRENCY=10

RATE_LIMIT_PER_MINUTE=600Создайте файл `.env` с настройками:

LOG_LEVEL=INFO

```**Обязательные настройки в `.env`:**```env



### 5. Проверка установки```bash# Resend настройки



```bash# Resend API ключ (получите на resend.com)RESEND_API_KEY=re_your_key_here

# Тест CLI

python -m mailing.cli --helpRESEND_API_KEY=re_xxxxxxxxxxRESEND_FROM_EMAIL=noreply@yourdomain.com



# Проверка dry-run режимаRESEND_FROM_NAME=Your Company

python -m mailing.cli --file samples/recipients.csv --template samples/template.html --subject "Test" --dry-run

```# Email отправителя (должен быть верифицирован в Resend)



### 6. Первый запускSENDER_EMAIL=noreply@yourdomain.com# Или Mailgun настройки



```bashMAILGUN_API_KEY=your_mailgun_key

# Запуск GUI приложения

python run_gui.py# Опциональные настройкиMAILGUN_DOMAIN=yourdomain.com



# Запуск веб-интерфейсаCONCURRENCY=3          # Параллельность отправкиMAILGUN_FROM_EMAIL=noreply@yourdomain.com

python minimal_web_gui.py

```DAILY_QUOTA=1000      # Дневной лимит



Откройте http://localhost:5001 в браузереLOG_LEVEL=INFO        # Уровень логирования# Общие настройки



## 🌐 Настройка Resend APIDEBUG=false           # Отладочный режимDAILY_EMAIL_LIMIT=100



1. **Регистрация**: Зарегистрируйтесь на [resend.com](https://resend.com)```CONCURRENCY=10

2. **API ключ**: Создайте API ключ в панели управления

3. **Домен**: Добавьте и верифицируйте ваш домен```

4. **DNS настройки**: Добавьте необходимые DNS записи

### 3️⃣ Проверка установки

## 🖥️ Системные требования

### 6. Первый запуск

| Компонент | Минимум | Рекомендуется |

|-----------|---------|---------------|```bash```bash

| **Python** | 3.10+ | 3.11+ |

| **RAM** | 256MB | 512MB+ |# Тест CLI# Запуск GUI приложения

| **Диск** | 100MB | 500MB+ |

| **ОС** | Windows 10, macOS 10.15, Ubuntu 18.04+ | Последние версии |python -m mailing.cli --helppython run_gui.py



## 🚦 Тест системы```



### Тест конфигурации# Запуск веб-интерфейса



```bashpython run_gui.py## Проверка установки

# Проверка dry-run режима

python -m mailing.cli --file samples/recipients.csv --template samples/template.html --subject "Test" --dry-run```

```

### Тест конфигурации

### Тест отправки

## 🌐 Настройка Resend API```bash

1. Откройте GUI приложение

2. Загрузите файл `samples/recipients.csv`# Проверка dry-run режима

3. Выберите `samples/template.html`

4. Нажмите "Тест" для проверки подключения1. **Регистрация**: Зарегистрируйтесь на [resend.com](https://resend.com)python -m mailing.cli --file samples/recipients.csv --template samples/template.html --subject "Test" --dry-run



## 🔧 Устранение проблем2. **API ключ**: Создайте API ключ в панели управления```



### ❌ Частые ошибки3. **Домен**: Добавьте и верифицируйте ваш домен



**1. ImportError / ModuleNotFoundError**4. **DNS настройки**: Добавьте необходимые DNS записи### Тест отправки

```bash

# Решение: Активируйте виртуальное окружение1. Откройте GUI приложение

source .venv/bin/activate  # Linux/Mac

.venv\Scripts\activate     # Windows## 🖥️ Системные требования2. Загрузите файл `samples/recipients.csv`

```

3. Выберите `samples/template.html`

**2. GUI не запускается (Qt проблемы)**

```bash| Компонент | Минимум | Рекомендуется |4. Нажмите "Тест" для проверки подключения

# Решение: Используйте веб-интерфейс

python minimal_web_gui.py|-----------|---------|---------------|

```

| **Python** | 3.9+ | 3.11+ |## Возможные проблемы

**3. API ошибки (401 Unauthorized)**

```bash| **RAM** | 256MB | 512MB+ |

# Решение: Проверьте API ключ в .env

echo $RESEND_API_KEY  # Linux/Mac| **Диск** | 100MB | 500MB+ |### Python не найден

```

| **ОС** | Windows 10, macOS 10.15, Ubuntu 18.04+ | Последние версии |- Убедитесь что Python 3.10+ установлен

**4. Email не отправляются**

- ✅ Проверьте верификацию домена в Resend- Проверьте переменную PATH

- ✅ Убедитесь что SENDER_EMAIL верифицирован

- ✅ Проверьте дневные лимиты в Resend## 🚦 Первый запуск



### 🆘 Диагностика### Ошибки pip



```bash### Шаг 1: Веб-интерфейс```bash

# Проверка конфигурации

python -c "from mailing.config import settings; print('✅ Конфигурация загружена')"```bash# Обновление pip



# Проверка API ключаpython run_gui.pypython -m pip install --upgrade pip

python -c "from mailing.config import settings; print('API ключ:', '✅ Установлен' if settings.resend_api_key else '❌ Не установлен')"

```

# Тест подключения

python -m mailing.cli --file samples/recipients.csv --template template.html --subject "Тест" --dry-runОткройте http://localhost:5001 в браузере# Установка через requirements

```

pip install -r requirements.txt --no-cache-dir

### Возможные проблемы

### Шаг 2: Тестовая рассылка```

**Python не найден**

- Убедитесь что Python 3.10+ установлен```bash

- Проверьте переменную PATH

python -m mailing.cli \### Проблемы с GUI

**Ошибки pip**

```bash  --file samples/recipients.csv \- На Linux: `sudo apt-get install python3-tk`

# Обновление pip

python -m pip install --upgrade pip  --template template.html \- На macOS: Установите через Homebrew



# Установка через requirements  --subject "Тест" \- Используйте CLI интерфейс как альтернативу

pip install -r requirements.txt --no-cache-dir

```  --dry-run



**Проблемы с GUI**```### API ошибки

- На Linux: `sudo apt-get install python3-tk`

- На macOS: Установите через Homebrew- Проверьте правильность API ключей

- Используйте CLI интерфейс как альтернативу

## 🔧 Устранение проблем- Убедитесь в настройке домена

**API ошибки**

- Проверьте правильность API ключей- Проверьте лимиты аккаунта

- Убедитесь в настройке домена

- Проверьте лимиты аккаунта### ❌ Частые ошибки



## 📁 Структура после установки## Поддержка



```**1. ImportError / ModuleNotFoundError**

email-marketing-tool/

├── .venv/                 # Виртуальное окружение```bashПри проблемах проверьте:

├── .env                   # Ваши настройки

├── .env.example          # Пример настроек# Решение: Активируйте виртуальное окружение1. Версию Python (`python --version`)

├── run_gui.py            # 🚀 Главная точка входа

├── minimal_web_gui.py    # 🌐 Веб-интерфейсsource .venv/bin/activate  # Linux/Mac2. Установленные пакеты (`pip list`)

├── requirements.txt      # 📦 Зависимости

├── samples/              # 📁 Примеры.venv\Scripts\activate     # Windows3. Права доступа к файлам

│   ├── recipients.csv   # Пример получателей

│   ├── template.html    # Пример шаблона```4. Настройки файрволла

│   └── data.json       # Пример JSON

└── [остальные модули...]**2. GUI не запускается (Qt проблемы)**

``````bash

# Решение: Используйте веб-интерфейс

## 🎯 Следующие шагиpython minimal_web_gui.py

```

1. **📧 Настройте Resend аккаунт** и верифицируйте домен

2. **📄 Подготовьте файлы получателей** (CSV/Excel/JSON)**3. API ошибки (401 Unauthorized)**

3. **🎨 Создайте HTML шаблоны** с Jinja2 переменными  ```bash

4. **🧪 Протестируйте** с `--dry-run` опцией# Решение: Проверьте API ключ в .env

5. **🚀 Запустите** реальную рассылкуecho $RESEND_API_KEY  # Linux/Mac

6. **📊 Мониторьте** статистику в веб-интерфейсе```



## Поддержка**4. Email не отправляются**

- ✅ Проверьте верификацию домена в Resend

При проблемах проверьте:- ✅ Убедитесь что SENDER_EMAIL верифицирован

1. Версию Python (`python --version`)- ✅ Проверьте дневные лимиты в Resend

2. Установленные пакеты (`pip list`)

3. Права доступа к файлам### 🆘 Диагностика

4. Настройки файрволла

```bash

## 🔗 Полезные ссылки# Проверка конфигурации

python -c "from mailing.config import settings; print('✅ Конфигурация загружена')"

- 📖 [Resend Documentation](https://resend.com/docs)

- 🎨 [Jinja2 Templates](https://jinja.palletsprojects.com/)# Проверка API ключа

- 📧 [Email Best Practices](https://resend.com/docs/best-practices)python -c "from mailing.config import settings; print('API ключ:', '✅ Установлен' if settings.resend_api_key else '❌ Не установлен')"



---# Тест подключения

python -m mailing.cli --file samples/recipients.csv --template template.html --subject "Тест" --dry-run

**Нужна помощь?** Проверьте логи приложения или используйте `--help` команды.```

## 📁 Структура после установки

```
email-marketing-tool/
├── .venv/                 # Виртуальное окружение
├── .env                   # Ваши настройки
├── .env.example          # Пример настроек
├── run_gui.py            # 🚀 Главная точка входа
├── minimal_web_gui.py    # 🌐 Веб-интерфейс
├── requirements.txt      # 📦 Зависимости
├── samples/              # 📁 Примеры
│   ├── recipients.csv   # Пример получателей
│   ├── template.html    # Пример шаблона
│   └── data.json       # Пример JSON
└── [остальные модули...]
```

## 🎯 Следующие шаги

1. **📧 Настройте Resend аккаунт** и верифицируйте домен
2. **📄 Подготовьте файлы получателей** (CSV/Excel/JSON)
3. **🎨 Создайте HTML шаблоны** с Jinja2 переменными  
4. **🧪 Протестируйте** с `--dry-run` опцией
5. **🚀 Запустите** реальную рассылку
6. **📊 Мониторьте** статистику в веб-интерфейсе

## 🔗 Полезные ссылки

- 📖 [Resend Documentation](https://resend.com/docs)
- 🎨 [Jinja2 Templates](https://jinja.palletsprojects.com/)
- 📧 [Email Best Practices](https://resend.com/docs/best-practices)

---

**Нужна помощь?** Проверьте логи приложения или используйте `--help` команды.