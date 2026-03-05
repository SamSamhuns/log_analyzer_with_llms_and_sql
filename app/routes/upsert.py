"""
Upsert file api
"""

import os
import os.path as osp
import json
import uuid
import logging
from typing import List, Dict
from datetime import datetime

from fastapi import APIRouter, File, Form, UploadFile, status, HTTPException
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
)
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import (
    HTMLHeaderTextSplitter,
    LatexTextSplitter,
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
    RecursiveJsonSplitter,
)

from app.api.mysql import entries_exist, insert_bulk_data_into_sql, insert_data_into_sql
from app.api.log_format.log_parser import gen_log_obj_list
from app.models.model import LogFileType, EmbeddingModel
from app.utils.common import get_file_md5
from app.utils.chunking import CODE_EXT_MAPPING
from app.core.setup import mysql_conn
from app.core.config import (
    FILE_STORAGE_DIR,
    VECTOR_STORE_DIR,
    MYSQL_LOG_ID_TB_NAME,
    MYSQL_GENERAL_ID_TB_NAME,
)


SUPPORTED_FILES_EXT = {".txt", ".pdf", ".html", ".json"}
MAX_LOG_FILE_ID_LEN = 32
router = APIRouter()
logger = logging.getLogger("upsert_route")


@router.post(
    "/logs",
    response_model=Dict,
    status_code=status.HTTP_200_OK,
    summary="Extract info from log files and store them in a sql database",
)
async def log_upsert(
    log_type: LogFileType,
    log_file_id: str = Form(...),
    files: List[UploadFile] = File(...),
):
    """
    Extract info from log file(s) and store them in a sql database.
    log_file_id should be unique string identifier for log files
    """
    status_code = status.HTTP_200_OK
    logfile_type = log_type.value
    log_file_id = log_file_id.strip()
    response_data = {}
    logged_files = []
    total_upserted_entries = 0
    if not log_file_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="log_file_id cannot be empty.")
    if len(log_file_id) > MAX_LOG_FILE_ID_LEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"log_file_id must be at most {MAX_LOG_FILE_ID_LEN} characters.",
        )
    try:
        for file in files:
            f_content = await file.read()
            f_name = file.filename

            # check if file alr exists in the db using md5sum
            fmd5 = get_file_md5(f_content)
            if entries_exist(
                mysql_conn,
                MYSQL_LOG_ID_TB_NAME,
                {"file_md5": fmd5},
            ):
                logger.info("%s already stored and indexed in db. Skipping", f_name)
                continue

            # decode txt file contents
            enc = json.detect_encoding(f_content)
            file_content_str = f_content.decode(enc)
            # get log object list from file contents using the appropriate logfile_type format
            log_obj_list = gen_log_obj_list(file_content_str, logfile_id=log_file_id, logfile_type=logfile_type)
            if not log_obj_list:
                logger.warning("%s contains no valid log lines for %s", f_name, logfile_type)
                continue

            log_fid_obj = {
                "log_fid": log_file_id,
                "file_md5": fmd5,
                "inserted_date": datetime.now().strftime("%Y-%m-%d"),
                "logfile_type": logfile_type,
                "size": len(f_content) / 1024,
            }  # size in KB
            with mysql_conn() as conn:  # atomic transaction for both log_fid and log_obj_list insertions
                try:
                    insertion_status = insert_data_into_sql(
                        mysql_conn=mysql_conn,
                        tb_name=MYSQL_LOG_ID_TB_NAME,
                        data_dict=log_fid_obj,
                        commit=False,
                        conn=conn,
                    )
                    if insertion_status["status"] == "failed":
                        raise ValueError(insertion_status["message"])

                    insertion_status = insert_bulk_data_into_sql(
                        mysql_conn=mysql_conn,
                        tb_name=logfile_type,
                        data_dicts=log_obj_list,
                        commit=False,
                        conn=conn,
                    )
                    if insertion_status["status"] == "failed":
                        raise ValueError(insertion_status["message"])
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise

            total_upserted_entries += len(log_obj_list)
            logged_files.append(f_name)
        if len(logged_files) > 0:
            response_data["status"] = "success"
            response_data["detail"] = (
                f"uploaded and upserted {total_upserted_entries} entries "
                + f"from {len(files)} file(s) into the sql table."
            )
            if len(logged_files) != len(files):
                response_data["detail"] += (
                    f"files {set(f.filename for f in files) - set(logged_files)} were not uploaded"
                )
            response_data["content"] = logged_files
        else:
            response_data["status"] = "failed"
            response_data["detail"] = "uploaded file(s) could not be uploaded or already exist in system"
    except HTTPException:
        raise
    except Exception as excep:
        logger.exception("failed to upsert log files: %s", excep)
        status_code = status.HTTP_400_BAD_REQUEST if status_code == status.HTTP_200_OK else status_code
        detail = response_data.get("detail") or str(excep) or "failed to upload files to server"
        raise HTTPException(status_code=status_code, detail=detail) from excep
    return response_data


