"""
Test mysql api
The mysql server must be running in the appropriate port
"""
from typing import Callable
import pytest
from tests.conftest import MYSQL_TEST_TABLE, MYSQL_TEST_ID
from pymysql.connections import Connection

from app.api.mysql import (
    sep_query_and_params,
    insert_data_into_sql,
    insert_bulk_data_into_sql,
    select_data_from_sql_with_id,
    select_all_data_from_sql,
    delete_data_from_sql_with_id,
    run_sql_script,
    table_exists,
    entries_exist
    )


@pytest.mark.parametrize("query, expected_output", [
    # Testing with integers
    ("SELECT * FROM users WHERE age > 30",
     ("SELECT * FROM users WHERE age > %s", (30,))),
    # Testing with floats
    ("UPDATE products SET price = 19.99 WHERE id = 1",
     ("UPDATE products SET price = %s WHERE id = %s", (19.99, 1))),
    # Testing with strings
    ("INSERT INTO logs (message) VALUES ('Error occurred at 3 PM')",
     ("INSERT INTO logs (message) VALUES (%s)", ("Error occurred at 3 PM",))),
    # Testing with dates
    ("SELECT * FROM events WHERE event_date = '2024-01-01'",
     ("SELECT * FROM events WHERE event_date = %s", ("2024-01-01",))),
    # Complex query with multiple types
    ("SELECT * FROM data WHERE id = 5 AND name = 'John' AND salary > 50000.75 AND birth_date = '1990-05-21'",
     ("SELECT * FROM data WHERE id = %s AND name = %s AND salary > %s AND birth_date = %s", (5, "John", 50000.75, "1990-05-21")))
])
def test_sep_query_and_params(query, expected_output):
    """Test the sep_query_and_params function."""
    result = sep_query_and_params(query)
    assert result == expected_output, f"Failed on query: {query}"


def test_check_table_existence(test_mysql_connec: Connection):
    """Check if the MYSQL_TEST_TABLE table exists"""
    exists = table_exists(test_mysql_connec, MYSQL_TEST_TABLE)
    assert exists is True


@pytest.mark.order(before="test_select_sql")
def test_insert_sql(test_mysql_connec: Connection, gen_mock_anomaly_det_log_data: Callable):
    """Inserts test data into MySQL database."""
    resp = insert_data_into_sql(
        test_mysql_connec, MYSQL_TEST_TABLE, gen_mock_anomaly_det_log_data(MYSQL_TEST_ID))

    assert resp == {"status": "success",
                    "message": "record inserted into mysql db"}


@pytest.mark.order(before="test_delete_sql")
def test_select_sql(test_mysql_connec: Connection, gen_mock_anomaly_det_log_data: Callable):
    """Selects test` data from MySQL database."""
    resp = select_data_from_sql_with_id(
        test_mysql_connec, MYSQL_TEST_TABLE, MYSQL_TEST_ID)
    assert resp == {"status": "success",
                    "message": f"record matching id: {MYSQL_TEST_ID} retrieved from mysql db",
                    "data": gen_mock_anomaly_det_log_data(MYSQL_TEST_ID)}


@pytest.mark.order(before="test_delete_sql")
def test_select_all_sql(test_mysql_connec, gen_mock_anomaly_det_log_data):
    """Selects test data from MySQL database."""
    resp = select_all_data_from_sql(
        test_mysql_connec, MYSQL_TEST_TABLE)
    assert resp == {"status": "success",
                    "message": "All records retrieved from mysql db",
                    "data": [gen_mock_anomaly_det_log_data(MYSQL_TEST_ID)]}


def test_delete_mysql(test_mysql_connec: Connection):
    """Deletes test data from MySQL database."""
    resp = delete_data_from_sql_with_id(
        test_mysql_connec, MYSQL_TEST_TABLE, MYSQL_TEST_ID)
    assert resp == {"status": "success",
                    "message": "record deleted from mysql db"}


def test_insert_bulk_data_into_sql(test_mysql_connec: Connection, gen_mock_anomaly_det_log_data: Callable):
    """Test bulk insert data"""
    bulk_data = [
        gen_mock_anomaly_det_log_data(MYSQL_TEST_ID - 1),
        gen_mock_anomaly_det_log_data(MYSQL_TEST_ID - 2),
        gen_mock_anomaly_det_log_data(MYSQL_TEST_ID - 3),
    ]
    response = insert_bulk_data_into_sql(test_mysql_connec, MYSQL_TEST_TABLE, bulk_data)
    assert response["status"] == "success"
    assert "Bulk records inserted into mysql db" in response["message"]


@pytest.mark.order(after="test_delete_mysql")
@pytest.mark.order(after="test_insert_bulk_data_into_sql")
@pytest.mark.parametrize("test_input,expected", [
    ({"ID": MYSQL_TEST_ID}, False),  # After deletion test, must be False
    ({"ID": MYSQL_TEST_ID - 1}, True)    # ID - 1 was bulk inserted & not deleted, must be True
])
def test_entry_existence(test_mysql_connec: Connection, test_input: dict, expected: bool):
    """Test for specific entries existence"""
    assert entries_exist(test_mysql_connec, MYSQL_TEST_TABLE, test_input) == expected


@pytest.mark.order(after="test_insert_bulk_data_into_sql")
def test_select_all_data_from_table_after_bulk_insert(test_mysql_connec: Connection):
    """Retrieve all data after bulk insertion"""
    response = select_all_data_from_sql(test_mysql_connec, MYSQL_TEST_TABLE)
    assert response["status"] == "success"
    assert len(response["data"]) >= 3  # Expect at least three records from the bulk insert


@pytest.mark.order(after="test_insert_bulk_data_into_sql")
def test_run_update_sql_script(test_mysql_connec: Connection):
    """Update a record and check the changes"""
    update_script = f"UPDATE {MYSQL_TEST_TABLE} SET prediction = %s WHERE ID = %s"
    params = (100, MYSQL_TEST_ID - 1)  # Change prediction for ID MYSQL_TEST_ID - 1
    response = run_sql_script(test_mysql_connec, update_script, params)
    assert response["status"] == "success"
    assert "SQL script executed and committed successfully" in response["message"]


@pytest.mark.order(after="test_run_update_sql_script")
def test_run_select_sql_script_after_update(test_mysql_connec: Connection):
    """Test running a select SQL script after updates to id hav been made"""
    resp1 = select_data_from_sql_with_id(
        test_mysql_connec, MYSQL_TEST_TABLE, MYSQL_TEST_ID - 1)

    update_script = f"SELECT * FROM {MYSQL_TEST_TABLE} WHERE ID = %s"
    params = (MYSQL_TEST_ID - 1,)
    resp2 = run_sql_script(test_mysql_connec, update_script, params, commit=False)

    assert sorted(resp1) == sorted(resp2)
