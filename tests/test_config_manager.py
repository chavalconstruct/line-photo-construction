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
        # "line_user_map" has been removed
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

# REMOVED: test_get_app_user
# REMOVED: test_get_app_user_for_unknown_user

def test_is_admin(mock_config_data):
    """Tests that the admin check correctly identifies an admin user."""
    config_manager = ConfigManager(mock_config_data)
    assert config_manager.is_admin("U_admin_1") is True
    assert config_manager.is_admin("U_admin_2") is True

def test_is_not_admin(mock_config_data):
    """Tests that the admin check correctly identifies a non-admin user."""
    config_manager = ConfigManager(mock_config_data)
    # A user not in the admin list
    assert config_manager.is_admin("U12345") is False
    assert config_manager.is_admin("U_unknown") is False

def test_add_secret_code(mock_config_data):
    """Tests that a new secret code can be added to the config."""
    config_manager = ConfigManager(mock_config_data)
    config_manager.add_secret_code("#s3", "Group_C")
    assert config_manager.get_group_from_secret_code("#s3") == "Group_C"

def test_remove_secret_code_returns_true_on_success(mock_config_data):
    """Tests that remove_secret_code returns True when a code is removed."""
    config_manager = ConfigManager(mock_config_data)
    assert config_manager.get_group_from_secret_code("#s2") == "Group_B"
    result = config_manager.remove_secret_code("#s2")
    assert result is True
    assert config_manager.get_group_from_secret_code("#s2") is None

def test_remove_non_existent_code_returns_false(mock_config_data):
    """Tests that remove_secret_code returns False if the code does not exist."""
    config_manager = ConfigManager(mock_config_data)
    result = config_manager.remove_secret_code("#non_existent_code")
    assert result is False

def test_get_all_secret_codes(mock_config_data):
    """Tests that we can retrieve the entire secret code map."""
    config_manager = ConfigManager(mock_config_data)
    all_codes = config_manager.get_all_secret_codes()
    expected_codes = {
        "#s1": "Group_A",
        "#s2": "Group_B"
    }
    assert all_codes == expected_codes

def test_save_config(mock_config_data):
    """
    Tests that the save method writes the current config state to a file.
    """
    config_manager = ConfigManager(mock_config_data)
    config_manager.add_secret_code("#s_new", "Group_New")

    m = mock_open()
    with patch('builtins.open', m):
        with patch('json.dump') as mock_json_dump:
            config_manager.save_config("dummy/path/config.json")

            m.assert_called_once_with("dummy/path/config.json", 'w')
            args, _ = mock_json_dump.call_args
            written_data = args[0]
            assert written_data["secret_code_map"]["#s_new"] == "Group_New"
            # Verify that line_user_map is NOT in the saved data
            assert "line_user_map" not in written_data