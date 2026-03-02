"""
SQL Question Answer api endpoint
"""

import logging
from typing import Dict
from fastapi import APIRouter, status, HTTPException

from app.api.langchain_custom.text2sql import text_to_sql
from app.api.mysql import run_sql_script, sep_query_and_params
from app.models.model import SQLQueryParams, SQLQARequest
from app.core.setup import mysql_conn, TEXT2SQL_CFG_DICT
from app.core.config import ALLOW_UNSAFE_SQL_SCRIPTS

router = APIRouter()
logger = logging.getLogger("sql_qa_route")


@router.post(
    "/script",
    response_model=Dict,
    status_code=status.HTTP_200_OK,
    summary="Runs SQL query in the database (read-only by default)",
)
async def sql_script(request_data: SQLQueryParams):
    """
    Runs an SQL query in the database with optional parameters.

    Args:
    - request_data (SQLQueryParams): The SQL query parameters, that contains query and params.
            query (str): The SQL query to execute.
            params (Optional[tuple]): Optional parameters for the SQL query.

    Example request body:
        {
            "query": "SELECT * FROM anomaly_detection_log LIMIT %s",
            "params": [10]
        }
    """
    status_code = status.HTTP_200_OK
    response_data = {}
    try:
        query, params = request_data.query, request_data.params
        allow_write = request_data.allow_write and ALLOW_UNSAFE_SQL_SCRIPTS
        if request_data.allow_write and not ALLOW_UNSAFE_SQL_SCRIPTS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Write SQL is disabled by server configuration.",
            )

        commit = allow_write and not query.strip().upper().startswith(("SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN"))
        sql_resp = run_sql_script(
            mysql_conn,
            query,
            params,
            commit=commit,
            allow_write=allow_write,
        )
        if sql_resp.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=sql_resp.get("message", "Failed to run SQL query."),
            )
        response_data = {
            "status": "success",
            "query": query,
            "params": params,
        } | sql_resp
    except HTTPException:
        raise
    except Exception as excep:
        logger.exception("Unexpected error while running SQL script: %s", excep)
        status_code = status.HTTP_400_BAD_REQUEST if status_code == status.HTTP_200_OK else status_code
        detail = response_data.get("detail", "Failed to run SQL query in the MySQL server")
        raise HTTPException(status_code=status_code, detail=detail) from excep
    return response_data


@router.post(
    "/qa",
    response_model=Dict,
    status_code=status.HTTP_200_OK,
    summary="Convert query into sql command & interact with SQL database",
)
async def sql_question_answer(request_data: SQLQARequest):
    """
    Converts query into sql command & interact with SQL database

    Example request body:
        {
            "log_type": "anomaly_detection_log",
            "question": "What are the latest 5 records?",
            "model": "gpt-4o-mini"
        }
    """
    status_code = status.HTTP_200_OK
    response_data = {}
    try:
        text2sql_cfg_obj = TEXT2SQL_CFG_DICT[request_data.log_type.value]
        llm_sql_query = text_to_sql(
            question=request_data.question,
            text2sql_cfg_obj=text2sql_cfg_obj,
            llm_config={"model": request_data.model.value, "temperature": 0},
            top_k=text2sql_cfg_obj.top_k,
        )

        query, params = sep_query_and_params(llm_sql_query.replace('"', ""))
        sql_resp = run_sql_script(
            mysql_conn,
            query,
            params,
            commit=False,
            allow_write=False,
        )
        if sql_resp.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=sql_resp.get("message", "Failed to execute generated SQL query."),
            )

        response_data = {
            "status": "success",
            "question": request_data.question,
            "query": llm_sql_query,
            "response": sql_resp,
        }
    except HTTPException:
        raise
    except Exception as excep:
        logger.exception("Unexpected error while running text-to-SQL: %s", excep)
        status_code = status.HTTP_400_BAD_REQUEST if status_code == status.HTTP_200_OK else status_code
        detail = response_data.get("detail", "failed to conduct query in the MySQL server")
        raise HTTPException(status_code=status_code, detail=detail) from excep
    return response_data
