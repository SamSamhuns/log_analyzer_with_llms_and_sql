import requests
import streamlit as st

import core.config as cfg
from models.model import LogFileType, SummarizerMode, LLMModel
from utils.common import parse_num_str

# Base URL for the API
API_URL = f"http://127.0.0.1:{cfg.API_SERVER_PORT}"

# Configuring the sidebar with options
st.sidebar.title("Log Analyzer Services")
option = st.sidebar.radio("Choose a service:", (
    "Question Answering",
    "SQL Query Answer",
    "Run SQL Script",
    "Summarize URLs",
    "Summarize Files",
    "Upsert Logs",
    "Upsert Files"
))


def post_api(endpoint, param_dict):
    """
    Helper function to post data to the API
    """
    response = requests.post(f"{API_URL}/{endpoint}", timeout=120, **param_dict)
    return response.json()


# Mapping option to functionality
if option == "Question Answering":
    model = st.selectbox("Select model:", [model.value for model in LLMModel])
    query = st.text_input("Enter your question for RAG retrieval:")

    request_data = {"query": query}
    if st.button("Get Answer"):
        result = post_api(f"qa?model={model}", {"json": request_data})
        st.write(result)

elif option == "SQL Query Answer":
    log_type = st.selectbox("Select log type:", [ftype.value for ftype in LogFileType])
    model = st.selectbox("Select model:", [model.value for model in LLMModel])
    query = st.text_input("Enter SQL-related plaintext query (E.g. Give the latest 5 records):")
    if st.button("Get SQL Answer"):
        result = post_api(f"sql/qa?log_type={log_type}&model={model}", {"json": {"query": query}})
        st.write(result)

elif option == "Run SQL Script":
    sql_query = st.text_area("Enter SQL script with params replaced with %s:")
    sql_params = st.text_area("Enter SQL parameters (comma-separated):")
    sql_params = [parse_num_str(param) for param in sql_params.split(',')]

    request_data = {"query": sql_query, "params": sql_params}
    if st.button("Execute SQL Script"):
        result = post_api("sql/script", {"json": request_data})
        st.write(result)

elif option == "Summarize URLs":
    model = st.selectbox("Select model:", [model.value for model in LLMModel])
    urls = st.text_area("Enter URLs separated by comma:")
    urls_list = urls.split(',')
    if st.button("Summarize URLs"):
        result = post_api(f"summarize/urls?model={model}", {"json": urls_list})
        st.write(result)

elif option == "Summarize Files":
    summarize_mode = st.selectbox("Select summarization mode:", [stype.value for stype in SummarizerMode])
    model = st.selectbox("Select model:", [model.value for model in LLMModel])
    uploaded_files = st.file_uploader("Choose files to summarize", accept_multiple_files=True)
    if st.button("Summarize Files"):
        files = [("files", (file.name, file.read(), "text/plain")) for file in uploaded_files]
        result = post_api(f"summarize/files?summarizer_mode={summarize_mode}&model={model}", {"files": files})
        st.write(result)

elif option == "Upsert Logs":
    log_type = st.selectbox("Select log file type:", [ftype.value for ftype in LogFileType])
    uploaded_logs = st.file_uploader("Upload log files", accept_multiple_files=True)
    if st.button("Upload Logs"):
        files = [("files", (log.name, log.read(), "text/plain")) for log in uploaded_logs]
        result = post_api(f"upsert/logs?log_type={log_type}", {"files": files})
        st.write(result)

elif option == "Upsert Files":
    uploaded_files = st.file_uploader("Upload files to upsert", accept_multiple_files=True)
    if st.button("Upsert Files"):
        files = [("files", (file.name, file.read(), "text/plain")) for file in uploaded_files]
        result = post_api("upsert/files", {"files": files})
        st.write(result)
