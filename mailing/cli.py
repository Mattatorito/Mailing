from __future__ import annotations
import argparse, asyncio, sys
from pathlib import Path
from typing import List, Optional
import click
from rich.table import Table
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

from mailing.logging_config import configure_logging, logger
from mailing.config import settings
from mailing.sender import run_campaign, CampaignController
from validation.email_validator import validate_email_list
from stats.aggregator import StatsAggregator
from data_loader.csv_loader import CSVLoader
from data_loader.excel_loader import ExcelLoader
from data_loader.json_loader import JSONLoader

console = Console()

LOADERS = {
    '.csv': CSVLoader(),
    '.xlsx': ExcelLoader(),
    '.json': JSONLoader(),
}

def load_recipients(path: str):
    ext = Path(path).suffix.lower()
    loader = LOADERS.get(ext)
    if not loader:
        raise SystemExit(f"Unsupported file extension: {ext}")
    recipients = loader.load(path)
    valid, errors = validate_email_list(r.email for r in recipients)
    email_to_rec = {r.email: r for r in recipients}
    filtered = [email_to_rec[v] for v in valid if v in email_to_rec]
    if errors:
        logger.warning(f"Отфильтровано {len(errors)} невалидных адресов")
    return filtered, errors

async def send_all(*, recipients, template_name: str, subject: str, dry_run: bool, concurrency: int):
    stats = StatsAggregator()
    controller = CampaignController()
    with Progress(SpinnerColumn(), *Progress.get_default_columns(), TimeElapsedColumn(), console=console) as progress:
        task = progress.add_task("Отправка", total=len(recipients))
        async for event in run_campaign(recipients=recipients, template_name=template_name, subject=subject, dry_run=dry_run, concurrency=concurrency, controller=controller):
            etype = event["type"]
            if etype == "progress":
                # добавляем результат в наш stats (чтобы summary работал на объекте)
                result = event["result"]
                stats.add(result)
                stats_snapshot = event["stats"]
                progress.update(task, advance=1, description=f"Отправка | OK:{stats_snapshot['success']} ERR:{stats_snapshot['failed']}")
            elif etype == "error":
                progress.update(task, description="Ошибка / отменено")
                break
            elif etype == "finished":
                progress.update(task, completed=progress.tasks[0].total, description="Готово")
                break
    # финальные агрегированные stats доступны в последнем event[stats]; пересоздадим из репозитория при необходимости
    return stats

def render_summary(stats: StatsAggregator):
    snap = stats.snapshot()
    table = Table(title="Результаты рассылки")
    table.add_column("Всего")
    table.add_column("Успех")
    table.add_column("Ошибок")
    table.add_column("Скорость (msg/s)")
    table.add_column("Время (с)")
    table.add_row(str(snap['total']), str(snap['success']), str(snap['failed']), str(snap['rate_per_sec']), str(snap['elapsed_sec']))
    console.print(table)


def parse_args(argv: List[str]):
    p = argparse.ArgumentParser("Mass Mailer (Resend)")
    p.add_argument("--file", required=True, help="Файл получателей (csv|xlsx|json)")
    p.add_argument("--template", required=True, help="Имя файла шаблона в samples/")
    p.add_argument("--subject", required=False, default="No subject", help="Тема письма")
    p.add_argument("--dry-run", action="store_true", help="Не отправлять письма, только симуляция")
    p.add_argument("--concurrency", type=int, default=settings.concurrency)
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None):
    configure_logging()
    args = parse_args(argv or sys.argv[1:])
    recipients, errors = load_recipients(args.file)
    logger.info(f"Получателей: {len(recipients)} (ошибок валидации: {len(errors)})")
    stats = asyncio.run(send_all(recipients=recipients, template_name=args.template, subject=args.subject, dry_run=args.dry_run, concurrency=args.concurrency))
    render_summary(stats)

if __name__ == "__main__":
    main()
