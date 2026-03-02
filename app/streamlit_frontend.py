import requests
import streamlit as st

import app.core.config as cfg
from app.models.model import LogFileType, SummarizerMode, LLMModel
from app.utils.common import parse_num_str

# Base URL for the API
API_URL = f"http://127.0.0.1:{cfg.API_SERVER_PORT}"

# Configuring the sidebar with options
st.sidebar.title("Log Analyzer Services")
option = st.sidebar.radio(
    "Choose a service:",
    (
        "Question Answering",
        "SQL Query Answer",
        "Run SQL Script",
        "Summarize URLs",
        "Summarize Files",
        "Upsert Logs",
        "Upsert Files",
    ),
)


def post_api(endpoint, param_dict):
    """
    Helper function to post data to the API
    """
    response = requests.post(f"{API_URL}/{endpoint}", timeout=120, **param_dict)
    response.raise_for_status()
    return response.json()


# Mapping option to functionality
if option == "Question Answering":
    model = st.selectbox("Select model:", [model.value for model in LLMModel])
    query = st.text_input("Enter your question for RAG retrieval:")

    if st.button("Get Answer"):
        try:
            result = post_api(f"qa?model={model}", {"json": {"query": query}})
            st.write(result)
        except requests.RequestException as excep:
            st.error(str(excep))

elif option == "SQL Query Answer":
    log_type = st.selectbox("Select log type:", [ftype.value for ftype in LogFileType])
    model = st.selectbox("Select model:", [model.value for model in LLMModel])
    query = st.text_input("Enter SQL-related plaintext query (E.g. Give the latest 5 records):")
    if st.button("Get SQL Answer"):
        payload = {"log_type": log_type, "question": query, "model": model}
        try:
            result = post_api("sql/qa", {"json": payload})
            st.write(result)
        except requests.RequestException as excep:
            st.error(str(excep))

elif option == "Run SQL Script":
    sql_query = st.text_area("Enter SQL script with params replaced with %s:")
    sql_params = st.text_area("Enter SQL parameters (comma-separated):")
    sql_params = [parse_num_str(param) for param in sql_params.split(",") if param.strip()]

    request_data = {"query": sql_query, "params": sql_params}
    if st.button("Execute SQL Script"):
        try:
            result = post_api("sql/script", {"json": request_data})
            st.write(result)
        except requests.RequestException as excep:
            st.error(str(excep))

elif option == "Summarize URLs":
    model = st.selectbox("Select model:", [model.value for model in LLMModel])
    urls = st.text_area("Enter URLs separated by comma:")
    urls_list = [url.strip() for url in urls.split(",") if url.strip()]
    if st.button("Summarize URLs"):
        try:
            result = post_api(f"summarize/urls?model={model}", {"json": urls_list})
            st.write(result)
        except requests.RequestException as excep:
            st.error(str(excep))

elif option == "Summarize Files":
    summarize_mode = st.selectbox("Select summarization mode:", [stype.value for stype in SummarizerMode])
    model = st.selectbox("Select model:", [model.value for model in LLMModel])
    uploaded_files = st.file_uploader("Choose files to summarize", accept_multiple_files=True)
    if st.button("Summarize Files"):
        files = [("files", (file.name, file.read(), "text/plain")) for file in uploaded_files]
        try:
            result = post_api(
                f"summarize/files?summarizer_mode={summarize_mode}&model={model}",
                {"files": files},
            )
            st.write(result)
        except requests.RequestException as excep:
            st.error(str(excep))

elif option == "Upsert Logs":
    log_type = st.selectbox("Select log file type:", [ftype.value for ftype in LogFileType])
    log_file_id = st.text_input("Log file ID (group identifier for uploaded log files):")
    uploaded_logs = st.file_uploader("Upload log files", accept_multiple_files=True)
    if st.button("Upload Logs"):
        files = [("files", (log.name, log.read(), "text/plain")) for log in uploaded_logs]
        try:
            result = post_api(
                f"upsert/logs?log_type={log_type}",
                {"files": files, "data": {"log_file_id": log_file_id}},
            )
            st.write(result)
        except requests.RequestException as excep:
            st.error(str(excep))

elif option == "Upsert Files":
    uploaded_files = st.file_uploader("Upload files to upsert", accept_multiple_files=True)
    if st.button("Upsert Files"):
        files = [("files", (file.name, file.read(), "text/plain")) for file in uploaded_files]
        try:
            result = post_api("upsert/files", {"files": files})
            st.write(result)
        except requests.RequestException as excep:
            st.error(str(excep))
