import pytest
import json
from unittest.mock import mock_open, patch
from src.config_manager import ConfigManager

@pytest.fixture
def mock_config_data():
    """Provides a sample config structure for testing."""
    return {
        "secret_code_map": {
            "#s1": "Group_A",
            "#s2": "Group_B"
        },
        "line_user_map": {
            "U12345": "Alice"
        },
        "admins": ["U_admin_1", "U_admin_2"]
    }

def test_get_group_from_secret_code(mock_config_data):
    """Tests that we can retrieve a group name from a valid secret code."""
    config_manager = ConfigManager(mock_config_data)
    group = config_manager.get_group_from_secret_code("#s1")
    assert group == "Group_A"

def test_get_group_from_invalid_secret_code(mock_config_data):
    """Tests that None is returned for a non-existent secret code."""
    config_manager = ConfigManager(mock_config_data)
    group = config_manager.get_group_from_secret_code("#invalid")
    assert group is None

def test_get_app_user(mock_config_data):
    """Tests that we can retrieve an application user name from a LINE User ID."""
    config_manager = ConfigManager(mock_config_data)
    user = config_manager.get_app_user("U12345")
    assert user == "Alice"

def test_get_app_user_for_unknown_user(mock_config_data):
    """Tests that None is returned for an unknown LINE User ID."""
    config_manager = ConfigManager(mock_config_data)
    user = config_manager.get_app_user("U_unknown")
    assert user is None

# --- NEW TESTS ---

def test_is_admin(mock_config_data):
    """Tests that the admin check correctly identifies an admin user."""
    config_manager = ConfigManager(mock_config_data)
    assert config_manager.is_admin("U_admin_1") is True
    assert config_manager.is_admin("U_admin_2") is True

def test_is_not_admin(mock_config_data):
    """Tests that the admin check correctly identifies a non-admin user."""
    config_manager = ConfigManager(mock_config_data)
    assert config_manager.is_admin("U12345") is False
    assert config_manager.is_admin("U_unknown") is False

def test_add_secret_code(mock_config_data):
    """Tests that a new secret code can be added to the config."""
    config_manager = ConfigManager(mock_config_data)
    config_manager.add_secret_code("#s3", "Group_C")
    assert config_manager.get_group_from_secret_code("#s3") == "Group_C"

def test_remove_secret_code(mock_config_data):
    """Tests that an existing secret code can be removed."""
    config_manager = ConfigManager(mock_config_data)
    # Ensure it exists first
    assert config_manager.get_group_from_secret_code("#s2") == "Group_B"
    # Remove it
    config_manager.remove_secret_code("#s2")
    # Assert it's gone
    assert config_manager.get_group_from_secret_code("#s2") is None

def test_save_config(mock_config_data):
    """
    Tests that the save method writes the current config state to a file.
    We use a mock file to prevent actual file I/O during the test.
    """
    config_manager = ConfigManager(mock_config_data)
    config_manager.add_secret_code("#s_new", "Group_New") # Modify the data

    # Use patch to mock the 'open' function and 'json.dump'
    m = mock_open()
    with patch('builtins.open', m):
        with patch('json.dump') as mock_json_dump:
            config_manager.save_config("dummy/path/config.json")

            # Assert that open was called correctly
            m.assert_called_once_with("dummy/path/config.json", 'w')

            # Assert that json.dump was called with the updated data
            # The first argument of the first call to mock_json_dump
            args, _ = mock_json_dump.call_args
            written_data = args[0]
            assert written_data["secret_code_map"]["#s_new"] == "Group_New"