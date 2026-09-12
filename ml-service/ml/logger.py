
import logging
import sys
from typing import Any

LOGGER_NAME = "ML_SERVER"


def setup_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


logger = setup_logger()


def short_value(value: Any, max_len: int = 500) -> str:
    text = str(value)
    if len(text) > max_len:
        return text[:max_len] + "...<truncated>"
    return text
