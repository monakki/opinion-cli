"""Logging configuration utilities for Opinion CLI."""

import os
import sys
from loguru import logger
from config.constants import ENV_LOG_LEVEL, LoggingConstants


def setup_logging():
    """Setup logging configuration based on environment variables."""
    # Remove default logger
    logger.remove()

    # Get log level from environment
    log_level = os.getenv(ENV_LOG_LEVEL)

    # If no log level is set, disable logging completely
    if not log_level:
        return

    # Validate log level
    log_level = log_level.upper()
    if log_level not in LoggingConstants.VALID_LOG_LEVELS:
        print(
            f"Warning: Invalid log level '{log_level}'. Valid levels: {LoggingConstants.VALID_LOG_LEVELS}"
        )
        return

    # Add logger with specified level
    logger.add(
        sys.stderr,
        format=LoggingConstants.DETAILED_FORMAT,
        level=log_level,
        colorize=True,
    )


def disable_logging():
    """Completely disable logging."""
    logger.remove()


def enable_logging(level: str = "INFO"):
    """Enable logging with specified level."""
    logger.remove()

    level = level.upper()
    if level not in LoggingConstants.VALID_LOG_LEVELS:
        level = "INFO"

    logger.add(
        sys.stderr,
        format=LoggingConstants.DETAILED_FORMAT,
        level=level,
        colorize=True,
    )
