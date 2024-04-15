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

    # Set the logging level
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO").upper()
        try:
            level = log_levels[level]
        except KeyError:
            raise ValueError(f"Invalid log level: {level}")

    # Configure the handler and set the formatter
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Get the package's logger (replace 'my_package' with the actual package name)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger
