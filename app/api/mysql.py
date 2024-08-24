"""
pymysql api functions
"""
import logging
import pymysql

logger = logging.getLogger('mysql_api')


def insert_data_into_sql(mysql_conn, mysql_tb, data_dict: dict, commit: bool = True) -> dict:
    """
    Insert data_dict into mysql table with param binding
    Note: the transaction must be commited after if commit is False
    """
    # query fmt: `INSERT INTO mysql_tb (id, col1_name, col2_name) VALUES (%s, %s, %s)`
    col_names = ', '.join(data_dict.keys())
    placeholders = ', '.join(['%s'] * len(data_dict))
    query = f"INSERT INTO {mysql_tb} ({col_names}) VALUES ({placeholders})".replace("'", '')
    values = tuple(data_dict.values())
    try:
        with mysql_conn.cursor() as cursor:
            cursor.execute(query, values)
            if commit:
                mysql_conn.commit()
                logger.info("record inserted into mysql db.✅️")
                return {"status": "success",
                        "message": "record inserted into mysql db"}
            logger.info("record insertion waiting to be committed to mysql db.🕓")
            return {"status": "success",
                    "message": "record insertion waiting to be committed to mysql db."}
    except pymysql.Error as excep:
        logger.error("%s: mysql record insertion failed ❌", excep)
        return {"status": "failed",
                "message": "mysql record insertion error"}


def select_data_from_sql_with_id(mysql_conn, mysql_tb, data_id: int) -> dict:
    """
    Query mysql db to get the data record using the uniq data_id
    """
    query = f"SELECT * FROM {mysql_tb} WHERE id = %s"
    values = (data_id,)
    try:
        with mysql_conn.cursor() as cursor:
            cursor.execute(query, values)
            data = cursor.fetchone()
            if data is None:
                logger.warning("mysql record with id: %s does not exist ❌.", data_id)
                return {"status": "failed",
                        "message": "mysql record with id: {data_id} does not exist"}
            logger.info("Data with id: %s retrieved from mysql db.✅️", data_id)
            return {"status": "success",
                    "message": f"record matching id: {data_id} retrieved from mysql db",
                    "data": data}
    except pymysql.Error as excep:
        logger.error("%s: mysql record retrieval failed ❌", excep)
        return {"status": "failed",
                "message": "mysql record retrieval error"}


def select_all_data_from_sql(mysql_conn, mysql_tb) -> dict:
    """
    Query mysql db to get all data
    """
    query = f"SELECT * FROM {mysql_tb}"
    try:
        with mysql_conn.cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()
            if not data:
                logger.warning("No mysql records were found ❌.")
                return {"status": "failed",
                        "message": "No mysql records were found."}
            logger.info("All records retrieved from mysql db.✅️")
            return {"status": "success",
                    "message": "All records retrieved from mysql db",
                    "data": data}
    except pymysql.Error as excep:
        logger.error("%s: mysql record retrieval failed ❌", excep)
        return {"status": "failed",
                "message": "mysql record retrieval error"}


def delete_data_from_sql_with_id(mysql_conn, mysql_tb, data_id: int, commit: bool = True) -> dict:
    """
    Delete record from mysql db using the uniq data_id
    """
    select_query = f"SELECT * FROM {mysql_tb} WHERE id = %s"
    del_query = f"DELETE FROM {mysql_tb} WHERE id = %s"
    try:
        with mysql_conn.cursor() as cursor:
            # check if record exists in db or not
            cursor.execute(select_query, (data_id))
            if not cursor.fetchone():
                logger.error("Data with id: %s does not exist in mysql db.❌", data_id)
                return {"status": "failed",
                        "message": f"mysql record with id: {data_id} does not exist in db"}

            cursor.execute(del_query, (data_id))
            if commit:
                mysql_conn.commit()
                logger.info("Data with id: %s deleted from mysql db.✅️", data_id)
                return {"status": "success",
                        "message": "record deleted from mysql db"}
            logger.info("record deletion waiting to be commited to mysql db.🕓")
            return {"status": "success",
                    "message": "record deletion waiting to be commited to mysql db."}
    except pymysql.Error as excep:
        logger.error("%s: mysql record deletion failed ❌", excep)
        return {"status": "failed",
                "message": "mysql record deletion error"}
