"""
Test sql route
"""
import pytest
import httpx
from pymysql.connections import Connection
from tests.conftest import MYSQL_TEST_ANOMALY_DET_LOG_TABLE


@pytest.mark.asyncio
async def test_sql_script(test_app_asyncio: httpx.AsyncClient, test_mysql_connec: Connection):
    request_data = {
        "query": f"SELECT * FROM {MYSQL_TEST_ANOMALY_DET_LOG_TABLE} LIMIT %s",
        "params": [10]
    }
    response = await test_app_asyncio.post("/sql/script", json=request_data)
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["message"] == "SQL script executed successfully, fetched results."


@pytest.mark.asyncio
async def test_sql_question_answer(test_app_asyncio: httpx.AsyncClient, test_mysql_connec: Connection, mock_text_to_sql):
    # Test for a specific log file type and a sample question
    params = {
        'log_type': 'anomaly_detection_log',
        'question': 'Give me the latest logs',
        'model': 'llamafile',
    }
    response = await test_app_asyncio.post("sql/qa/{LogFileType}", params=params)
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["response"]["status"] == "success"
    assert data["response"]["message"] == "SQL script executed successfully, fetched results."
