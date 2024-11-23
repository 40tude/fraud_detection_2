import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from typing import Generator
from confluent_kafka import Consumer
from sqlalchemy.engine import Engine
from confluent_kafka import KafkaException
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.logger_04 import (
    create_SQL_engine,
    check_table_exist,
    create_table,
    insert_observation,
    read_transaction_from_topic_2,
    topic_to_sql,
    # create_topic_consumer,
)


# -----------------------------------------------------------------------------
# Fixture to mock the SQL engine
@pytest.fixture
def mock_engine() -> Generator[MagicMock, None, None]:
    with patch("app.logger_04.create_engine") as mock_engine:
        yield mock_engine.return_value


# -----------------------------------------------------------------------------
# Fixture to mock the Kafka consumer
@pytest.fixture
def mock_consumer() -> Generator[MagicMock, None, None]:
    with patch("app.logger_04.Consumer") as mock_consumer:
        yield mock_consumer.return_value


# -----------------------------------------------------------------------------
# Test to check if `check_table_exist` correctly detects existing or non-existing tables
def test_check_table_exist(mock_engine: MagicMock) -> None:
    # Mocking the inspector to simulate SQLAlchemy's table inspection behavior
    with patch("app.logger_04.inspect") as mock_inspect:
        mock_inspector = MagicMock()
        mock_inspect.return_value = mock_inspector
        mock_inspector.has_table.return_value = True

        # Call the function and assert that it detects the table existence
        assert check_table_exist(mock_engine, "test_table") is True


# -----------------------------------------------------------------------------
# Test to verify that the SQL table is created without errors
def test_create_table(mock_engine: MagicMock) -> None:
    # Mocking the connection for table creation
    mock_conn = mock_engine.connect.return_value.__enter__.return_value
    create_table(mock_engine)
    # Verify that `execute` and `commit` were called for table creation
    mock_conn.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


# -----------------------------------------------------------------------------
# Test inserting a single observation (row) into the SQL table
def test_insert_observation(mock_engine: MagicMock) -> None:
    # Mocking the DataFrame and SQL connection transaction
    test_df = pd.DataFrame({"id": [1], "is_fraud": [True]})
    mock_conn = mock_engine.begin.return_value.__enter__.return_value

    # Test the insertion function
    with patch.object(test_df, "to_sql") as mock_to_sql:
        insert_observation(mock_engine, test_df, "test_table")
        # Verify `to_sql` was called with the transaction connection
        mock_to_sql.assert_called_once_with("test_table", mock_conn, if_exists="append", index=False)


# -----------------------------------------------------------------------------
# Test if ValueError is raised for a DataFrame with more than one row
def test_insert_observation_invalid_df(mock_engine: MagicMock) -> None:
    with pytest.raises(ValueError):
        insert_observation(mock_engine, pd.DataFrame({"id": [1, 2]}), "test_table")


# -----------------------------------------------------------------------------
# Test reading a valid Kafka message and converting it to a DataFrame
def test_read_transaction_from_topic_2_valid_message(mock_consumer: MagicMock) -> None:
    # Mocking a valid Kafka message with a value and no error
    mock_message = MagicMock()
    mock_message.value = lambda: b'[{"is_fraud": true, "id": 1}]'
    mock_message.error = lambda: None  # Simulate no error

    # Configure poll to return the mocked message
    mock_consumer.poll.return_value = mock_message

    # Call the function to read the message and assert DataFrame structure
    df = read_transaction_from_topic_2(mock_consumer)
    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]["is_fraud"] == True


# -----------------------------------------------------------------------------
# Test to verify that KafkaException is raised when there's a consumer error
def test_read_transaction_from_topic_2_kafka_error(mock_consumer: MagicMock) -> None:
    # Mocking a consumer error in the Kafka message
    mock_consumer.poll.return_value = MagicMock(error=lambda: KafkaException("Kafka error"))
    # Assert that KafkaException is raised during function execution
    with pytest.raises(KafkaException):
        read_transaction_from_topic_2(mock_consumer)


# -----------------------------------------------------------------------------
# Test SQL engine creation and verify table creation when it does not exist
def test_create_SQL_engine_table_creation() -> None:
    # Patch engine creation, table check, and table creation functions
    with patch("app.logger_04.create_engine") as mock_create_engine, patch(
        "app.logger_04.check_table_exist", return_value=False
    ), patch("app.logger_04.create_table") as mock_create_table:
        engine = create_SQL_engine()
        # Verify `create_table` was called if the table didn't exist
        mock_create_table.assert_called_once()


# -----------------------------------------------------------------------------
# Test data insertion from Kafka topic to SQL table
def test_topic_to_sql_data_insertion(mock_consumer: MagicMock, mock_engine: MagicMock) -> None:
    # Mocking a valid Kafka message with data and no error
    mock_message = MagicMock()
    mock_message.value = lambda: b'[{"is_fraud": true, "id": 1}]'
    mock_message.error = lambda: None  # Simulate no error

    # Configure `poll` to return the mocked message
    mock_consumer.poll.return_value = mock_message

    # Patch `insert_observation` and `time.sleep` to avoid delays
    with patch("app.logger_04.insert_observation") as mock_insert_observation, patch("time.sleep", return_value=None):

        # Call `topic_to_sql`, expecting a single iteration
        try:
            with patch(
                "app.logger_04.read_transaction_from_topic_2",
                side_effect=[pd.DataFrame([{"is_fraud": True}]), StopIteration],
            ):
                topic_to_sql(mock_consumer, mock_engine)
        except StopIteration:
            pass  # Expected to stop after one iteration

        # Verify `insert_observation` was called once with the correct DataFrame
        mock_insert_observation.assert_called_once()

        # Extract the actual DataFrame passed to `insert_observation`
        actual_df = mock_insert_observation.call_args[0][1]  # Retrieve the DataFrame argument

        # Compare the actual DataFrame with the expected DataFrame for equality
        expected_df = pd.DataFrame([{"is_fraud": True}])
        assert_frame_equal(actual_df, expected_df)
