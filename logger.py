import logging
import logging.handlers
import os
from datetime import datetime

# TODO : Better refine logging to have multiple log handler
LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)
date_str = datetime.now().strftime("%y_%m_%d")
LOG_FILE = os.path.join(LOG_DIR, f"trade_{date_str}.log")
LOG_LEVEL = logging.DEBUG
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logger():
    logger = logging.getLogger("Trade")
    logger.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
