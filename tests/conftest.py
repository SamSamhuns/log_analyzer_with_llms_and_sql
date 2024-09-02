"""
Test configurations
"""
import os
import sys
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
import pymysql
from pymysql.cursors import DictCursor

sys.path.append("app")

# custom test settings
MYSQL_TEST_ID = -3
MYSQL_TEST_TABLE = "test"
os.environ["MYSQL_CUR_TABLE"] = MYSQL_TEST_TABLE  # chg cur table for test duration

# custom imports
from app.server import app  # must be import after changing MYSQL_CUR_TABLE env var
from app.core.config import (
    MYSQL_HOST, MYSQL_PORT,
    MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)
from app.core.setup import ANOMALY_DETECTION_LOG_TEXT2SQL_CFG


def _load_file_content(fpath: str) -> bytes:
    """
    Load file from fpath and return as bytes
    """
    with open(fpath, 'rb') as fptr:
        file_content = fptr.read()
    return file_content


@pytest_asyncio.fixture(scope="function")
async def test_app_asyncio():
    """
    Sets up the async server
    for httpx>=20, follow_redirects=True (cf. https://github.com/encode/httpx/releases/tag/0.20.0)
    """
    async with AsyncClient(app=app, base_url="http://test") as aclient:
        yield aclient  # testing happens here


@pytest.fixture(scope="module")
def test_mysql_connec():
    """Yields a mysql connection instance"""
    print("Setting mysql connection")
    mysql_conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        db=MYSQL_DATABASE,
        cursorclass=DictCursor
    )
    # create test table if not present & purge all existing data
    with mysql_conn.cursor() as cursor:
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {MYSQL_TEST_TABLE} LIKE {ANOMALY_DETECTION_LOG_TEXT2SQL_CFG.table_name};")
        cursor.execute(f"DELETE FROM {MYSQL_TEST_TABLE}")
    mysql_conn.commit()
    yield mysql_conn
    # drop table in teardown
    print("Tearing mysql connection")
    with mysql_conn.cursor() as cursor:
        cursor.execute(f"DROP TABLE {MYSQL_TEST_TABLE}")
    mysql_conn.commit()
    mysql_conn.close()


@pytest.fixture(scope="session")
def gen_mock_data():
    """
    returns a func to create a data dict for testing with anomaly_detection_log
    """
    def _gen_data(fid: int = -1):
        test_data = {
            'ID': fid,
            'log_fid': '2bd5f7de3578d0ecc13de276ea4a16d8',
            'timestamp': date(2024, 8, 21),
            'inference_time': 50.12,
            'prediction': 1
        }
        return test_data
    return _gen_data


@pytest.fixture(scope="session")
def mock_one_anomaly_detection_log_file():
    """
    load and return an anomaly detection log file
    """
    fpath = "tests/static/sample_anomaly_detection.log"
    return fpath, _load_file_content(fpath)


@pytest.fixture(scope="session")
def mock_file_url():
    """
    returns an anomaly detection log file url
    """
    return "https://raw.githubusercontent.com/SamSamhuns/log_analyzer/master/tests/static/sample_anomaly_detection.log"
