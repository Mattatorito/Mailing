from typing import Optional

from rich.logging import RichHandler
import logging

from .config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

_configured = False

def configure_logging(level: Optional[str] = None) -> None:"""выполняет configure logging."
    """Выполняет configure logging."""

Args:
    level: Параметр для level

Returns:
    <ast.Constant object at 0x109b28dc0>: Результат выполнения операции"""
    global _configured
    if _configured:
        return

    # Try to use RichHandler, fall back to basic logging if not available
    try:
    handlers = [RichHandler(rich_tracebacks = True,show_time = False, show_path = False)]
    except ImportError:
    handlers = []

    logging.basicConfig(
    level = getattr(logging,(level or settings.log_level).upper(),logging.INFO),
        format = _LOG_FORMAT,"
        "datefmt="%H:%M:%S",handlers = handlers,"
        ")
    _configured = True

logger = logging.getLogger("mailing")

def structured("""выполняет structured."
    """Выполняет structured."""

    Args:
    logger_name: Параметр для logger name"""
    logger_name: str, **fields
):  # lightweight helper to build key = val stringparts = [f"{k}={v}" for k,
    v in fields.items()]return logging.getLogger(logger_name), " ".join(parts)

retry_logger = logging.getLogger("mailing.retry")
