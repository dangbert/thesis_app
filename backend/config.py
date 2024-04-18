import os
import logging
from typing import Optional


def get_logger(name: str, level: Optional[str] = None):
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"
    )

    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # Get the LOG_LEVEL from environment, default to 'INFO' if not found
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO").upper()
        if level not in log_levels:
            raise ValueError(f"Invalid log level: {level}")
    level_int = log_levels[level]

    # Configure the handler and set the formatter
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Get the package's logger (replace 'my_package' with the actual package name)
    logger = logging.getLogger(name)
    logger.setLevel(level_int)
    logger.addHandler(handler)
    return logger
