"""
Setup connections
"""
from typing import Callable
import pymysql
from pymysql.cursors import DictCursor
from models.model import LogFileType, LogText2SQLConfig
from core.config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER,
    MYSQL_PASSWORD, MYSQL_DATABASE)
from contextlib import contextmanager


def get_mysql_connection() -> pymysql.connections.Connection:
    """Return mysql connec object"""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        db=MYSQL_DATABASE,
        cursorclass=DictCursor)


@contextmanager
def mysql_conn() -> Callable:
    """Yield mysql connection obj"""
    conn = get_mysql_connection()
    try:
        yield conn
    finally:
        conn.close()


######################################################################
#### Configuration and helpful templates for the text2sql agent. #####
############# Should be based on the log file type ###################
######################################################################



class ANOMALY_DETECTION_LOG_TEXT2SQL_CFG(LogText2SQLConfig):
    """
    anomaly_detection_log text to sql config
    """

    table_name = "anomaly_detection_log"
    table_schema = str(["ID", "log_fid", "timestamp", "inference_time", "prediction"])
    table_examples = '''[
        (1, '1bd5f7de3578d0ecc13de276ea4a16d7', 2024-08-21, 176.04, 0),
        (2, '1bd5f7de3578d0ecc13de276ea4a16d7', 2024-08-21, 90.99, 0),
        (3, '1bd5f7de3578d0ecc13de276ea4a16d7', 2024-08-21, 53.99, 0),
        (4, '1bd5f7de3578d0ecc13de276ea4a16d7', 2024-08-21, 44.56, 0),
        (5, '1bd5f7de3578d0ecc13de276ea4a16d7', 2024-08-21, 49.74, 0)]
    '''
    table_info = table_schema + '\nExamples of entries:\n' + table_examples
    top_k = 5

    # Definition of the running logic of the tool
    sql_prompt_template = """You are a mariadb MySQL expert.
    Given an input question, create a syntactically correct MySQL query to run with pymysql. The database contains only one table, called '{table_name}'.
    Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MySQL.
    Order the results to return the most informative data in the database.
    Never query for all columns from a table. You must query only the columns that are needed to answer the question.
    Pay attention to use only the column names you can see in the table below. Be careful to not query for columns that do not exist.
    Pay attention to use CURRENT_DATE function to get the current date, if the question involves "today".

    Only use the following table:
    {table_info}

    The table describes anomaly detection logs in a drone. The fields are:
    - ID INT NOT NULL AUTO_INCREMENT, # PRIMARY KEY that autoincrements
    - log_fid VARCHAR(32) NOT NULL # log file id which is the md5 hash of the log file
    - timestamp DATE NOT NULL # timestamp of the log
    - inference_time FLOAT NOT NULL # inference time of the anomaly detection model
    - prediction INT NOT NULL # prediction status of the anomaly detection model

    Here are some examples of questions that you may get:
    1. What are the recent anomaly predictions?
    2. How many anomalies were detected today?
    3. What are the top 5 longest inference times recorded?
    4. Are there any anomalies detected on a specific date, e.g., 2023-01-15?
    5. What is the average inference time for anomalies detected this month?
    """


TEXT2SQL_CFG_DICT = {
    LogFileType.ANOMALY_DETECTION_LOG.value: ANOMALY_DETECTION_LOG_TEXT2SQL_CFG
}
