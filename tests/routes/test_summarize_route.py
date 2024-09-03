"""
Test summarization endpoint
WARNING: The load_llm and load_summarize_chain fixtures are defined in conftest.py and are mocked
If lagnchain does breaking changes in  the apis of load_llm and load_summarize_chain, this test mights till pass
"""
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("summarizer_mode", ["individual", "combined"])
async def test_summarize_single_file(mock_load_summarize_chain, mock_load_llm,
                                     test_app_asyncio, gen_mock_upload_file, summarizer_mode):
    """Test the individual file summarize mode"""
    upload_file = gen_mock_upload_file()
    response = await test_app_asyncio.post(
        "summarize/files/{SummarizerMode}?summarizer_mode=" + summarizer_mode,
        files={"files": (upload_file.filename,
                         upload_file.file.read(), "text/plain")},
    )

    data = response.json()
    assert response.status_code == 200
    assert "success" in data["status"]
    if summarizer_mode == "individual":
        assert "Mocked Summary" in data["summaries"][upload_file.filename]
    else:
        assert "Mocked Summary" in data["summary"]


@pytest.mark.asyncio
@pytest.mark.parametrize("summarizer_mode", ["individual", "combined"])
async def test_summarize_multiple_files(mock_load_summarize_chain, mock_load_llm,
                                        test_app_asyncio, gen_mock_upload_file, summarizer_mode):
    """Test the individual file summarize mode"""
    upload_file1 = gen_mock_upload_file("sample1.log")
    upload_file2 = gen_mock_upload_file("sample2.log")
    response = await test_app_asyncio.post(
        "summarize/files/{SummarizerMode}?summarizer_mode=" + summarizer_mode,
        files=[
            ('files', (upload_file1.filename, upload_file1.file.read(), "text/plain")),
            ('files', (upload_file2.filename, upload_file2.file.read(), "text/plain")),],
    )
    data = response.json()
    assert response.status_code == 200
    assert "success" in data["status"]
    if summarizer_mode == "individual":
        assert "Mocked Summary" in data["summaries"][upload_file1.filename]
        assert "Mocked Summary" in data["summaries"][upload_file2.filename]
    else:
        assert "Mocked Summary" in data["summary"]


@pytest.mark.asyncio
async def test_summarize_urls(test_app_asyncio, mock_file_url,
                              mock_load_summarize_chain, mock_load_llm):
    response = await test_app_asyncio.post(
        "/summarize/urls",
        json=[mock_file_url]
    )
    data = response.json()
    assert response.status_code == 200
    assert "success" in data["status"]
    assert "Mocked Summary" in data["summary"]
