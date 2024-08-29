"""
API data models
"""
from pydantic import BaseModel
from enum import Enum
from typing import List, Any, Optional


class InputModel(BaseModel):
    """
    API input model format
    """
    file_path: str


class SQLQueryParams(BaseModel):
    query: str
    params: Optional[List[Any]] = None


class SummarizerMode(str, Enum):
    """
    Summarization modes
    """
    INDIVIDUAL: str = "individual"
    COMBINED: str = "combined"


class LogFileType(str, Enum):
    """
    Log file types and table names in sql database
    """
    ANOMALY_DETECTION_LOG: str = "anomaly_detection_log"
