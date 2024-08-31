"""
SQL Question Answer api endpoint
"""
import logging
import traceback
from typing import Dict, Optional
from fastapi import APIRouter, status, HTTPException

from api.mysql import run_sql_script
from core.setup import mysql_conn
from models.model import SQLQueryParams

router = APIRouter()
logger = logging.getLogger('sql_qa_route')


@router.post("/script", response_model=Dict,
             status_code=status.HTTP_200_OK,
             summary="Runs SQL query in the database as is")
async def sql_script(
        request_data: SQLQueryParams):
    """
    Runs an SQL query in the database with optional parameters.
    
    Args:
    - query (str): The SQL query to execute.
    - params (Optional[tuple]): Optional parameters for the SQL query.

    Example params:
        {"query": "UPDATE users SET name = %s, email = %s WHERE id = %s",
        "params": ["Jane Doe", "jane.doe@example.com", 1]}
    """
    status_code = status.HTTP_200_OK
    response_data = {}
    try:
        query, params = request_data.query, request_data.params
        sql_resp = run_sql_script(
            mysql_conn, query, params, commit=not query.lower().startswith("select"))
        response_data = {"status": "success", "query": query, "params": params} | sql_resp
    except Exception as excep:
        logger.error("%s: %s", excep, traceback.print_exc())
        status_code = status.HTTP_400_BAD_REQUEST if status_code == status.HTTP_200_OK else status_code
        detail = response_data.get("detail", "Failed to run SQL query in MySQL server")
        raise HTTPException(status_code=status_code, detail=detail) from excep
    return response_data


@router.post("/qa", response_model=Dict,
             status_code=status.HTTP_200_OK,
             summary="Convert query into sql command & interact with SQL database")
async def sql_question_answer(
        query: str):
    """Converts query into sql comamnd & interact with SQL database"""
    status_code = status.HTTP_200_OK
    response_data = {}
    try:
        sql_data_response = {"status": "success", "query": query}  # TODO query with langchain + text2sql
        response_data = sql_data_response
    except Exception as excep:
        logger.error("%s: %s", excep, traceback.print_exc())
        status_code = status.HTTP_400_BAD_REQUEST if status_code == status.HTTP_200_OK else status_code
        detail = response_data.get("detail", "failed to conduct query search in server")
        raise HTTPException(status_code=status_code, detail=detail) from excep
    return response_data
