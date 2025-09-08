"""
Load configurations and constants 
"""
import os
from logging.config import dictConfig
from models.logging import LogConfig
from dotenv import load_dotenv

# load environment variables from .env file
load_dotenv(override=True)

# project information
PROJECT_NAME: str = "Log Analyzer API template"
PROJECT_DESCRIPTION: str = "Template API for Log Analyzer"
DEBUG: bool = os.environ.get("DEBUG", "") != "False"
VERSION: str = "0.0.1"

# server settings
API_SERVER_PORT = int(os.getenv("API_SERVER_PORT", default="8080"))

# save directories
ROOT_STORAGE_DIR = os.getenv("ROOT_STORAGE_DIR", default="volumes/log_analyzer")
FILE_STORAGE_DIR = os.getenv("FILE_STORAGE_DIR", default=os.path.join(ROOT_STORAGE_DIR, "files"))
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", default=os.path.join(ROOT_STORAGE_DIR, "vector_store"))
LOG_STORAGE_DIR = os.getenv("LOG_STORAGE_DIR", default=os.path.join(ROOT_STORAGE_DIR, "logs"))

os.makedirs(ROOT_STORAGE_DIR, exist_ok=True)
os.makedirs(FILE_STORAGE_DIR, exist_ok=True)
os.makedirs(LOG_STORAGE_DIR, exist_ok=True)

# logging conf
log_cfg = LogConfig()
# override info & error log paths
log_cfg.handlers["info_rotating_file_handler"]["filename"] = os.path.join(LOG_STORAGE_DIR, "info.log")
log_cfg.handlers["warning_file_handler"]["filename"] = os.path.join(LOG_STORAGE_DIR, "error.log")
log_cfg.handlers["error_file_handler"]["filename"] = os.path.join(LOG_STORAGE_DIR, "error.log")
dictConfig(log_cfg.model_dump())

# mysql conf
MYSQL_HOST = os.getenv("MYSQL_HOST", default="0.0.0.0")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", default="3306"))
MYSQL_USER = os.getenv("MYSQL_USER", default="user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", default="pass")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", default="default")

# mysql table info
MYSQL_LOG_ID_TB_NAME = "log_fid"
MYSQL_GENERAL_ID_TB_NAME = "general_fid"
