"""
pymysql api functions
"""

from typing import List, Tuple, Sequence
import re
import logging
import pymysql

logger = logging.getLogger("mysql_api")

READ_ONLY_SQL_PREFIXES = ("SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN")
ALWAYS_BLOCKED_SQL_TOKENS = ("DROP", "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE", "LOCK", "UNLOCK",)


def sep_query_and_params(query: str) -> Tuple[str, Tuple]:
    """
    Prepare a SQL query by replacing numeric and string values with '%s'.
    Correctly handles integers, floating-point numbers, strings in single quotes, and date formats.
    This version ensures that full strings within quotes are not parsed or altered,
    which prevents incorrect separations of literal strings.
    """
    # Regular expression to match floating point numbers, integers, quoted strings, and dates
    # Also ignores the interiors of quoted strings
    pattern = re.compile(r"'\d{4}-\d{2}-\d{2}'|'\d+\.\d+'|'\d+'|'.+?'|\d+\.\d+|\d+")

    def replace_with_placeholder(match):
        value = match.group(0)
        # Handling for quoted strings and numbers
        if value.startswith("'") and value.endswith("'"):
            converted_value = value[1:-1]  # Remove the surrounding quotes
        else:
            try:
                converted_value = float(value) if "." in value else int(value)
            except ValueError:
                converted_value = value  # Leave as is if it's not a recognized numeric format
        params.append(converted_value)
        return "%s"

    params = []
    query_with_placeholders = pattern.sub(replace_with_placeholder, query)
    return query_with_placeholders, tuple(params)


def _split_sql_statements(sql_script: str) -> List[str]:
    """Split SQL script into statements while respecting quoted strings."""
    statements = []
    current = []
    in_single_quote = False
    in_double_quote = False

    for ch in sql_script:
        if ch == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        if ch == ";" and not in_single_quote and not in_double_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            continue
        current.append(ch)

    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)
    return statements


def validate_sql_script(sql_script: str, allow_write: bool = False) -> tuple[bool, str]:
    """
    Validate a SQL statement.
    - exactly one statement
    - no comment tokens that can hide payloads
    - no always-blocked destructive/admin DDL
    - read-only by default
    """
    script = sql_script.strip()
    if not script:
        return False, "SQL script is empty."
    if "--" in script or "/*" in script or "*/" in script:
        return False, "SQL comments are not allowed."

    statements = _split_sql_statements(script)
    if len(statements) != 1:
        return False, "Only one SQL statement is allowed."
    statement = statements[0]
    upper = statement.upper()

    for token in ALWAYS_BLOCKED_SQL_TOKENS:
        if re.search(rf"\b{token}\b", upper):
            return False, f"SQL command '{token}' is blocked."

    if not allow_write:
        if not upper.startswith(READ_ONLY_SQL_PREFIXES):
            return False, "Only read-only SQL statements are allowed."

    return True, statement


def run_sql_script(
    mysql_conn,
    sql_script: str,
    params: Sequence | None = None,
    commit: bool = False,
    allow_write: bool = False,
) -> dict:
    """
    Execute an arbitrary SQL script with parameter binding.
    sql_script: The SQL script to be executed.
    params: A tuple of optional parameters to be used in the SQL script.
    commit: Indicates whether changes should be committed.

    Example:
        {"query": "UPDATE users SET name = %s, email = %s WHERE id = %s",
        "params": ["Jane Doe", "jane.doe@example.com", 1]}
    """
    is_valid, validation_result = validate_sql_script(sql_script, allow_write=allow_write)
    if not is_valid:
        logger.warning("SQL validation failed: %s", validation_result)
        return {"status": "failed", "message": validation_result}
    safe_sql_script = validation_result

    try:
        with mysql_conn() as conn:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(safe_sql_script, tuple(params))
                else:
                    cursor.execute(safe_sql_script)
                if commit:
                    conn.commit()
                    logger.info("SQL script executed successfully and committed to MySQL database. ✅️")
                    return {
                        "status": "success",
                        "message": "SQL script executed and committed successfully.",
                    }
                results = cursor.fetchall()  # Fetch results from a SELECT query
                logger.info("SQL script executed successfully, fetched results. ✅️")
                return {
                    "status": "success",
                    "message": "SQL script executed successfully, fetched results.",
                    "data": results,
                }
    except pymysql.Error as excep:
        logger.error("%s: SQL script execution failed ❌", excep)
        return {"status": "failed", "message": f"MySQL script execution error: {excep}"}


