"""
logger.py
=========
Configures logging for the dashboard.
Call setup_logging() once in main.py before any other imports.
"""
import logging
import os
from uk_housing_dashboard.config import OUTPUTS_DIR


def setup_logging(level: str = "INFO") -> None:
    """
    Configure root logger with console + rotating file handler.

    Args:
        level: Logging level string ("DEBUG", "INFO", "WARNING", "ERROR").
    """
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    log_file = os.path.join(OUTPUTS_DIR, "dashboard.log")

    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not root.handlers:
        root.addHandler(ch)
        root.addHandler(fh)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
