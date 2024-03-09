from unittest.mock import patch

import pytest


@pytest.fixture
def make_database_available():
    with patch("app.main.check_connection", return_value=None):
        yield


@pytest.fixture
def use_test_config_file():
    with patch("app.settings.CONFIG_FILE", return_value="tests/config.yaml"):
        yield
