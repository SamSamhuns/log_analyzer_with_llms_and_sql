"""
Test configurations
"""
import sys
from io import BytesIO
from datetime import datetime
from typing import Callable, Tuple

import httpx
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import UploadFile
sys.path.append("app")

# custom test settings
MYSQL_TEST_ID = -3
MYSQL_TEST_ANOMALY_DET_LOG_TABLE = "test_anomaly_detection_log"
MYSQL_TEST_LOG_ID_TB_NAME = "test_log_fid"
MYSQL_TEST_GENERAL_ID_TB_NAME = "test_general_fid"

# config imports
from app.core.config import (
    MYSQL_LOG_ID_TB_NAME, MYSQL_GENERAL_ID_TB_NAME)
from app.server import upsert
from app.core.setup import mysql_conn, ANOMALY_DETECTION_LOG_TEXT2SQL_CFG
# get default table names and rename to test tables
upsert.MYSQL_LOG_ID_TB_NAME = MYSQL_TEST_LOG_ID_TB_NAME
upsert.MYSQL_GENERAL_ID_TB_NAME = MYSQL_TEST_GENERAL_ID_TB_NAME
from app.server import app  # must be import after changing all the core_config vars


def _load_file_content(fpath: str) -> bytes:
    """
    Load file from fpath and return as bytes
    """
    with open(fpath, 'rb') as fptr:
        file_content = fptr.read()
    return file_content


@pytest_asyncio.fixture(scope="function")
async def test_app_asyncio() -> httpx.AsyncClient:
    """
    Sets up the async server
    """
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as aclient:
        yield aclient  # testing happens here


@pytest.fixture(scope="module")
def test_mysql_connec():
    """Yields a mysql connection instance"""
    try:
        print("Setting mysql connection")
        # create test tables if not present & purge all existing data
        print("Creating test tables based on existing table schemas")
        for orig_tb, test_tb in zip(
                [ANOMALY_DETECTION_LOG_TEXT2SQL_CFG.table_name, MYSQL_LOG_ID_TB_NAME, MYSQL_GENERAL_ID_TB_NAME],
                [MYSQL_TEST_ANOMALY_DET_LOG_TABLE, MYSQL_TEST_LOG_ID_TB_NAME, MYSQL_TEST_GENERAL_ID_TB_NAME]
                ):
            with mysql_conn() as conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(f"CREATE TABLE IF NOT EXISTS {test_tb} LIKE {orig_tb};")
                        cursor.execute(f"DELETE FROM {test_tb};")
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    raise e
        yield mysql_conn
    finally:
        # drop tables in teardown
        print("Tearing mysql connection")
        for test_tb in [MYSQL_TEST_ANOMALY_DET_LOG_TABLE, MYSQL_TEST_LOG_ID_TB_NAME, MYSQL_TEST_GENERAL_ID_TB_NAME]:
            with mysql_conn() as conn:
                with conn.cursor() as cursor:
                    try:
                        cursor.execute(f"DROP TABLE {test_tb}")
                        conn.commit()
                    except Exception:
                        pass


@pytest.fixture(scope="session")
def gen_mock_anomaly_det_log_data() -> Callable:
    """
    returns a func to create a data dict 
    for testing with anomaly_detection_log
    """
    def _gen_data(fid: int = -1):
        test_data = {
            'ID': fid,
            'log_fid': '2bd5f7de3578d0ecc13de276ea4a16d8',
            'timestamp': datetime(2024, 8, 21, 0, 0),
            'inference_time': 50.12,
            'prediction': 1
        }
        return test_data
    return _gen_data


@pytest.fixture(scope="session")
def mock_valid_anomaly_det_log_str() -> str:
    """Generate valid anomaly det log str"""
    return """
    2024-01-01T12:00:00Z, 100ms, 1
    2024-01-01T13:00:00Z, 200ms, 0
    """


@pytest.fixture(scope="session")
def mock_invalid_anomaly_det_log_str() -> str:
    """Generate anomaly det log str 
    with one valid and one invalid line"""
    return """
    2024-01-01 12:00:00, 100ms, 1
    2024-01-01T13:00:00Z, xyz ms, 0
    """


@pytest.fixture(scope="session")
def mock_one_anomaly_det_log_file_path_and_content() -> Tuple[str, bytes]:
    """
    load and return an anomaly detection log file
    """
    fpath = "tests/static/sample_anomaly_detection.log"
    return fpath, _load_file_content(fpath)


@pytest.fixture(scope="session")
def mock_file_url() -> str:
    """
    returns a random file url
    """
    return "https://raw.githubusercontent.com/SamSamhuns/face_registration_and_recognition_milvus/master/README.md"


@pytest.fixture
def gen_mock_upload_file() -> Callable:
    """Mock UploadFile"""
    def _gen_uploadfile(fname: str = "sample.log"):
        return UploadFile(
            filename=fname,
            file=BytesIO(b"example content"))
    return _gen_uploadfile


@pytest.fixture
def mock_load_summarize_chain(mocker):
    """
    Mock load_summarize_chain using a separate fixture
    Note: IMPORTANT the app.server.summarize must be patched instead of the app.routes.summarize
    since the conftest.py already imports app from server.py where summarize.py is loaded
    """
    mock_chain = mocker.MagicMock()
    mock_chain.invoke.return_value = {"output_text": "Mocked Summary"}
    mocker.patch('app.server.summarize.load_summarize_chain', return_value=mock_chain)
    return mock_chain


@pytest.fixture
def mock_load_llm(mocker):
    """Mock load_llm using a separate fixture"""
    mock_llm = mocker.MagicMock()
    mocker.patch('app.server.summarize.load_llm', return_value=mock_llm)
    return mock_llm


@pytest.fixture
def mock_text_to_sql(mocker):
    """Mock text_to_sql using a separate fixture"""
    mock_text2sql_resp = f"SELECT * FROM {MYSQL_TEST_ANOMALY_DET_LOG_TABLE} LIMIT 5;"
    mocker.patch('app.server.sql.text_to_sql', return_value=mock_text2sql_resp)
    return mock_text2sql_resp


@pytest.fixture
def mock_chroma_db(mocker):
    """Mock Chroma db using a separate fixture"""
    mock_chroma = mocker.MagicMock()
    mocker.patch('app.server.upsert.Chroma')
    mocker.patch('app.server.upsert.Chroma.from_documents')
    return mock_chroma


@pytest.fixture
def mock_openai_emb(mocker):
    """Mock OpenAIEmbeddings"""
    mock_openai_emb = mocker.MagicMock()
    mocker.patch('app.server.upsert.OpenAIEmbeddings')
    return mock_openai_emb