def insert_bulk_data_into_sql(mysql_conn, tb_name, data_dicts: list, commit: bool = True) -> dict:
    """
    Insert multiple records into a MySQL table with param binding. Efficiently handles bulk inserts.
    Note: the transaction must be committed after if commit is False
    """
    if not data_dicts:
        return {"status": "failed", "message": "No data provided"}

    # Assuming all dictionaries have the same keys,
    # which should be the case for consistent bulk inserts
    col_names = ", ".join(data_dicts[0].keys())
    placeholders = ", ".join(["%s"] * len(data_dicts[0]))
    query = f"INSERT INTO {tb_name} ({col_names}) VALUES ({placeholders})".replace("'", "")

    # Prepare the list of tuples for insertion
    values = [tuple(data_dict.values()) for data_dict in data_dicts]

    try:
        with mysql_conn() as conn:
            with conn.cursor() as cursor:
                logger.info("Attempting to bulk insert %d records into mysql db.", len(values))
                cursor.executemany(query, values)
                if commit:
                    conn.commit()
                    logger.info("%d records bulk inserted into mysql db.✅️", len(values))
                    return {
                        "status": "success",
                        "message": "Bulk records inserted into mysql db",
                    }
                logger.info("Bulk record insertion waiting to be committed to mysql db.🕓")
                return {
                    "status": "success",
                    "message": "Bulk record insertion waiting to be committed to mysql db.",
                }
    except pymysql.Error as excep:
        logger.error("%s: mysql bulk record insertion failed ❌", excep)
        return {
            "status": "failed",
            "message": f"mysql bulk record insertion error: {str(excep)}",
        }


def insert_data_into_sql(mysql_conn, tb_name, data_dict: dict, commit: bool = True) -> dict:
    """
    Insert data_dict into mysql table with param binding
    Note: the transaction must be commited after if commit is False
    """
    # query fmt: `INSERT INTO tb_name (id, col1_name, col2_name) VALUES (%s, %s, %s)`
    col_names = ", ".join(data_dict.keys())
    placeholders = ", ".join(["%s"] * len(data_dict))
    query = f"INSERT INTO {tb_name} ({col_names}) VALUES ({placeholders})".replace("'", "")
    values = tuple(data_dict.values())
    try:
        with mysql_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                if commit:
                    conn.commit()
                    logger.info("record inserted into mysql db.✅️")
                    return {
                        "status": "success",
                        "message": "record inserted into mysql db",
                    }
                logger.info("record insertion waiting to be committed to mysql db.🕓")
                return {
                    "status": "success",
                    "message": "record insertion waiting to be committed to mysql db.",
                }
    except pymysql.Error as excep:
        logger.error("%s: mysql record insertion failed ❌", excep)
        return {"status": "failed", "message": "mysql record insertion error"}


def select_data_from_sql_with_id(mysql_conn, tb_name, data_id: int) -> dict:
    """
    Query mysql db to get the data record using the uniq data_id
    """
    query = f"SELECT * FROM {tb_name} WHERE id = %s"
    values = (data_id,)
    try:
        with mysql_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                data = cursor.fetchone()
                if data is None:
                    logger.warning("mysql record with id: %s does not exist ❌.", data_id)
                    return {
                        "status": "failed",
                        "message": f"mysql record with id: {data_id} does not exist",
                    }
                logger.info("Data with id: %s retrieved from mysql db.✅️", data_id)
                return {
                    "status": "success",
                    "message": f"record matching id: {data_id} retrieved from mysql db",
                    "data": data,
                }
    except pymysql.Error as excep:
        logger.error("%s: mysql record retrieval failed ❌", excep)
        return {"status": "failed", "message": "mysql record retrieval error"}


