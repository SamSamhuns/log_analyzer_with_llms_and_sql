"""
Summarization api endpoints
"""
import logging
import traceback
from typing import Dict, List
from fastapi import APIRouter, File, UploadFile, status, HTTPException
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import WebBaseLoader

from models.model import SummarizerMode, LLMModel
from api.langchain_custom.llms import load_llm
from api.langchain_custom.stream_document_loader import CustomStreamDocumentLoader

router = APIRouter()
logger = logging.getLogger('summarize_route')


@router.post("/files/{SummarizerMode}", response_model=Dict,
             status_code=status.HTTP_200_OK,
             summary="Summarize uploaded file(s)")
async def summarize_files(
        summarizer_mode: SummarizerMode,
        model: LLMModel = LLMModel.Llamafile,
        files: List[UploadFile] = File(...),):
    """Extract text from files and summarize based on selected mode"""
    response_data = {}
    try:
        print(f"Running summarization for files: {[file.filename for file in files]}")
        llm = load_llm(model.value)
        if summarizer_mode == "combined":
            # Combined summarization logic
            combined_docs = []
            for file in files:
                content = await file.read()
                loader = CustomStreamDocumentLoader(content)
                docs = loader.load()
                combined_docs.extend(docs)
            chain = load_summarize_chain(llm, chain_type="stuff")
            summary = chain.invoke(combined_docs)["output_text"]
            response_data = {
                "status": "success",
                "detail": "Combined summarization successful",
                "summary": summary}
        else:
            # Individual summarization logic
            summaries = {}
            for file in files:
                content = await file.read()
                loader = CustomStreamDocumentLoader(content)
                docs = loader.load()
                chain = load_summarize_chain(llm, chain_type="stuff")
                summaries[file.filename] = chain.invoke(docs)["output_text"]
            response_data = {
                "status": "success",
                "detail": "Individual summarization successful",
                "summaries": summaries}
    except Exception as excep:
        logger.error("%s: %s", excep, traceback.print_exc())
        detail = "Failed to summarize file contents in server"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from excep
    return response_data


@router.post("/urls", response_model=Dict,
             status_code=status.HTTP_200_OK,
             summary="Summarize content(s) from url")
async def summarize_urls(
        urls: List[str],
        model: LLMModel = LLMModel.Llamafile):
    """Extract text from files, summarize contents & return summary"""
    status_code = status.HTTP_200_OK
    response_data = {}
    try:
        llm = load_llm(model.value)
        loader = WebBaseLoader(urls)
        docs = loader.load()
        chain = load_summarize_chain(llm, chain_type="stuff")
        summary = chain.invoke(docs)["output_text"]

        # run summarization api
        summarization_results = {"status": "success", "summary": summary}
        response_data = summarization_results
    except Exception as excep:
        logger.error("%s: %s", excep, traceback.print_exc())
        status_code = status.HTTP_400_BAD_REQUEST if status_code == status.HTTP_200_OK else status_code
        detail = response_data.get("detail", "failed to summarize url contents in server")
        raise HTTPException(status_code=status_code, detail=detail) from excep
    return response_data
