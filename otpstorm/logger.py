"""
Logging configuration for OTPStorm.

Provides a unified logging system with console colors and optional file output.
"""

import logging
import sys
from typing import Optional, Dict

# Track created loggers
_loggers: Dict[str, logging.Logger] = {}

# ANSI color codes for log levels
LEVEL_COLORS = {
    "DEBUG": "\033[1;90m",      # Gray
    "INFO": "\033[1;92m",       # Green
    "WARNING": "\033[1;93m",    # Yellow
    "ERROR": "\033[1;91m",      # Red
    "CRITICAL": "\033[1;41m",   # Red background
}
RESET = "\033[0m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds ANSI colors to log output."""

    def __init__(self, fmt: str, datefmt: Optional[str] = None, use_color: bool = True):
        super().__init__(fmt, datefmt=datefmt)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        if self.use_color and record.levelname in LEVEL_COLORS:
            record.levelname = f"{LEVEL_COLORS[record.levelname]}{record.levelname}{RESET}"
        return super().format(record)


def setup_logger(
    name: str = "otpstorm",
    level: str = "INFO",
    log_file: Optional[str] = None,
    use_color: bool = True,
) -> logging.Logger:
    """
    Set up and return a logger instance.

    Args:
        name: Logger name.
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional path to log file.
        use_color: Whether to use ANSI colors in console output.

    Returns:
        Configured Logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
        use_color=use_color,
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger


def get_logger(name: str = "otpstorm") -> logging.Logger:
    """Get an existing logger or create a default one."""
    if name not in _loggers:
        return setup_logger(name)
    return _loggers[name]