@router.post(
    "/files",
    response_model=Dict,
    status_code=status.HTTP_200_OK,
    summary="Extract text from file(s) & save emb in a vector db. Supported file types are .txt, .pdf, .html, and .json.",
)
async def file_upsert(
    embedding_model: EmbeddingModel = EmbeddingModel.OPENAI_TEXT_EMBEDDING_MODEL,
    files: List[UploadFile] = File(...),
):
    """
    Extract text from file(s) & save emb in a vector db
    """
    status_code = status.HTTP_200_OK
    response_data = {}
    emb_files = []

    # Initialize Embedding Model once outside the loop
    if embedding_model == EmbeddingModel.HUGGINGFACE_TEXT_EMBEDDING_MODEL:
        emb = HuggingFaceEmbeddings(model_name=embedding_model.value)
    else:
        emb = OpenAIEmbeddings(model=embedding_model.value)

    try:
        for file in files:
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in SUPPORTED_FILES_EXT:
                response_data["detail"] = (
                    f"Only files with extensions {SUPPORTED_FILES_EXT} supported. {file.filename} is invalid"
                )
                raise ValueError(response_data["detail"])

            f_content = await file.read()
            f_name = file.filename
            fmd5 = get_file_md5(f_content)
            if entries_exist(mysql_conn, MYSQL_GENERAL_ID_TB_NAME, {"file_md5": fmd5}):
                logger.info("%s already stored and indexed in db. Skipping", f_name)
                continue

            # insert log file entry into log_fid table if it didn't exist
            fid_obj = {
                "file_md5": fmd5,
                "inserted_date": datetime.now().strftime("%Y-%m-%d"),
                "file_type": file_ext,
                "size": len(f_content) / 1024,
            }  # size in KB
            insertion_status = insert_data_into_sql(
                mysql_conn,
                tb_name=MYSQL_GENERAL_ID_TB_NAME,
                data_dict=fid_obj,
            )
            if insertion_status["status"] == "failed":
                raise ValueError(insertion_status["message"])

            doc_id = str(uuid.uuid4())
            fsave_path = osp.join(FILE_STORAGE_DIR, doc_id + osp.splitext(f_name)[-1])
            with open(fsave_path, "wb") as f_write:
                f_write.write(f_content)

            # Load the data
            f_ext = osp.splitext(file.filename)[-1].lower()
            # Determine the best splitting strategy
            splits = []

            # 1. SPECIALIZED CODE SPLITTING
            if f_ext in CODE_EXT_MAPPING:
                lang = CODE_EXT_MAPPING[f_ext]
                # .from_language automatically selects separators like 'def ', 'class ', etc.
                splitter = RecursiveCharacterTextSplitter.from_language(language=lang, chunk_size=1200, chunk_overlap=150)
                splits = splitter.create_documents([f_content.decode("utf-8")])

            # 2. LATEX SUPPORT
            elif f_ext == ".tex":
                # Specifically looks for \section, \begin{itemize}, etc.
                splitter = LatexTextSplitter(chunk_size=1000, chunk_overlap=100)
                splits = splitter.create_documents([f_content.decode("utf-8")])

            # 3. MARKDOWN (Structure-Aware)
            elif f_ext == ".md":
                headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
                md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
                # This returns documents with header info in metadata
                splits = md_splitter.split_text(f_content.decode("utf-8"))

            # 4. JSON (Structure-Aware Hierarchical Preservation)
            elif f_ext == ".json":
                import json

                with open(fsave_path, "r") as f:
                    data = json.load(f)
                json_splitter = RecursiveJsonSplitter(max_chunk_size=1000)
                splits = json_splitter.create_documents(texts=[data])

            # 5. PDF
            elif f_ext == ".pdf":
                loader = PyMuPDFLoader(fsave_path)
                docs = loader.load()
                # PDFs are tricky; use recursive but with specific separators
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1200, chunk_overlap=200, separators=["\n\n", "\n", ". ", " ", ""]
                )
                splits = splitter.split_documents(docs)

            # 6. HTML (Structure-Aware)
            elif f_ext == ".html":
                # Split by HTML headers to keep sections together
                headers_to_split_on = [("h1", "Header 1"), ("h2", "Header 2"), ("h3", "Header 3")]
                html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
                splits = html_splitter.split_text_from_file(fsave_path)

            else:
                # Fallback: Semantic Chunking (Optional: requires langchain_experimental)
                # This splits by topic boundaries rather than character count
                loader = TextLoader(fsave_path)
                docs = loader.load()
                # splitter = SemanticChunker(emb, breakpoint_threshold_type="percentile")
                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
                splits = splitter.split_documents(docs)

            # Add Metadata for "Answer-Sufficient" Context
            # We tag each split with the source filename and a unique ID for parent retrieval
            for i, split in enumerate(splits):
                split.metadata.update(
                    {"source": file.filename,
                     "file_type": f_ext,
                     "chunk_id": f"{fmd5}_{i}",
                     "language": CODE_EXT_MAPPING.get(f_ext, "text")}
                )

            # Index in Vector Store
            Chroma.from_documents(
                documents=splits,
                embedding=emb,
                persist_directory=VECTOR_STORE_DIR,
                collection_name="structured_knowledge",
            )
            emb_files.append(file.filename)
        if len(emb_files) > 0:
            response_data["status"] = "success"
            response_data["detail"] = f"uploaded and embedded {len(emb_files)} file(s)."
            if len(emb_files) != len(files):
                response_data["detail"] += f"files {set(f.filename for f in files) - set(emb_files)} were not uploaded"
            response_data["content"] = emb_files
        else:
            response_data["status"] = "failed"
            response_data["detail"] = "uploaded file(s) could not be uploaded or already exist in system"
    except Exception as excep:
        logger.exception("failed to upsert files: %s", excep)
        status_code = status.HTTP_400_BAD_REQUEST if status_code == status.HTTP_200_OK else status_code
        detail = response_data.get("detail", "failed to upload files to server")
        raise HTTPException(status_code=status_code, detail=detail) from excep
    return response_data
