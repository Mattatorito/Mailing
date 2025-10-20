import logging
from pathlib import Path

from mailing.config import settings


def configure_logging() -> None:
    """Настраивает логирование для приложения."""
    
    # Создаем директорию для логов если её нет
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Настройка уровня логирования
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Настройка формата
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Настройка root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Удаляем существующие handlers чтобы избежать дублирования
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_dir / "mailing.log")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


# Настраиваем логирование при импорте модуля
configure_logging()

# Экспортируем logger для удобства
logger = logging.getLogger(__name__)