"""
Upsert file api
"""
import os
import os.path as osp
import json
import uuid
import logging
import traceback
from typing import List, Dict
from datetime import datetime

from fastapi import APIRouter, File, Form, UploadFile, status, HTTPException
from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, JSONLoader, UnstructuredHTMLLoader)
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from api.langchain_custom.stream_document_loader import CustomStreamDocumentLoader
from api.mysql import entries_exist, insert_data_into_sql, insert_bulk_data_into_sql
from api.log_format.log_parser import gen_log_obj_list
from models.model import LogFileType
from utils.common import get_file_md5
from core.setup import mysql_conn
from core.config import (
    FILE_STORAGE_DIR, VECTOR_STORE_DIR,
    MYSQL_LOG_ID_TB_NAME, MYSQL_GENERAL_ID_TB_NAME)


SUPPORTED_FILES_EXT = {".txt", ".pdf", ".html", ".json"}
router = APIRouter()
logger = logging.getLogger('upsert_route')


@router.post("/logs", response_model=Dict,
             status_code=status.HTTP_200_OK,
             summary="Extract info from log files and store them in a sql database")
async def log_upsert(
        log_type: LogFileType,
        log_file_id: str = Form(...),
        files: List[UploadFile] = File(...)):
    """
    Extract info from log file(s) and store them in a sql database.
    log_file_id should be unique string identifier for log files 
    """
    status_code = status.HTTP_200_OK
    logfile_type = log_type.value
    response_data = {}
    logged_files = []
    try:
        for file in files:
            f_content = file.file.read()
            f_name = file.filename

            # check if file alr exists in the db using md5sum
            fmd5 = get_file_md5(f_content)
            if entries_exist(mysql_conn, MYSQL_LOG_ID_TB_NAME, {"file_md5": fmd5, "logfile_type": logfile_type}):
                logger.info("%s already stored and indexed in db. Skipping", f_name)
                continue

            # insert log file entry into log_fid table if it didn't exist
            log_fid_obj = {"log_fid": log_file_id,
                           "file_md5": fmd5,
                           "inserted_date": datetime.now().strftime('%Y-%m-%d'),
                           "logfile_type": logfile_type,
                           "size": len(f_content) / 1024}  # size in KB
            insert_data_into_sql(mysql_conn, tb_name=MYSQL_LOG_ID_TB_NAME, data_dict=log_fid_obj)

            # decode txt file contents
            enc = json.detect_encoding(f_content)
            file_content_str = f_content.decode(enc)
            # get log object list from file contents using the appropriate logfile_type format
            log_obj_list = gen_log_obj_list(file_content_str, logfile_id=log_file_id, logfile_type=logfile_type)
            # insert contents of logfile into logfile_type table
            insertion_status = insert_bulk_data_into_sql(mysql_conn, tb_name=logfile_type, data_dicts=log_obj_list)
            if insertion_status["status"] == "failed":
                raise Exception(insertion_status["message"])

            logged_files.append(f_name)
        if len(logged_files) > 0:
            response_data["status"] = "success"
            response_data["detail"] = f"uploaded and upserted {len(log_obj_list)} entries " + \
                f"from {len(files)} file(s) into the sql table."
            if len(logged_files) != len(files):
                response_data["detail"] += \
                    f"files {set(f.filename for f in files) - set(logged_files)} were not uploaded"
            response_data["content"] = logged_files
        else:
            response_data["status"] = "failed"
            response_data["detail"] = "uploaded file(s) could not be uploaded or already exist in system"
    except Exception as excep:
        logger.error("%s: %s", excep, traceback.print_exc())
        status_code = status.HTTP_400_BAD_REQUEST if status_code == status.HTTP_200_OK else status_code
        detail = response_data.get("detail", "failed to upload files to server")
        raise HTTPException(status_code=status_code, detail=detail) from excep
    return response_data


@router.post("/files", response_model=Dict,
             status_code=status.HTTP_200_OK,
             summary="Extract text from file(s) & save emb in a vector db")
async def file_upsert(
        files: List[UploadFile] = File(...)):
    """
    Extract text from file(s) & save emb in a vector db
    """
    status_code = status.HTTP_200_OK
    response_data = {}
    emb_files = []
    try:
        for file in files:
            file_ext = os.path.splitext(file.filename)[1]
            if file_ext not in SUPPORTED_FILES_EXT:
                response_data["detail"] = \
                    f"Only files with extensions {SUPPORTED_FILES_EXT} supported. {file.filename} is invalid"
                raise ValueError(response_data["detail"])

            f_content = file.file.read()
            f_name = file.filename
            fmd5 = get_file_md5(f_content)
            if entries_exist(mysql_conn, MYSQL_GENERAL_ID_TB_NAME, {"file_md5": fmd5}):
                logger.info("%s already stored and indexed in db. Skipping", f_name)
                continue

            # insert log file entry into log_fid table if it didn't exist
            fid_obj = {"file_md5": fmd5,
                       "inserted_date": datetime.now().strftime('%Y-%m-%d'),
                       "file_type": file_ext,
                       "size": len(f_content) / 1024}  # size in KB
            insert_data_into_sql(mysql_conn, tb_name=MYSQL_GENERAL_ID_TB_NAME, data_dict=fid_obj)

            doc_id = str(uuid.uuid4())
            fsave_path = osp.join(FILE_STORAGE_DIR, doc_id + osp.splitext(f_name)[-1])
            with open(fsave_path, 'wb') as f_write:
                f_write.write(f_content)

            f_ext = osp.splitext(f_name)[-1]
            if f_ext == ".pdf":
                loader = PyPDFLoader(fsave_path)
            elif f_ext in {".txt"}:
                loader = TextLoader(fsave_path)
            elif f_ext == ".json":
                loader = JSONLoader(fsave_path, jq_schema=".[]")
            elif f_ext == ".html":
                loader = UnstructuredHTMLLoader(fsave_path)
            else:
                loader = CustomStreamDocumentLoader(f_content)

            docs = loader.load()
            # visualizing chunking https://chunkviz.up.railway.app/
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(docs)

            # index doc in vector store
            Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings(),
                                  persist_directory=VECTOR_STORE_DIR)
            emb_files.append(f_name)
        if len(emb_files) > 0:
            response_data["status"] = "success"
            response_data["detail"] = f"uploaded and embedded {len(emb_files)} file(s)."
            if len(emb_files) != len(files):
                response_data["detail"] += \
                    f"files {set(f.filename for f in files) - set(emb_files)} were not uploaded"
            response_data["content"] = emb_files
        else:
            response_data["status"] = "failed"
            response_data["detail"] = "uploaded file(s) could not be uploaded or already exist in system"
    except Exception as excep:
        logger.error("%s: %s", excep, traceback.print_exc())
        status_code = status.HTTP_400_BAD_REQUEST if status_code == status.HTTP_200_OK else status_code
        detail = response_data.get("detail", "failed to upload files to server")
        raise HTTPException(status_code=status_code, detail=detail) from excep
    return response_data
