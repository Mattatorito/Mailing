import logging
from typing import Optional
from rich.logging import RichHandler
from .config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

_configured = False

def configure_logging(level: Optional[str] = None) -> None:
    global _configured
    if _configured:
        return
    logging.basicConfig(
        level=getattr(logging, (level or settings.log_level).upper(), logging.INFO),
        format=_LOG_FORMAT,
        datefmt="%H:%M:%S",
        handlers=[RichHandler(rich_tracebacks=True, show_time=False, show_path=False)],
    )
    _configured = True

logger = logging.getLogger("mailing")

def structured(logger_name: str, **fields):  # lightweight helper to build key=val string
    parts = [f"{k}={v}" for k, v in fields.items()]
    return logging.getLogger(logger_name), " ".join(parts)

retry_logger = logging.getLogger("mailing.retry")
