from __future__ import annotations

import os
import sys

from loguru import logger

from itw.errors import ItwError

_VALID_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})

_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def resolve_log_level(*, verbose: bool = False) -> str:
    """Return effective log level from LOG_LEVEL env, overridden by verbose→DEBUG."""
    if verbose:
        return "DEBUG"
    raw = os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO"
    if raw not in _VALID_LEVELS:
        raise ItwError(
            f"Invalid LOG_LEVEL={raw!r}. "
            f"Use one of: {', '.join(sorted(_VALID_LEVELS))}."
        )
    return raw


def configure_logging(level: str) -> None:
    """Reset Loguru and attach a single stderr sink at the given level."""
    normalized = level.strip().upper()
    if normalized not in _VALID_LEVELS:
        raise ItwError(
            f"Invalid log level={normalized!r}. "
            f"Use one of: {', '.join(sorted(_VALID_LEVELS))}."
        )
    logger.remove()
    logger.add(sys.stderr, level=normalized, format=_LOG_FORMAT, enqueue=False)
    logger.debug("Logging configured at level={}", normalized)
