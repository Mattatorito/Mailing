#!/usr/bin/env python3

from __future__ import annotations
import asyncio
import sys
from pathlib import Path
from typing import List
from rich.console import Console
from src.mailing.config import settings
from src.mailing.models import Recipient
from src.mailing.sender import run_campaign, CampaignController
from src.data_loader.csv_loader import CSVLoader
from src.data_loader.excel_loader import ExcelLoader
import json

console = Console()


def load_recipients(data_file: str) -> List[Recipient]:
    """Загружает получателей из файла данных."""
    data_path = Path(data_file)
    
    if not data_path.exists():
        console.print(f"[red]Файл не найден: {data_file}[/red]")
        raise FileNotFoundError(f"Файл не найден: {data_file}")
    
    ext = data_path.suffix.lower()
    
    if ext == '.csv':
        loader = CSVLoader()
        return loader.load(str(data_path))
    elif ext in ['.xlsx', '.xls']:
        loader = ExcelLoader()
        return loader.load(str(data_path))
    elif ext == '.json':
        return load_json_recipients(str(data_path))
    else:
        console.print(f"[red]Неподдерживаемый формат: {ext}[/red]")
        raise ValueError(f"Неподдерживаемый формат файла: {ext}")


def load_json_recipients(json_file: str) -> List[Recipient]:
    """Загружает получателей из JSON файла."""
    from email_validator import validate_email, EmailNotValidError
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    recipients = []
    for item in data:
        if isinstance(item, dict) and 'email' in item:
            email = item['email']
            
            # Validate email format
            try:
                validate_email(email)
            except EmailNotValidError:
                console.print(f"[yellow]Пропуск неверного email: {email}[/yellow]")
                continue
            name = item.get('name', '')
            variables = {k: v for k, v in item.items() if k not in ['email', 'name']}
            
            recipient = Recipient(
                email=email,
                name=name,
                variables=variables
            )
            recipients.append(recipient)
    
    return recipients


async def send_all(
    recipients_file: str,
    template_name: str,
    subject: str,
    dry_run: bool = False,
    concurrency: int = 5
):
    """Отправляет email всем получателям."""
    console.print(f"Запуск кампании: {subject}")
    console.print(f"📧 Шаблон: {template_name}")
    console.print(f"📁 Получатели: {recipients_file}")
    console.print(f"🔧 Режим: {'Тестовый (dry-run)' if dry_run else 'Реальная отправка'}")
    
    # Загружаем получателей
    try:
        recipients = load_recipients(recipients_file)
        console.print(f"�� Загружено получателей: {len(recipients)}")
    except Exception as e:
        console.print(f"[red]Ошибка загрузки получателей: {e}[/red]")
        return False
    
    # Создаем контроллер кампании
    controller = CampaignController()
    
    # Запускаем кампанию
    campaign_success = True
    try:
        async for event in run_campaign(
            recipients=recipients,
            template_name=template_name,
            subject=subject,
            dry_run=dry_run,
            concurrency=concurrency,
            controller=controller
        ):
            if event['type'] == 'progress':
                console.print(f"Прогресс: {event['sent']}/{event['total']}")
            elif event['type'] == 'error':
                console.print(f"[red]Ошибка: {event['message']}[/red]")
                campaign_success = False
            elif event['type'] == 'finished':
                stats = event['stats']
                console.print(f"Кампания завершена!")
                console.print(f"Отправлено: {stats['sent']}")
                console.print(f"Доставлено: {stats['delivered']}")
                console.print(f"Ошибок: {stats['failed']}")
                if stats.get('failed', 0) > 0:
                    campaign_success = False
        
        return campaign_success
    except Exception as e:
        console.print(f"[red]Критическая ошибка кампании: {e}[/red]")
        return False


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 4:
        console.print("Использование: python -m mailing.cli <recipients_file> <template> <subject> [--dry-run]")
        sys.exit(1)
    
    recipients_file = sys.argv[1]
    template_name = sys.argv[2]
    subject = sys.argv[3]
    dry_run = '--dry-run' in sys.argv
    
    # Use return value for proper exit codes
    success = asyncio.run(send_all(recipients_file, template_name, subject, dry_run))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
