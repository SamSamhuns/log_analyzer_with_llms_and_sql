"""
API data models
"""
from enum import Enum
from pydantic import BaseModel
from abc import ABC, abstractmethod
from typing import List, Any, Optional


class InputModel(BaseModel):
    """
    API input model format
    """
    file_path: str


class QueryRequest(BaseModel):
    """
    Query request model for query string
    """
    query: str


class SQLQueryParams(BaseModel):
    """
    SQL query and optional parameters
    """
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


class LLMModel(Enum):
    """
    LLM Model Types
    """
    GPT_3: str = "gpt-3"
    GPT_4: str = "gpt-4"
    GPT_3_5_TURBO_0125: str = "gpt-3.5-turbo-0125"
    GPT_4_Turbo: str = "gpt-4-turbo"
    GPT_4o: str = "gpt-4o"
    GPT_4o_Mini: str = "gpt-4o-mini"
    # most be locally hosted in the same env as the server
    Llamafile: str = "llamafile"


class LogText2SQLConfig(ABC):
    """
    log text to sql config
    """
    @abstractmethod
    def table_name(self):
        pass

    @abstractmethod
    def table_schema(self):
        pass

    @abstractmethod
    def table_examples(self):
        pass

    @abstractmethod
    def table_info(self):
        pass

    @abstractmethod
    def top_k(self):
        pass

    @abstractmethod
    def sql_prompt_template(self):
        pass
