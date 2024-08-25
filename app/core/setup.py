"""
Setup connections
"""
import pymysql
from pymysql.cursors import DictCursor
from core.config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER,
    MYSQL_PASSWORD, MYSQL_DATABASE)


# Connect to MySQL
mysql_conn = pymysql.connect(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    db=MYSQL_DATABASE,
    cursorclass=DictCursor)
