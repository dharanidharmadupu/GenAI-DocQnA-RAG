"""Logging configuration for the application."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
    format_json: bool = False
) -> None:
    """
    Configure application logger.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file. If None, logs only to console
        rotation: When to rotate log file (e.g., "10 MB", "1 day")
        retention: How long to keep old logs (e.g., "7 days", "10 days")
        format_json: If True, output logs in JSON format
    """
    # Remove default logger
    logger.remove()
    
    # Configure format
    if format_json:
        log_format = "{message}"
        
        def serialize(record):
            import json
            subset = {
                "timestamp": record["time"].isoformat(),
                "level": record["level"].name,
                "message": record["message"],
                "module": record["module"],
                "function": record["function"],
                "line": record["line"],
            }
            return json.dumps(subset)
        
        # Add console handler
        logger.add(
            sys.stdout,
            format=log_format,
            level=log_level,
            serialize=True
        )
    else:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        # Add console handler
        logger.add(
            sys.stdout,
            format=log_format,
            level=log_level,
            colorize=True
        )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format=log_format,
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression="zip"
        )
    
    logger.info(f"Logger initialized with level: {log_level}")


def get_logger(name: str = __name__):
    """
    Get logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logger.bind(name=name)
