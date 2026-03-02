"""
Logging configurations

Logging Levels (Only events of selected level or higher recorded)

CRITICAL 50
ERROR    40
WARNING  30
INFO     20
DEBUG    10
NOTSET    0
"""

import os
from pydantic import BaseModel


class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    INFO_FILE_PATH: str = "info.log"
    ERROR_FILE_PATH: str = "error.log"

    # Fetch debug level from environment variable or default to 'DEBUG' if not set
    DEBUG_LEVEL: str = os.getenv("DEBUG_LEVEL", "INFO").upper()

    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        "info": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s | %(asctime)s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "error": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": ("%(levelprefix)s | %(asctime)s | %(name)s | %(process)d::%(module)s|%(lineno)s:: %(message)s"),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: dict = {
        "debug_console_handler": {
            "level": DEBUG_LEVEL,
            "formatter": "info",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "info_rotating_file_handler": {
            "level": "INFO",
            "formatter": "info",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": INFO_FILE_PATH,
            "mode": "a",
            "maxBytes": 1048576,
            "backupCount": 10,
        },
        "error_file_handler": {
            "level": "ERROR",
            "formatter": "error",
            "class": "logging.FileHandler",
            "filename": ERROR_FILE_PATH,
            "mode": "a",
        },
    }
    loggers: dict = {
        "": {
            "level": DEBUG_LEVEL,
            "handlers": [
                "debug_console_handler",
                "info_rotating_file_handler",
                "error_file_handler",
            ],
        },
        "log_analyzer": {
            "level": "INFO",
            "propagate": False,
            "handlers": [
                "debug_console_handler",
                "info_rotating_file_handler",
                "error_file_handler",
            ],
        },
    }
