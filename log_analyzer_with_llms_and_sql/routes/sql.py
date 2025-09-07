"""
SQL Question Answer api endpoint
"""
import logging
import traceback
from typing import Dict
from fastapi import APIRouter, status, HTTPException, Form

from api.langchain_custom.text2sql import text_to_sql
from api.mysql import run_sql_script, sep_query_and_params
from models.model import SQLQueryParams, LogFileType, LLMModel
from core.setup import mysql_conn, TEXT2SQL_CFG_DICT

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
    - request_data (SQLQueryParams): The SQL query parameters, that contains query and params.
            query (str): The SQL query to execute.
            params (Optional[tuple]): Optional parameters for the SQL query.

    Example request body:
        {
            "query": "UPDATE users SET name = %s, email = %s WHERE id = %s",
            "params": ["Jane Doe", "jane.doe@example.com", 1]
        }
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
        detail = response_data.get("detail", "Failed to run SQL query in the MySQL server")
        raise HTTPException(status_code=status_code, detail=detail) from excep
    return response_data


@router.post("/qa", response_model=Dict,
             status_code=status.HTTP_200_OK,
             summary="Convert query into sql command & interact with SQL database")
async def sql_question_answer(
        log_type: LogFileType,
        question: str = Form(...),
        model: LLMModel = LLMModel.GPT_4o_Mini):
    """
    Converts query into sql command & interact with SQL database

    Example request body:
        {
            "query": "What are the latest 5 records?"
        }
    """
    status_code = status.HTTP_200_OK
    response_data = {}
    try:
        text2sql_cfg_obj = TEXT2SQL_CFG_DICT[log_type.value]
        llm_sql_query = text_to_sql(
            question=question,
            text2sql_cfg_obj=text2sql_cfg_obj,
            llm_config={"model": model.value, "temperature": 0},
            top_k=text2sql_cfg_obj.top_k)

        query, params = sep_query_and_params(
            llm_sql_query.replace("\"", ''))

        try:
            sql_resp = run_sql_script(
                mysql_conn, query, params, commit=not query.lower().startswith("select"))
            sql_data_response = {
                "status": "success",
                "question": question,
                "query": llm_sql_query,
                "response": sql_resp}
        except Exception as excep:
            response_data["detail"] = \
                f"Failed to run SQL query {query} with params {params} in MySQL server: {excep}"
            raise Exception

        response_data = sql_data_response
    except Exception as excep:
        logger.error("%s: %s", excep, traceback.print_exc())
        status_code = status.HTTP_400_BAD_REQUEST if status_code == status.HTTP_200_OK else status_code
        detail = response_data.get("detail", "failed to conduct query in the MySQL server")
        raise HTTPException(status_code=status_code, detail=detail) from excep
    return response_data
