"""
Test upsert route
"""

from typing import Tuple
from pymysql.connections import Connection
import pytest
import httpx

from app.server import upsert
from app.utils.common import get_file_md5


@pytest.mark.asyncio
async def test_log_upsert(
    test_app_asyncio: httpx.AsyncClient,
    test_mysql_connec: Connection,
    mock_one_anomaly_det_log_file_path_and_content: Tuple[str, bytes],
):
    """
    Test one log upsert
    """
    fpath, fcontent = mock_one_anomaly_det_log_file_path_and_content
    files = [("files", (fpath, fcontent, "text/plain"))]
    data = {"log_file_id": "test_logfile_id"}
    response = await test_app_asyncio.post("/upsert/logs?log_type=anomaly_detection_log", data=data, files=files)

    data = response.json()
    assert response.status_code == 200
    assert data["content"][0] == fpath
    assert data["status"] == "success"
    assert "uploaded and upserted 587 entries from 1 file(s) into the sql table." in data["detail"]


@pytest.mark.asyncio
async def test_log_upsert_log_file_id_too_long(test_app_asyncio: httpx.AsyncClient):
    """Reject log_file_id values that exceed DB column length."""
    files = [("files", ("sample.log", b"2024-01-01T12:00:00Z, 100ms, 1\n", "text/plain"))]
    data = {"log_file_id": "x" * 33}
    response = await test_app_asyncio.post("/upsert/logs?log_type=anomaly_detection_log", data=data, files=files)

    assert response.status_code == 400
    assert "at most 32 characters" in response.json()["detail"]


@pytest.mark.asyncio
async def test_log_upsert_skips_duplicate_file_md5_across_log_types(
    test_app_asyncio: httpx.AsyncClient,
    test_mysql_connec: Connection,
):
    """A duplicate file_md5 should be skipped regardless of selected log type."""
    log_content = b"2024-01-01T12:00:00Z, 100ms, 1\n"
    files = [("files", ("duplicate.log", log_content, "text/plain"))]

    first_response = await test_app_asyncio.post(
        "/upsert/logs?log_type=anomaly_detection_log",
        data={"log_file_id": "dup_log_group_1"},
        files=files,
    )
    assert first_response.status_code == 200
    assert first_response.json()["status"] == "success"

    second_response = await test_app_asyncio.post(
        "/upsert/logs?log_type=rta_worker_switch_log",
        data={"log_file_id": "dup_log_group_2"},
        files=files,
    )
    second_data = second_response.json()
    assert second_response.status_code == 200
    assert second_data["status"] == "failed"
    assert "already exist" in second_data["detail"]

    with test_mysql_connec() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) AS cnt FROM {upsert.MYSQL_LOG_ID_TB_NAME} WHERE file_md5 = %s",
                (get_file_md5(log_content),),
            )
            result = cursor.fetchone()
    assert result["cnt"] == 1


@pytest.mark.asyncio
async def test_log_upsert_invalid_content_does_not_insert_log_fid_metadata(
    test_app_asyncio: httpx.AsyncClient,
    test_mysql_connec: Connection,
):
    """Invalid log content should not create orphan metadata records."""
    bad_content = b"this line is invalid for anomaly parser\n"
    files = [("files", ("bad.log", bad_content, "text/plain"))]
    response = await test_app_asyncio.post(
        "/upsert/logs?log_type=anomaly_detection_log",
        data={"log_file_id": "invalid_log_group"},
        files=files,
    )

    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "failed"

    with test_mysql_connec() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) AS cnt FROM {upsert.MYSQL_LOG_ID_TB_NAME} WHERE file_md5 = %s",
                (get_file_md5(bad_content),),
            )
            result = cursor.fetchone()
    assert result["cnt"] == 0


@pytest.mark.asyncio
async def test_file_upsert_success(
    test_app_asyncio: httpx.AsyncClient,
    test_mysql_connec: Connection,
    mock_chroma_db,
    mock_openai_emb,
):
    """Test the file_upsert endpoint"""
    files = [
        ("files", ("document.txt", b"TXT file content", "text/plain")),
    ]
    response = await test_app_asyncio.post("/upsert/files", files=files)
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "success"
    assert "document.txt" in data["content"]


@pytest.mark.asyncio
async def test_file_duplicated_upsert(test_app_asyncio: httpx.AsyncClient, test_mysql_connec: Connection):
    """Test the file_upsert endpoint"""
    files = [
        ("files", ("document.txt", b"TXT file content", "text/plain")),
    ]
    response = await test_app_asyncio.post("/upsert/files", files=files)
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "failed"
    assert data["detail"] == "uploaded file(s) could not be uploaded or already exist in system"


@pytest.mark.asyncio
async def test_file_upsert_unsupported_file(test_app_asyncio: httpx.AsyncClient):
    """Test the file_upsert endpoint with an unsupported file type"""
    files = [
        ("files", ("data.xml", b"<xml>data</xml>", "text/xml")),
    ]
    response = await test_app_asyncio.post("/upsert/files", files=files)
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"]
