"""
Test upsert route
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_log_upsert(
        test_app_asyncio: httpx.AsyncClient, test_mysql_connec,
        mock_one_anomaly_det_log_file_path_and_content):
    """
    Test one log upsert
    """
    fpath, fcontent = mock_one_anomaly_det_log_file_path_and_content
    files = [("files", (fpath, fcontent, "text/plain"))]

    response = await test_app_asyncio.post(
        "/upsert/logs/{LogFileType}?log_type=anomaly_detection_log",
        files=files)

    data = response.json()
    assert response.status_code == 200
    assert data["content"][0] == fpath
    assert data["status"] == "success"
    assert "uploaded and upserted 587 entries from 1 file(s) into the sql table." in data["detail"]


@pytest.mark.asyncio
async def test_file_upsert_success(test_app_asyncio: httpx.AsyncClient, test_mysql_connec):
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
async def test_file_upsert_unsupported_file(test_app_asyncio: httpx.AsyncClient):
    """Test the file_upsert endpoint with an unsupported file type"""
    files = [
        ("files", ("data.xml", b"<xml>data</xml>", "text/xml")),
    ]
    response = await test_app_asyncio.post("/upsert/files", files=files)
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"]
