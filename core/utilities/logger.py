import logging
import logging.handlers
import os
from datetime import datetime

# TODO : Better refine logging to have multiple log handler
LOG_DIR = "out/log"
os.makedirs(LOG_DIR, exist_ok=True)
date_str = datetime.now().strftime("%d_%m_%y")
LOG_FILE = os.path.join(LOG_DIR, f"trade_{date_str}.log")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def _parse_level(level_name: str, default: int) -> int:
    """Return a logging level from string, defaulting when invalid."""
    return getattr(logging, level_name.upper(), default)


def setup_logger(
    console_level: int | None = None, file_level: int | None = None
) -> logging.Logger:

    if console_level is None:
        console_level = _parse_level(
            os.getenv("LOG_LEVEL_CONSOLE", "INFO"), logging.INFO
        )
    if file_level is None:
        file_level = _parse_level(os.getenv("LOG_LEVEL_FILE", "DEBUG"), logging.DEBUG)

    logger = logging.getLogger("Trade")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