def select_all_data_from_sql(mysql_conn, tb_name) -> dict:
    """
    Query mysql db to get all data
    """
    query = f"SELECT * FROM {tb_name}"
    try:
        with mysql_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                data = cursor.fetchall()
                if not data:
                    logger.warning("No mysql records were found ❌.")
                    return {
                        "status": "failed",
                        "message": "No mysql records were found.",
                    }
                logger.info("All records retrieved from mysql db.✅️")
                return {
                    "status": "success",
                    "message": "All records retrieved from mysql db",
                    "data": data,
                }
    except pymysql.Error as excep:
        logger.error("%s: mysql record retrieval failed ❌", excep)
        return {"status": "failed", "message": "mysql record retrieval error"}


def delete_data_from_sql_with_id(mysql_conn, tb_name, data_id: int, commit: bool = True) -> dict:
    """
    Delete record from mysql db using the uniq data_id
    """
    select_query = f"SELECT * FROM {tb_name} WHERE id = %s"
    del_query = f"DELETE FROM {tb_name} WHERE id = %s"
    try:
        with mysql_conn() as conn:
            with conn.cursor() as cursor:
                # check if record exists in db or not
                cursor.execute(select_query, (data_id,))
                if not cursor.fetchone():
                    logger.error("Data with id: %s does not exist in mysql db.❌", data_id)
                    return {
                        "status": "failed",
                        "message": f"mysql record with id: {data_id} does not exist in db",
                    }

                cursor.execute(del_query, (data_id,))
                if commit:
                    conn.commit()
                    logger.info("Data with id: %s deleted from mysql db.✅️", data_id)
                    return {
                        "status": "success",
                        "message": "record deleted from mysql db",
                    }
                logger.info("record deletion waiting to be commited to mysql db.🕓")
                return {
                    "status": "success",
                    "message": "record deletion waiting to be commited to mysql db.",
                }
    except pymysql.Error as excep:
        logger.error("%s: mysql record deletion failed ❌", excep)
        return {"status": "failed", "message": "mysql record deletion error"}


def table_exists(mysql_conn, tb_name: str) -> bool:
    """Check if table exists in the database"""
    try:
        with mysql_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SHOW TABLES LIKE '{tb_name}'")
                result = cursor.fetchone()
                return result is not None
    except pymysql.MySQLError as e:
        logger.error("Error checking if table exists: %s", e)
        return False


def entries_exist(mysql_conn, tb_name: str, conditions: dict, logic: str = "AND") -> bool:
    """
    CHeck if entries exist in a table
    Example use:
        table_name = 'table_name'
        conditions = {
            "col1": 123,  # Column 'col1' should equal 123
            "col2": 456   # Column 'col2' should equal 456
        }
        Choose 'AND' or 'OR' based on how to combine the conditions
    """
    try:
        assert logic in {"AND", "OR"}
        with mysql_conn() as conn:
            with conn.cursor() as cursor:
                # Construct the WHERE clause dynamically based on provided conditions and logic
                clause = f" {logic} ".join([f"{column} = %s" for column in conditions.keys()])
                query = f"SELECT 1 FROM `{tb_name}` WHERE {clause} LIMIT 1"
                # Extract values for the SQL query parameters
                values = tuple(value for value in conditions.values())
                cursor.execute(query, values)
                result = cursor.fetchone()
                return result is not None
    except pymysql.MySQLError as e:
        logger.error("Error checking if entries exist: %s", e)
        return False
