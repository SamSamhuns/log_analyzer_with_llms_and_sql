"""
API data models
"""
from pydantic import BaseModel
from enum import Enum


class InputModel(BaseModel):
    """
    API input model format
    """
    file_path: str


class SummarizerMode(str, Enum):
    """
    Summarization modes
    """
    INDIVIDUAL: str = "individual"
    COMBINED: str = "combined"
