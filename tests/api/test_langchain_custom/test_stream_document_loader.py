"""
Test redis api
The redis server must be running in the appropriate port
"""
import json
import pytest
from app.api.langchain_custom.stream_document_loader import CustomStreamDocumentLoader


def test_lazy_load(mock_one_anomaly_det_log_file_path_and_content):
    """Test the lazy loading of documents synchronously."""
    _, content = mock_one_anomaly_det_log_file_path_and_content
    enc = json.detect_encoding(content)
    loader = CustomStreamDocumentLoader(content)
    documents = list(loader.lazy_load())

    assert len(documents) == 600
    for doc, cline in zip(documents, content.splitlines()):
        cline = cline.decode(enc)
        assert doc.page_content.strip() == cline

@pytest.mark.asyncio
async def test_alazy_load(mock_one_anomaly_det_log_file_path_and_content):
    """Test the lazy loading of documents asynchronously."""
    _, content = mock_one_anomaly_det_log_file_path_and_content
    enc = json.detect_encoding(content)
    loader = CustomStreamDocumentLoader(content)
    async_documents = []
    async for doc in loader.alazy_load():
        async_documents.append(doc)

    assert len(async_documents) == 600
    for doc, cline in zip(async_documents, content.splitlines()):
        cline = cline.decode(enc)
        assert doc.page_content.strip() == cline
