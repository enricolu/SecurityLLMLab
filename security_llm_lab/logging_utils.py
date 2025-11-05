"""Utility helpers to configure logging consistently across modules."""

from __future__ import annotations

import logging
from typing import Optional


def configure_logging(level: int = logging.INFO, name: Optional[str] = None) -> logging.Logger:
    """Configure and return a logger instance.

    Parameters
    ----------
    level:
        Logging level to use for the root handler.
    name:
        Optional logger name; if omitted the root logger is returned.
    """

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


__all__ = ["configure_logging"]
