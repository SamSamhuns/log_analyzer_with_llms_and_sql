"""
Question Answer api endpoint
"""
import logging
import traceback
from typing import Dict
from fastapi import APIRouter, status, HTTPException
from langchain import hub
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from api.langchain_custom.llms import llm
from core.config import VECTOR_STORE_DIR


router = APIRouter()
logger = logging.getLogger('qa_route')


@router.post("", response_model=Dict,
             status_code=status.HTTP_200_OK,
             summary="Extract query emb, find most similar embs from vector db & answer query with chatbot")
async def question_answer(
        query: str):
    """Extract query emb, find most similar embs from vector db & answer query with chatbot"""
    status_code = status.HTTP_200_OK
    response_data = {}
    try:
        vectorstore = Chroma(persist_directory=VECTOR_STORE_DIR, embedding_function=OpenAIEmbeddings(),)
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})
        prompt = hub.pull("rlm/rag-prompt")

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        retrieved_docs = rag_chain.invoke(query)["answer"]
        response_data = {"query": query,
                         "retrieved_docs": retrieved_docs}
    except Exception as excep:
        logger.error("%s: %s", excep, traceback.print_exc())
        status_code = status.HTTP_400_BAD_REQUEST if status_code == status.HTTP_200_OK else status_code
        detail = response_data.get("detail", "failed to conduct query search in server")
        raise HTTPException(status_code=status_code, detail=detail) from excep
    return response_data
