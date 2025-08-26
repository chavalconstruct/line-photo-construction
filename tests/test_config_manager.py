import pytest
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
        }
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