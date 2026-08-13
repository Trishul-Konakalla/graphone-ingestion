import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger. Safe to call repeatedly - only attaches
    a handler the first time a given logger name is requested."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
