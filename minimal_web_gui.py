    from flask import request
from pathlib import Path
import os
import sys

from flask import Flask

#!/usr/bin/env python3
"""
Минимальный веб-интерфейс для почтовой рассылки"""


app = Flask(__name__)

@app.route("/")
def index():"""Главная страница - минимальная версия"""
    return ("""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
    <title>Почтовая рассылка</title>
    <style>
        body { font-family: Arial,
            sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; text-align: center; }
        .form-group { margin: 20px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input,
            select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .info { background: #f0f8ff; padding: 15px; border-radius: 4px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>📧 Почтовая рассылка</h1>
<div class="info">
        <h3>Информация о приложении:</h3>
        <p>✅ Веб-интерфейс запущен успешно!</p>
        <p>📁 Проверьте папку samples/ для примеров файлов</p>
        <p>💡 Используйте CLI для полнофункциональной работы:</p>
        <code>python -m mailing.cli --help</code>
    </div>
<form action="/test" method="get"><div class="form-group">
            <label>📋 Файл получателей:</label><input type="text" name="file" placeholder="samples/recipients.csv" required>
        </div>
<div class="form-group">
            <label>📄 Шаблон письма:</label><input type="text" name="template" placeholder="template.html" required>
        </div>
<div class="form-group">
            <label>✉️ Тема письма:</label><input type="text" name="subject" placeholder="Тестовая рассылка" required>
        </div>
<div class="form-group">
            <label>🚀 Режим:</label><select name="mode"><option value="dry-run">🧪 Тестовый (без отправки)</option><option value="real">🚀 Реальная отправка</option>
            </select>
        </div>
<button type="submit">▶️ Показать команду CLI</button>
    </form>
<div class="info">
        <h3>📁 Доступные файлы в samples/:</h3><ul>"""+ "".join(
            [f"<li>{f.name}</li>"for f in (Path(__file__).parent / "samples").iterdir()
                if f.is_file()
            ]
        )+ """
        </ul>
    </div>
<div class="info">
        <h3>🚀 Как использовать:</h3>
        <ol>
            <li>Заполните форму выше</li><li>Нажмите "Показать команду CLI"</li>
            <li>Скопируйте и выполните команду в терминале</li>
        </ol>
    </div>
</body>
</html>"""
    )

@app.route("/test")
def test():"""Показ команды для выполнения"""
    """Выполняет test."""
file = request.args.get("file",
    "samples/recipients.csv")template = request.args.get("template",
    "template.html")subject = request.args.get("subject",
    "Тестовая рассылка")mode = request.args.get("mode", "dry-run")

    cmd_parts = ["python -m mailing.cli",f"--file {file}",f"--template {template}",
        f'--subject "{subject}"',
    ]

    if mode == "dry-run":cmd_parts.append("--dry-run")
command = " ".join(cmd_parts)
return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
    <title>Команда для выполнения</title>
    <style>
        body {{ font-family: Arial,
            sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
        .command {{ background: #f5f5f5; padding: 15px; border-radius: 4px; font-family: monospace; margin: 20px 0; }}
        .success {{ background: #d4edda; color: #155724; padding: 15px; border-radius: 4px; }}
        .info {{ background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 4px; }}
    </style>
</head>
<body>
    <h1>📧 Команда для выполнения рассылки</h1>
<div class="success">
        ✅ Команда сформирована успешно!
    </div>

    <h3>💻 Выполните эту команду в терминале:</h3><div class="command">
        {command}
    </div>
<div class="info">
        <h3>📋 Параметры:</h3>
        <ul>
            <li><strong>Файл получателей:</strong> {file}</li>
            <li><strong>Шаблон:</strong> {template}</li>
            <li><strong>Тема:</strong> {subject}</li>
            <li><strong>Режим:</strong> {mode}</li>
        </ul>
    </div>
<div class="info">
        <h3>🚀 Инструкция:</h3>
        <ol>
            <li>Откройте терминал</li>
            <li>Перейдите в папку проекта: <code>cd /Users/alexandr/Desktop/VS_progect/Scripts/Mailing</code></li>
            <li>Активируйте виртуальное окружение: <code>source .venv/bin/activate</code></li>
            <li>Выполните команду выше</li>
        </ol>
    </div>
<p><a href="/">← Назад к форме</a></p>
</body>
</html>"""


def main():print("🌐 Запуск минимального веб-интерфейса...")print("📍 Откройте в браузере: http://localhost:5000")print("⏹  Для остановки нажмите Ctrl+C")
    """Выполняет main."""

    try:app.run(host="127.0.0.1", port = 5001, debug = True)  # Используем порт 5001
    except KeyboardInterrupt:print("\n👋 Веб-сервер остановлен")

if __name__ == "__main__":
    main()
