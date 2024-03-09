import signal
from datetime import datetime
from unittest.mock import patch, Mock, call

import pytest

from app.main import clean_from_database, do_cleanup, main, check_connection
from app.settings import (
    TARGET_COLLECTION,
    METADATA_COLLECTION,
    ID_CRITERIA,
    EXPIRATION_CRITERIA
)


@pytest.mark.parametrize(
    "find_objects,remove_calls,remove_batch_size",
    [
        (
            [{ID_CRITERIA: 0}, {ID_CRITERIA: 1}],
            [{ID_CRITERIA: {"$in": [0]}}, {ID_CRITERIA: {"$in": [1]}}],
            1,
        ),
        (
            [{ID_CRITERIA: 0},
             {ID_CRITERIA: 1},
             {ID_CRITERIA: 2},
             {ID_CRITERIA: 3},
             {ID_CRITERIA: 4}],
            [{ID_CRITERIA: {"$in": [0, 1]}},
             {ID_CRITERIA: {"$in": [2, 3]}},
             {ID_CRITERIA: {"$in": [4]}}],
            2,
        )
    ],
)
def test_clean_database_files(find_objects, remove_calls, remove_batch_size):
    database = {}
    target_collection = Mock()
    database[TARGET_COLLECTION] = target_collection
    metadata_collection = Mock()
    database[METADATA_COLLECTION] = metadata_collection
    metadata_collection.find.return_value = find_objects
    call_index_mock = Mock()
    call_index_mock.value = 0

    def get_args_on_delete(filter_query):
        mock = None
        index = call_index_mock.value // 2
        if index < len(remove_calls):
            deleted = len(remove_calls[index][ID_CRITERIA]["$in"])
            mock = Mock()
            mock.deleted_count = deleted
        call_index_mock.value += 1

        return mock

    metadata_collection.delete_many.side_effect = get_args_on_delete
    target_collection.delete_many.side_effect = get_args_on_delete

    settings_mock = Mock()
    settings_mock.cleanup.remove_batch_size = remove_batch_size

    now_datetime = datetime.now()
    with patch("app.main.datetime") as datetime_mock:
        datetime_mock.now.return_value = now_datetime

        clean_from_database(database, settings_mock)

    metadata_collection.find.assert_called_once_with(
        {EXPIRATION_CRITERIA: {"$lte": now_datetime.timestamp()}},
        projection={ID_CRITERIA: 1}
    )
    assert target_collection.delete_many.call_args_list == [
        call(args) for args in remove_calls
    ]
    assert metadata_collection.delete_many.call_args_list == [
        call(args) for args in remove_calls
    ]


def test_clean_database_files_with_error():
    database = {}
    target_collection = Mock()
    database[TARGET_COLLECTION] = target_collection
    metadata_collection = Mock()
    database[METADATA_COLLECTION] = metadata_collection

    def raise_db_error(*args, **kwargs):
        raise Exception("Unexpected error")

    metadata_collection.find.side_effect = raise_db_error
    metadata_collection.delete_many.side_effect = raise_db_error
    target_collection.delete_many.side_effect = raise_db_error

    clean_from_database(database, Mock())

    metadata_collection.find.assert_called_once()
    target_collection.delete_many.assert_not_called()
    target_collection.delete_many.assert_not_called()


def test_clean_files_periodically():
    def handler(signum, frame):
        raise TimeoutError("Function execution timed out")

    signal.signal(signal.SIGALRM, handler)
    db_mock = Mock()
    settings_mock = Mock()
    settings_mock.cleanup.seconds_period = 0.09

    with patch("app.main.clean_from_database") as clean_mock:
        signal.alarm(1)
        try:
            do_cleanup(db_mock, settings_mock)
        except Exception:
            pass
        finally:
            assert clean_mock.call_count > 10


def test_check_database_connection_success():
    db_client = Mock()
    db_client.server_info.return_value = None

    try:
        check_connection(db_client)
    except Exception:
        pytest.fail()


def test_check_database_connection_unavailable():
    db_client = Mock()

    def raise_db_unavailable_error():
        raise Exception("Database unavailable")

    db_client.server_info.side_effect = raise_db_unavailable_error

    with pytest.raises(Exception):
        check_connection(db_client)


@pytest.mark.usefixtures("make_database_available", "use_test_config_file")
def test_start_service_success():
    with patch("app.main.do_cleanup"):
        main()
