"""
Question Answer api endpoint
"""

import logging
from typing import Dict
from fastapi import APIRouter, status, HTTPException
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from app.api.langchain_custom.llms import load_llm
from app.core.config import VECTOR_STORE_DIR
from app.models.model import QARequest, LLMModel


router = APIRouter()
logger = logging.getLogger("qa_route")
RAG_PROMPT = ChatPromptTemplate.from_template(
    "Answer the question using only the provided context.\n\nContext:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"
)


@router.post(
    "",
    response_model=Dict,
    status_code=status.HTTP_200_OK,
    summary="Extract query emb, find most similar embs from vector db & answer query with chatbot",
)
async def question_answer(request_data: QARequest, model: LLMModel = LLMModel.GPT_4o_Mini):
    """Extract query emb, find most similar embs from vector db & answer query with chatbot"""
    status_code = status.HTTP_200_OK
    response_data = {}
    try:
        vectorstore = Chroma(
            persist_directory=VECTOR_STORE_DIR,
            embedding_function=OpenAIEmbeddings(),
        )
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | RAG_PROMPT
            | load_llm(model)
            | StrOutputParser()
        )

        answer = rag_chain.invoke(request_data.query)
        response_data = {
            "status": "success",
            "query": request_data.query,
            "answer": answer,
        }
    except Exception as excep:
        logger.exception("failed to run RAG QA: %s", excep)
        status_code = status.HTTP_400_BAD_REQUEST if status_code == status.HTTP_200_OK else status_code
        detail = response_data.get("detail", "failed to conduct query search in server")
        raise HTTPException(status_code=status_code, detail=detail) from excep
    return response_data
