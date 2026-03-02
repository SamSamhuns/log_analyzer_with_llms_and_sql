"""Application configuration and logging setup."""
import os
from logging.config import dictConfig
from pathlib import Path

from dotenv import load_dotenv

from app.models.logging import LogConfig


def _to_bool(raw_value: str | None, default: bool = False) -> bool:
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _to_csv(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


# keep existing environment variables as source of truth
load_dotenv(override=False)

# project information
PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Log Analyzer API")
PROJECT_DESCRIPTION: str = os.getenv(
    "PROJECT_DESCRIPTION",
    "Log analysis with FastAPI, LangChain, and MariaDB.",
)
DEBUG: bool = _to_bool(os.getenv("DEBUG"), default=False)
VERSION: str = os.getenv("API_VERSION", "0.2.0")

# server settings
API_SERVER_PORT = int(os.getenv("API_SERVER_PORT", "8080"))

# CORS settings
CORS_ALLOW_ORIGINS = _to_csv(
    os.getenv("CORS_ALLOW_ORIGINS", "http://localhost,http://127.0.0.1")
)
if not CORS_ALLOW_ORIGINS:
    CORS_ALLOW_ORIGINS = ["http://localhost", "http://127.0.0.1"]
CORS_ALLOW_CREDENTIALS = _to_bool(os.getenv("CORS_ALLOW_CREDENTIALS"), default=False)

# save directories
ROOT_STORAGE_DIR = os.getenv("ROOT_STORAGE_DIR", "volumes/log_analyzer")
FILE_STORAGE_DIR = os.getenv("FILE_STORAGE_DIR", os.path.join(ROOT_STORAGE_DIR, "files"))
VECTOR_STORE_DIR = os.getenv(
    "VECTOR_STORE_DIR",
    os.path.join(ROOT_STORAGE_DIR, "vector_store"),
)
LOG_STORAGE_DIR = os.getenv("LOG_STORAGE_DIR", os.path.join(ROOT_STORAGE_DIR, "logs"))

Path(ROOT_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
Path(FILE_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
Path(LOG_STORAGE_DIR).mkdir(parents=True, exist_ok=True)

# logging conf
log_cfg = LogConfig()
log_cfg.handlers["info_rotating_file_handler"]["filename"] = os.path.join(
    LOG_STORAGE_DIR,
    "info.log",
)
log_cfg.handlers["error_file_handler"]["filename"] = os.path.join(
    LOG_STORAGE_DIR,
    "error.log",
)
dictConfig(log_cfg.model_dump())

# mysql conf
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "pass")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "default")
MYSQL_CONNECT_TIMEOUT = int(os.getenv("MYSQL_CONNECT_TIMEOUT", "10"))

# SQL execution safety
ALLOW_UNSAFE_SQL_SCRIPTS = _to_bool(os.getenv("ALLOW_UNSAFE_SQL_SCRIPTS"), default=False)

# mysql table info
MYSQL_LOG_ID_TB_NAME = "log_fid"
MYSQL_GENERAL_ID_TB_NAME = "general_fid"
