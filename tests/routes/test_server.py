"""
Tests if server is running or not
"""
import httpx
import pytest


@pytest.mark.asyncio
@pytest.mark.timeout(10)  # Timeout in seconds
async def test_server_root(test_app_asyncio: httpx.AsyncClient):
    """
    Test if fastapi+uvicorn server is up
    """
    response = await test_app_asyncio.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "Welcome to the Log Analysis service": "Please visit /docs for list of apis"}
