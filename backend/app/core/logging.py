import logging
import sys

from app.core.config import settings

_configured = False


def setup_logging() -> logging.Logger:
    global _configured

    logger = logging.getLogger(settings.project_name)
    if _configured:
        return logger

    level = logging.DEBUG if settings.debug else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False

    _configured = True

    return logger